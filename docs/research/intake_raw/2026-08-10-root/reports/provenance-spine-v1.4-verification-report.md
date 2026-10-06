---
# --- UpgradableArtifact Header ---
id: "provenance-spine-v1.4-verification-report"
version: "1.0.0"
kind: "verification_report"
status: "Accepted"
updated: "2026-07-30"
supersedes: []
truth_status: "mixed"          # see truth_status_breakdown — NOT a kernel enum value, see note
truth_status_breakdown:
  verified: "Part B B1–B4, B7, B8 (keripy source, RFC 8785, PyPI); Part A items 1–6, 8, 10 (file contents, single reader pass)"
  refuted: >
    Part B B5–B6 (t:'prov' unregistered; 'additive KERI migration' claim FALSE);
    Part A greenfield assumption FALSE.
    CORRECTION 2026-08-04 (merged in from verification-report-sidecar.md on
    2026-08-10): the spine is on origin/main via PR #36 (merged 2026-06-16),
    NOT merely on a working branch. An intermediate claim that provenance.py
    was absent from main came from a stale local main ref and was itself wrong.
    PR #38 is docs-only and stacked cleanly on #36
    (merge-base --is-ancestor = 0). This supersedes §9's "undetermined"
    finding below.
  specified: "consent_integrity deployment status; repo-claimed test passes"
  unverified: "PR #38 in entirety; RUNTIME_SURFACES.md; METAHARNESS_OPERATING_MODEL.md; materializer --check; Action record volume; identity zome symbols; per-package dep pins"
evidence_sources:
  - "G-0-B/FLOSS branch main — file contents via repository reader (single pass, not re-fetched)"
  - "G-0-B/FLOSS PR #25 (merged 2026-06-16) — rendered HTML"
  - "WebOfTrust/keripy src/keri/core/coring.py — MtrDex, Codes, Ilkage tables"
  - "IETF draft-ssmith-said; ToIP KERI specification"
  - "RFC 8785; PyPI (rfc8785, jcs, jsoncanon, blake3)"
  - "SLSA v1.0 Distributing Provenance; in-toto ITE-6; C2PA"
upgrade_path: "PR #38 half-resolved 2026-08-04 (docs-only, stacked on #36) — see the CORRECTION in refuted. Still supersede when a live CI run replaces self-reported test counts."
rollback_plan: "N/A — report is evidence, not a mutation. Discard and re-run verification if repo state has moved."
friction_tier: "low"           # document; changes nothing executable
license: "Compassion Clause + Apache-2.0"
---

> **Schema note (worth a kernel amendment).** `truth_status: "mixed"` is **not** a value in
> the Master Metaprompt v1.3.1 §4 enum (Verified | Specified | Aspirational | Unverified).
> A verification report legitimately carries heterogeneous claims — some Verified, some
> actively Refuted — and collapsing it to a single label would either overclaim (calling
> the whole thing Verified while PR #38 is unretrieved) or underclaim (calling it Unverified
> while six KERI codes are confirmed against keripy source). The enum also has **no value for
> "actively disproven,"** which is a distinct and more useful state than "Unverified." Proposed
> v1.3.2 amendment: add `Refuted` to the enum, and permit `mixed` on composite artifacts
> **only** when accompanied by a `truth_status_breakdown` map. Until that ADR lands, treat this
> header as a documented deviation, not precedent.

# Provenance Spine v1.4 — Repository & Primary-Source Verification Report

