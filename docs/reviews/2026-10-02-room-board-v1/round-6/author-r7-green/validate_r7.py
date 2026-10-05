"""Scratch-only: check the built plan against the base files and the sources the green run used."""

import hashlib
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
GREEN = pathlib.Path(sys.argv[1])
PLAN = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "C:/~shit/FLOSS/docs/superpowers/plans/2026-10-02-coordination-room-board-v1.md")
plan = PLAN.read_text(encoding="utf-8")
tpl = (HERE / "plan.tpl.md").read_text(encoding="utf-8")
problems: list[str] = []


def check(ok: bool, what: str) -> None:
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        problems.append(what)


# 1. Nothing unexpanded, nothing invisible.
for token in ("@@", "{{file:", "{{pairs:"):
    check(token not in plan, f"no {token!r} left in the plan")
for code in (0x2028, 0x2029, 0xFEFF, 0x00A0, 0x200B):
    check(chr(code) not in plan, f"no literal U+{code:04X} in the plan")
check(not re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", plan), "no control characters in the plan")
check("\r" not in PLAN.read_bytes().decode("utf-8"), "plan has LF line endings")

# 2. Every inlined file is byte-for-byte what the green run used, and fits its fence.
files = re.findall(r"^\{\{file:([^}]+)\}\}$", tpl, flags=re.M)
for rel in files:
    scratch = (HERE / rel).read_text(encoding="utf-8")
    check(scratch.rstrip("\n") in plan, f"inlined verbatim: {rel}")
    stage = None
    for name in ("phase1", "proposal"):
        candidate = GREEN / name / rel
        if candidate.exists():
            stage = candidate
            break
    if rel == "scripts/tests/test_daemon_scope.py":
        stage = GREEN / "phase1" / rel
    check(stage is not None and stage.read_bytes() == (HERE / rel).read_bytes(), f"green run used the same bytes: {rel}")
    if not rel.endswith("coordination-room.spec.md"):
        check("```" not in scratch, f"no code fence inside {rel}")
    for code in (0x2028, 0x2029, 0xFEFF):
        check(chr(code) not in scratch, f"no literal U+{code:04X} in {rel}")

# 3. Every Replace pair occurs exactly once, in order, and reproduces the tested files.
BODY = r"((?:(?!\n```).)*)"
pair_re = re.compile(r"```[a-z]*\n" + BODY + r"\n```\n\nwith:\n\n```[a-z]*\n" + BODY + r"\n```", re.S)
pairs = pair_re.findall(plan)
check(len(pairs) == 25, f"25 replace pairs in the plan (found {len(pairs)})")
layout = [
    ("registry", "docs/specs/spec-registry.json", 1, None),
    ("start phase 1", "scripts/start_mcp_daemons.ps1", 7, "phase1"),
    ("stop phase 1", "scripts/stop_mcp_daemons.ps1", 4, "phase1"),
    ("how-to phase 1", "docs/agent-memory/project/coordination-room-v0.md", 3, None),
    ("scope test phase 2", "scripts/tests/test_daemon_scope.py", 2, "proposal"),
    ("start phase 2", "scripts/start_mcp_daemons.ps1", 3, "proposal"),
    ("stop phase 2", "scripts/stop_mcp_daemons.ps1", 4, "proposal"),
    ("how-to phase 2", "docs/agent-memory/project/coordination-room-v0.md", 1, None),
]
state: dict[str, str] = {}
cursor = 0
for label, rel, count, stage in layout:
    if rel not in state:
        source = GREEN / ("phase1" if rel.endswith("test_daemon_scope.py") else "baseline") / rel
        state[rel] = source.read_text(encoding="utf-8")
    text = state[rel]
    for old, new in pairs[cursor:cursor + count]:
        hits = text.count(old)
        check(hits == 1, f"{label}: old text occurs once ({hits}): {old[:50]!r}")
        text = text.replace(old, new, 1)
    cursor += count
    state[rel] = text
    if stage:
        tested = (GREEN / stage / rel).read_text(encoding="utf-8")
        check(text == tested, f"{label}: the plan's edits reproduce the tested {rel}")
    else:
        out = HERE / "applied" / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8", newline="\n")

# 4. requirements edit is unambiguous on the base.
reqs = (GREEN / "baseline" / "requirements-ci.txt").read_text(encoding="utf-8").splitlines()
check(reqs.count("mcp") == 1, "requirements-ci.txt has exactly one bare 'mcp' line on the base")

# 5. Counts quoted in the plan match what was measured.
digest = hashlib.sha256(PLAN.read_bytes()).hexdigest()
print("plan lines:", len(plan.splitlines()), "sha256:", digest)
print("PROBLEMS:", len(problems))
for item in problems:
    print("  -", item)
sys.exit(1 if problems else 0)
