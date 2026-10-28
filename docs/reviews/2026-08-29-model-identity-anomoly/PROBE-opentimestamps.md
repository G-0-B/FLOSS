# Direct probe — OpenTimestamps

**Date:** 2026-08-29
**Trigger:** review group `G2` (6 reviewers) said the ADR-18 ladder was not
satisfied; three named OpenTimestamps, which the anchor's prior-art survey never
covered.
**Method:** installed and run, not read about. Isolated venv; the project
environment was not modified and no dependency was added to any requirements file.
**Platform:** Windows, CPython 3.13.1, `win32`.

## Result: it works, and its reference tooling does not work here

### What succeeded

Stamped the real genesis anchor file and got a real proof.

```
sha256(anchor.json) = aba2ec52cec1dcc12dbbb2630ac22f12dbb18bb7698975f0790e6c14052229c4
proof               = 235 bytes
attestation         = PendingAttestation https://bob.btc.calendar.opentimestamps.org
```

The proof deserializes to a genuine Merkle path — five `sha256` steps with
`append`/`prepend` operands — terminating in a calendar attestation. The library
upgrade path is reachable and correctly reports
`CommitmentNotFoundError: 'Pending confirmation in Bitcoin blockchain'` minutes
after stamping, which is the expected state.

Minimal dependency set for stamping is **`opentimestamps` alone** — no
`opentimestamps-client`, no GitPython:

```
opentimestamps==0.4.5
pycryptodomex==3.23.0
python-bitcoinlib==0.12.2
```

Verified by stamping successfully from a second venv containing only those.

### What failed

**1. Every `ots` CLI subcommand is unusable on this platform.** `stamp`,
`upgrade`, `verify` and even `info` all die at import:

```
bitcoin/core/key.py: ctypes.cdll.LoadLibrary(
    ctypes.util.find_library('ssl.35') or ... or ctypes.util.find_library('libeay32'))
TypeError: argument of type 'NoneType' is not iterable
```

`python-bitcoinlib` looks for an OpenSSL DLL that CPython 3.13 on Windows does
not expose. `import bitcoin` succeeds; `import bitcoin.core.key` does not. The
library API avoids that module entirely, which is why stamping worked — but
**the reference client is not an option here without shipping OpenSSL DLLs.**

**2. Two of three default calendars had expired TLS certificates at probe time.**

```
a.pool.opentimestamps.org                 CERTIFICATE_VERIFY_FAILED: certificate has expired
alice.btc.calendar.opentimestamps.org     CERTIFICATE_VERIFY_FAILED: certificate has expired
b.pool.opentimestamps.org                 OK, notAfter=Nov 24 04:22:31 2026 GMT
```

One of three reachable. The proof therefore rests on a single calendar. That is
an availability property of a volunteer-operated public service and it will vary;
it is not a permanent defect. It does mean **calendar failure must be a handled
outcome, not an exception**, and that the calendar list must be configurable.

**3. Bitcoin confirmation is hours, not immediate.** Between stamping and
confirmation you hold a *calendar promise*, not a Bitcoin proof. Any gate built
on this needs a pending state, and pending is not a pass.

## What it actually solves

The reviewers partly conflated two different things, and the probe separates
them:

| | Provides a set commitment | Provides an external witness |
|---|---|---|
| Our Merkle tree | **yes** | no |
| OpenTimestamps | no — it timestamps *a digest* | **yes** |

**OpenTimestamps is not a replacement for the anchor. It is a replacement for
the anchor's publication mechanism.** It cannot commit to the packet set; it can
only attest that a digest existed by a certain time. So the correct ladder
verdict is **compose**, not `adopt` and not `build`: keep the leaf/tree
construction, replace git-tag-as-witness with an OTS stamp over the root.

That is a more precise answer than any single reviewer reached, and it means
`G3` ("git is already a Merkle tree") is *not* answered by adopting OTS.

### Against the open findings

- **`G6` — the tag/firehose is not an immutable witness.** Solved by
  construction. No operator-controlled ref sits in the trust path.
- **`G21` — the 30-day retention cliff.** This is the decisive advantage.
  GitHub Events retention is 30 days; a Bitcoin block header does not expire.
  The tag mechanism has a hard expiry and this does not.
- **`G12` — republishing over a truncated store returns VERIFIED.** Improved,
  not solved. The operator can still stamp a fresh consistent anchor. What
  changes is that they **cannot delete the earlier one** — a verifier holding any
  prior proof can demonstrate permanent, self-verifying equivocation, where the
  git-tag path lets the record simply expire.
- **`G2` — the ladder.** Adopting this for witnessing satisfies it.
- **`G26` — "no network egress" was already contradicted** by the git push, so
  OTS's egress-at-stamp-time costs nothing that was not already spent.

### What it still does not do

- Proves "no later than", never "no earlier than". Backdating remains
  unprevented.
- Attests a digest, not that the digest is *the* store's true contents.
- The operator can simply stop stamping. Absence of a proof is not evidence of
  anything.
- Verification against Bitcoin needs block headers — a node, or trusting a block
  explorer, which reintroduces a third party at verify time.

## Recommendation

**Compose: keep the set commitment, replace the witness.** Stamp the
`merkle_root`, not the file, so the proof binds the commitment rather than one
serialization of it. Carry the proof in `anchor.json` as a `witnesses[]` entry —
the shape the spec already anticipated.

Land it behind the platform findings above: use the library API rather than the
`ots` CLI, make the calendar list configurable with a documented default, treat
calendar failure and pending confirmation as first-class outcomes, and do not
report a pending stamp as a witness.

**This is a probe, not an adoption.** Nothing in the project depends on
OpenTimestamps as of this commit, and no requirements file was touched.
