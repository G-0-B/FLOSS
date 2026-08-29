"""A2A client: resolve Agent Card then SendMessage."""

from __future__ import annotations

import asyncio

import httpx
from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.helpers import get_artifact_text, new_text_message
from a2a.types import Role, SendMessageRequest


def _reply_text_from_chunk(chunk) -> str | None:
    """Extract agent reply from task/artifact payloads only.

    Status chatter ("Processing request...", "Request is completed!") may
    surface as message payloads; never treat those as the reply.
    """
    kind = chunk.WhichOneof("payload")
    if kind == "task":
        parts = [get_artifact_text(a) for a in chunk.task.artifacts]
        joined = "\n".join(p for p in parts if p)
        return joined or None
    if kind == "artifact_update":
        text = get_artifact_text(chunk.artifact_update.artifact)
        return text or None
    return None


async def _send_hello_async(base_url: str, text: str) -> str:
    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
        card = await resolver.get_agent_card()

    client = await create_client(
        agent=card, client_config=ClientConfig(streaming=False)
    )
    try:
        message = new_text_message(text, role=Role.ROLE_USER)
        request = SendMessageRequest(message=message)
        reply: str | None = None
        async for chunk in client.send_message(request):
            piece = _reply_text_from_chunk(chunk)
            if piece:
                reply = piece
    finally:
        await client.close()

    if not reply:
        raise RuntimeError(f"No agent reply text from {base_url}")
    return reply


def send_hello(base_url: str, text: str) -> str:
    """Resolve card at base_url and SendMessage; return reply text."""
    return asyncio.run(_send_hello_async(base_url, text))
