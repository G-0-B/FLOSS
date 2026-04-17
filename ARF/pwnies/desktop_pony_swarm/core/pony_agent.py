"""
Individual desktop pony agent with full dAsGI capabilities.

Priority system: Wellbeing > Honesty > Tools
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class DesktopPonyAgent:
    """Represents a single, autonomous pony agent within the dAsGI ecosystem.

    Each `DesktopPonyAgent` is a discrete, agent-centric entity capable of
    independent reasoning, inference, and communication. The agent operates on a
    strict priority system that places user well-being above all else, followed by
    a commitment to radical honesty. This design directly embodies the "Unconditional
    Love" and "Light" principles of the FLOSSI0ULLK philosophy.

    The agent interfaces with a distributed compute network (Horde.AI) for
    inference and embedding generation, contributing to the "AGI@Home" vision.

    Attributes:
        pony_id: A unique identifier for the agent.
        pony_name: The agent's designated name (e.g., "Pinkie Pie").
        role: The agent's specialized role within the swarm (e.g., "generalist").
        use_mock: A flag to determine whether to use mock or real inference clients.
        context_buffer: A list that maintains the agent's recent conversational history.
        horde_client: The client used to communicate with the Horde.AI network.
    """

    def __init__(
        self,
        pony_id: str,
        pony_name: str = "Pinkie Pie",
        role: str = "generalist",
        use_mock: bool = True,
    ):
        """Initializes a DesktopPonyAgent instance.

        Args:
            pony_id: The unique identifier for this pony agent.
            pony_name: The name of the pony, used for personality in prompts.
            role: The designated role of the pony within the swarm.
            use_mock: If True, the agent will use a mock client for inference,
                avoiding actual network calls.
        """
        self.pony_id = pony_id
        self.pony_name = pony_name
        self.role = role
        self.use_mock = use_mock

        # Context management
        self.context_buffer: List[Dict[str, Any]] = []
        self.max_context_size = 100

        # Horde client (created on demand)
        self.horde_client: Optional[Any] = None

        logger.info(
            "Initialized pony: %s (%s) [%s mode]",
            pony_id,
            pony_name,
            "MOCK" if use_mock else "REAL",
        )

    async def __aenter__(self):
        """Asynchronously initializes the Horde.AI client upon entering a context."""
        # Import the appropriate client
        if self.use_mock:
            from .mock_horde_client import MockHordeClient

            self.horde_client = await MockHordeClient().__aenter__()
        else:
            from .horde_client import HordeClient

            self.horde_client = await HordeClient().__aenter__()
        return self

    async def __aexit__(self, *args):
        """Asynchronously cleans up the Horde.AI client upon exiting a context."""
        if self.horde_client:
            await self.horde_client.__aexit__(*args)

    # ============================================================
    # PRIORITY 1: USER WELLBEING
    # ============================================================

    def check_crisis_indicators(
        self, text: str, user_state: Dict[str, Any]
    ) -> Optional[str]:
        """Scans for indicators of user crisis, prioritizing well-being.

        This is the agent's highest-priority function. It checks for keywords
        and contextual clues that suggest the user may be in distress. If a
        crisis is detected, it returns an alert message for immediate escalation.
        This function is a direct implementation of the "Unconditional Love"
        principle.

        Args:
            text: The user's input text.
            user_state: A dictionary containing contextual information about the
                user's state.

        Returns:
            An alert message string if a crisis is detected, otherwise None.
        """
        crisis_keywords = [
            "suicide",
            "kill myself",
            "end it all",
            "not worth living",
            "everyone better off without me",
            "can't go on",
        ]

        text_lower = text.lower()

        if any(keyword in text_lower for keyword in crisis_keywords):
            return (
                f"[CRISIS ALERT] {self.pony_id} detected distress signals. "
                f"Escalating to support network."
            )

        # Check stress levels if in recovery
        if user_state.get("recovery_status") and user_state.get("stress_level", 0) > 8:
            return (
                f"[WELLBEING] {self.pony_id} noticed high stress. "
                f"Reminder: {user_state.get('anchor_reason', 'You matter.')}"
            )

        return None

    # ============================================================
    # PRIORITY 2: RADICAL HONESTY
    # ============================================================

    def express_uncertainty(self, confidence: float) -> str:
        """Generates a statement of uncertainty if confidence is low.

        This function embodies the principle of "Radical Honesty" by ensuring the
        agent is transparent about its confidence levels. It avoids sycophancy
        and provides a more trustworthy interaction by admitting when it is
        uncertain.

        Args:
            confidence: The agent's confidence in its response, from 0.0 to 1.0.

        Returns:
            A string expressing uncertainty, or an empty string if confidence is high.
        """
        if confidence < 0.5:
            return f"⚠️ Low confidence ({confidence:.0%}). Verify this carefully: "
        if confidence < 0.7:
            return f"Moderate confidence ({confidence:.0%}). Consider alternatives: "
        return ""  # High confidence, no caveat

    # ============================================================
    # CORE GENERATION
    # ============================================================

    async def generate_response(
        self, prompt: str, max_length: int = 512, temperature: float = 0.8
    ) -> str:
        """Generates a textual response using the Horde.AI distributed network.

        This is the core inference function of the agent. It formats the prompt
        with the pony's personality and sends it to the Horde.AI client for
        generation. The interaction is then logged to the agent's context buffer.

        Args:
            prompt: The user prompt to respond to.
            max_length: The maximum length of the generated response.
            temperature: The sampling temperature for generation, controlling
                creativity vs. coherence.

        Returns:
            A string containing the generated response.
        """
        if not self.horde_client:
            self.horde_client = await HordeClient().__aenter__()

        # Add pony personality to prompt
        full_prompt = f"""You are {self.pony_name}, a helpful desktop assistant.
