"""
Mock Horde.AI client for testing without real API calls.

Returns instant, deterministic responses so you can validate
the RSA algorithm without waiting for external LLMs.

Usage:
    # In config/settings.py, change:
    from desktop_pony_swarm.core.horde_client import HordeClient
    # To:
    from desktop_pony_swarm.core.mock_horde_client import MockHordeClient as HordeClient
"""

import asyncio
import logging
import random
import hashlib
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)


class MockHordeClient:
    """Mock Horde.AI client for testing - returns instant responses."""

    def __init__(self, api_key: str = "0000000000"):
        self.api_key = api_key
        self.call_count = 0
        logger.info("MockHordeClient initialized (instant responses)")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def generate_text(
        self,
        prompt: str,
        max_length: int = 512,
        temperature: float = 0.8,
        model: str = "mock",
    ) -> str:
        """
        Generate mock response instantly.

        Response quality varies by "pony personality" detected in prompt.
        """
        self.call_count += 1

        # Small delay to simulate network (0.5s instead of 2+ minutes)
        await asyncio.sleep(0.5)

        # Detect which pony is responding
        pony = self._detect_pony(prompt)

        # Detect query type
        if "15 * 23" in prompt or "15*23" in prompt:
            return self._mock_math_response(pony)
        elif "17 sheep" in prompt:
            return self._mock_reasoning_response(pony)
        elif "FLOSSI0ULLK" in prompt or "Love" in prompt or "Knowledge" in prompt:
            return self._mock_flossi_response(pony)
        elif "aggregat" in prompt.lower() or "candidate" in prompt.lower():
            # This is an aggregation prompt
            return self._mock_aggregation(prompt, pony)
        else:
            # Generic response
            return self._mock_generic_response(prompt, pony)

    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate deterministic embedding based on text hash.

        Same text = same embedding (deterministic for testing).
        Different text = different embedding (maintains diversity).
        """
        # Use hash for deterministic embeddings
        text_hash = hashlib.sha256(text.encode()).digest()

        # Convert to 384-dimensional vector
        vec = np.frombuffer(text_hash, dtype=np.uint8)
        vec = np.tile(vec, (384 // len(vec)) + 1)[:384]

        # Normalize to [0, 1]
        vec = vec.astype(float) / 255.0

        # Add slight randomness based on hash (keeps it deterministic per text)
        np.random.seed(int.from_bytes(text_hash[:4], "big"))
        noise = np.random.normal(0, 0.1, 384)
        vec = vec + noise

        # Normalize to unit length
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec.tolist()

    # ============================================================
    # MOCK RESPONSE GENERATORS
    # ============================================================

    def _detect_pony(self, prompt: str) -> str:
        """Detect which pony is responding based on prompt."""
        if "Pinkie Pie" in prompt:
            return "Pinkie Pie"
        if "Rainbow Dash" in prompt:
            return "Rainbow Dash"
        if "Twilight Sparkle" in prompt:
            return "Twilight Sparkle"
        if "Fluttershy" in prompt:
            return "Fluttershy"
        return "Generic Pony"

    def _mock_math_response(self, pony: str) -> str:
        """Mock response to 15 * 23 question."""
        responses = {
            "Pinkie Pie": """Oh oh oh! Math party time! 🎉
