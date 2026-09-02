from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

FLOSS_ROOT = Path(__file__).resolve().parents[2]


def load_memory_module():
    script_path = FLOSS_ROOT / "scripts" / "materialize_shared_agent_memory.py"
    spec = importlib.util.spec_from_file_location("shared_agent_memory", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["shared_agent_memory"] = module
    spec.loader.exec_module(module)
    return module


def test_imports_legacy_claude_memory_into_canonical_tree(tmp_path):
    memory = load_memory_module()
    legacy_dir = tmp_path / "legacy"
    legacy_dir.mkdir()
    (legacy_dir / "MEMORY.md").write_text("# Memory Index\n", encoding="utf-8")
    (legacy_dir / "feedback_pressure_helps.md").write_text(
        "\n".join(
            [
                "---",
                "name: Pressure Helps",
                "description: Direct pressure: useful context.",
                "type: feedback",
                "originSessionId: test-session",
                "---",
                "# Pressure Helps",
                "",
                "The user benefits from direct pressure.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    imported = memory.import_legacy_claude_memory(
        legacy_dir=legacy_dir,
        canonical_root=tmp_path / "FLOSS" / "docs" / "agent-memory",
    )

    assert [entry.path.as_posix() for entry in imported] == [
        (
            tmp_path
            / "FLOSS"
            / "docs"
            / "agent-memory"
            / "feedback"
            / "pressure-helps.md"
        ).as_posix()
    ]
    text = imported[0].path.read_text(encoding="utf-8")
    assert "id: feedback-pressure-helps" in text
    assert "type: feedback" in text
    assert "title: Pressure Helps" in text
    assert "legacy_description: 'Direct pressure: useful context.'" in text
    assert "origin_session_id: test-session" in text
    assert text.splitlines().count("---") == 2
    assert "# Pressure Helps" in text


def test_materializes_registry_shared_index_and_claude_projection(tmp_path):
    memory = load_memory_module()
    workspace = tmp_path
    canonical_root = workspace / "FLOSS" / "docs" / "agent-memory"
    feedback_dir = canonical_root / "feedback"
    feedback_dir.mkdir(parents=True)
    (feedback_dir / "pressure-helps.md").write_text(
        "\n".join(
            [
                "---",
                "id: feedback-pressure-helps",
                "type: feedback",
                "status: active",
                "applies_to:",
                "  - any-agent",
                "---",
                "",
                "# Pressure Helps",
                "",
                "Direct pressure helps avoid analysis paralysis.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = workspace / "FLOSS" / "shared-agent-memory-surface.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "manifest_version": "0.1.0",
                "workspace_id": "flossi0ullk",
                "workspace_name": "FLOSSI0ULLK",
                "canonical_root": "FLOSS/docs/agent-memory",
                "targets": {
                    "claude": {
                        "enabled": True,
                        "memory_dir": ".claude/projects/C---shit/memory",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    messages = memory.materialize(
        workspace_root=workspace,
        manifest_path=manifest,
        output_dir=workspace / ".agent-surface" / "memory",
        check=False,
        dry_run=False,
    )

    assert any(message.startswith("WROTE") for message in messages)
    registry = json.loads(
        (workspace / ".agent-surface" / "memory" / "memory-registry.json").read_text(
            encoding="utf-8"
        )
    )
    assert registry["entries"][0]["id"] == "feedback-pressure-helps"
    shared_index = (
        workspace / ".agent-surface" / "memory" / "AGENT_MEMORY.md"
    ).read_text(encoding="utf-8")
    assert "Pressure Helps" in shared_index
    claude_memory = (
        workspace
        / ".claude"
        / "projects"
        / "C---shit"
        / "memory"
        / "feedback_pressure_helps.md"
    ).read_text(encoding="utf-8")
    assert "Direct pressure helps" in claude_memory
    assert "feedback-pressure-helps" in (
        workspace / ".claude" / "projects" / "C---shit" / "memory" / "MEMORY.md"
    ).read_text(encoding="utf-8")


def test_index_gists_are_complete_sentences():
    """The index line must not stop where the source file happened to wrap.

    Canonical memory files are hard-wrapped at ~80 columns and the index used to
    take the first physical LINE, so entries ended mid-sentence -- "does not gate
    on the full pytest suite," -- which reads as the whole rule while dropping
    the half that carries the reason.
    """
    module = load_memory_module()

    body = (
        "`.github/workflows/python-ci.yml` (PR #44) does not gate on the full\n"
        "pytest suite, because the full suite is red and gating on red produces\n"
        "a required check everyone learns to ignore.\n"
        "\nA second paragraph that must not appear.\n"
    )
    gist = module.first_sentence(body)

    assert gist.endswith("learns to ignore.")
    assert "second paragraph" not in gist
    assert "\n" not in gist


def test_index_gists_skip_headings_and_blank_leaders():
    module = load_memory_module()
    body = "\n# A heading\n\nThe first real sentence. And a second one.\n"
    assert module.first_sentence(body) == "The first real sentence."


def test_a_very_long_single_sentence_is_capped_with_an_ellipsis():
    """An ellipsis must mean 'genuinely longer', never 'the author wrapped here'."""
    module = load_memory_module()
    body = "word " * 200
    gist = module.first_sentence(body)

    assert len(gist) <= module._INDEX_GIST_MAX_CHARS + 1
    assert gist.endswith("…")


def test_an_empty_body_produces_no_gist():
    module = load_memory_module()
    assert module.first_sentence("") == ""
    assert module.first_sentence("\n\n# only a heading\n") == ""


# --- R3: aggregate validators must not hide failures behind the first one ----
#
# 2026-08-29: commit 726d568 added one memory file with no frontmatter.
# collect_memory_entries raised on it and the whole 62-memory projection
# stopped. Nobody noticed for three days, because the error named one file and
# therefore read as one file's problem rather than as a dead surface. Failing
# closed is correct; failing closed on the FIRST problem while staying silent
# about the rest is what cost the three days.


def _valid_memory(name: str) -> str:
    return "\n".join(
        [
            "---",
            f"id: project-{name}",
            "type: project",
            "status: active",
            f"title: {name}",
            "---",
            "",
            f"# {name}",
            "",
            "Body sentence.",
            "",
        ]
    )


def _canonical_tree(tmp_path):
    canonical = tmp_path / "agent-memory"
    (canonical / "project").mkdir(parents=True)
    return canonical


def test_every_rejected_memory_file_is_named_not_just_the_first(tmp_path):
    memory = load_memory_module()
    canonical = _canonical_tree(tmp_path)
    (canonical / "project" / "aaa-good.md").write_text(
        _valid_memory("aaa-good"), encoding="utf-8"
    )
    (canonical / "project" / "bbb-no-frontmatter.md").write_text(
        "# no frontmatter here\n", encoding="utf-8"
    )
    (canonical / "project" / "ccc-unclosed.md").write_text(
        "---\nid: x\n", encoding="utf-8"
    )

    try:
        memory.collect_memory_entries(tmp_path, canonical)
    except memory.AgentMemoryError as exc:
        message = str(exc)
    else:
        raise AssertionError("collect_memory_entries accepted invalid memory files")

    assert "bbb-no-frontmatter.md" in message
    # The load-bearing assertion: a failure AFTER the first one still reaches
    # the reader. Sorted order puts bbb first, so ccc is only present if the
    # walk continued past a raise.
    assert "ccc-unclosed.md" in message


def test_the_rejection_reports_how_much_it_examined(tmp_path):
    """A validator that says what it rejected but not what it looked at leaves
    the reader unable to tell one bad file from a dead surface."""
    memory = load_memory_module()
    canonical = _canonical_tree(tmp_path)
    for name in ("aaa-good", "bbb-good"):
        (canonical / "project" / f"{name}.md").write_text(
            _valid_memory(name), encoding="utf-8"
        )
    (canonical / "project" / "ccc-bad.md").write_text(
        "no frontmatter\n", encoding="utf-8"
    )

    try:
        memory.collect_memory_entries(tmp_path, canonical)
    except memory.AgentMemoryError as exc:
        message = str(exc)
    else:
        raise AssertionError("collect_memory_entries accepted an invalid memory file")

    assert "1 of 3" in message, message


def test_a_clean_tree_still_returns_every_entry(tmp_path):
    memory = load_memory_module()
    canonical = _canonical_tree(tmp_path)
    for name in ("aaa", "bbb", "ccc"):
        (canonical / "project" / f"{name}.md").write_text(
            _valid_memory(name), encoding="utf-8"
        )
    entries = memory.collect_memory_entries(tmp_path, canonical)
    assert [entry.memory_id for entry in entries] == [
        "project-aaa",
        "project-bbb",
        "project-ccc",
    ]
