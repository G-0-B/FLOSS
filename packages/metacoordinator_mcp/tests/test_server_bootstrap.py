"""Tests for MCP server bootstrap env loading."""

from __future__ import annotations

import importlib
import builtins
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
    """Temporarily replace the MCP bootstrap environment variables."""
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
    """Re-import the server module so bootstrap runs from scratch."""
    sys.modules.pop("packages.metacoordinator_mcp.server", None)
    return importlib.import_module("packages.metacoordinator_mcp.server")


@contextmanager
def missing_fastmcp():
    """Temporarily block the FastMCP import to exercise bootstrap-only paths."""
    blocked = "mcp.server.fastmcp"
    cached = sys.modules.pop(blocked, None)

    def fake_import(
        name, module_globals=None, module_locals=None, fromlist=(), level=0
    ):
        """Raise on FastMCP imports while delegating everything else."""
        if name == blocked:
            raise ImportError("blocked for test")
        return original_import(name, module_globals, module_locals, fromlist, level)

    original_import = builtins.__import__
    builtins.__import__ = fake_import
    try:
        yield
    finally:
        builtins.__import__ = original_import
        if cached is not None:
            sys.modules[blocked] = cached


@contextmanager
def missing_dotenv():
    """Temporarily block python-dotenv imports to exercise bootstrap failures."""
    blocked = "dotenv"
    cached = sys.modules.pop(blocked, None)

    def fake_import(
        name, module_globals=None, module_locals=None, fromlist=(), level=0
    ):
        """Raise on dotenv imports while delegating every other import unchanged."""
        if name == blocked:
            raise ImportError("blocked for test")
        return original_import(name, module_globals, module_locals, fromlist, level)

    original_import = builtins.__import__
    builtins.__import__ = fake_import
    try:
        yield
    finally:
        builtins.__import__ = original_import
        if cached is not None:
            sys.modules[blocked] = cached


def test_server_bootstrap_loads_repo_env_when_process_env_missing():
    """Load provider keys from the repo env file when process env is empty."""
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
    """Keep explicit process env values ahead of repo env defaults."""
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


def test_server_imports_without_fastmcp_for_bootstrap_paths():
    """Import bootstrap paths cleanly when FastMCP is unavailable."""
    with tempfile.TemporaryDirectory() as tmp:
        env_path = Path(tmp) / ".env"
        env_path.write_text("GROQ_API_KEY=from-file\n", encoding="utf-8")
        with (
            patched_env(FLOSS_AGENT_DIR=tmp, FLOSS_ENV_PATH=str(env_path)),
            missing_fastmcp(),
        ):
            server = import_server_module()
            assert server.mcp is None
            assert os.environ["GROQ_API_KEY"] == "from-file"


def test_server_bootstrap_surfaces_missing_dotenv_for_repo_env_file():
    """Raise a clear bootstrap error when a repo env file exists but dotenv is missing."""
    with tempfile.TemporaryDirectory() as tmp:
        env_path = Path(tmp) / ".env"
        env_path.write_text("GROQ_API_KEY=from-file\n", encoding="utf-8")
        with (
            patched_env(FLOSS_AGENT_DIR=tmp, FLOSS_ENV_PATH=str(env_path)),
            missing_dotenv(),
        ):
            try:
                import_server_module()
            except RuntimeError as exc:
                assert "python-dotenv is required" in str(exc)
            else:
                raise AssertionError("Expected RuntimeError when dotenv is unavailable")


def _run_all() -> int:
    """Run the standalone bootstrap test module without requiring pytest."""
    tests = [
        test_server_bootstrap_loads_repo_env_when_process_env_missing,
        test_server_bootstrap_preserves_explicit_process_env,
        test_server_imports_without_fastmcp_for_bootstrap_paths,
        test_server_bootstrap_surfaces_missing_dotenv_for_repo_env_file,
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