## TL;DR
- **The design's central "greenfield" assumption is FALSE.** A KERI-shaped provenance packet subsystem (`packages/activity_log/provenance.py`), an evidence-bearing `submit_claim` with a governed hard-block, an `EvidenceRef` that already includes `provenance_packet`, an `Action` record with `provenance_path`/`provenance_packet_id`/`provenance_hash`, and a Rust `consent_integrity` Holochain zome with `ConsentPayload`/`ConsentDecision` all already exist on `main`. The design largely re-specifies work that is already merged.
- **PR #38 could not be verified.** GitHub PR pages are robots-blocked and un-indexed; the rendered open-PR list tops out at #35. Whether #38 is a real merged/closed PR, or does not exist, is undetermined — but the provenance/consent subject-matter it supposedly produced is already present in `main`.
- **On Part B, most KERI claims check out, but the load-bearing "migration is additive" claim is FALSE.** `D`/`B`, `E`, `0B`, and the `#` SAID placeholder are all verified against keripy source. But `t:"prov"` is not a registered KERI ilk, KERI does not use RFC 8785/JCS serialization, and a real KERI migration requires a translation/re-canonicalization step — so the main stated rationale for the Ed25519 choice does not hold on those grounds.

---

## PART A — Repository Findings (G-0-B/FLOSS, branch `main`)

**Access note.** The public repo, its README, and PR #25 were retrievable in rendered HTML. GitHub tree/blob/raw/API pages and the PR list beyond the rendered HTML were robots-blocked for automated fetch. File-level internals below were retrieved by a subagent using a repository-reader tool reading `main` directly; those are marked **Verified (file contents)**. The repo is public (3 stars, 2 forks, 254 commits, GPL-3.0), languages HTML/Python/Rust/TypeScript, described as "a biomimetic distributed intelligence platform … built on agent-centric architecture, verifiable provenance, and voluntary convergence."

### 9 & PR-status. What PR #38 is about — ~~UNVERIFIED (retrieval blocked)~~ **RESOLVED 2026-08-04**

> **CORRECTION merged 2026-08-10** from the detached sidecar (`verification-report-sidecar.md`,
> now in the same directory). PR #38 **exists**, is **docs-only**, and is stacked cleanly on
> PR #36 (`merge-base --is-ancestor` = 0). The provenance spine reached `origin/main` via
> **PR #36, merged 2026-06-16** — not merely a working branch. An intermediate claim that
> `provenance.py` was absent from `main` came from a stale local `main` ref and was itself
> wrong.
>
> ⚠️ **Unreconciled detail, flagged not fixed:** this report's own §9 text below cites
> **PR #25** as "merged 2026-06-16", and the sidecar's `evidence_sources` repeats that,
> while the sidecar's correction attributes the same date to **PR #36**. One of the two
> numbers is wrong. Resolving it needs authenticated repo access; do not treat either
> number as Verified until then.
>
> The original text is retained unedited below because it is a dated record of what was
> checkable on 2026-07-30. Corrections annotate; they do not rewrite history.

PR #38 could not be retrieved through any available channel (GitHub HTML robots-blocked; `.diff`/`.patch`/`api.github.com`/DeepWiki all unreachable; PR pages for this small repo are not search-indexed). The rendered open-PR list shows only **#35, #32, #31, #30, #25** (highest *open* is #35; 29 closed, 5 open). I therefore cannot confirm whether #38 exists, nor its title, description, author, commit count, files changed, merge status, review comments, or CI checks. This is a **could-not-verify**, not a confirmation of non-existence — a merged or closed PR can carry a number higher than the highest open one.

Indirect evidence: the entire subject matter the design attributes to "two months of work in PR #38" — provenance packets, evidence-bearing claims, a consent gate — is already implemented and present on `main`. The last fully-visible large PR, **#25 (merged 2026-06-16, 79 commits, author kalisam, branch `lappytop`)**, delivered the ADR batch (ADR-0 marked Validated, ADR-5 Cognitive Virology, ADR-6 Four-System Integration), the Phase-0 substrate bridge spec + 2-agent Tryorama tests, the Seam-1 consensus gate (`packages/orchestrator/` with `claim_schema.py`, `consensus_gate.py`, 16/16 tests), signed-gradient confidence `[-1,+1]`, and a `ConversationMemory` module. CodeRabbit reviewed it (docstring coverage 45% vs 80% threshold flagged). The provenance/consent layer post-dates #25.

