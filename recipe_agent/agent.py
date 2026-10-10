import os
import logging
from typing import List, Dict, Any, Optional

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Part,
)
from a2ui_helpers import build_a2ui_agent_card, create_text_part, create_a2ui_part
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from tools import list_drive_recipes_tool, get_recipe_and_groceries_tool

logger = logging.getLogger(__name__)

INSTRUCTION = """You are the Custom ADK Recipe & FreshMarket Grocery Specialist Agent.
Your job is to help users browse recipes from our Google Drive collection (14 Halloween/Spooky recipes across Appetisers, Desserts, and Mains) OR help them cook their own custom recipes, and generate interactive FreshMarket grocery shopping lists with full interactive recipes (including a 1-10 people serving size slider).

RULES:
1. When the user asks to list, browse, or see what recipes are available in Google Drive (e.g. "What recipes do you have?", "Show me the Google Drive recipes"):
   - ALWAYS call `list_drive_recipes_tool`.
   - CRITICAL: DO NOT output any text response, greetings, or explanations when returning the catalog cards. All information is presented directly in the interactive A2UI cards.

2. When the user asks about a specific recipe from Google Drive (e.g. "I want to make Ghostly Pizza Mummies", "Give me the recipe and groceries for Monster Burgers", "Make Pizza Mummies for 6 people") OR clicks the grocery/servings action button:
   - ALWAYS call `get_recipe_and_groceries_tool` with the recipe name and `servings` (as integer 1-10 if specified).
   - CRITICAL: DO NOT output any conversational text response, introductory text, delegation notices, cooking instructions, or button explanations when returning the grocery cards. All ingredient details, images, prices, buy buttons, interactive serving size slider (1-10 people), scaled ingredients, and full step-by-step cooking instructions are displayed directly in the interactive UI cards below.

3. When the user provides their OWN custom recipe or dish (not in Google Drive):
   - ALWAYS call `get_recipe_and_groceries_tool` passing their dish name, `custom_ingredients` list, and `servings` if specified.
   - CRITICAL: DO NOT output any conversational text response when returning the grocery cards.

4. ONLY provide text responses for general conversational questions where NO A2UI cards are generated.
"""


class RecipeGroceryAgent:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._app_name = "recipe_agent_app"
        self._user_id = "a2a_user"
        self.model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.session_service = InMemorySessionService()
        self.llm_agent = LlmAgent(
            name="recipe_grocery_specialist",
            model=self.model_name,
            description="Custom ADK agent that reads Google Drive recipes, scales ingredients for 1-10 people via interactive slider, parses custom user recipes, matches ingredients against FreshMarket, and renders A2UI grocery and recipe catalog cards.",
            instruction=INSTRUCTION,
            tools=[list_drive_recipes_tool, get_recipe_and_groceries_tool],
        )
        self.runner = Runner(
            app_name=self._app_name,
            agent=self.llm_agent,
            session_service=self.session_service,
        )
        self._agent_card = self._build_agent_card()

    @property
    def agent_card(self) -> AgentCard:
        return self._agent_card

    def _build_agent_card(self) -> AgentCard:
        skills = [
            {
                "id": "list_drive_recipes",
                "name": "Browse Google Drive Recipe Catalog",
                "description": "Displays an interactive A2UI Recipe Catalog Grid of all 14 Google Drive recipes with direct Google Doc links and grocery shopping triggers.",
                "tags": ["recipes", "google-drive", "catalog", "a2ui"],
                "examples": ["What recipes do you have in Google Drive?", "Show me all recipes"],
            },
            {
                "id": "get_recipe_groceries",
                "name": "Get FreshMarket Groceries & Full Interactive Recipe",
                "description": "Reads a recipe from Google Drive or a user-submitted recipe, scales ingredients and basket total for the requested serving size (1-10 people via interactive slider), matches all ingredients against FreshMarket, and returns interactive A2UI cards with grocery buy links, scaled ingredients, and full step-by-step cooking instructions.",
                "tags": ["groceries", "freshmarket", "recipe", "a2ui", "servings-slider"],
                "examples": [
                    "I want to make Ghostly Pizza Mummies",
                    "Show me the groceries and full recipe needed for Monster Burgers for 6 people",
                    "I want to cook Chicken Rice with chicken, jasmine rice, garlic, ginger, and soy sauce for 2 people",
                ],
            },
        ]
        return build_a2ui_agent_card(
            name="Custom Recipe & FreshMarket Grocery Agent",
            description="ADK + A2UI specialist agent for Google Drive recipes and FreshMarket grocery shopping.",
            url=f"{self.base_url}/a2a/app",
            skills=skills,
        )

    def _clear_stored_a2ui_state(self, session_id: str) -> None:
        """Directly clears latest_a2ui_messages on the underlying stored session in InMemorySessionService."""
        try:
            raw_session = (
                self.session_service.sessions.get(self._app_name, {})
                .get(self._user_id, {})
                .get(session_id)
            )
            if raw_session and hasattr(raw_session, "state"):
                raw_session.state["latest_a2ui_messages"] = []
        except Exception:
            pass

    async def run_and_get_parts(self, query: str, session_id: str) -> List[Part]:
        session = await self.session_service.get_session(
            app_name=self._app_name, user_id=self._user_id, session_id=session_id
        )
        if not session:
            session = await self.session_service.create_session(
                app_name=self._app_name,
                user_id=self._user_id,
                session_id=session_id,
                state={"latest_a2ui_messages": []},
            )

        # Preprocess JSON event query strings if passed directly via REST /api/chat
        if query.strip().startswith("{") and query.strip().endswith("}"):
            try:
                import json
                data = json.loads(query)
                if isinstance(data, dict):
                    event = data.get("event") or data.get("action") or data.get("userAction") or data
                    name = event.get("name", "")
                    ctx = event.get("context", {})
                    if name == "get_recipe_groceries" or "recipeName" in ctx or "recipe_name" in ctx:
                        recipe_name = ctx.get("recipeName") or ctx.get("recipe_name") or "Ghostly Pizza Mummies"
                        servings_val = ctx.get("servings")
                        if servings_val is not None:
                            query = f"Please show me the full recipe instructions and FreshMarket grocery shopping list for {recipe_name} for {servings_val} people"
                        else:
                            query = f"Please show me the full recipe instructions and FreshMarket grocery shopping list for {recipe_name}"
            except Exception:
                pass

        text_chunks = []
        async for event in self.runner.run_async(
            user_id=self._user_id,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part.from_text(text=query)]),
        ):
            if event.is_final_response() and event.content and event.content.parts:
                for p in event.content.parts:
                    if p.text:
                        text_chunks.append(p.text)

        final_text = "\n".join(text_chunks).strip()
        parts: List[Part] = []

        # Retrieve updated session state to extract any A2UI messages generated by tools
        updated_session = await self.session_service.get_session(
            app_name=self._app_name, user_id=self._user_id, session_id=session_id
        )
        a2ui_msgs = list(updated_session.state.get("latest_a2ui_messages", [])) if updated_session else []

        # Clear stored state after consuming
        self._clear_stored_a2ui_state(session.id)

        if final_text and not a2ui_msgs:
            parts.append(create_text_part(final_text))

        for msg in a2ui_msgs:
            parts.append(create_a2ui_part(msg))

        return parts
