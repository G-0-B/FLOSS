# Existing Work Board Reconciliation — Design

```yaml
id: flossi0ullk-work-board-reconciliation
version: 0.1.1
date: 2026-09-05
status: Proposed written design; operator review required before execution planning
truth_status: Specified
canonical_promotion: false
implementation_performed: false
operator_scope: "Documentation-only first"
base_commit: 08b377e86293a16ae6b71a2917384c920bbdeb72
revision_base_commit: 3f9e1aba7ec2c3d33a59720525e1c3dcd7338a1e
branch_observed: feat/coordination-room
board_sha256: 6d187e55aed71547e5916dc54730791dc4a7ebee59d3d1ec23e1d3b052316edb
```

This is a bounded documentation design, not a new work board, runtime contract,
canonical promotion, or authorization to implement the source documents.
The operator selected the documentation-only approach after reviewing the
six-part reconciliation outline in the current conversation. The five additional
coordination/plugin/reminder files and the two later-supplied historical atlases
are evidence to reconcile, not instructions to execute. No source document gains
authority by being cited here.

## 1. Purpose and boundaries

⚠️ Specified: restore one usable navigation surface at
[`2026-05-15-working-todo-list.md`](../../research/2026-05-15-working-todo-list.md).
Make unfinished obligations, already-landed work, dependencies, and conflicting
claims discoverable without losing the history that explains them. This enables
less duplicated effort and more accountable collaboration toward universal
flourishing; it does not rank research by startup velocity or commercial value.

The deliverable is reconciliation of the existing board, not implementation of
the work it lists. No new daemon, task database, skill, hook, authority registry,
automatic pruning, or board generator is proposed by this pass.

Out of scope: code/configuration edits; ADR edits; integrity-zome or consensus
gateway changes; installing or starting services; repairing provider rosters;
assigning work to other agents; resolving governance choices; promotions;
deletions/moves; merges; pushes; and generated-surface refreshes. Preserve all
unrelated tracked, staged, and untracked work. Do not stash or clean the checkout.

## 2. Reuse and alternatives

⚠️ Specified decision: **reconcile now; preserve the existing automation path**.

| Approach | Benefit | Cost / boundary |
| --- | --- | --- |
| Reconcile the existing board and link coordination-v1 | Immediate orientation with preserved obligations; recommended | Still a dated snapshot until the separately gated derived view works |
| Correct only a few stale rows | Smallest edit | Leaves contradictory sections and omitted obligations unaccounted for |
| Implement coordination-v1 during reconciliation | Could reduce later manual state maintenance | Separate scope, evidence, runtime changes, and unresolved decision gates |

✅ Verified as a document fact: coordination-v1 already proposes extending
`orient_probe.py`, retaining the room prototype, and replacing only the
branch/worktree half of manual Section 0 after the relevant implementation is
verified. Reuse that proposal rather than inventing another status command.
Source: [coordination-v1 design](2026-09-02-coordination-v1-design.md),
§4.4 and §9. No claim of implemented derived status follows from this reference.

Prior-art conclusion is local and bounded: this pass edits documents using
existing Git/readback tools. It does not select a new software dependency or
claim that a new coordination implementation passed ADR-18.

## 3. Evidence baseline and source roles

✅ Verified in this authoring pass: the board has 832 lines and Sections 0 and
A–I; its bytes match the header hash. Its current status sections include dated
service and branch snapshots. A recent snapshot is not continuously current.
Source: direct board read plus `Get-FileHash -Algorithm SHA256` on 2026-09-05.

✅ Verified in this authoring pass: the room package contains implementation and
tests. [`server.py`](../../../packages/coordination_room/server.py) exposes
`room_claim`, `room_release`, `room_broadcast`, `room_read`, and `room_state`, and
its executable entry configures port 7334. **Live reachability, active clients,
and current test results were not checked here.** Do not import that server for
a read-only inventory: module initialization constructs runtime objects.