### 1. `hook_post_write.py` — **Verified (file contents)**
- Location: `scripts/hook_post_write.py`, wired in `.claude/settings.json` as a `PostToolUse` hook matching `Write|Edit|MultiEdit`; a `PreToolUse` hook runs `scripts/hook_pre_write.py`.
- **Receives CONTENT and DIFF, plus the full tool payload** — not just a path. It reads the hook JSON from stdin, extracts `tool_name`/`tool_input`, resolves `file_path` (from `file_path`/`filePath`/`path`/`target_file`), and renders the actual change: `old_string`→`new_string` for Edit, per-sub-edit iteration for MultiEdit (capped at 5), full `content` for Write. Change blocks trimmed to ~1500 chars/side (`_MAX_CHANGE_CHARS`).
- **Computes sha256 at hook time: YES.** Imports `packages.metacoordinator_mcp.hashline` (`verify_tool_edit`, `claim_pre_write_checkpoint`, `render_verification_section`) and `packages.activity_log.provenance` (`sha256_file`, `artifact_ref`, `create_packet`); builds a provenance packet and attaches `{"type":"provenance_packet","ref":...,"sha256":...}` as evidence.
- **Failure behavior: SILENT / non-blocking.** Every failure path calls `finish()` returning 0 ("Never blocks the user: exits 0 on every failure path"). Errors logged to `FLOSS_AGENT_DIR/hook.log`. Advisory only.
- Fires once per hook invocation (not obviously parallelized per-file); path-filtered to `/packages/` `.py/.rs/.toml`, skipping tests/venv/archive/scripts (edits under `scripts/` are skipped to prevent self-recursion). Spawns a **detached background** consensus round via `scripts/hook_bg_round.py`. A D7 spec-gate advisory (`scripts/spec_gate.py advisory_note`) runs read-only for `scripts/`, `docs/specs/`, `docs/adr/`.
- `shared-hook-surface.json` exists at repo root (listed in the tree) but its generated-vs-canonical status was not confirmed.

### 2. `GatewayTools.submit_claim()` and `EvidenceRef` — **Verified (file contents)**
- File: `packages/metacoordinator_mcp/tools.py` (class `GatewayTools`); thin wrapper in `server.py`. (Note: `packages/metacoordinator_mcp/DESIGN.md` describes an older `submit_claim(content, metadata)` shape and is stale relative to the implemented code.)
- Signature: `submit_claim(self, proposer, proposal_type, summary, body, blast_radius, evidence: list[dict] | None = None) -> str`. **Accepts `evidence`** — a list of `{"type","ref","sha256"?}` dicts converted to `EvidenceRef` objects and validated.
- **Has filesystem read access: YES.** `_validate_provenance_evidence()` resolves packet paths against `workspace_root`, checks existence, recomputes `provenance.sha256_file()`, and calls `provenance.validate_packet()`. **A re-validation path for evidence already exists** and re-reads files from disk (it is not sandboxed away from the filesystem).
- **Governed hard-block already implemented:** SYSTEM/SUBSTRATE blast radius with ADR/CONFIG/SPEC changes **fail closed** with `E_GOVERNED_PROVENANCE_REQUIRED` unless a valid `provenance_packet` carrying a consent ref is present. Non-packet evidence (test/spec/commit) skips the provenance import (keeps lean installs working).
- `EvidenceRef` is a **frozen `@dataclass`** in `packages/orchestrator/claim_schema.py` (not pydantic/TypedDict/JSON schema/Rust struct): `type: str`, `ref: str`, `sha256: Optional[str]`, with `.validate()`/`.to_dict()`. `sha256`, if present, must be 64 lowercase hex chars.
- **Allowed `type` values today:** `EVIDENCE_TYPES = frozenset({"spec","test","adr","url","commit","provenance_packet"})`. The design assumed only spec/test/adr/url/commit; the code **already added `provenance_packet`** (a 6th value). Adding `file/log/activity/source_chain` would be a one-line frozenset change — **no schema version bump required**, because this is a plain dataclass, not a migrated/versioned schema. (The same file defines `ProposalType`, `BlastRadius`, `TruthStatus`, `Outcome`, and `Claim`/`Vote`/`Decision`; claim IDs are UUIDv7; implements `docs/specs/consensus-gate.spec.md`, ref ADR-6.)

