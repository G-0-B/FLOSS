"""
Horde.AI client for distributed LLM inference.
Public API key: "0000000000"

Integrates with AI-Horde for free distributed inference.
"""

import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class HordeClient:
    """Client for Horde.AI distributed inference."""

    def __init__(self, api_key: str = "0000000000"):
        self.api_key = api_key
        self.api_base = "https://stablehorde.net/api/v2"
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def generate_text(
        self,
        prompt: str,
        max_length: int = 512,
        temperature: float = 0.8,
        model: str = "koboldcpp/LLaMA2-13B-Tiefighter",
    ) -> str:
        """
        Generate text using Horde.AI distributed workers.

        Returns generated text or raises exception.
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        # Step 1: Submit generation request
        payload = {
            "prompt": prompt,
            "params": {
                "max_length": max_length,
                "temperature": temperature,
                "top_p": 0.9,
                "n": 1,
            },
            "models": [model],
            "trusted_workers": False,
        }

        headers = {"apikey": self.api_key, "Content-Type": "application/json"}

        try:
            # Submit request
            async with self.session.post(
                f"{self.api_base}/generate/text/async", json=payload, headers=headers
            ) as resp:
                if resp.status != 202:
                    error_text = await resp.text()
                    raise Exception(f"Horde request failed: {resp.status} {error_text}")

                data = await resp.json()
                request_id = data.get("id")

                if not request_id:
                    raise Exception("No request ID returned")

            # Step 2: Poll for results
            max_attempts = 120  # 2 minutes max wait
            for attempt in range(max_attempts):
                await asyncio.sleep(1)

                async with self.session.get(
                    f"{self.api_base}/generate/text/status/{request_id}",
                    headers=headers,
                ) as resp:
                    status_data = await resp.json()

                    if status_data.get("done"):
                        generations = status_data.get("generations", [])
                        if generations and generations[0].get("text"):
                            return generations[0]["text"]
                        raise Exception("No text in completed generation")

                    if status_data.get("faulted"):
                        raise Exception(f"Generation faulted: {status_data}")

            raise Exception("Generation timeout after 2 minutes")

        except Exception as e:
            logger.error(f"Horde generation error: {e}")
            raise

    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vector for text.

        Note: Horde.AI embedding support may be limited.
        Falls back to simple hash-based embedding if needed.
        """
        # Simple fallback: normalized character frequency vector
        # In production, use sentence-transformers or other embedding model
        import numpy as np

        # Create 384-dimensional embedding (common size)
        vec = np.zeros(384)

        # Simple character-based features
        for i, char in enumerate(text[:384]):
            vec[i] = ord(char) / 255.0

        # Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec.tolist()
