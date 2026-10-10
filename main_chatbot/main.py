import os
import logging
import uvicorn
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from google.adk.a2a.utils.agent_to_a2a import (
    _compat,
    InMemoryTaskStore,
    InMemoryPushNotificationConfigStore,
)

# Configure Vertex AI defaults for Cloud Run
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "TRUE")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", os.environ.get("GOOGLE_CLOUD_PROJECT", "your-project-id"))
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"))
os.environ.setdefault(
    "RECIPE_AGENT_URL",
    os.environ.get("RECIPE_AGENT_URL", "https://recipe-grocery-agent-<PROJECT_HASH>.run.app"),
)
if os.environ.get("K_SERVICE"):
    os.environ.setdefault(
        "SERVICE_URL",
        "https://main-chatbot-agent-<PROJECT_HASH>.run.app",
    )

from agent import MainChatbotAgent
from agent_executor import MainChatbotAgentExecutor
from a2ui_helpers import extract_part_text, extract_part_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = int(os.environ.get("PORT", "8080"))
BASE_URL = os.environ.get("SERVICE_URL", f"http://localhost:{PORT}")

main_agent = MainChatbotAgent(base_url=BASE_URL)
agent_executor = MainChatbotAgentExecutor(main_agent)
task_store = InMemoryTaskStore()
push_store = InMemoryPushNotificationConfigStore()

app = FastAPI(
    title="Gemini Enterprise Main Chatbot (Google Drive Recipe Catalog & FreshMarket Grocery A2A)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "main-chatbot-agent",
        "a2a_recipe_agent_url": os.environ.get("RECIPE_AGENT_URL"),
    }


def _serialize_card(card, req: Request):
    if hasattr(card, "model_dump"):
        d = card.model_dump(exclude_none=True)
    else:
        from google.protobuf.json_format import MessageToDict
        d = MessageToDict(card)
    # Determine public HTTPS base URL from request headers or env
    host = req.headers.get("x-forwarded-host") or req.headers.get("host") or "localhost:8080"
    proto = req.headers.get("x-forwarded-proto", "https" if "run.app" in host else "http")
    public_base = os.environ.get("SERVICE_URL") or f"{proto}://{host}"
    endpoint_url = f"{public_base.rstrip('/')}/a2a/app"
    d["url"] = endpoint_url
    d["protocolVersion"] = d.get("protocolVersion", "0.2.1")
    if "supportedInterfaces" in d:
        for iface in d["supportedInterfaces"]:
            iface["url"] = endpoint_url
    return d


@app.get("/.well-known/agent-card.json")
def get_root_agent_card(req: Request):
    return _serialize_card(main_agent.agent_card, req)


@app.get("/a2a/app/.well-known/agent-card.json")
def get_sub_agent_card(req: Request):
    return _serialize_card(main_agent.agent_card, req)


@app.post("/api/chat")
async def chat_endpoint(req: Request):
    body = await req.json()
    query = body.get("query", "What recipes do you have in Google Drive?")
    session_id = body.get("session_id", "default_session")
    parts = await main_agent.run_and_get_parts(query, session_id)

    text_out = []
    a2ui_out = []
    for p in parts:
        txt = extract_part_text(p)
        if txt:
            text_out.append(txt)
        else:
            data = extract_part_data(p)
            if data:
                a2ui_out.append(data)

    return JSONResponse({
        "text": "\n".join(text_out),
        "a2ui_messages": a2ui_out,
        "parts_count": len(parts),
    })


# Attach A2A routes at both /a2a/app and root / using ADK's version-compatible helper
_compat.attach_a2a_routes_to_app(
    app,
    agent_card=main_agent.agent_card,
    agent_executor=agent_executor,
    task_store=task_store,
    push_config_store=push_store,
    prefix="/a2a/app",
)
_compat.attach_a2a_routes_to_app(
    app,
    agent_card=main_agent.agent_card,
    agent_executor=agent_executor,
    task_store=task_store,
    push_config_store=push_store,
    prefix="",
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
