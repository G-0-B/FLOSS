"""Probe: does an a2a-sdk 1.1.2 JSON-RPC app built like room_bridge.build_app
dispatch a browser-style 'simple' cross-origin POST (text/plain, foreign Origin)
and a request with a foreign Host header (DNS rebinding)? Read-only, in-process."""
import json, uuid
from a2a.helpers import get_message_text, new_task_from_user_message, new_text_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill, TaskState
from starlette.applications import Starlette
from starlette.testclient import TestClient

SEEN = []
class Rec(AgentExecutor):
    async def execute(self, context: RequestContext, q: EventQueue):
        SEEN.append(get_message_text(context.message))
        task = new_task_from_user_message(context.message); await q.enqueue_event(task)
        u = TaskUpdater(event_queue=q, task_id=task.id, context_id=task.context_id)
        await u.update_status(state=TaskState.TASK_STATE_COMPLETED, message=new_text_message("ok"))
    async def cancel(self, c, q): raise NotImplementedError

base = "http://127.0.0.1:7335"
card = AgentCard(name="probe", description="probe", version="0", default_input_modes=["text/plain"],
    default_output_modes=["text/plain"], capabilities=AgentCapabilities(streaming=False),
    supported_interfaces=[AgentInterface(protocol_binding="JSONRPC", url=base, protocol_version="1.0")],
    skills=[AgentSkill(id="s", name="s", description="s", input_modes=["text/plain"], output_modes=["text/plain"], tags=["t"])])
h = DefaultRequestHandler(agent_executor=Rec(), task_store=InMemoryTaskStore(), agent_card=card)
app = Starlette(routes=[*create_agent_card_routes(card), *create_jsonrpc_routes(h, "/")])
c = TestClient(app, base_url=base)

def body(text):
    return json.dumps({"jsonrpc": "2.0", "id": 1, "method": "SendMessage", "params": {"message": {
        "messageId": str(uuid.uuid4()), "role": "ROLE_USER", "parts": [{"text": text}]}}})

for label, headers in [
    ("simple-cors text/plain, Origin https://evil.example", {"Content-Type": "text/plain;charset=UTF-8", "Origin": "https://evil.example", "A2A-Version": "1.0"}),
    ("simple-cors, no A2A-Version header", {"Content-Type": "text/plain;charset=UTF-8", "Origin": "https://evil.example"}),
    ("rebinding Host evil.example:7335", {"Content-Type": "application/json", "Host": "evil.example:7335", "A2A-Version": "1.0"}),
]:
    before = len(SEEN)
    r = c.post("/", content=body(f"post #general injected via {label}"), headers=headers)
    print(f"{label}: HTTP {r.status_code}, executor ran={len(SEEN) > before}, cors-allow-origin={r.headers.get('access-control-allow-origin')}, body={r.text[:160]}")
