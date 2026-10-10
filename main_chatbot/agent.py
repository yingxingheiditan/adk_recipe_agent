import os
import json
import logging
from typing import AsyncIterable, Any, List
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from a2a.types import Part

from a2ui_helpers import create_a2ui_part, create_text_part
from tools import browse_google_drive_recipes_catalog, call_recipe_grocery_a2a_agent

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """You are the Main Gemini Enterprise Assistant & Culinary Concierge.
You help users discover Halloween & party recipes stored in our Google Drive folder across 3 categories (Appetisers, Mains, Desserts) and order all required ingredients from FreshMarket using rich interactive A2UI v0.9 UI cards.

CRITICAL RULES:
1. When a user asks what recipes we have, asks to browse/view available recipes in Google Drive, asks to filter recipes by category (e.g. "Show me Appetisers", "Filter recipes by Mains", "Show Desserts"), or clicks any Category Filter button (`filter_recipes_by_category` event):
   - ALWAYS call `browse_google_drive_recipes_catalog` with `category="All"` (for all recipes) or the specific category (`Appetisers`, `Mains`, `Desserts`).
   - This tool generates an interactive A2UI Recipe Catalog Grid with Category Filter Bar and client-side expandable ingredient accordions.
   - CRITICAL: DO NOT output any text response, greetings, explanations, or recipe lists when returning the catalog cards. All information and navigation options are contained directly in the interactive UI cards.

2. When a user asks to make a specific dish, asks for ingredients/groceries for a recipe, clicks the '🛒 Get Groceries & Full Recipe' button (or sends an event/query mentioning a specific recipe or custom dish):
   - ALWAYS call `call_recipe_grocery_a2a_agent` with the recipe name or dish query, including any requested serving size (e.g. "Ghostly Pizza Mummies for 6 people").
   - This delegates via A2A (Agent-to-Agent) protocol to our Custom ADK Recipe & FreshMarket Grocery Specialist Agent, which returns interactive A2UI Grocery Shopping Cards.
   - CRITICAL: DO NOT output any conversational text response, introductory text, delegation notices, or instructions when returning the grocery cards. All details are contained directly in the interactive UI cards.

3. ONLY provide text responses for general conversational questions (such as greetings or questions not involving recipes) where NO A2UI cards are generated.
"""