### 3. `Action` record — **Verified (file contents)**
- File: `packages/activity_log/schema.py`, `@dataclass Action`. **Already has `provenance_path`** (`Optional[str]`), plus **`provenance_packet_id`** (the KERI packet SAID `d`) and **`provenance_hash`** (sha256 of the packet sidecar bytes). The two optional fields the design proposes to add (`provenance_packet_id`, `provenance_hash`) already exist.
- **Serialized to JSONL: YES** — `append_action()` appends one JSON object per line (append-only) to `.agent-surface/activity.jsonl`; best-effort, never raises. `SCHEMA_VERSION = "0.1-experimental"`. Because the new fields are optional, adding them **is backward-compatible** with existing log lines. Total record volume on disk was not measured. Ref doc: `docs/research/2026-05-18-metaharness-unification.md`.

### 4/5. Existing provenance packet implementation — **Verified: EXISTS (greenfield assumption FALSE)**
- File: `packages/activity_log/provenance.py` (~22 KB, fully implemented, KERI-shaped): self-addressing packet IDs (SAID), Ed25519 signatures (pynacl), RFC 8785 canonical bytes (via the `jcs` package), blake3 digests, per-agent hash-linked chain (`s` sequence, `p` prior back-link), `.chain.json` head state with file locking.
- Functions: `create_packet`, `validate_packet` (signature + SAID digest + version-length + artifact-hash + prior-chain continuity + recursive evidence-DAG checks with cycle detection and depth cap), `load_or_create_identity` (writes `private.key`/`public.key`/`aid`, chmod 600), `sha256_file`, `artifact_ref`, `packet_has_consent`/`entry_has_consent` (checks `consent_ref.decision_action_hash`), `narrative_lines`.
- Constants: `VERSION_PREFIX="FLOSSI10JSON"`; AIDs prefixed `D`; signatures prefixed `0B`; packet fields `v, t="prov", d, i, s, p, a, sigs`. Output to `.agent-surface/provenance/<YYYY-MM-DD>/<digest>.json` — **matching the design's assumed `.agent-surface/provenance/` directory**. Lazy-imported (PEP 562 `__getattr__`) so lean installs without blake3/jcs/nacl still work. There is a `docs/specs/provenance-packet.spec.md`.

### 6. Consent coordinator (Rose Forest / Holochain) — **Verified (file contents); deployment Specified, not Validated**
- Location: `ARF/dnas/rose_forest/zomes/`. The DNA has 4 active workspace zomes: `integrity`, `coordinator` (`rose_forest`, 9 externs, 8/8 tests), and the consent pair. The consent zome = **`consent_integrity`** (Rust, HDI; `Cargo.toml` name `consent_integrity` v0.1.0, deps `hdi`/`serde`/`holochain_serialized_bytes`/`thiserror`), plus `consent_coordinator` (`consent`, 5 externs). It implements **`ConsentPayload`** and **`ConsentDecision`** entry types per **ADR-12** (`docs/adr/ADR-12-consent-gate-protocol.md`), spec `docs/specs/consent-payload.spec.md` + `.schema.json`.
  - `ConsentPayload`: pattern_id, pattern_type, pattern_hash (64-char sha256), proposer_did, recipient_did, blast_radius, non-empty consent_scope, optional refusal_modes/parent_consent_id/rationale.
  - `ConsentDecision.outcome` ∈ {Accept, BoundedAccept, Reject, TouristObserve, CounterPropose}; `scope_granted ⊆ consent_scope`; optional counter_frame_ref/rationale/expiry. Link types PatternHashToPayload, PayloadToDecision, DeciderToDecision.
