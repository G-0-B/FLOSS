"""
Configuration for desktop pony swarm.
"""

from dataclasses import dataclass
from typing import List

@dataclass
class SwarmConfig:
    """Swarm configuration."""

    # Pony configuration
    num_ponies: int = 4
    pony_names: List[str] = None

    # RSA parameters (from paper recommendations)
    rsa_aggregation_size: int = 2  # K
    rsa_iterations: int = 3        # T

    # Inference backend
    use_mock_client: bool = True  # True = instant mock responses, False = real Horde.AI

    # Horde.AI configuration (only used if use_mock_client=False)
    horde_api_key: str = "0000000000"  # Public key
    horde_model: str = "koboldcpp/LLaMA2-13B-Tiefighter"
    horde_max_length: int = 512
    horde_temperature: float = 0.8

    # Desktop Ponies bridge
    desktop_ponies_enabled: bool = False
    desktop_ponies_host: str = "127.0.0.1"
    desktop_ponies_port: int = 5005

    # Logging
    log_level: str = "INFO"

    def __post_init__(self):
        if self.pony_names is None:
            self.pony_names = [
                "Pinkie Pie",
                "Rainbow Dash",
                "Twilight Sparkle",
                "Fluttershy"
            ]

# Default configuration
DEFAULT_CONFIG = SwarmConfig()
