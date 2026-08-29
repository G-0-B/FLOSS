"""A2A client: resolve Agent Card then SendMessage."""

from __future__ import annotations

import asyncio

import httpx
from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.helpers import get_stream_response_text, new_text_message
from a2a.types import Role, SendMessageRequest


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
        collected: list[str] = []
        async for chunk in client.send_message(request):
            piece = get_stream_response_text(chunk)
            if piece:
                collected.append(piece)
    finally:
        await client.close()

    if not collected:
        return ""
    # Prefer the longest non-empty piece (artifact reply over status chatter).
    return max(collected, key=len)


def send_hello(base_url: str, text: str) -> str:
    """Resolve card at base_url and SendMessage; return reply text."""
    return asyncio.run(_send_hello_async(base_url, text))