| Source | Role in reconciliation; limits |
| --- | --- |
| [Existing board](../../research/2026-05-15-working-todo-list.md) | Primary obligation inventory; preserve original identifiers and historical corrections |
| [August 23 atlas](../../../../.toilet/2026-08-23-flossi0ullk-repo-atlas/START_HERE.md) | PR41 snapshot at `db80571ddd29f8a5e76dd5121e667d1dd322db67`; domain/share-set routing and historical file identities, not current status |
| [August 11 atlas](../../../../.toilet/2026-08-11-flossi0ullk-repo-atlas/START_HERE.md) | PR38 snapshot at `4657bdaa40e1288c3ebbf830596e49eacd9d4d28`; historical comparison, retained unchanged |
| [Room v0 design](2026-08-30-coordination-room-design.md) and [package](../../../packages/coordination_room/README.md) | Existing prototype, path claims, broadcast/read log; not consensus or semantic truth admission |
| [Coordination-v1 design](2026-09-02-coordination-v1-design.md) and [plan](../plans/2026-09-02-coordination-v1.md) | Proposed derived status and Git-ref ownership; preserve milestone-specific gates |
| [M1 decision record](../../reviews/2026-09-02-coordination-v1-design/consensus-decision.md) | Records DEFERRED for one exact submission, and blocked M2/M3; not a live source-chain read or approval of later revisions |
| [Task-time reminder design](2026-08-30-task-time-skill-reminder-design.md) | v0.3 design, per-target evidence and re-approval requirements; delivery, visibility, and behavior are separate |
| [Polyglot materializer design](2026-09-01-polyglot-evolving-plugin-materializer-design.md) | Package distribution and governed evolution; integrates reminder without replacing its behavioral contract |
| [Polyglot review result](../../reviews/2026-09-01-polyglot-plugin-materializer-spec/RESULT.md) | Single-reviewer findings, later corrections, implemented remedies and explicitly open remainder; not protocol-conformant independent approval |
| [v0.4 bundle README](../../../../.toilet/flossi0ullk_v0_4_continuation_package/00_README_CONTINUE_HERE.md) and [review result](../../reviews/2026-09-04-v04-continuation-bundle/RESULT.md) | Proposed shared-context direction and bounded schema reconciliation; not completed architecture |
| [MAS reevaluation intake](../../research/2026-08-31-mas-papers-reeval-intake.md) | Candidate follow-ups, dated experiment reports and corrections; paper claims are not independently revalidated by this pass |
| [Chain audit](../../research/2026-08-24-provenance-chain-integrity-audit-packet.md) | Read adjudication and limitations, not just the original claims |
| [Failure register](../../research/2026-08-25-provenance-failure-mode-register.md) and [cross-audit learnings](../../research/2026-08-29-cross-audit-learnings.md) | Regression examples, witness/commitment distinction, and unresolved dependencies |
| [Root intake map](../../research/2026-08-10-root-intake-digestion.md) | Existing cluster/destination decisions; classification does not prove files were moved |
| [File-locking spec](../../specs/file-locking.spec.md) | Existing lock-reuse work; no new locking primitive in this reconciliation |

The execution evidence set starts with these sources. Add another only to resolve
a named item or conflict; record the reason. Do not recursively ingest the
research library or treat memory-search ranking as coverage.

### Historical atlas reuse, without refreshing by default

✅ Verified in the v0.1.1 authoring pass: all seven checksum-listed files in the
August 11 packet and all nine in the August 23 packet match their respective
`SHA256SUMS.txt`. This checks byte consistency against colocated manifests, not
authorship, truth, or an independently authenticated seal. The August 23 TSV
contains 1,319 rows and zero `packages/coordination_room/` paths, while the
current checkout contains `packages/coordination_room/server.py`. Therefore
absence from that inventory cannot establish absence from current work.

⚠️ Specified reuse procedure:

1. Use August 23 `DOMAINS.md` and `context-domains.json` share sets for the
   smallest relevant L0/L1 source request. Consult August 11 and the existing
   `PATH_DELTA.tsv` / `DELTA_FROM_2026-08-11.md` only for a named historical
   discrepancy. Do not reload the entire atlas for each obligation.
2. Label every atlas-derived reference with its snapshot commit. The atlas
   inventories describe tracked paths inside `FLOSS/`, not the outer workspace,
   local untracked intake, running services, or all obligations.
3. Before relying on a selected path, check current existence, active manifest
   membership where relevant, and content/commit identity. Record unchanged,
   changed, renamed, absent, or unverified; resolve rename candidates by evidence,
   not name resemblance. Do not infer completion or deletion from atlas absence.
4. Add the post-snapshot sources already supplied by the operator and targeted
   current Git/path discovery. The atlas's physical primary-domain ownership is
   not a human/agent assignment, and its file count is not task coverage.
5. Preserve both atlas directories and their manifests unchanged. A complete
   atlas refresh is not a prerequisite for board reconciliation. Record a
   separate refresh candidate only if a demonstrated navigation gap warrants it;
   a future refresh must use a new dated packet and an explicit immutable target,
   never silently overwrite historical snapshots with dirty-checkout content.

## 4. Relationships that must not disappear

⚠️ Specified reconciliation constraints:

