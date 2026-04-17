"""Route queries to the most relevant FLOSSI0ULLK context corpora."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST_PATH = REPO_ROOT / "shared-context-surface.json"
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9\-_/.:+]*")


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("corpora"), list):
        raise ValueError(f"Invalid context manifest: {path}")
    return payload


def tokenize(text: str) -> set[str]:
    lower = text.lower()
    return set(TOKEN_RE.findall(lower))


def score_corpus(corpus: dict[str, Any], query: str) -> tuple[int, list[str]]:
    tokens = tokenize(query)
    matched: list[str] = []
    score = 0

    for keyword in corpus.get("keywords", []):
        keyword_tokens = tokenize(str(keyword))
        if keyword_tokens and keyword_tokens.issubset(tokens):
            matched.append(str(keyword))
            score += 120 if len(keyword_tokens) > 1 else 80
        elif keyword_tokens and tokens.intersection(keyword_tokens):
            matched.append(str(keyword))
            score += 35

    id_tokens = tokenize(str(corpus.get("id", "")))
    uri_tokens = tokenize(str(corpus.get("uri", "")))
    summary_tokens = tokenize(str(corpus.get("summary", "")))
    overlap = tokens.intersection(id_tokens | uri_tokens | summary_tokens)
    score += len(overlap) * 15
    score += int(corpus.get("priority", 0))
    return score, sorted(set(matched))


def choose_corpora(manifest: dict[str, Any], query: str, limit: int) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for corpus in manifest["corpora"]:
        score, matched = score_corpus(corpus, query)
        enriched = dict(corpus)
        enriched["score"] = score
        enriched["matched_keywords"] = matched
        ranked.append(enriched)

    ranked.sort(key=lambda item: (-int(item["score"]), -int(item.get("priority", 0)), item["id"]))
    return ranked[:limit]


def render_markdown(results: list[dict[str, Any]], query: str) -> str:
    lines = [
        f"# Context Route For `{query}`",
        "",
    ]
    for item in results:
        lines.extend([
            f"## `{item['id']}` (`{item['uri']}`)",
            f"- Score: `{item['score']}`",
            f"- Tier: `{item['tier']}`",
            f"- Summary: {item['summary']}",
        ])
        if item["matched_keywords"]:
            lines.append("- Matched keywords:")
            for keyword in item["matched_keywords"]:
                lines.append(f"  - `{keyword}`")
        lines.append("- Roots:")
        for root in item.get("roots", []):
            lines.append(f"  - `{root}`")
        lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Route a query to FLOSSI0ULLK context corpora")
    parser.add_argument("query", nargs="*", help="Query or intent text to route")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--list", action="store_true", help="List corpora without scoring")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest.resolve())

    if args.list:
        payload = manifest["corpora"]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    query = " ".join(args.query).strip()
    if not query:
        raise SystemExit("Provide a query or use --list")

    results = choose_corpora(manifest, query, max(1, args.limit))
    if args.format == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(results, query))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
