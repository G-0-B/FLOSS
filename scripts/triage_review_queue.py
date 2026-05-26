"""Quick triage classification for the review queue.

Reads docs/knowledge_log/staging/*_draft.json and harvest staging YAMLs, and
classifies them by source-file survival + size + area. Read-only.
"""

import json
import re
import statistics
import sys
from pathlib import Path

STAGING = Path("docs/knowledge_log/staging")
HARVEST = Path("../.agent-surface/harvest/staging")
WS = Path("C:/~shit")
FLOSS = Path("C:/~shit/FLOSS")


def classify_synthesis_drafts():
    drafts = sorted(STAGING.glob("*_draft.json"))
    if not drafts:
        print("No synthesis drafts found.")
        return
    exists_in_canon = 0
    missing_source = 0
    sizes = []
    by_area = {}
    samples_missing = []
    for p in drafts:
        try:
            d = json.load(p.open())
            src = d.get("file_path", "")
            ins = d.get("insights", "")
            sizes.append(len(ins))
            src_norm = src.replace("\\", "/")
            m = re.search(r"C:/~shit/(.+)$", src_norm)
            rel = m.group(1) if m else src_norm
            area = rel.split("/")[0] if rel else "?"
            by_area[area] = by_area.get(area, 0) + 1
            abs_path = WS / rel
            if abs_path.exists():
                exists_in_canon += 1
            else:
                missing_source += 1
                if len(samples_missing) < 8:
                    samples_missing.append((p.name, rel))
        except Exception:
            pass
    print(f"# Synthesis drafts: {len(drafts)}")
    print(f"  Source still in canon: {exists_in_canon}")
    print(f"  Source missing (moved/deleted): {missing_source}")
    print(
        f"  Insights total: {sum(sizes) / 1024:.1f} KB  "
        f"median={statistics.median(sizes):.0f}  max={max(sizes)}"
    )
    print()
    print("By source area:")
    for area, count in sorted(by_area.items(), key=lambda x: -x[1]):
        print(f"  {count:>4}  {area}")
    print()
    print("Sample missing-source drafts (orphans):")
    for n, r in samples_missing:
        print(f"  {n[:70]}\n      <- {r[:90]}")


if __name__ == "__main__":
    classify_synthesis_drafts()
