# Cross-Harness Seam Packet — 2026-09-02

**For any agentic reader** — human, AI, synthetic, hybrid, or otherwise, in any
harness (Claude Code, Codex, Gemini, OpenCode, Kilocode, Windsurf, or one not
yet built). Written to be read cold, with no access to the thread that produced
it.

**Kind:** thread-seam handoff. Plane A evidence. Promotes nothing to canon.
**Written:** 2026-09-02, from `FLOSS` on branch `feat/coordination-room`.
**Truth labels** follow the workspace convention: ✅ Verified / ⚠️ Specified /
🔮 Aspirational / ❌ Blocked. Every ✅ below carries the command that reproduces
it. Re-run rather than trust — this packet ages.

## How to use this

Read §1 and §5 before touching anything. §1 stops you writing into the wrong
git repository; §5 stops you losing another agent's work. Everything else is
reference.

---

## 1. Repository topology — read this first ✅ Verified

**There are two separate git repositories, and they are easy to confuse.**

| Path | Repo | Contains |
|---|---|---|
| `C:\~shit\` | workspace root repo | `.toilet/`, `_reference/`, `INDEX.md`, intake drops |
| `C:\~shit\FLOSS\` | **its own repo** | all project code, docs, ADRs, specs, packages |

`git -C FLOSS rev-parse --show-toplevel` returns `C:/~shit/FLOSS`. A `git status`
run at the workspace root does **not** show FLOSS changes and vice versa.

Two important directories are not durable:

- `.agent-surface/` — **not tracked by the root repo.** Local-only. Anything
  written there does not survive a clone. It is a projection target, generated
  by `FLOSS/scripts/materialize_shared_agent_surface.py`; `CONTEXT_POINTERS.md`
  and `harness/HARNESS_UPDATE_PACKET.md` are generated views — do not hand-edit.
- `.toilet/` — **gitignored** (`C:\~shit\.gitignore:158`). Staging for
  undigested material. Durable evidence must move out of it.

`docs/agent-memory/` is the repo-owned shared memory that materializes outward
to every harness. That is the propagation path for anything other agents must
know. This packet is pointed at from
`docs/agent-memory/project/gates-exempt-by-default.md`.

## 2. Tooling traps ✅ Verified 2026-09-02

**`st` silently reports dotted directories as empty.**

```
st --mode ai .agent-surface               ->  F:0 D:0 S:0 (0.0MB)
st --mode ai --everything .agent-surface  ->  689.5 MB, full tree
ls .agent-surface                         ->  18 entries
```

`FLOSS/CLAUDE.md` mandates `st` as a required replacement for `ls`, `grep` and
`find`. Follow that mandate **with `--everything`** on this workspace, because
every surface that matters here is dotted (`.agent-surface`, `.toilet`,
`.claude`, `.gemini`). Without it you will conclude the coordination surface
does not exist. Reported as R7 below.

**Transcript retention** ✅ Verified: `~/.claude/settings.json` now carries
`cleanupPeriodDays: 99999` (set by the operator 2026-09-02, all 17 other keys
preserved). Before that, 25 transcripts / 124.5 MB were on the default 30-day
delete clock with no backup. They are not yet copied into
`FLOSS/ai-conversations/`; that remains open.

## 3. What landed this session ✅ Verified

| Commit | Repo | What |
|---|---|---|
| `2deb8c9` | FLOSS | `docs/agent-memory/project/gates-exempt-by-default.md` — the standing rule |
| `633c87a` | FLOSS | `spec_gate.py` coverage reporting (R1) + 4 TDD tests + this review directory |
| `86cd7d5` | FLOSS | the ADR-20 correction — the reuse decision was made, then lost |

R1's effect, reproducible with `python FLOSS/scripts/spec_gate.py --check`:

```
SPEC-GATE COVERAGE: reuse gate active on 9/109 registered artifact(s) (8%); 100 untiered, of which 57 not grandfathered
```

`reuse_coverage()` in `scripts/spec_gate.py` derives that from the registry —
it is not a recorded constant, because a hand-maintained coverage number is the
next thing to drift. It prints **before** the verdict and **on the fail path
too**; a test pins that ordering.

## 4. The finding that generalises — three ungated classes ⚠️ Specified

Full evidence in [`GATE-ADOPTION-AUDIT.md`](GATE-ADOPTION-AUDIT.md). Compressed:

ADR-18's prior-art/reuse gate is Accepted (2026-07-16), correctly implemented,
fail-closed — and reaches 9 of 109 registered artifacts. `spec_gate`'s own error
text states the mechanism: *"an omitted tier is an exemption, not a default."*
Fail-closed centre, fail-open boundary. `ADR-18-prior-art-reuse-gate.md` is
itself registered untiered; so are ADR-13 through 17 and 19.

| Class | Why every current gate misses it |
|---|---|
| Unregistered artifacts | No registry entry exists; the gate cannot see them |
| Untiered entries | Registered, but an omitted tier is an exemption — 100/109 |
| **Accepted-but-not-implemented** | **Nothing checks that accepted decisions were carried out** |

The third is invisible by construction. `spec_gate` validates that evidence
exists for artifacts that were *built*. Nothing validates that artifacts get
built for decisions that were *accepted*. `ADR-20:589` — *"Accepted but not
implemented here"* — lists six, including **`filelock` adoption**, accepted
2026-08-25 after a four-auditor external meta-audit. Eight days later the
hand-rolled `packages/activity_log/filelock.py` was still accruing review rounds
while **py-filelock 3.18.0 sat installed** at
`C:/Python313/Lib/site-packages/filelock/`, declared in no requirements file.

**Per-surface caveat — carry this with the reuse verdict or you will break
something.** py-filelock is correct for **process-lifetime** locks (materializer
transaction, anchor publish). It is **wrong** for the daemon claim, which must
*outlive* its process — an OS lock is released on process death by definition.
That claim still needs the pid-file + identity-sidecar + compare-and-swap-remove
design. Reuse verdicts here are per-surface, never per-repo.

**Standing rule adopted:** *measure gate coverage, not just gate verdict.* A
gate reporting pass/fail must also report the size of the set it examined
against the set it could have examined. A gate with no coverage number is an
unfalsifiable claim of compliance.

**Corollary, and the reason no new skill or hook was created:** *the remedy for
a forgotten surface is never an additional surface.* This workspace's dominant
failure mode is surface proliferation — adding a reminder mechanism to remember
the reminder mechanisms extends the defect. See
`docs/agent-memory/project/doc-explosion-acknowledged.md` and
`docs/agent-memory/project/installation-not-adoption.md`.

## 5. Hazards for concurrent agents — read before writing ✅ Verified

**5.1 The coordination room claims file paths; it does not claim the git index.**
Two agents working in one checkout share one staging area. One agent's `git add`
plus another agent's `git commit` merges both sets of work into one commit under
one message, regardless of who holds which path claim. Observed 2026-08-31:
commit `7bbc725` ("fix(locks,daemons): serialise the claim transition…") swept
in two unrelated documentation files staged by a different agent.

**Mitigation, use it every time:** commit path-scoped.

```bash
git commit -F- -- path/one path/two
```

Every commit in §3 was made this way. Better still, work in separate worktrees.

**5.2 The coordination room was DOWN for this entire session.**
`flossiullk-coordination-room` on `127.0.0.1:7334` returned `ConnectionRefused`.
So did `flossiullk-computer-use`. `agentmemory` disconnected mid-session. Do not
assume the room is arbitrating writes — check it responds before relying on it.
Its claims are advisory even when up (see 5.1).

**5.3 Aggregate materializers abort on first failure.**
`scripts/materialize_shared_agent_memory.py:199` raises `AgentMemoryError` on the
first memory file missing YAML frontmatter. On 2026-08-29 one such file
(`commitment-built-witness-improvised.md`, added in `726d568`) stopped the entire
62-memory projection. It went unnoticed for ~3 days — the error named one file,
so it read as one file's problem rather than as a dead surface. Fixed in
`48875cf`. **If a projection looks stale, run the materializer and read its first
error; it may be masking every file after it.** Filed as R3.

**5.4 Signed history cannot be repaired.** Per ADR-20: a signed provenance packet
cannot be corrected — fixing a field breaks the signature. Any contract enforced
against ancestors can therefore permanently kill a chain. Enforcement belongs at
authorship, where failure is actionable. Identity `DkuYPguG98HM2nyR` currently
carries an unrepairable false genesis and needs operator-initiated rotation.

**5.5 Do-not-modify-without-authorization:** `FLOSS/packages/metacoordinator_mcp/`
and the consent zomes. Report findings; do not edit.

## 6. Known-red, none of it introduced this session ✅ Verified

- `python FLOSS/scripts/spec_gate.py --check` exits **1**: `hooks/grok_pretool_st.py`
  and `hooks/grok_session_register.py` unregistered; `scripts/research_log.py`
  registered but absent. A habitually-red gate has been demoted to a log line.
- `scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded`
  fails. Confirmed pre-existing by stashing this session's change and re-running.
- `black --check scripts/spec_gate.py` wants a reformat at ~line 434, in
  pre-existing code. Left alone deliberately rather than swept into an unrelated
  commit.
- `docs/agent-memory/` files carry CRLF; git warns on every add. Cosmetic.

## 7. Open, and waiting on the operator

| Item | State |
|---|---|
| **R2** — untiered stops meaning exempt for new entries | Needs explicit consent; convention-establishing |
| **R3** — materializers report all failures, not the first | Proposed |
| **R4** — register the lock capability under ADR-18, per-surface verdicts, declare the dependency | Proposed |
| **R6** — count accepted-but-not-implemented promises and print it | Proposed |
| **R7** — fix the `st` directive (`--everything`, or drop "always") | Proposed |
| Back up 25 transcripts / 124.5 MB into `FLOSS/ai-conversations/` | Undone |
| ADR-20 open questions 1, 2, 4, 6 | Open; Q2's exit condition was never satisfied |

## 8. What NOT to do

1. **Do not add a skill, hook, agent, or checklist** to make any of the above
   stick. That is the defect, not the fix. Every remedy here is subtractive or
   relocating.
2. **Do not cite `RESULT.md` as `reuse.reviewer.record`** for any tier-2 entry.
   It is a single-reviewer record and says so in its own second section.
3. **Do not adopt py-filelock for the daemon claim.** §4's caveat.
4. **Do not hand-edit** `.agent-surface/CONTEXT_POINTERS.md` or
   `harness/HARNESS_UPDATE_PACKET.md`; they are generated.
5. **Do not treat this packet as canon.** It is Plane A evidence with a
   timestamp. Repository canon wins; re-derive before relying.

## 9. Re-derive everything here

```bash
cd C:/~shit/FLOSS
python scripts/spec_gate.py --check                      # coverage + red state
python -m pytest -q scripts/tests/                        # 1 pre-existing failure
python scripts/materialize_shared_agent_memory.py         # memory projection
git log --oneline -3                                      # 86cd7d5 633c87a 2deb8c9
python -c "import filelock; print(filelock.__version__)"  # 3.18.0, undeclared
grep -n filelock docs/adr/ADR-20-provenance-validator-reconciliation.md   # :589
st --mode ai --everything ../.agent-surface               # needs --everything
```
