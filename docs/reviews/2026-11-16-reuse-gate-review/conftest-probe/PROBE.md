# conftest / OPA probe against the reuse gate's requirements

Run 2026-11-16 by Claude Fable 5.2 (self-reported), on the operator's go-ahead
to download conftest. Truth status: the four runs below are **Verified** (run
on this machine, output quoted). The conclusion drawn from them is the
proposer's judgement and is **Specified** until an independent reviewer
accepts it.

Why: three independent reviews of the reuse-gate entry voted REVISE because
every rejected candidate was unprobed. Two of them named Open Policy Agent /
conftest as the strongest replacement for the custom checks in
`scripts/spec_gate.py`.

## What was run

- conftest 0.71.1 (OPA 1.21.1), Windows x86_64 release asset from
  `open-policy-agent/conftest`, published 2026-10-06. Zip sha256
  `34d623334b5e7ed4465bf62a4cb3b092684859cd3d224bbd390925a0852b922a`, equal to
  the release's `checksums.txt`. Not installed; run from a scratch directory.
- Policy: `policy/reuse.rego` beside this file (37 lines).
- Input: `docs/specs/spec-registry.json` at commit `ff58215`.

| Run | Requirement | Command (abridged) | Result |
|---|---|---|---|
| A | R1: a tier-2 entry whose reviewer is a string fails | `conftest test spec-registry.json -p policy` | Fired on `FLOSS/docs/specs/reuse-gate.spec.md`, the one entry with a string reviewer |
| B | R2: evidence older than 120 days fails | same, on a copy with `search_date` set to 2026-07-01 | Fired on that entry |
| C | R4: a file on a gated surface with no entry fails | same, plus `-d tree.json`, a file list made by `git ls-files` in a wrapper | Fired, including on a planted path. conftest did not list the tree; the wrapper did |
| D | R3: the reviewer record is a real file whose sha256 matches | `conftest test ADR-18-prior-art-reuse-gate.md` | `unknown parser: md`; with `--parser json`, `invalid character '#'`. conftest evaluates parsed documents and cannot read or hash an arbitrary file |

Run C produced 56 R4 failures because the probe policy does not carry the
gate's exemptions (`__init__.py`, `tests/`). Those are string rules and would
port to Rego; the count is not a finding about the tree.

Run A's own exit code, captured separately without a pipe, was 1.

## What the probe shows

- R1 and R2, and by extension the other JSON-shape checks, are expressible in
  Rego. A policy engine can replace that part.
- R3 is not possible in conftest: no file read, no hashing of file bytes. The
  same limit applies to the gate's content-pinned exemption and to
  `record_digest`.
- R4 needs a program outside conftest to walk the tree and apply path
  normalisation, then hand the result in as data.

So adopting conftest does not remove the custom script. It splits the gate
into a Rego policy plus a wrapper that still walks the tree, resolves and
hashes record files, and calls a Go binary that every CI runner and every
agent workstation must install. The requirement it fails as a replacement is
"one fail-closed command with no dependency beyond the Python the repository
already needs".

## What the probe does not show

- Nothing about archgate or in-toto. Both remain unprobed.
- Nothing about Rego maintainability against the gate's 91 tests.
- A `compose` design (conftest for shape rules, a thinner wrapper for the
  rest) is not ruled out on capability. It is declined here on dependency
  cost, which is a judgement a reviewer may reject.