- **It is Rust (a Holochain zome), not Python.** **Test status:** compiles clean to wasm32-unknown-unknown; native unit tests **10/10 pass** (`cargo test -p consent_integrity`). **Tryorama/Sweettest integration FAILS** at `AdminWebsocket.installApp` — no `@holochain/tryorama` version pairs with hc 0.6.1 (tracked blocker "M13"). Self-described status: "Specified with verified implementation slices."
- **This is the design's biggest self-lockout risk.** The design hard-blocks governed edits on a `ConsentDecision` action hash, but the consent substrate is **not reachable end-to-end** (no running conductor with passing integration tests). If `submit_claim`'s governed block ever requires a real on-chain Holochain `ConsentDecision` action hash, governed edits would self-lockout until the Tryorama/hc version mismatch is resolved. Currently the Python side only checks that a `consent_ref.decision_action_hash` string is present — which can be satisfied without a live conductor, but that weakens the guarantee to a non-verified string.
- Identity zome (`identity_integrity`/`identity_coordinator`, intended "KERI/ACDC identity", `AutonomousIdentifier`/`register_aid`/`rotate_key`) exists on disk but is **EXCLUDED from the workspace pre-migration** (Holochain 0.4 line; not in `ARF/Cargo.toml` members). It does not currently compile or participate; specific symbols were not read. So the design should not assume a live KERI identity substrate either.

### 7. Shared surfaces — **Partially Verified**
- Confirmed at repo root (README tree): `shared-context-surface.json`, `shared-skill-surface.json`, `shared-hook-surface.json`, `shared-agent-surface.json`, `shared-agent-memory-surface.json`, `shared-ai-roster-surface.json`.
- `RUNTIME_SURFACES.md`, `METAHARNESS_OPERATING_MODEL.md`, and a materializer with a `--check` mode were **not located** (the repo is large; these are not confirmed absent). `docs/adr/INDEX.md` is referenced by the README and exists. A spec-gate registry mechanism exists (`scripts/spec_gate.py`, `advisory_note`). The generated-vs-canonical distinction was not confirmed for the surface JSONs.

### 8. Python dependencies — **Partially Verified**
- No root `pyproject.toml` or `requirements.txt` was found; dependency declarations must live per-package or in a subdir not reached. **Deps proven used via imports:** `blake3`, `jcs` (RFC 8785 canonicalization), `pynacl` (`nacl.signing` → Ed25519 signing), stdlib `hashlib` (sha256), plus `litellm`, `requests`, `python-dotenv`, and optional `mcp` (FastMCP). So Ed25519 signing (via **pynacl**, not a separate `cryptography` dependency), blake3, JSON canonicalization (jcs), and hashlib are all already present and central to the existing provenance spine. Existing canonicalization code = the `jcs` library.

