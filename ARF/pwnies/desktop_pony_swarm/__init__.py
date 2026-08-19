"""Desktop Pony RSA Swarm - FLOSSI0ULLK Implementation"""

__version__ = "0.1.0"

from .core import PonySwarm, DesktopPonyAgent, HordeClient, SwarmEmbeddingManager
from .config.settings import DEFAULT_CONFIG

__all__ = [
    "PonySwarm",
    "DesktopPonyAgent",
    "HordeClient",
    "SwarmEmbeddingManager",
    "DEFAULT_CONFIG",
]
