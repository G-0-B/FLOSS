"""Rotate the post-write hook's provenance identity, 2026-10-14.

Carries out the remedy ADR-20 accepted and left as an operator action:
"identity rotation with a signed lineage statement". Operator go-ahead given
2026-10-14 in session ("this is the authorization go is green").

Nothing is deleted. The old identity folder is renamed, its key kept, so the
old chain stays verifiable as an audit record and the lineage statement can be
signed by both keys.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
from datetime import datetime, timezone

sys.path.insert(0, r"C:/~shit/FLOSS")
from nacl.signing import SigningKey, VerifyKey  # noqa: E402

from packages.activity_log import provenance as pv  # noqa: E402

AGENT = pathlib.Path(os.path.expanduser("~")) / ".floss_agent"
LIVE = AGENT / "identity"
RETIRED = AGENT / "identity.retired-2026-10-14"
LINEAGE_DIR = pathlib.Path(r"C:/~shit/.agent-surface/identity-lineage")
STORE = pathlib.Path(r"C:/~shit/.agent-surface/provenance")

assert LIVE.is_dir(), "no live identity folder"
assert not RETIRED.exists(), "retired folder already exists; refusing to reuse it"

old_aid = (LIVE / "aid").read_text(encoding="utf-8").strip()
old_state = json.loads((LIVE / f"{old_aid}.chain.json").read_text(encoding="utf-8"))
print("old identity:", old_aid, "state:", old_state)

# 1. Hold both of the identity's locks so no hook writes while the folder moves.
seq_lock, id_lock = LIVE / ".sequence.lock", LIVE / ".identity.lock"
seq_token = pv._acquire_lock(seq_lock)
id_token = pv._acquire_lock(id_lock)
try:
    os.rename(LIVE, RETIRED)
finally:
    # The lock files moved with the folder; remove them there, by token.
    pv._release_lock(RETIRED / ".sequence.lock", seq_token)
    pv._release_lock(RETIRED / ".identity.lock", id_token)
print("renamed to", RETIRED)

# 2. The new identity, created exactly as the hook would create it.
new = pv.load_or_create_identity(LIVE)
print("new identity:", new.aid)
assert new.aid != old_aid
assert not (LIVE / f"{new.aid}.chain.json").exists(), "new identity should have no chain yet"

# 3. The lineage statement, signed by both keys over its JCS canonical bytes.
old_key = SigningKey(pv._b64url_decode((RETIRED / "private.key").read_text(encoding="utf-8").strip()))
assert "D" + pv._b64url_encode(bytes(old_key.verify_key)) == old_aid, "retired key does not match its aid"
statement = {
    "t": "lineage",
    "v": "floss-identity-lineage/0.1-draft",
    "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "from": {
        "aid": old_aid,
        "head": {"d": old_state["head"], "s": str(int(old_state["next_sequence"]) - 1)},
        "valid_through_s": "1",
        "defects": [
            "s=2 names s=0 as its prior while s=1 exists (a fork, 2026-05-25)",
            "s=4 and s=5 carry no prior although they are not s=0 (false origins, 2026-05-25)",
            "s=3, 36, 37 and 39 are absent from the store",
            "s=36, 37 and 39 were signed between 2026-07-17 and 2026-07-30 by a writer that is not the post-write hook; unidentified",
        ],
        "kept_at": str(RETIRED),
    },
    "to": {"aid": new.aid, "starts_at_s": "0"},
    "reason": "Every packet after s=1 fails the validator's whole-ancestry check (E_PROVENANCE_SEQUENCE_DISCONTINUOUS), so no claim from the post-write hook has landed since 2026-08-25. Signed packets cannot be repaired.",
    "decision": "ADR-20, 'identity rotation with a signed lineage statement' (accepted, not implemented until now); operator go-ahead 2026-10-14",
    "trace": "docs/research/2026-10-14-session-control/provenance-trace.md (branch feat/coordination-room-rebased)",
    "sigs": {},
}
unsigned = pv.canonical_bytes(statement)
statement["sigs"] = {
    "from": "0B" + pv._b64url_encode(old_key.sign(unsigned).signature),
    "to": "0B" + pv._b64url_encode(new.signing_key.sign(unsigned).signature),
}

# Verify both signatures from the public keys alone.
check = dict(statement, sigs={})
for role, aid in (("from", old_aid), ("to", new.aid)):
    VerifyKey(pv._b64url_decode(aid[1:])).verify(pv.canonical_bytes(check), pv._b64url_decode(statement["sigs"][role][2:]))
print("both signatures verify")

# 4. Store it outside the packet store, and beside the retired key.
LINEAGE_DIR.mkdir(parents=True, exist_ok=True)
name = f"2026-10-14-{old_aid[:12]}-to-{new.aid[:12]}.json"
body = json.dumps(statement, indent=2, sort_keys=True) + "\n"
(LINEAGE_DIR / name).write_text(body, encoding="utf-8")
(RETIRED / "lineage.json").write_text(body, encoding="utf-8")
(RETIRED / "RETIRED.md").write_text(
    "# Retired provenance identity\n\n"
    f"`{old_aid}` was the post-write hook's identity from 2026-05-24 to 2026-10-14.\n"
    "Its chain forked on 2026-05-25, so every packet after sequence 1 fails validation.\n"
    f"Retired 2026-10-14 under ADR-20's accepted remedy; successor `{new.aid}`.\n"
    "The lineage statement in `lineage.json`, also at `C:/~shit/.agent-surface/identity-lineage/`, is signed by both keys.\n"
    "Keep this folder. Do not use this key for new packets. Any packet signed by it after 2026-10-14 is evidence of an unknown writer.\n",
    encoding="utf-8",
)
print("lineage written:", LINEAGE_DIR / name)
print("old packets still in store:", sum(1 for p in STORE.rglob("*.json") if json.loads(p.read_text(encoding="utf-8")).get("i") == old_aid))
print(json.dumps({"old_aid": old_aid, "new_aid": new.aid, "lineage": str(LINEAGE_DIR / name)}))