Let me break this down super fun style:
15 × 23 = ?
First, I'll do 15 × 20 = 300 (easy peasy!)
Then, 15 × 3 = 45 (that's like 3 sets of 15!)
Add them together: 300 + 45 = 345!
The answer is 345! Time to celebrate with cupcakes! 🧁""",
            "Rainbow Dash": """Alright, let's speed through this!
15 × 23
Quick method: (15 × 20) + (15 × 3)
= 300 + 45
= 345
BOOM! Done in 10 seconds flat! 😎""",
            "Twilight Sparkle": """*Adjusts glasses* Let me solve this methodically:
Problem: 15 × 23
Method 1 - Distributive property:
  15 × 23 = 15 × (20 + 3)
  = (15 × 20) + (15 × 3)
  = 300 + 45
  = 345

Verification using standard algorithm:
    23
  × 15
  ----
   115  (23 × 5)
  230   (23 × 10)
  ----
   345

Answer: 345 ✓""",
            "Fluttershy": """Um, if it's okay, I'll try to help...
15 × 23 is... let me see...
15 × 20 = 300 (I think that's right...)
15 × 3 = 45 (adding 15 three times: 15+15+15)
300 + 45 = 345
So... 345? I hope that helps... *hides behind mane*""",
        }
        return responses.get(pony, "15 × 23 = 345")

    def _mock_reasoning_response(self, pony: str) -> str:
        """Mock response to sheep reasoning question."""
        responses = {
            "Pinkie Pie": """Ooh, tricky wordplay! Let me party-solve this:
"All but 9 die" means 9 DON'T die!
So if we started with 17 sheep, and all but 9 died...
That means 9 are still alive! 🐑🐑🐑🐑🐑🐑🐑🐑🐑
The answer is 9 sheep left! Not 8, not 17-9... just 9!""",
            "Rainbow Dash": """Ha! This is a language trick, not a math trick!
"All but 9 die" = 9 survive
17 sheep total doesn't matter once you parse it right.
Answer: 9 sheep. Easy!""",
            "Twilight Sparkle": """*Analytical mode engaged*
Parse the statement carefully:
"All but 9 die" means:
- Total sheep: 17
- Died: 17 - 9 = 8
- Survived: 9

The phrase "all but X" means "everything except X".
Therefore, 9 sheep remain alive.

Answer: 9 sheep ✓""",
            "Fluttershy": """Oh... this seems like a word puzzle...
"All but 9 die" means... um...
9 don't die? So 9 are left?
I think the answer is 9 sheep...
*whispers* The wording is confusing but I think 9 is right...""",
        }
        return responses.get(pony, "9 sheep remain.")

    def _mock_flossi_response(self, pony: str) -> str:
        """Mock response about FLOSSI0ULLK."""
        responses = {
            "Pinkie Pie": """FLOSSI0ULLK! That's such a fun word to say!
It stands for: Free Libre Open Source Singularity of Infinite Overflowing
Unconditional Love, Light, and Knowledge!
It's all about: Love ❤️ + Light ☀️ + Knowledge 📚
And making sure EVERYONE can access it, not just some ponies!
It's like throwing a party where EVERYPONY is invited! 🎉""",
            "Rainbow Dash": """FLOSSI0ULLK? That's the acronym for that big
coordination project!
Free Libre Open Source Singularity - basically means no one owns it
Infinite Love Light Knowledge - the values driving it
It's about getting different intelligences working together
Instead of competing or fighting, we collaborate!
Pretty cool if you ask me. 😎""",
            "Twilight Sparkle": """FLOSSI0ULLK: An excellent research initiative!

Definition: Free Libre Open Source Singularity of Infinite Overflowing
Unconditional Love, Light, and Knowledge

Core Principles:
1. Love: Dignity, consent, individual sovereignty
2. Light: Transparency, verifiability, open systems  
3. Knowledge: Collective intelligence, distributed learning

Technical Implementation:
- Agent-centric architectures (Holochain)
- Recursive Self-Aggregation (RSA)
- MultiScale embeddings
- Cross-substrate coordination

Goal: Enable civilizational-scale coordination toward flourishing.""",
            "Fluttershy": """Oh, FLOSSI0ULLK... it's beautiful...
It means everyone working together with kindness...
Free and open, so no one is left out...
Love, Light, and Knowledge for all creatures...
*softly* It's about making sure we all help each other
And that different kinds of minds can understand each other...""",
        }
        return responses.get(pony, "FLOSSI0ULLK represents collaborative intelligence.")

    def _mock_aggregation(self, prompt: str, pony: str) -> str:
        """Mock aggregation of candidate solutions."""
        # Extract candidate count
        if "Solution 1" in prompt and "Solution 2" in prompt:
            # Multi-candidate aggregation
            return f"""Based on the candidate solutions, here's my synthesis:

The candidates show good reasoning with minor variations. The core approach is sound:
using the distributive property to break down the multiplication into manageable parts.

Synthesized solution:
15 × 23 = 15 × (20 + 3) = (15 × 20) + (15 × 3) = 300 + 45 = 345

This combines the clarity of Solution 1 with the verification from Solution 2.
Answer: 345 ✓

- {pony}"""
        else:
            # Self-refinement
            return f"""Reviewing the candidate solution, I can refine it:

The approach is correct. Let me make it clearer:
15 × 23 = 345

Step-by-step verification:
1. Break apart: 23 = 20 + 3
2. Distribute: 15 × 20 = 300, and 15 × 3 = 45
3. Sum: 300 + 45 = 345

This is the refined, clearer version.

- {pony}"""

    def _mock_generic_response(self, prompt: str, pony: str) -> str:
        """Generic mock response."""
        return f"""I understand you're asking about: {prompt[:50]}...

Here's my response based on the available context and reasoning.

- {pony}"""
