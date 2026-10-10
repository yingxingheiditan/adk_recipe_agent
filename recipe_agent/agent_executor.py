import uuid
import logging
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Task
from google.adk.a2a.utils.agent_to_a2a import _compat
from a2ui_helpers import extract_part_data, extract_part_text
from agent import RecipeGroceryAgent

logger = logging.getLogger(__name__)


class RecipeGroceryAgentExecutor(AgentExecutor):
    """A2A AgentExecutor for the Custom ADK Recipe & FreshMarket Grocery Agent."""

    def __init__(self, agent: RecipeGroceryAgent):
        self._agent = agent

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = ""
        ui_event_part = None

        if context.message and context.message.parts:
            for part in context.message.parts:
                data = extract_part_data(part)
                if isinstance(data, dict):
                    if "action" in data:
                        ui_event_part = data["action"]
                    elif "userAction" in data:
                        ui_event_part = data["userAction"]
                    elif "event" in data:
                        ui_event_part = data["event"]
                else:
                    txt = extract_part_text(part)
                    if txt and not query:
                        query = txt

        if ui_event_part:
            action_name = ui_event_part.get("name")
            ctx = ui_event_part.get("context", {})
            if action_name == "get_recipe_groceries" or "recipeName" in ctx or "recipe_name" in ctx:
                recipe_name = ctx.get("recipeName") or ctx.get("recipe_name") or "Ghostly Pizza Mummies"
                servings_val = ctx.get("servings")
                if servings_val is not None:
                    query = f"Please show me the full recipe instructions and FreshMarket grocery shopping list for {recipe_name} for {servings_val} people"
                else:
                    query = f"Please show me the full recipe instructions and FreshMarket grocery shopping list for {recipe_name}"
            else:
                query = f"User triggered UI action {action_name} with context {ctx}"
        elif not query:
            query = context.get_user_input() or "What recipes do you have in Google Drive?"

        logger.info(f"Executing RecipeGroceryAgent query: '{query}'")

        await _compat.enqueue_submitted_signal(event_queue, context=context)

        task_id = context.task_id or str(uuid.uuid4())
        context_id = context.context_id or str(uuid.uuid4())

        # Publish working event
        await event_queue.enqueue_event(
            _compat.make_task_status_update_event(
                task_id=task_id,
                context_id=context_id,
                status=_compat.make_task_status(_compat.TS_WORKING),
                final=False,
            )
        )

        parts = await self._agent.run_and_get_parts(query, context_id)

        agent_message = _compat.make_message(
            message_id=str(uuid.uuid4()),
            role=_compat.ROLE_AGENT,
            parts=parts,
            context_id=context_id,
            task_id=task_id,
        )

        await event_queue.enqueue_event(
            _compat.make_task_status_update_event(
                task_id=task_id,
                context_id=context_id,
                status=_compat.make_task_status(
                    _compat.TS_COMPLETED,
                    message=agent_message,
                ),
                final=True,
            )
        )

    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise NotImplementedError("Cancel is not supported")
