CONTEXT_CONTINUATION_PACKET_2026-09-01_polyglot-plugin-spec-review

Kind: Plane A critical review packet (spec review; no code written, no spec edited).
Subject: FLOSS/docs/superpowers/specs/2026-09-01-polyglot-evolving-plugin-materializer-design.md v0.1.0
Reviewer: Claude Opus 5 / Claude Code session 1af99060
Human collision node: Anthony / kalisam
Created: 2026-09-01
Truth status of this packet: [Verified] for every reproduced hash and count below; [Specified] for each proposed remedy.
Consensus gateway ready: false. Consent ref: none. No spec file was modified by this review.

Why this packet exists
The reviewed spec's own status line says "written-spec review required; not implemented".
This packet is that review, recorded so the next thread does not re-derive it.

VERIFIED FIRST — what the spec got right
Reproduced independently at base commit a15f5f3 (exists; "fix(memory): preserve substantive witness gist", 2026-09-01 00:18:52 -0400):

  - All six probe SHA-256 values in the Design provenance table match byte-exact
    against .toilet/polyglot-plugin-validator-probe-2026-09-01/. Nothing drifted.
    Note the fixture path in the spec is workspace-root-relative, not FLOSS-relative.
  - The two claims that would actually bite are correctly labelled Blocked, not
    hand-waved: dialect precedence between root plugin.json and
    .codex-plugin/plugin.json, and hook trust before install.
  - The corrections list is technically right on all counts checked: fcntl is not
    the Windows answer, uv.lock cannot pin a Node-distributed dependency, in-toto
    structures attestations without signing them, no SLSA level without a builder.

A provenance table that reproduces is rare in this repo. The topology decision
(one physical polyglot directory) holds up. The findings below are defects inside
a sound design, not reasons to reject it.

FINDING 1 — "the existing three materializers" undercounts by four
Spec lines 219-220 and the authority table at 113-120.
FLOSS/scripts/ contains seven materializers; six carry --check:
  materialize_shared_agent_surface.py    has --check
  materialize_shared_hook_surface.py     has --check
  materialize_shared_skill_surface.py    has --check
  materialize_shared_context_surface.py  has --check
  materialize_shared_ai_roster.py        has --check
  materialize_shared_agent_memory.py     has --check
  materialize_gemini_mcp.py              (no --check)
The spec names three (agent, hook, skill). Four surfaces sit outside the stated
composition with no reason given. Remedy: state whether the omission is scope or
oversight, and if scope, say what governs the other four.

FINDING 2 — no error-aggregation contract, with a three-day empirical proof
Spec lines 237-244 define check as "nonzero on drift or invalidity" and never say
whether validation collects every failure or aborts on the first.

The repo already paid for this. materialize_shared_agent_memory.py:199 raises
AgentMemoryError on the first file missing YAML frontmatter. On 2026-08-29 commit
726d568 added docs/agent-memory/project/commitment-built-witness-improvised.md
with no frontmatter block. The entire 62-memory projection stopped. It was not
noticed until 2026-09-01 00:07, fixed in 48875cf (11 insertions, zero deletions —
the frontmatter was genuinely absent, not malformed). Roughly three days, because
the error named one file and therefore read as one file's problem rather than as
"this whole surface is not projecting".

Scale first-failure-abort to a package with N skills, two manifests, two MCP
serializations and hooks and you get one finding per run, serially — the same
long-tail shape diagnosed in docs/research/2026-08-31-review-loop-session-learnings.md.

Remedy: check MUST validate every admitted component and report all failures. The
materialization receipt needs a field separating validated-and-failed from
never-reached-because-aborted. Receipt line 284's "known limitations and
unresolved capability cells" does not cover this: an aborted run's problem is
unknown unknowns, not known limitations.

FINDING 3 — the lock section repeats the shape that was already corrected
Spec lines 251-256 specify lock identity CONTENT (process, host, start-time,
command, source-commit) plus "an age threshold alone never steals a live lock".
That is checking harder. The correction that landed on the PR41 lineage was to
serialise the TRANSITION: compare-and-swap removal of the exact inspected
instance, not inspect-then-unlink. Between the staleness check and the unlink another
process can create a fresh lock; richer identity does not close that window.

Implementer note: packages/activity_log/filelock.py (msvcrt + POSIX, held()
context manager) exists at commits 222d27b and 29feb91 but is NOT on
feat/coordination-room. It cannot simply be imported from here.
See also FINDING 6 — it should probably not be re-imported at all.

FINDING 4 — "atomic where the host filesystem supports it" is untestable on the primary platform
Spec lines 258-259. On Windows os.replace is atomic same-volume only. The spec
mandates a transaction-specific staging directory but never constrains it to the
target's volume. Cross-volume silently degrades to copy-then-delete, which is
exactly the non-atomic case the write-ahead journal exists to survive.
Remedy: staging directory MUST be on the target volume; verify at plan time and
fail closed when it is not. This repo is Windows-primary, so the vague form is
not a portability courtesy, it is the untested path.

FINDING 5 — plan is the default mode but nothing binds apply to it
Spec lines 237-244 plus the receipt's "exact diff hash" at line 281. Nothing
forbids apply without a preceding plan, and no field ties an apply to the diff
hash a plan produced. Operator consent then attaches to a diff that may no longer
be the diff — the same source-commit drift the receipt already tracks for inputs.
Remedy: apply requires the plan diff hash at the same source commit, else refuse.

FINDING 6 — ADDED POST-REVIEW: the spec's own governing gate did not fire on it
Governed_by declares ADR-18 Prior-Art and Reuse Gate. The concrete instance:
py-filelock is a maintained cross-platform library with exactly the semantics of
the hand-rolled packages/activity_log/filelock.py. It is version 3.18.0, already
installed at C:/Python313/Lib/site-packages/filelock/, and is NOT declared in any
requirements file. We built the lock next to the library.

Correct technical split, so this is not a blanket "just use the library":
  - py-filelock IS the right reuse target for the materializer transaction lock
    and the anchor-publish lock. Those are process-lifetime locks.
  - py-filelock is the WRONG tool for the daemon claim, which must OUTLIVE its
    process. An OS lock is released on process death by definition. That claim
    still needs the pid-file plus identity-sidecar plus CAS-remove design.
Recording this split matters more than the reuse verdict: an undifferentiated
"reuse py-filelock" would break the daemon claim.

Remedy: register the lock capability under ADR-18 with a tier, record the
adopt/extend/compose/build verdict per surface, and declare the dependency.
See the companion packet GATE-ADOPTION-AUDIT.md
for why the gate did not fire, which is a larger problem than this one instance.

WHAT WAS NOT DONE
No spec file edited. No code written. No dependency added. No registry entry
created. Findings 1-6 are proposals for the spec author and for the first
implementation plan (spec section "Implementation decomposition" workstream 1).

NEXT THREAD SHOULD
1. Decide per finding: fold into the spec, or file against implementation plan 1.
2. Not re-derive the review. Everything above is reproducible from the commands
   named in it.
