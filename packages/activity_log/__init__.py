"""Shared activity-log primitive for the metaharness unification.

Per `FLOSS/docs/research/2026-05-18-metaharness-unification.md` §3.2:
all harnesses emit a uniform Action record to `.agent-surface/activity.jsonl`.
This module is the shared helper. Backwards-compatible: per-subsystem logs
keep working; this is the global tee that lets the holistic surface roll up.
"""

from .schema import Action, append_action

__all__ = ["Action", "append_action", "provenance"]


def __getattr__(name):
    """Lazily expose the provenance submodule (PEP 562).

    Importing `packages.activity_log` (or a sibling submodule such as
    `.schema`, which runs this `__init__` first) must NOT eagerly import
    `provenance`, because that pulls in the provenance extras (blake3, jcs,
    nacl). Lean consumers — the reasoning router/MCP server, plain activity
    logging — only need `Action`/`append_action` and would otherwise fail at
    import time when those extras are absent. Provenance consumers still get
    the module on first attribute access (`activity_log.provenance`) or via the
    direct submodule import (`from packages.activity_log import provenance`).
    """
    if name == "provenance":
        # Use importlib rather than `from . import provenance`: the latter goes
        # through the import machinery's `hasattr(self, "provenance")` check,
        # which re-enters this very __getattr__ and infinite-loops when the
        # provenance deps are missing. import_module imports the submodule
        # directly and lets a genuine ModuleNotFoundError(blake3/...) propagate.
        import importlib

        return importlib.import_module(f"{__name__}.provenance")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