| Thread | Preserve as distinct | Relationship / outstanding evidence question |
| --- | --- | --- |
| Historical repository atlases | Noncanonical navigation and bounded share sets | Guide where to look; cannot supply current task status, assigned ownership, or approval |
| Shared MCP room v0 | Implemented prototype with separately measured runtime state | Keep broadcast/log role; proposed Git-ref exclusivity does not itself retire the room |
| Coordination-v1 M1/M2/M3 | Three milestones with different gates | M1 observed-status work is not M2 enforcement or M3 retirement of manual views |
| Verified shared context / room admission | Proposed evidence admission, SharedGist, capability freshness | A room broadcast is not admitted evidence; map the integration seam, do not claim it exists |
| Task-time skill reminders | Target-specific delivery and behavioral evaluation | Plugin packaging depends on/remaps this contract; packaging success does not establish reminder efficacy |
| Polyglot evolving plugin | Distribution, loader behavior, materializer transactions, later evolution | Generated package remains downstream of repository manifests and skill corpus |
| Consent/provenance/review reliability | Separate trust and authorization obligations | Signatures, provider availability, review independence, human decisions and substrate enforcement are not interchangeable |
| Sweettest/PR61 and preservation-spine work | Execution-path proof and integration/landing status | Historical test counts cannot close currently unverified merge blockers |
| Yumeichan, commitment architecture, research and flourishing | Intent-level obligations with original context | Do not silently discard them because coordination engineering is the first tranche |

✅ Verified as document facts, not new runtime assertions:

- The September 1 plugin design says the older Codex documentation-level hook
  blocker is resolved, while local delivery, privacy and exact-once probes remain
  required (§Task-time skill discovery integration). Record **partial
  supersession**, not wholesale completion of the August 30 reminder.
- The coordination decision record binds M1 to submitted commits `c1a08f1` and
  `ff1f5c0`; the current design/plan have later changes. Reconciliation must show
  the revision relation, not extend that decision to unreviewed text.
- The polyglot review's later disposition records R1/R2/R6 implemented and R3
  only partially implemented. Carry these as dated evidence candidates until
  exact code/commit verification; do not leave the original audit's entire
  remedy list marked untouched.

An endpoint-label discrepancy also requires a bounded check: the v0.4 review
calls an unavailable service at port 7334 the consensus gateway, while the room
server source configures 7334. Preserve the report as dated testimony; do not
infer current availability of either service from that wording.

## 5. Reconciliation model — no new runtime schema

⚠️ Specified: use ordinary Markdown in the existing board. Maintain a compact
current section with links to detailed/history sections. Do not impose every
field as a wide table; a short table plus per-item notes is acceptable.

Each active or unresolved item needs:

- stable existing item identifier where present; otherwise a receipt-local ID;
- desired outcome and why it matters;
- owner only if supported by an assignment; otherwise `unassigned`;
- workflow state and next check/action;
- dependency IDs or precise linked decision gates;
- code/document location and relevant branch/commit, with observation time;
- evidence status, evidence source, and what has **not** been verified;
- authorization scope/revision if relevant; and
- explicit duplicate/supersession relationships and retained dissent.

Keep three axes separate:

1. **Workflow:** active, blocked, deferred, completed, superseded, or unverified.
2. **Evidence:** ✅ Verified, ⚠️ Specified, 🔮 Aspirational, ❌ Blocked as
   applicable to the precise claim. Unknown evidence is explicitly unverified,
   not silently promoted into one of the positive categories.
3. **Authority:** exact human/recorded decision and scope; approval is neither
   implementation nor test evidence. The author of a document is not by default
   the currently assigned owner.

Do not convert unknown state to zero, absent, not started, or closed. A local
commit proves local content, not remote merge status. Existing `.git` refs are
local observations unless refreshed or separately corroborated. A test report
proves only its stated revision, environment and exercised path.

## 6. Bounded reconciliation sequence

The following are acceptance-oriented work units for the later execution plan;
none is executed by writing this design.

### A. Capture and account

- Freeze board bytes/hash, local HEAD and worktree/index state without mutation.
- Use the atlas reuse procedure in §3 to route bounded reads, then fill its
  post-snapshot blind spots from current evidence. Never use tracked-file
  inventory coverage as a substitute for obligation accounting.
- Inventory every obligation in Sections 0 and A–I, including prose-only items,
  retrospective entries that still contain follow-ups, and accepted/deferred
  decisions in the bounded source set.
- Assign receipt-local references using original ID plus heading/line location
  and frozen board hash. The hash disambiguates changing line numbers.