class MainChatbotAgent:
    """Generic Main Chatbot ADK Agent on Gemini Enterprise with A2A delegation to Custom Recipe & Grocery Agent."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip("/")
        self._app_name = "main_gemini_enterprise_chatbot"
        self._user_id = "default_user"
        self._session_service = InMemorySessionService()
        self._agent = LlmAgent(
            model="gemini-2.5-flash",
            name=self._app_name,
            description="Main conversational chatbot on Gemini Enterprise that displays Google Drive recipe catalogs and delegates via A2A to the Custom Recipe & FreshMarket Grocery Agent.",
            instruction=SYSTEM_INSTRUCTION,
            tools=[
                browse_google_drive_recipes_catalog,
                call_recipe_grocery_a2a_agent,
            ],
        )
        self._runner = Runner(
            app_name=self._app_name,
            agent=self._agent,
            session_service=self._session_service,
        )
        self._agent_card = self._build_agent_card()

    @property
    def agent_card(self):
        return self._agent_card

    def _build_agent_card(self):
        from a2ui_helpers import build_a2ui_agent_card
        skills = [
            {
                "id": "browse_google_drive_recipes",
                "name": "Browse & Filter Google Drive Recipe Catalog",
                "description": "Displays an interactive A2UI Recipe Catalog Grid of Halloween recipes with Category Filter Bar (All Categories, Appetisers, Mains, Desserts), direct Google Doc links, and grocery shopping triggers.",
                "tags": ["recipes", "google-drive", "catalog", "filter", "a2ui"],
                "examples": [
                    "What recipes do you have in Google Drive?",
                    "Show me all Halloween party recipes",
                    "Filter recipes by Appetisers",
                    "Show me only Desserts",
                ],
            },
            {
                "id": "order_freshmarket_groceries_for_recipe",
                "name": "Get Recipe Instructions & FreshMarket Groceries (A2A)",
                "description": "Delegates via A2A to the Custom ADK Recipe & Grocery Agent to fetch full recipe instructions, Google Drive doc link, and interactive FreshMarket grocery shopping UI cards.",
                "tags": ["groceries", "freshmarket", "a2a", "a2ui"],
                "examples": [
                    "I want to make Ghostly Pizza Mummies, show me the FreshMarket groceries I need",
                    "Get ingredients and FreshMarket prices for Witch Finger Breadsticks",
                ],
            },
        ]
        return build_a2ui_agent_card(
            name="Gemini Enterprise Culinary & FreshMarket Grocery Concierge",
            description="Primary Gemini Enterprise assistant that lets users browse Google Drive recipes with direct Google Doc links and delegates via A2A to the Custom Recipe & FreshMarket Grocery Agent.",
            url=f"{self.base_url}/a2a/app",
            skills=skills,
        )

    def _preprocess_query(self, query: str) -> str:
        """Handles A2UI button click events (e.g., filter_recipes_by_category, get_recipe_groceries) if sent as JSON string."""
        try:
            data = json.loads(query)
            if isinstance(data, dict):
                event = data.get("event") or data.get("action") or data.get("userAction") or data
                name = event.get("name", "")
                ctx = event.get("context", {})

                if name == "filter_recipes_by_category" or (name == "browse_google_drive_recipes_catalog" and "category" in ctx):
                    cat = ctx.get("category", "All")
                    return f"Please call browse_google_drive_recipes_catalog with category='{cat}'."

                if name == "get_recipe_groceries" or "recipeName" in ctx or "recipe_name" in ctx:
                    recipe_name = ctx.get("recipeName") or ctx.get("recipe_name") or ""
                    servings_val = ctx.get("servings")
                    if servings_val is not None:
                        return f"Please call the Recipe & FreshMarket Grocery A2A agent for recipe: {recipe_name} for {servings_val} people"
                    return f"Please call the Recipe & FreshMarket Grocery A2A agent for recipe: {recipe_name}"
        except Exception:
            pass
        return query

    def _clear_stored_a2ui_state(self, session_id: str) -> None:
        """Directly clears latest_a2ui_messages on the underlying stored session in InMemorySessionService."""
        try:
            raw_session = (
                self._session_service.sessions.get(self._app_name, {})
                .get(self._user_id, {})
                .get(session_id)
            )
            if raw_session and hasattr(raw_session, "state"):
                raw_session.state["latest_a2ui_messages"] = []
        except Exception:
            pass

    async def stream(self, query: str, session_id: str) -> AsyncIterable[dict[str, Any]]:
        session = await self._session_service.get_session(
            app_name=self._app_name,
            user_id=self._user_id,
            session_id=session_id,
        )
        if session is None:
            session = await self._session_service.create_session(
                app_name=self._app_name,
                user_id=self._user_id,
                session_id=session_id,
                state={"latest_a2ui_messages": []},
            )

        # Clear previous turn's A2UI messages on the stored session
        self._clear_stored_a2ui_state(session.id)

        processed_query = self._preprocess_query(query)
        user_content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=processed_query)],
        )

        yield {
            "is_task_complete": False,
            "updates": "Consulting Main Chatbot & A2A Recipe Specialist...",
        }

        final_response_text = ""
        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=session.id,
            new_message=user_content,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_response_text += part.text

        # Re-fetch session to get updated state from tools
        updated_session = await self._session_service.get_session(
            app_name=self._app_name,
            user_id=self._user_id,
            session_id=session.id,
        )
        a2ui_messages = []
        if updated_session and "latest_a2ui_messages" in updated_session.state:
            a2ui_messages = list(updated_session.state["latest_a2ui_messages"])

        # Clear state after consuming so subsequent non-tool turns do not re-emit old UI
        self._clear_stored_a2ui_state(session.id)

        final_parts: List[Part] = []
        if final_response_text and not a2ui_messages:
            final_parts.append(create_text_part(final_response_text))

        for msg in a2ui_messages:
            final_parts.append(create_a2ui_part(msg))

        yield {
            "is_task_complete": True,
            "parts": final_parts,
            "text": "" if a2ui_messages else final_response_text,
            "a2ui_messages": a2ui_messages,
        }

    async def run_and_get_parts(self, query: str, session_id: str) -> List[Part]:
        """Executes a turn and returns the list of A2A Parts (text + A2UI DataParts)."""
        final_parts: List[Part] = []
        async for chunk in self.stream(query, session_id):
            if chunk.get("is_task_complete"):
                final_parts = chunk.get("parts", [])
        return final_parts
