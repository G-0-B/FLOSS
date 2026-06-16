"""Backfill `kalisam_fork:` URLs in harvest staging drafts.

The harvest script (FLOSS/scripts/harvest_reuse_ledger.py) populates a YAML
draft per upstream repo with most fields, but `kalisam_fork:` is left blank
because the script doesn't know which kalisam fork (if any) points at each
upstream as its parent. This script fills in those URLs after the fact via
a single `gh api` call to enumerate kalisam's forks, builds a parent →
fork URL map, then rewrites each staging draft in place.

Plane A only — only touches `.agent-surface/harvest/staging/*_draft.yaml`.
Does not modify the canonical reuse-ledger-seed.yaml.

Usage:
    python FLOSS/scripts/backfill_kalisam_fork.py
    python FLOSS/scripts/backfill_kalisam_fork.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
STAGING_DIR = WORKSPACE_ROOT / ".agent-surface" / "harvest" / "staging"


def fetch_kalisam_forks() -> dict[str, str]:
    """Return {parent_owner/parent_name: kalisam_fork_url} for all kalisam forks."""
    cmd = ["gh", "repo", "list", "kalisam", "--fork", "--limit", "200",
           "--json", "name,parent"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    if proc.returncode != 0:
        print(f"ERROR: gh repo list failed: {proc.stderr}", file=sys.stderr)
        sys.exit(1)
    forks = json.loads(proc.stdout)
    mapping: dict[str, str] = {}
    for f in forks:
        parent = f.get("parent")
        if not parent:
            continue
        parent_owner = parent.get("owner", {}).get("login", "")
        parent_name = parent.get("name", "")
        if parent_owner and parent_name:
            key = f"{parent_owner}/{parent_name}".lower()
            mapping[key] = f"https://github.com/kalisam/{f['name']}"
    return mapping


def extract_url(yaml_text: str) -> str | None:
    """Pull the `url:` field value (top-level) from a YAML draft."""
    # match either `url: "..."` or `url: ...`
    m = re.search(r"^\s*url:\s*\"?([^\"\s]+)\"?\s*$", yaml_text, re.MULTILINE)
    return m.group(1) if m else None


def parse_owner_repo(url: str) -> tuple[str, str] | None:
    """Parse https://github.com/owner/repo → (owner, repo). None on miss."""
    m = re.match(r"https?://github\.com/([^/]+)/([^/\s]+?)(?:\.git)?/?$", url.strip())
    if not m:
        return None
    return m.group(1), m.group(2)


def backfill_draft(draft_path: Path, fork_map: dict[str, str], dry_run: bool) -> str:
    """Inspect one draft, attempt to fill kalisam_fork. Return status string."""
    text = draft_path.read_text(encoding="utf-8")

    # Already filled?
    already = re.search(r"^\s*kalisam_fork:\s*\"?(https?://\S+)", text, re.MULTILINE)
    if already:
        return "already_filled"

    url = extract_url(text)
    if not url:
        return "no_url_field"

    parsed = parse_owner_repo(url)
    if not parsed:
        return f"unparseable_url: {url}"
    owner, repo = parsed
    key = f"{owner}/{repo}".lower()

    fork_url = fork_map.get(key)
    if not fork_url:
        return f"no_kalisam_fork_for: {owner}/{repo}"

    # Match `kalisam_fork:` line (with or without trailing value) — replace it
    # Common shapes from the harvest output:
    #   kalisam_fork:           <empty>
    #   kalisam_fork:
    #   kalisam_fork: ""
    pattern = re.compile(r"^(\s*)kalisam_fork:\s*\"?\"?\s*$", re.MULTILINE)
    if not pattern.search(text):
        return "no_kalisam_fork_line"

    new_text = pattern.sub(rf'\1kalisam_fork: "{fork_url}"', text, count=1)

    if dry_run:
        return f"would_fill: {fork_url}"

    draft_path.write_text(new_text, encoding="utf-8")
    return f"filled: {fork_url}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without writing")
    args = parser.parse_args()

    if not STAGING_DIR.exists():
        print(f"ERROR: staging dir not found: {STAGING_DIR}", file=sys.stderr)
        return 1

    print("Fetching kalisam fork list...")
    fork_map = fetch_kalisam_forks()
    print(f"Loaded {len(fork_map)} kalisam forks")

    drafts = sorted(STAGING_DIR.glob("*_draft.yaml"))
    print(f"Found {len(drafts)} staging drafts\n")

    counts: dict[str, int] = {}
    for d in drafts:
        status = backfill_draft(d, fork_map, args.dry_run)
        # Categorize for summary
        bucket = status.split(":")[0]
        counts[bucket] = counts.get(bucket, 0) + 1
        # Print individual lines only for changes or anomalies
        if status.startswith(("filled", "would_fill", "no_kalisam_fork_for",
                              "unparseable_url", "no_kalisam_fork_line", "no_url_field")):
            print(f"  {d.name}: {status}")

    print("\n=== Summary ===")
    for bucket, n in sorted(counts.items()):
        print(f"  {bucket}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
