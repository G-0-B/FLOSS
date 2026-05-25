"""Shared activity-log primitive for the metaharness unification.

Per `FLOSS/docs/research/2026-05-18-metaharness-unification.md` §3.2:
all harnesses emit a uniform Action record to `.agent-surface/activity.jsonl`.
This module is the shared helper. Backwards-compatible: per-subsystem logs
keep working; this is the global tee that lets the holistic surface roll up.
"""

from . import provenance
from .schema import Action, append_action

__all__ = ["Action", "append_action", "provenance"]