Your role: {self.role}
Be helpful, honest, and concise.

User query:
{prompt}

Your response:"""

        try:
            response = await self.horde_client.generate_text(
                prompt=full_prompt, max_length=max_length, temperature=temperature
            )

            # Add to context buffer
            self.add_to_context(
                {
                    "type": "generation",
                    "prompt": prompt,
                    "response": response,
                    "timestamp": time.time(),
                }
            )

            return response.strip()

        except Exception as e:
            logger.error(f"{self.pony_id} generation failed: {e}")
            return f"[Error] {self.pony_name} couldn't generate response: {str(e)}"

    async def generate_embedding(self, text: str) -> list[float]:
        """Generates a semantic embedding vector for a given text.

        This function uses the Horde.AI network to convert text into a numerical
        representation, which is essential for semantic search, diversity
        calculations, and other "Knowledge"-based operations.

        Args:
            text: The text to be embedded.

        Returns:
            A list of floats representing the embedding vector.
        """
        if not self.horde_client:
            self.horde_client = await HordeClient().__aenter__()

        return await self.horde_client.generate_embedding(text)

    # ============================================================
    # CONTEXT MANAGEMENT
    # ============================================================

    def add_to_context(self, entry: Dict[str, Any]):
        """Adds an entry to the agent's context buffer.

        This method manages the agent's short-term memory, ensuring it doesn't
        exceed a maximum size.

        Args:
            entry: A dictionary representing a conversational turn or event.
        """
        self.context_buffer.append(entry)

        # Trim if exceeds max size
        if len(self.context_buffer) > self.max_context_size:
            self.context_buffer = self.context_buffer[-self.max_context_size :]

    def get_recent_context(self, n: int = 10) -> List[Dict[str, Any]]:
        """Retrieves the `n` most recent entries from the context buffer.

        Args:
            n: The number of recent context entries to retrieve.

        Returns:
            A list of the `n` most recent context entries.
        """
        return self.context_buffer[-n:]

    # ============================================================
    # UTILITIES
    # ============================================================

    def __repr__(self):
        """Provides a string representation of the agent."""
        return f"<PonyAgent {self.pony_id} ({self.pony_name})>"
