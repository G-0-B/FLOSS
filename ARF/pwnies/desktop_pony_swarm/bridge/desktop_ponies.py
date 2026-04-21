"""
Bridge to Desktop Ponies application.

Uses socket communication to send commands to Desktop Ponies.
"""

import socket
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class DesktopPoniesBridge:
    """
    Communication bridge to Desktop Ponies app.
    
    Desktop Ponies can display:
    - Speech bubbles
    - Animations
    - Position changes
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 5005):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None

    def connect(self):
        """Connect to Desktop Ponies."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            logger.info(f"Connected to Desktop Ponies at {self.host}:{self.port}")
        except Exception as e:
            logger.warning(f"Could not connect to Desktop Ponies: {e}")
            self.socket = None

    def send_speech(self, pony_name: str, text: str):
        """Send speech bubble to pony."""
        if not self.socket:
            logger.debug(f"[{pony_name}] {text}")
            return

        try:
            message = f"{pony_name} says: {text}\n"
            self.socket.sendall(message.encode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to send speech: {e}")

    def send_animation(self, pony_name: str, animation: str):
        """Trigger pony animation."""
        if not self.socket:
            logger.debug(f"[{pony_name}] animation: {animation}")
            return

        try:
            message = f"{pony_name} animate: {animation}\n"
            self.socket.sendall(message.encode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to send animation: {e}")

    def close(self):
        """Close connection."""
        if self.socket:
            self.socket.close()
            self.socket = None
