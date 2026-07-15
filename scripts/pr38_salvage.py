from __future__ import annotations

from pathlib import Path
import sys

# Direct checkout invocation puts ``scripts/`` rather than the repository root
# on sys.path. Keep this bootstrap local to the process so the delegated entry
# point remains a thin call into the tested package implementation.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.salvage_spine.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