### 10. CI / tests — **Verified (partial)**
- `.github/workflows/codeql.yml` is active (CodeQL on push/PR to `main`, merge_group, weekly cron, workflow_dispatch; analyzes actions/javascript-typescript/python/rust with `+security-and-quality`; ignores archive/docs/media/*.md).
- `.github/workflows/rust-ci.md` — **note the `.md` extension**, so it **does not execute** (Actions only runs `.yml`/`.yaml`). The intended Rust CI (cargo fmt/clippy/test, SARIF upload) is effectively disabled.
- Python tests live in per-package `tests/` dirs (`packages/metacoordinator_mcp/tests`, `packages/activity_log/tests`). No pytest workflow was found among CI files (CodeQL analyzes Python but does not run pytest). Rust: `consent_integrity` 10/10, `rose_forest` 8/8 (native). Overall "tests pass" is **claimed/Specified in repo docs, not independently observed via a live CI run.**

---

## PART B — Primary-Source Technical Verification

### B1. Ed25519 codes `D` (transferable) / `B` (non-transferable) — **Verified**
keripy `MtrDex` (src/keri/core/coring.py): `Ed25519N: 'B'` ("Ed25519 verification key non-transferable, basic derivation") and `Ed25519: 'D'` ("Ed25519 verification key basic derivation"). This confirms the correction: the prior claim that `B` is transferable was wrong — **`B` is Ed25519N (non-transferable), `D` is transferable.** The `NonTransDex` codex contains `B`, `1AAA`, `1AAC`; `Matter.transferable` returns True iff the code is NOT in `NonTransDex`. For a basic (non-delegated, non-multisig) transferable Ed25519 AID, the prefix `i` is the qb64 of the public verification key with code `D` — i.e. **self-certifying** (the identifier IS the encoded key), not self-addressing. Correct.

### B2. `E` = Blake3-256 digest, 44 chars — **Verified**
`MtrDex.Blake3_256 = 'E'`. In Matter's `Codes` table, `'E': Sizage(hs=1, ss=0, fs=44)`. So `E` (1 hard char) + 43 base64url chars = 44 total, encoding a 32-byte digest (with CESR front-padding/type-code substitution). Correct.

### B3. SAID `#` placeholder = final length (44) — **Verified**
Per keripy's `Saider.saidify` and IETF `draft-ssmith-said`: the digest field (`d`) is replaced with dummy `#` characters (ASCII 35 decimal) equal in length to the final SAID string — **44 characters for a Blake3-256 SAID** — the digest is computed over that serialization, then the placeholder is replaced with the CESR-encoded digest of the same total length. This is exactly keripy's convention (its `Saider` uses this dummy-and-recompute-and-compare procedure for verification).

### B4. `0B` = Ed25519 signature, 88 chars — **Verified**
`MtrDex.Ed25519_Sig = '0B'`; `Codes['0B'] = Sizage(hs=2, ss=0, fs=88)`. So `0B` (2 hard chars) + 86 base64url chars = 88 total, encoding a 64-byte signature. `0B` is the **non-indexed** (Matter/Cigar) signature code — correct for a single detached, non-indexed signature. Indexed signatures inside a multisig event use the separate Indexer/Siger tables (e.g. `A##`); those do NOT apply to a standalone detached signature.

### B5. Event-type (`t`) ilks; `t:"prov"` — **Verified**
keripy's `Ilkage`/`Ilks`: `icp, rot, ixn, dip, drt, rct, ksn, vcp, vrt, iss, rev, bis, brv, req`. **`"prov"` is not a registered ilk.** If fed to keripy's Kevery/parser as a key event, `t:"prov"` would not be recognized or routed as a KEL event. In the FLOSS repo this is moot because `provenance.py` uses `t="prov"` in its **own** `FLOSSI10JSON` packet format and never hands packets to a keripy parser — but it means these packets are KERI-*shaped*, not KERI, and would be rejected by a real KERI implementation.

### B6. KERI inception required fields; is migration "additive"? — **Fields Verified; the claim is FALSE**
A real KERI inception (`icp`) requires, in field order: `v, t, d, i, s, kt, k, nt, n, bt, b, c, a` (CESR 2.00 adds field-ordering and count-code rules). Semantics: `d`=SAID of the event; `i`=controller AID; `s`=sequence number (MUST be 0 for `icp`); `kt`=signing threshold; `k`=current signing keys; `nt`/`n`=next-key threshold and pre-rotation digest commitment; `bt`/`b`=witness threshold and witness list; `c`=configuration traits; `a`=anchored seals/data.

**The claim that adopting KERI field conventions now makes a future migration to real KERI "additive (just add fields)" is not supported.** A genuine migration requires more than adding fields: (a) KERI serializes with its own version-string-sized fixed field maps, **not RFC 8785/JCS** — the repo's `jcs`-canonicalized bytes are a different serialization, so any SAID would have to be recomputed under KERI's rules; (b) the ilk must change from `"prov"` to a registered type; (c) the self-certifying `i` prefix, KEL chaining, pre-rotation (`nt`/`n`), and witnessing (`bt`/`b`) have no analog in the current packet's `i/s/p` fields; (d) the version string is `FLOSSI10JSON`, not a `KERI` version string. In short, **a translation/re-canonicalization step is required regardless.** The "additive migration" rationale for choosing Ed25519 therefore does not hold. Ed25519 remains a defensible choice on independent merits (32-byte keys, 64-byte signatures, pynacl already a dependency) — just not on that stated ground.

### B7. RFC 8785 (JCS) Python implementations — **Verified**
- **`rfc8785`** (trailofbits, v0.1.4): pure-Python, no-dependency, actively maintained; README states it is "behaviorally comparable to Andrew Rundgren's reference implementation" and it is tested against RFC 8785 vectors — the strongest correctness story. Caveat: it is a small project (~12 GitHub stars) despite the vector testing.
- **`jcs`** (titusz, v0.2.1) — **the package the FLOSS repo actually imports.** A thin Python-3 wrapper around Anders Rundgren's reference `cyberphone/json-canonicalization` code, which is itself the RFC 8785 Appendix G reference implementation. Correct, but minimal/low-activity (v0.2.1) with a small comprehensive test-data set inherited from upstream.
- **`json-canonical`** — Rundgren-derived, older, Python-2-oriented lineage.
- **`jsoncanon`** (v0.2.x) — partial; **does not support floating-point numbers**, a real divergence from RFC 8785.
Caveat: KERI itself does **not** use JCS; JCS is the FLOSS packet's own choice, not a KERI convention — reinforcing B6.

### B8. `blake3` Python package — **Verified**
Latest **`blake3` 1.0.9** (line 1.0.x), Python bindings over the official Rust implementation via PyO3, author "Jack O'Connor," license "CC0-1.0 OR Apache-2.0." The API matches Python's `hashlib` (`blake3(b"..").digest()`, incremental `update()`, hex output, keyed/derive-key modes) — for BLAKE3-256 output use the default 32-byte `.digest()`. Actively maintained; PyPI Stats reports ~3.5M downloads/month ("Downloads last month: 3,513,108"); wheels for CPython incl. 3.13/3.14. **Stability caveat (verbatim from the PyPI page):** "This wrapper is not currently thread-safe… we release the GIL during update, to avoid blocking the entire process. However, that means that calling the update method on the same object from multiple threads at the same time is undefined behavior." This matters only for shared-hasher concurrency, not for the one-packet-at-a-time hook path.

### Compose-before-build: existing standards for signed provenance sidecars — **Verified (important)**
Mature standards already cover "signed provenance sidecar records for artifacts":
- **in-toto attestations** (ITE-6): a signed statement/subject/predicate envelope, the common substrate under Sigstore and SLSA.
- **SLSA provenance**: expressed as an in-toto predicate. SLSA's own "Distributing provenance" spec (v1.0/v1.2) explicitly recommends **sidecar files** — "The provenance SHOULD have a filename that is directly related to the build artifact filename … (for example in-toto recommends `<filename>.intoto.jsonl`)" — plus a hash pointer in a transparency log. GitHub Actions has native generation via `actions/attest-build-provenance`.
- **Sigstore/Cosign**: keyless signing + the Rekor transparency log.
- **C2PA**: content provenance/attribution. It is being pulled into regulation: EU AI Act **Article 50** machine-readable-marking obligations become enforceable **August 2, 2026** (penalties up to €7.5M or 1.5% of global turnover), and California's **SB 942 (AI Transparency Act)** took effect **January 1, 2026**, with **AB 853** (signed Oct 2025) moving the watermarking date to **August 2, 2026** and explicitly recognizing C2PA as a compliance mechanism.
These target build artifacts rather than per-edit agent actions, but the envelope + sidecar + transparency-log shape is exactly what Provenance Spine reinvents. Agent-specific provenance work is also emerging (e.g. Prov-Agent, 2025; IETF `draft-jiang-seat-dynamic-attestation`; OWASP Top 10 for Agentic Applications 2026). Adopting or wrapping an in-toto predicate would likely be less work than a bespoke `FLOSSI10JSON` format and would interoperate with existing verifiers.

---

## Could NOT be verified
- **PR #38 in its entirety** — existence, state, contents, commits, reviews, CI. GitHub PR/tree/blob/raw/API robots-blocked and un-indexed; no authenticated API access available. This is the single largest gap and should be resolved out-of-band.
- **`RUNTIME_SURFACES.md`, `METAHARNESS_OPERATING_MODEL.md`, materializer `--check` mode** — not located (not confirmed absent).
- **Action-record volume / line count** on disk.
- **Live test pass/fail** — Rust unit counts and Python suite counts are self-reported in repo docs; no live CI run was observed, and `rust-ci.md` does not execute.
- **Identity-zome specific symbols** (`AutonomousIdentifier`, `KeyEventLog`) — folder excluded pre-migration; source not read.
- **Exact per-package dependency pins** — no root manifest found.

## Recommendations
1. **Stop treating this as greenfield (do this first).** Before any Provenance Spine v1.4 implementation work, read `packages/activity_log/provenance.py`, `packages/metacoordinator_mcp/tools.py`, `packages/orchestrator/claim_schema.py`, `packages/activity_log/schema.py`, and `docs/specs/provenance-packet.spec.md`. Reframe v1.4 as a *diff* against the existing implementation, not a from-scratch contract. Benchmark to change this stance: none — the implementation demonstrably exists.
2. **Resolve PR #38 out-of-band.** Use an authenticated GitHub session/API to confirm its state and diff before assuming it is "the latest work." If it is unmerged, reconcile it against what is already on `main`; if it does not exist, treat `main` (post-#25) as ground truth.
3. **Fix the consent self-lockout before enabling the governed hard-block in production.** `consent_integrity` passes native tests (10/10) but has **no working Tryorama/Sweettest end-to-end path** (hc 0.6.1 vs tryorama mismatch, blocker M13). Either (a) keep the governed block satisfiable by a validated-but-not-yet-on-chain consent ref until the conductor path works, or (b) gate the hard-block behind a feature flag that is off until a running conductor with passing integration tests exists. **Threshold to flip it on:** a green Tryorama run against hc 0.6.x.
4. **Use the existing `EvidenceRef` extension path.** Adding `file/log/activity/source_chain` is a one-line `EVIDENCE_TYPES` frozenset edit with no migration or version bump; `provenance_packet` is already present. Keep `sha256` validation (64-char lowercase hex).
5. **Reconsider the KERI/Ed25519 rationale.** Keep Ed25519 (pynacl is already a dep; keys/sigs are small), but drop the "additive migration to real KERI" justification — it is false (B5/B6). If real KERI interop is genuinely a goal, plan an explicit translation layer and consider using keripy's `Saider`/`Matter` directly rather than a hand-rolled `FLOSSI10JSON` format; do not use `t:"prov"` if the packets are ever to touch a KERI parser.
6. **Compose before building.** Evaluate an in-toto/SLSA predicate + Sigstore/Rekor (or C2PA where content attribution is the goal) as the wire format instead of a bespoke packet. **Threshold to justify bespoke:** only if a concrete requirement (per-edit granularity, offline Holochain-native operation, no external transparency-log dependency) is shown to be unmet by an in-toto predicate.
7. **Pin dependencies explicitly.** Add a root manifest pinning `blake3` (1.0.x), `pynacl`, and a JCS library. Prefer `rfc8785` (trailofbits, vector-tested) over `jcs` 0.2.1 for the canonicalizer; at minimum pin `jcs==0.2.1` and add RFC 8785 test vectors to CI so canonicalization can't silently drift.
8. **Turn on real CI.** Rename `rust-ci.md` → `rust-ci.yml` and add a pytest workflow so the claimed Rust/Python test passes are actually enforced on push/PR.

## Caveats
- All file-level Part A findings depend on a single repository-reader pass on `main`; they were not independently re-fetched from github.com (robots-blocked). Line-level details (exact signatures, frozenset contents, field names) are as reported by that reader and should be spot-checked directly before relying on them for implementation.
- keripy has two mirrors (WebOfTrust/keripy current; decentralized-identity/keripy archived Apr 2023). The code tables cited (`B`/`D`/`E`/`0B`, ilks, sizes) are consistent across both; CESR 2.00 adds native field-ordering/count-code details beyond the 1.0 tables but does not change those code assignments.
- "Verified" for Part B means confirmed against a primary source (keripy source, IETF drafts, RFC 8785, PyPI). "Specified" means documented in the repo as design/intent but not confirmed running end-to-end. "Unverified" means retrieval was blocked or the item was not found.