- Reconcile each source obligation to retained, completed-with-evidence,
  superseded-with-successor, duplicate-with-both-sources, blocked, or unverified.
  One source may contain several obligations. One item may have several sources.
  Every source obligation gets exactly one primary disposition; notes preserve
  secondary relationships.
- Record non-action research context as retained context, not a missing task.

### B. Verify selectively and expose gaps

- Prioritize checks that prevent duplicate work or unblock several real tasks:
  coordination, consent/provenance, review readiness, substrate/landing evidence,
  shared surfaces and packaging/reminders. This order is a working judgment,
  not a measured global ROI ranking.
- Inspect referenced commits and containing branches before reopening old fixes.
  Similar patches/rebased commits require content comparison, not SHA equality.
- Time-bound service/remote checks; if unavailable record the failed check and
  leave state unknown. Do not restart services or repair authentication here.
- Keep claims from supplied documents distinguished from independently checked
  results. Do not run expensive suites simply to make every row green.
- Coverage means obligation dispositions / all inventoried obligations in the
  bounded set. Report verified and unresolved counts separately. Never call this
  whole-workspace coverage or equate complete accounting with all work completed.

### C. Apply a lossless documentation edit

- Re-read board hash immediately before editing. If it differs, stop that edit,
  inspect changes, and reconcile the inventory with the new version. This is a
  collision-detection practice, not a concurrency lock or an atomicity claim.
- Apply a minimal patch to the existing board. Label dated snapshots as history
  and add current pointers; retain historical text during this first pass.
- Do not run Section H's old timed-purging convention. Do not silently rewrite
  past claims as if the corrected evidence had been known at the time.
- Add links to the distinct room, coordination, admission, plugin and reminder
  threads. Link rather than copy their design requirements into the board.
- Keep manual PR information explicitly dated until an online derived view is
  implemented and verified. No `Generated` label for hand-edited output.

### D. Review, land, and verify propagation boundaries

- A fresh read-only reviewer checks obligation preservation, false closures,
  unsupported ownership/approval, partial supersession, and exact file scope.
  A different model family is preferred if an authorized functioning review
  surface is available; record actual identity/completeness and dissent. If not
  available, record single-agent self-review and pending independence; do not
  fabricate a consensus or call a provider outage a neutral vote.
- Recheck links, hashes, board diff, and obligation accounting after edits.
- Stage/commit only the approved board and reconciliation receipt paths after
  checking the exact staged set; preserve foreign staged changes. No push.
- Read back the landed paths. Record commit and still-open dependencies. Any
  downstream materializer refresh is a separately scoped task; do not hand-edit
  generated L0 or client files to make the board appear propagated.

## 7. Files and durability

⚠️ Specified file scope:

- Design now: this file only; no board edit in the authoring pass.
- After written-design review: create
  `docs/superpowers/plans/2026-09-05-work-board-reconciliation.md` as the detailed
  documentation execution plan. It will contain exact evidence/readback commands
  and reviewer checklists, not runtime implementation tasks.
- Reconciliation execution: modify only
  `docs/research/2026-05-15-working-todo-list.md` and create
  `docs/reviews/2026-09-05-work-board-reconciliation/RESULT.md`.

The receipt contains frozen source hashes, observation times, obligation mapping,
commands/results, unverified/conflicting items, scope checks and review verdicts.
It is a historical receipt, **not a second maintained status board**. Additional
source files are read-only. A necessary expansion is presented to the operator
before changing another path.

No protected source, registry, generated projection, ADR, or canonical-status
flag is modified by this scope. Self-review/commit of this proposed design does
not satisfy independent review or authorize execution.

## 8. Acceptance and adversarial cases

⚠️ Specified acceptance for reconciliation execution:

- 100% disposition coverage for the frozen, bounded obligation inventory;
  every retained/reframed item has a destination link and no orphan dependency.
- Every completion/merge assertion has claim-appropriate evidence; unknown remote
  state and historical test results stay visibly limited.
- Original room prototype remains discoverable; no room broadcast is called
  admission-validated or used as a substitute for consent/consensus.
- Partial supersession is preserved for reminder documentation versus runtime
  delivery, M1 versus M2/M3, and partially implemented materializer remedies.
- Old work such as Yumeichan remains accounted for without invented assignment.
- Every dispute records both sources and the smallest next check/decision.
- Board remains one navigation surface; no new authority or runtime is created.
- Changed file set is bounded, unrelated work survives, board readback matches
  the committed content, and receipt states actual review independence.

Review against these concrete counterexamples:

| Counterexample | Required outcome |
| --- | --- |
| Header says OPEN, later dated subsection records MERGED | Preserve history; reconcile using appropriate current/dated evidence, not first-match text |
| Same fix exists only on a sibling branch | Record location/landing gap; do not reimplement or mark globally complete |
| Two descriptions share words but have different consent or execution scope | Retain separately; semantic resemblance is not task identity |
| Old hook-documentation blocker superseded; live probe absent | Close only the documentation subclaim |
| Room has code/tests but endpoint was once unreachable | Track implementation, dated tests and runtime health separately |
| Old atlas omits a now-present prototype or uses an obsolete path | Check current Git/worktree sources; do not reopen, retire, or declare missing from atlas data alone |
| Atlas checksum matches but source snapshot is old | Integrity passes; freshness remains separately unverified |
| Provider errors in a DEFERRED vote record | Preserve DEFERRED; expose missing participation, no outcome reinterpretation |
| A changed spec cites an older approval | Bind approval to its revision; later changes are not automatically covered |
| Board changes during editing | Stop and reconcile; never overwrite the concurrent update |
| Source item cannot be verified within bounded checks | Retain as unverified with exact next check; no silent omission |

## 9. Authoring verification and remaining gate

✅ Verified baseline command: `python FLOSS/scripts/spec_gate.py --check` exited
1 before this file was added. Output named two unregistered paths
`FLOSS/hooks/grok_pretool_st.py`, `FLOSS/hooks/grok_session_register.py`, and stale
`FLOSS/scripts/research_log.py`. It reported reuse coverage 11/120 and six ADR
sections with ungated accepted/deferred work. These are observed gate reports,
not claims that those underlying issues were repaired here.

The board was clean at the scoped Git-status check; the wider checkout contains
foreign work. Authoring verification must compare the board hash again and show
that this one additive design does not add a new spec-gate finding. Document-link
and whitespace checks establish only document hygiene, not architecture validity.

❌ Blocked for the next workflow stage: written-design review by the operator is
still required under brainstorming. The documentation-only scope is selected;
the detailed execution plan, board edit and runtime work have not been performed.

### v0.1.1 delta and concurrent-work observation

✅ Verified: while the atlas addition was being prepared, current branch HEAD
was `3f9e1ab`, a coordination-v1 design/plan review-correction commit after this
design's initial commit `34ba0a1`. The reconciliation design was clean before
this patch and the board hash remained unchanged. Preserve that other work;
re-read the latest coordination design/plan at execution time. Do not mistake
the initial source hashes below for promises that those inputs stayed current.

This revision adds atlas discovery, snapshot/freshness boundaries, and related
counterexamples only. It does not refresh an atlas, edit the board, resolve the
coordination review, or broaden the documentation-only scope.

### Initial source hash anchors recorded 2026-09-05

SHA-256 below binds raw file bytes, not normalized text or an approval signature.

| Path relative to FLOSS | SHA-256 |
| --- | --- |
| `docs/research/2026-05-15-working-todo-list.md` | `6d187e55aed71547e5916dc54730791dc4a7ebee59d3d1ec23e1d3b052316edb` |
| `docs/superpowers/plans/2026-09-02-coordination-v1.md` | `4a041d3c9bd2af38ad4d5fb1e10e076094a6c89a0c56ee649480e942c024db37` |
| `docs/superpowers/specs/2026-09-02-coordination-v1-design.md` | `e62e2847b51a32beb36c1f9253a8fd5f6774af90299817b7cd45dbeeb73f7000` |
| `docs/superpowers/specs/2026-09-01-polyglot-evolving-plugin-materializer-design.md` | `1c21998f2182e416760d567cdc4efdaadbeab798ac1afe8c1fb473f1163ba468` |
| `docs/superpowers/specs/2026-08-30-task-time-skill-reminder-design.md` | `ef08fc3bcbebcff074678509ea3ee756b6b24d10f3da57a960bf4c32b04ae6ef` |
| `docs/superpowers/specs/2026-08-30-coordination-room-design.md` | `2c16ac8acf9e847dade872e2fa875cb86e7f4e7bde2756f716bd72174235a364` |

Atlas entrypoint hashes recorded for v0.1.1; paths relative to the outer workspace:

| Path | SHA-256 |
| --- | --- |
| `.toilet/2026-08-23-flossi0ullk-repo-atlas/START_HERE.md` | `4dca54f0a3e30e5b941c1daa5caddaf8f726bba264ddcfa8ad1ebd78b16c2334` |
| `.toilet/2026-08-11-flossi0ullk-repo-atlas/START_HERE.md` | `d191ace265896f1b84aa0d76ac74a8cb43a89013c33ef175a858302bb112f210` |
