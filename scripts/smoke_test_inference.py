"""
Smoke test: verify Cerebras + Groq free-tier inference works.

Loads FLOSS/.env, makes one call to each provider, prints result + latency.
Exits 0 if BOTH work, 1 if any fail.

Run:
    C:/Python313/python.exe FLOSS/scripts/smoke_test_inference.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"

if not ENV_PATH.exists():
    print(f"FAIL: {ENV_PATH} not found", file=sys.stderr)
    sys.exit(1)

load_dotenv(ENV_PATH)

if not os.environ.get("CEREBRAS_API_KEY"):
    print("FAIL: CEREBRAS_API_KEY not loaded", file=sys.stderr)
    sys.exit(1)
if not os.environ.get("GROQ_API_KEY"):
    print("FAIL: GROQ_API_KEY not loaded", file=sys.stderr)
    sys.exit(1)

from litellm import completion  # noqa: E402

PROMPT = "Say the single word READY and nothing else."

# Conservative model picks: 8B Llama everywhere. Known-good across providers.
# Upgrade to 70B / Llama 4 once these prove the pipe works.
TARGETS = [
    ("Cerebras", "cerebras/llama3.1-8b"),
    ("Groq", "groq/llama-3.1-8b-instant"),
]


def call_one(model: str) -> tuple[bool, str, float]:
    """Run one inference call against `model` and return success, text, and latency."""
    t0 = time.perf_counter()
    try:
        resp = completion(
            model=model,
            messages=[{"role": "user", "content": PROMPT}],
            max_tokens=16,
            temperature=0.0,
        )
        dt = time.perf_counter() - t0
        content = resp.choices[0].message.content or ""
        return True, content.strip(), dt
    except Exception as exc:  # noqa: BLE001
        dt = time.perf_counter() - t0
        return False, f"{type(exc).__name__}: {exc}", dt


def main() -> int:
    """Run the smoke test against the configured free-tier inference providers."""
    failures = 0
    print("=" * 60)
    print("FLOSSIØULLK inference smoke test")
    print(f"Keys loaded from: {ENV_PATH}")
    print("=" * 60)

    for label, model in TARGETS:
        ok, msg, dt = call_one(model)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {label:10s} {model}  ({dt*1000:.0f} ms)")
        print(f"         → {msg[:200]}")
        if not ok:
            failures += 1

    print("=" * 60)
    if failures == 0:
        print("All providers responded. Sovereign inference stack is LIVE.")
        return 0
    print(f"{failures} provider(s) failed. See errors above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
