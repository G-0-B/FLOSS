"""ObjectGraph spike — typed node-level projection over skill-corpus (N6).

Concept-not-import re-expression of ObjectGraph progressive-disclosure
traversal (OVCA audit decision D2; spike GO per Anthony 2026-06-12). Extends
the document-granular CONTEXT_L0/L1 emitter pattern with the two dimensions it
deliberately omits: per-section nodes and edges (contains / next / refs).

Spec: FLOSS/docs/superpowers/specs/2026-06-12-objectgraph-spike.md
Output: .agent-surface/context/objectgraph/skill-corpus.json — a READ-ONLY,
NON-CANONICAL projection. It never feeds canon writes. Keyword scoring only
(symbolic-first; no LLM in the loop), same posture as context_router.py.

Usage:
    python FLOSS/scripts/objectgraph_spike.py                    # build index
    python FLOSS/scripts/objectgraph_spike.py resolve --query "token budget"
    python FLOSS/scripts/objectgraph_spike.py expand --node <node_id>

Risk mitigations built in (per the resume gate):
  - Cross-node synthesis regression: resolve emits an advisory to read full
    docs when hits spread across >=3 documents with near-equal scores.
  - Adversarial routing: provenance paths always printed; deterministic
    rebuild from sources; index carries a non-canonical banner.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
CORPUS_ROOT = REPO_ROOT / "skill-corpus"
OUTPUT_PATH = WORKSPACE_ROOT / ".agent-surface" / "context" / "objectgraph" / "skill-corpus.json"

SUMMARY_CHARS = 240
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_LINK_RE = re.compile(r"\]\(([^)#?]+\.md)[^)]*\)")
_WORD_RE = re.compile(r"[a-z0-9]+")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:80] or "untitled"


def _doc_type(rel_path: Path) -> str:
    name = rel_path.name.lower()
    if name == "skill.md":
        return "skill"
    if name == "changelog.md":
        return "changelog"
    if "references" in rel_path.parts:
        return "reference"
    return "doc"


def _summary(lines: list[str]) -> str:
    para: list[str] = []
    in_code = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code or _HEADING_RE.match(stripped):
            continue
        if stripped:
            para.append(stripped)
        elif para:
            break
    return " ".join(para)[:SUMMARY_CHARS]


def _split_sections(text: str) -> list[tuple[str, int, int, int]]:
    """Return (heading, level, start_line, end_line) per section.

    Line 0 to the first heading is the preamble section (heading = '').
    Headings inside fenced code blocks are ignored.
    """
    lines = text.splitlines()
    marks: list[tuple[int, str, int]] = []
    in_code = False
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = _HEADING_RE.match(line)
        if m:
            marks.append((i, m.group(2).strip(), len(m.group(1))))
    sections: list[tuple[str, int, int, int]] = []
    if not marks or marks[0][0] > 0:
        end = marks[0][0] if marks else len(lines)
        sections.append(("", 0, 0, end))
    for idx, (start, heading, level) in enumerate(marks):
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(lines)
        sections.append((heading, level, start, end))
    return sections


def build_index(corpus_root: Path = CORPUS_ROOT) -> dict:
    nodes: list[dict] = []
    edges: list[dict] = []
    doc_ids_by_rel: dict[str, str] = {}
    docs = sorted(p for p in corpus_root.rglob("*.md") if p.is_file())

    for path in docs:
        rel = path.relative_to(corpus_root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        doc_id = "doc:" + _slug(rel)
        doc_ids_by_rel[rel] = doc_id
        title = next(
            (m.group(2).strip() for ln in lines[:20] if (m := _HEADING_RE.match(ln))),
            path.stem,
        )
        nodes.append(
            {
                "id": doc_id,
                "type": _doc_type(Path(rel)),
                "title": title,
                "path": (REPO_ROOT / "skill-corpus" / rel).relative_to(WORKSPACE_ROOT).as_posix(),
                "word_count": len(_WORD_RE.findall(text.lower())),
            }
        )

        prev_section_id: str | None = None
        for heading, level, start, end in _split_sections(text):
            section_lines = lines[start:end]
            body = "\n".join(section_lines)
            sec_id = f"{doc_id}#{_slug(heading) if heading else 'preamble'}-{start}"
            nodes.append(
                {
                    "id": sec_id,
                    "type": "section",
                    "title": heading or "(preamble)",
                    "doc": doc_id,
                    "level": level,
                    "lines": [start, end],
                    "summary": _summary(section_lines),
                    "word_count": len(_WORD_RE.findall(body.lower())),
                }
            )
            edges.append({"from": doc_id, "to": sec_id, "kind": "contains"})
            if prev_section_id:
                edges.append({"from": prev_section_id, "to": sec_id, "kind": "next"})
            prev_section_id = sec_id

        for target in _LINK_RE.findall(text):
            target_rel = (Path(rel).parent / target).as_posix()
            target_rel = re.sub(r"(^|/)\./", r"\1", target_rel)
            while "../" in target_rel:
                target_rel = re.sub(r"[^/]+/\.\./", "", target_rel, count=1)
            if target_rel in doc_ids_by_rel or (corpus_root / target_rel).exists():
                edges.append({"from": doc_id, "to_rel": target_rel, "kind": "refs"})

    # second pass: resolve refs edges to node ids where possible
    for edge in edges:
        if edge["kind"] == "refs" and "to_rel" in edge:
            target = doc_ids_by_rel.get(edge.pop("to_rel"))
            if target:
                edge["to"] = target
            else:
                edge["to"] = "unresolved"

    return {
        "banner": "NON-CANONICAL read-only projection — rebuild from sources; never cite as truth, always verify at the provenance path",
        "spec": "FLOSS/docs/superpowers/specs/2026-06-12-objectgraph-spike.md",
        "corpus_root": corpus_root.relative_to(WORKSPACE_ROOT).as_posix(),
        "stats": {
            "documents": len(docs),
            "nodes": len(nodes),
            "edges": len(edges),
        },
        "nodes": nodes,
        "edges": [e for e in edges if e.get("to") != "unresolved"],
    }


def write_index(index: dict) -> bool:
    """Content-diffed write (materializer pattern). True if written."""
    rendered = json.dumps(index, indent=2, ensure_ascii=False) + "\n"
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        if OUTPUT_PATH.read_text(encoding="utf-8") == rendered:
            return False
    except OSError:
        pass
    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    return True


def _score(query_words: list[str], node: dict) -> int:
    haystack = " ".join(
        [node.get("title", ""), node.get("summary", ""), node.get("id", "")]
    ).lower()
    return sum(3 if w in node.get("title", "").lower() else 1 for w in query_words if w in haystack)


def resolve(query: str, limit: int = 5) -> dict:
    index = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    query_words = _WORD_RE.findall(query.lower())
    sections = [n for n in index["nodes"] if n["type"] == "section"]
    scored = sorted(
        ((s, _score(query_words, s)) for s in sections),
        key=lambda pair: -pair[1],
    )
    hits = [(s, sc) for s, sc in scored[:limit] if sc > 0]
    docs_by_id = {n["id"]: n for n in index["nodes"] if n["type"] != "section"}

    top_docs = {s["doc"] for s, _ in hits}
    advisory = None
    if len(hits) >= 3 and len(top_docs) >= 3:
        scores = [sc for _, sc in hits[:3]]
        if scores[0] and scores[-1] / scores[0] >= 0.6:
            advisory = (
                "synthesis-query advisory: top hits spread across "
                f"{len(top_docs)} documents with near-equal scores — node-level "
                "retrieval underperforms full-doc reading on cross-node "
                "synthesis (ObjectGraph eval: 77.9 vs 82.1). Consider reading "
                "the full documents listed instead of assembling nodes."
            )

    return {
        "query": query,
        "advisory": advisory,
        "hits": [
            {
                "node": s["id"],
                "score": sc,
                "title": s["title"],
                "summary": s.get("summary", ""),
                "provenance": docs_by_id.get(s["doc"], {}).get("path", "?")
                + f" lines {s['lines'][0]}-{s['lines'][1]}",
            }
            for s, sc in hits
        ],
    }


def expand(node_id: str) -> str:
    index = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    node = next((n for n in index["nodes"] if n["id"] == node_id), None)
    if node is None:
        return f"objectgraph: unknown node {node_id}"
    if node["type"] != "section":
        return f"objectgraph: {node_id} is a document node — read {node['path']} directly"
    doc = next(n for n in index["nodes"] if n["id"] == node["doc"])
    source = WORKSPACE_ROOT / doc["path"]
    lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    start, end = node["lines"]
    return "\n".join(
        [f"# source: {doc['path']} lines {start}-{end} (verify at the artifact)"]
        + lines[start:end]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="ObjectGraph spike over skill-corpus")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("build", help="Build/refresh the index (default)")
    p_resolve = sub.add_parser("resolve", help="Query the node index")
    p_resolve.add_argument("--query", required=True)
    p_resolve.add_argument("--limit", type=int, default=5)
    p_expand = sub.add_parser("expand", help="Fetch full section text for a node")
    p_expand.add_argument("--node", required=True)
    args = parser.parse_args()

    if args.cmd == "resolve":
        if not OUTPUT_PATH.exists():
            write_index(build_index())
        print(json.dumps(resolve(args.query, args.limit), indent=2, ensure_ascii=False))
        return 0
    if args.cmd == "expand":
        print(expand(args.node))
        return 0

    index = build_index()
    wrote = write_index(index)
    stats = index["stats"]
    print(
        f"objectgraph: {'WROTE' if wrote else 'OK (unchanged)'} {OUTPUT_PATH} — "
        f"{stats['documents']} docs, {stats['nodes']} nodes, {stats['edges']} edges"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
