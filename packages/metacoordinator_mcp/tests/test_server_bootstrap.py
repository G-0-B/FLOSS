"""Tests for MCP server bootstrap env loading."""

from __future__ import annotations

import importlib
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

ENV_KEYS = (
    "FLOSS_AGENT_DIR",
    "FLOSS_ENV_PATH",
    "GROQ_API_KEY",
    "MISTRAL_API_KEY",
)


@contextmanager
def patched_env(**updates: str | None):
    snapshot = {key: os.environ.get(key) for key in ENV_KEYS}
    try:
        for key in ENV_KEYS:
            os.environ.pop(key, None)
        for key, value in updates.items():
            if value is not None:
                os.environ[key] = value
        yield
    finally:
        for key in ENV_KEYS:
            os.environ.pop(key, None)
        for key, value in snapshot.items():
            if value is not None:
                os.environ[key] = value


def import_server_module():
    sys.modules.pop("packages.metacoordinator_mcp.server", None)
    return importlib.import_module("packages.metacoordinator_mcp.server")


def test_server_bootstrap_loads_repo_env_when_process_env_missing():
    with tempfile.TemporaryDirectory() as tmp:
        env_path = Path(tmp) / ".env"
        env_path.write_text(
            "GROQ_API_KEY=from-file\nMISTRAL_API_KEY=from-file-mistral\n",
            encoding="utf-8",
        )
        with patched_env(FLOSS_AGENT_DIR=tmp, FLOSS_ENV_PATH=str(env_path)):
            server = import_server_module()
            assert os.environ["GROQ_API_KEY"] == "from-file"
            assert os.environ["MISTRAL_API_KEY"] == "from-file-mistral"
            assert server.BASE_DIR == Path(tmp)


def test_server_bootstrap_preserves_explicit_process_env():
    with tempfile.TemporaryDirectory() as tmp:
        env_path = Path(tmp) / ".env"
        env_path.write_text(
            "GROQ_API_KEY=from-file\nMISTRAL_API_KEY=from-file-mistral\n",
            encoding="utf-8",
        )
        with patched_env(
            FLOSS_AGENT_DIR=tmp,
            FLOSS_ENV_PATH=str(env_path),
            GROQ_API_KEY="from-env",
        ):
            import_server_module()
            assert os.environ["GROQ_API_KEY"] == "from-env"
            assert os.environ["MISTRAL_API_KEY"] == "from-file-mistral"


def _run_all() -> int:
    tests = [
        test_server_bootstrap_loads_repo_env_when_process_env_missing,
        test_server_bootstrap_preserves_explicit_process_env,
    ]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL  {test.__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(_run_all())
