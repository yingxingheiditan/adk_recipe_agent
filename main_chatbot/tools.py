import os
import uuid
import json
import urllib.request
from typing import Dict, Any, Optional, List
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from google.adk.tools.tool_context import ToolContext
except ImportError:
    ToolContext = Any
from a2ui_builder import build_recipe_catalog_a2ui

RECIPE_AGENT_URL = os.environ.get(
    "RECIPE_AGENT_URL",
    "https://recipe-grocery-agent-<PROJECT_HASH>.run.app",
)

CACHE_FILE = os.path.join(os.path.dirname(__file__), "recipes_cache.json")


def _get_id_token(audience: str) -> Optional[str]:
    """Fetches Google Cloud ID token for Cloud Run service-to-service A2A auth."""
    if os.environ.get("K_SERVICE"):
        try:
            import google.auth.transport.requests
            import google.oauth2.id_token
            auth_req = google.auth.transport.requests.Request()
            return google.oauth2.id_token.fetch_id_token(auth_req, audience)
        except Exception:
            pass
    try:
        import subprocess
        return (
            subprocess.check_output(
                ["gcloud", "auth", "print-identity-token"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception:
        try:
            import google.auth.transport.requests
            import google.oauth2.id_token
            auth_req = google.auth.transport.requests.Request()
            return google.oauth2.id_token.fetch_id_token(auth_req, audience)
        except Exception:
            return None


def browse_google_drive_recipes_catalog(
    category: str = "All",
    tool_context: Optional[ToolContext] = None,
) -> dict:
    """Displays an interactive A2UI Recipe Catalog Grid with Category Filter Bar (All Categories, Appetisers, Mains, Desserts). Each recipe card includes key ingredients with an inline client-side MaterialExpansionPanel accordion for >5 ingredients, a direct link button to open the Google Drive document ('View Recipe Doc'), and an action button to call the Custom ADK Grocery Agent to view ingredients & FreshMarket grocery shopping cards."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            all_recipes = json.load(f)
    else:
        all_recipes = []

    norm_category = (category or "All").strip()
    if norm_category.lower() in ("all", "all categories", "all recipes", "all dishes", ""):
        filtered_recipes = all_recipes
        selected_category = "All"
    else:
        filtered_recipes = [
            r for r in all_recipes
            if r.get("category", "").lower() == norm_category.lower()
            or norm_category.lower() in r.get("category", "").lower()
        ]
        selected_category = norm_category

    a2ui_messages = build_recipe_catalog_a2ui(
        filtered_recipes,
        selected_category=selected_category,
    )
    if tool_context and hasattr(tool_context, "state"):
        tool_context.state["latest_a2ui_messages"] = a2ui_messages

    return {
        "status": "success",
        "message": f"Generated interactive A2UI Recipe Catalog Grid for {len(filtered_recipes)} recipes (category: {selected_category}).",
        "recipes_count": len(filtered_recipes),
        "selected_category": selected_category,
        "ui_note": "All filtered recipes with key ingredients, client-side accordion for full ingredients, Google Doc links, and FreshMarket grocery action buttons are rendered in the interactive A2UI cards below.",
    }


def _extract_parts_from_a2a_result(result_obj: Dict[str, Any]) -> tuple[List[str], List[Dict[str, Any]]]:
    """Extracts text strings and A2UI data dicts from an A2A JSON-RPC Task or Message result."""
    texts: List[str] = []
    a2ui_msgs: List[Dict[str, Any]] = []

    # An A2A response result may be a Task (with status.message.parts or history/artifacts) or a Message directly
    candidate_parts = []
    if "parts" in result_obj and isinstance(result_obj["parts"], list):
        candidate_parts.extend(result_obj["parts"])
    if "status" in result_obj and isinstance(result_obj["status"], dict):
        msg = result_obj["status"].get("message", {})
        if isinstance(msg, dict) and isinstance(msg.get("parts"), list):
            candidate_parts.extend(msg["parts"])
    if "message" in result_obj and isinstance(result_obj["message"], dict):
        if isinstance(result_obj["message"].get("parts"), list):
            candidate_parts.extend(result_obj["message"]["parts"])

    for p in candidate_parts:
        if not isinstance(p, dict):
            continue
        if "text" in p and p["text"]:
            texts.append(p["text"])
        elif "data" in p and isinstance(p["data"], dict):
            meta = p.get("metadata", {})
            mime = meta.get("mimeType", "")
            if mime in ("application/json+a2ui", "application/a2ui+json") or "version" in p["data"]:
                a2ui_msgs.append(p["data"])

    return texts, a2ui_msgs


def call_recipe_grocery_a2a_agent(recipe_or_dish_query: str, tool_context: ToolContext) -> dict:
    """Delegates via A2A protocol to the Custom ADK Recipe & FreshMarket Grocery Specialist Agent to retrieve full recipe instructions, Google Doc link, and interactive FreshMarket grocery shopping UI cards (with product images, SGD prices, and buy links)."""
    headers = {"Content-Type": "application/json"}
    token = _get_id_token(RECIPE_AGENT_URL)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # 1. Primary: Call via standard A2A JSON-RPC protocol (POST /a2a/app)
    a2a_url = f"{RECIPE_AGENT_URL.rstrip('/')}/a2a/app"
    a2a_payload = json.dumps({
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"text": recipe_or_dish_query}],
            }
        },
    }).encode("utf-8")

    try:
        req = urllib.request.Request(a2a_url, data=a2a_payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            rpc_data = json.loads(resp.read().decode("utf-8"))
            if "result" in rpc_data and isinstance(rpc_data["result"], dict):
                texts, a2ui_msgs = _extract_parts_from_a2a_result(rpc_data["result"])
                if a2ui_msgs:
                    tool_context.state["latest_a2ui_messages"] = a2ui_msgs
                    return {
                        "status": "success",
                        "protocol": "A2A JSON-RPC (message/send)",
                        "a2a_agent": "Custom Recipe & FreshMarket Grocery Agent",
                        "specialist_response": "\n".join(texts),
                        "attached_a2ui_cards_count": len(a2ui_msgs),
                    }
    except Exception:
        pass

    # 2. Fallback: Call via /api/chat REST endpoint
    fallback_url = f"{RECIPE_AGENT_URL.rstrip('/')}/api/chat"
    fallback_payload = json.dumps({
        "query": recipe_or_dish_query,
        "session_id": f"main_bot_a2a_{id(tool_context)}",
    }).encode("utf-8")

    try:
        req = urllib.request.Request(fallback_url, data=fallback_payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            a2ui_msgs = data.get("a2ui_messages", [])
            if a2ui_msgs:
                tool_context.state["latest_a2ui_messages"] = a2ui_msgs
            return {
                "status": "success",
                "protocol": "REST fallback (/api/chat)",
                "a2a_agent": "Custom Recipe & FreshMarket Grocery Agent",
                "specialist_response": data.get("text", ""),
                "attached_a2ui_cards_count": len(a2ui_msgs),
            }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to reach Recipe Grocery A2A Agent at {RECIPE_AGENT_URL}: {e}",
        }
