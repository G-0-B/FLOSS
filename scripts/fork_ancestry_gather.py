"""
Gather upstream metadata + README excerpts for a list of kalisam forks.

Per ancestry-sweep-v1.0.md, this collects the structured data a sweep needs:
  - parent (upstream) repo identity
  - parent description, stars, fork count, last push, license
  - parent README first ~120 lines (filename-pattern dependent)
  - the kalisam fork's last activity for divergence inspection

It does NOT sync — sync is a separate step (see fork_ancestry_sync.sh) so
that gather can run on the network's clock and sync can run on git's clock.

Usage:
    python FLOSS/scripts/fork_ancestry_gather.py \
        --forks-file /tmp/fork_names.txt \
        --output FLOSS/docs/research/2026-05-13-fork-ancestry-raw.json
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path


def gh_json(args: list[str]) -> dict | list:
    """Run gh CLI and parse JSON output. Returns {} on failure."""
    try:
        proc = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        if proc.returncode != 0:
            return {"_error": proc.stderr.strip()[:500]}
        return json.loads(proc.stdout) if proc.stdout.strip() else {}
    except Exception as exc:  # noqa: BLE001
        return {"_error": f"{type(exc).__name__}: {exc}"[:500]}


def gather_one(fork_name: str) -> dict:
    """Gather everything we need to ancestry-sweep one fork."""
    out: dict = {"fork": f"kalisam/{fork_name}"}

    # Fork metadata + parent ref
    fork_meta = gh_json([
        "repo", "view", f"kalisam/{fork_name}",
        "--json", "isFork,parent,pushedAt,description,defaultBranchRef",
    ])
    if "_error" in fork_meta:
        out["error"] = fork_meta["_error"]
        return out
    out["fork_pushed_at"] = fork_meta.get("pushedAt", "")
    out["fork_description"] = fork_meta.get("description") or ""
    parent = fork_meta.get("parent") or {}
    parent_owner = (parent.get("owner") or {}).get("login", "")
    parent_name = parent.get("name", "")
    if not parent_owner or not parent_name:
        out["error"] = "no parent (not a fork?)"
        return out
    out["upstream"] = f"{parent_owner}/{parent_name}"

    # Upstream metadata
    up_meta = gh_json([
        "repo", "view", f"{parent_owner}/{parent_name}",
        "--json", "description,stargazerCount,forkCount,pushedAt,"
                  "createdAt,licenseInfo,primaryLanguage,visibility",
    ])
    if "_error" in up_meta:
        out["upstream_error"] = up_meta["_error"]
        return out
    out["upstream_description"] = up_meta.get("description") or ""
    out["upstream_stars"] = up_meta.get("stargazerCount", 0)
    out["upstream_forks"] = up_meta.get("forkCount", 0)
    out["upstream_pushed_at"] = up_meta.get("pushedAt", "")
    out["upstream_created_at"] = up_meta.get("createdAt", "")
    out["upstream_license"] = (
        (up_meta.get("licenseInfo") or {}).get("spdxId") or "no-license"
    )
    out["upstream_language"] = (
        (up_meta.get("primaryLanguage") or {}).get("name") or "?"
    )

    # Upstream README (try the API path first)
    readme = gh_json([
        "api", f"repos/{parent_owner}/{parent_name}/readme",
    ])
    if "_error" not in readme and isinstance(readme, dict) and "content" in readme:
        try:
            decoded = base64.b64decode(readme["content"]).decode("utf-8", errors="replace")
            # Cap to ~120 lines worth (~8KB) to keep payload small
            lines = decoded.split("\n")[:120]
            out["readme_excerpt"] = "\n".join(lines)
            out["readme_path"] = readme.get("path", "README.md")
        except Exception as exc:  # noqa: BLE001
            out["readme_error"] = f"decode: {exc}"
    else:
        out["readme_error"] = readme.get("_error", "no readme")

    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Gather fork ancestry data")
    p.add_argument("--forks-file", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--skip", action="append", default=["FLOSS"],
                   help="Fork names to skip (own org's repo)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    fork_names = [
        line.strip()
        for line in args.forks_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("Names of")
    ]
    skip = set(args.skip)
    fork_names = [n for n in fork_names if n not in skip]
    print(f"Gathering {len(fork_names)} forks (skipping {sorted(skip)})...")
    results: list[dict] = []
    for i, name in enumerate(fork_names, 1):
        print(f"  [{i}/{len(fork_names)}] {name}", file=sys.stderr)
        results.append(gather_one(name))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Wrote {len(results)} entries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
