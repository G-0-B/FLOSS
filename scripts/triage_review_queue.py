"""DEPRECATED shim — merged into review_queue.py.

Use `python FLOSS/scripts/review_queue.py --triage` instead.

The former standalone triage classifier only covered synthesis drafts (its
docstring claimed harvest coverage it never implemented) and carried hardcoded
workspace paths. Its unique capability — source-survival/orphan detection plus
size and area stats — now lives in `review_queue.render_triage`, extended to
both staging surfaces. Merge per metaharness-inventory decision D6
(consolidation pass, 2026-06-12). This shim is kept for entry-point
compatibility and delegates entirely.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from review_queue import collect_review_items, render_triage  # noqa: E402


if __name__ == "__main__":
    print(render_triage(collect_review_items()), end="")
    print(
        "[deprecated] use: python FLOSS/scripts/review_queue.py --triage",
        file=sys.stderr,
    )
