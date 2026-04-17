"""Core modules for desktop pony swarm."""

from .horde_client import HordeClient
from .pony_agent import DesktopPonyAgent
from .swarm import PonySwarm
from .embedding import SwarmEmbeddingManager

__all__ = ["HordeClient", "DesktopPonyAgent", "PonySwarm", "SwarmEmbeddingManager"]
