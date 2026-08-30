"""In-process exclusive file-claim table.

One holder per normalized path. Not the computer-use surface lease table.
"""

from __future__ import annotations


class ClaimConflict(Exception):
    """Path already held, or release holder mismatch."""

    def __init__(self, path: str, holder: str, message: str | None = None) -> None:
        self.path = path
        self.holder = holder
        super().__init__(message or f"path {path!r} held by {holder}")


class ClaimTable:
    """Exclusive map path -> agent_id."""

    def __init__(self) -> None:
        self._holders: dict[str, str] = {}

    def claim(self, agent_id: str, path: str) -> None:
        if not agent_id.strip():
            raise ValueError("empty agent_id")
        holder = self._holders.get(path)
        if holder is None:
            self._holders[path] = agent_id
            return
        if holder == agent_id:
            return
        raise ClaimConflict(path, holder)

    def release(self, agent_id: str, path: str) -> None:
        holder = self._holders.get(path)
        if holder is None:
            return
        if holder != agent_id:
            raise ClaimConflict(path, holder, f"holder mismatch on release of {path!r}")
        del self._holders[path]

    def force_set(self, path: str, agent_id: str) -> None:
        """Replay helper. Log already recorded a successful claim."""
        self._holders[path] = agent_id

    def force_drop(self, path: str) -> None:
        """Replay helper. Log already recorded a successful release."""
        self._holders.pop(path, None)

    def snapshot(self) -> dict[str, str]:
        return dict(self._holders)
