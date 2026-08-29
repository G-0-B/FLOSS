"""Loopback A2A helloworld agent (Agent Card + JSON-RPC only)."""

from __future__ import annotations

import threading

import uvicorn
from a2a.helpers import (
    get_message_text,
    new_task_from_user_message,
    new_text_message,
    new_text_part,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    TaskState,
)
from starlette.applications import Starlette

AGENT_NAME = "flossi0ullk-a2a-helloworld"

_serving: dict[tuple[str, int], bool] = {}
_serve_lock = threading.Lock()


class _HelloExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.current_task:
            task = context.current_task
        else:
            task = new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(
            event_queue=event_queue, task_id=task.id, context_id=task.context_id
        )
        await updater.update_status(
            state=TaskState.TASK_STATE_WORKING,
            message=new_text_message("Processing request..."),
        )
        query = get_message_text(context.message) if context.message else ""
        result = f"Hello, World! I have received your request ({query})"
        await updater.add_artifact(
            parts=[new_text_part(text=result, media_type="text/plain")]
        )
        await updater.update_status(
            state=TaskState.TASK_STATE_COMPLETED,
            message=new_text_message("Request is completed!"),
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("Cancel is not supported.")


def _build_app(host: str, port: int) -> Starlette:
    base = f"http://{host}:{port}"
    skill = AgentSkill(
        id="hello",
        name="Hello",
        description="Acknowledge a client message with a hello-world reply.",
        input_modes=["text/plain"],
        output_modes=["text/plain"],
        tags=["a2a", "helloworld"],
        examples=["ping", "hi"],
    )
    card = AgentCard(
        name=AGENT_NAME,
        description="Spec-minimum FLOSSI0ULLK A2A helloworld agent.",
        version="0.0.1",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        supported_interfaces=[
            AgentInterface(
                protocol_binding="JSONRPC",
                url=base,
                protocol_version="1.0",
            )
        ],
        skills=[skill],
    )
    handler = DefaultRequestHandler(
        agent_executor=_HelloExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    routes = []
    routes.extend(create_agent_card_routes(card))
    routes.extend(create_jsonrpc_routes(handler, "/"))
    return Starlette(routes=routes)


def serve_helloworld(host: str, port: int) -> None:
    """Serve Agent Card + JSON-RPC on loopback. No-op if already serving."""
    if host != "127.0.0.1":
        raise ValueError("serve_helloworld binds 127.0.0.1 only")
    key = (host, port)
    with _serve_lock:
        if _serving.get(key):
            return
        _serving[key] = True
    app = _build_app(host, port)
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
    )
    # Help sequential pytest rebinds / TIME_WAIT on the same port.
    config.timeout_graceful_shutdown = 0
    server = uvicorn.Server(config)
    server.run()
