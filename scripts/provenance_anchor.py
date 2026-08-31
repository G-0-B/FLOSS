"""Publish and verify the Merkle anchor over the provenance packet store.

    python scripts/provenance_anchor.py publish
    python scripts/provenance_anchor.py verify

`publish` writes a signed anchor to `.anchors/anchor.json` and prints the root.
`verify` recomputes the root from the current store and compares.

WHY THE ROOT GOES IN A TAG NAME

Publishing the anchor file is not, by itself, an external anchor. The operator
controls the packet store AND the git remote, so a ref they can rewrite
constrains nobody. What the operator does NOT control is the record third
parties keep of a public push: a public repository emits `PushEvent` and
`CreateEvent` into GitHub's public events firehose, and those events carry ref
names and commit message text into mirrors with no write path back to the
operator.

That is why `--print-tag` emits the root as part of a tag NAME rather than only
inside the file: the file is what a verifier recomputes against, and the tag
name is what survives in somebody else's copy. Pushing is left to the operator
-- this script never touches the network.

Exit codes: 0 VERIFIED, 1 ANCHOR_STALE, 2 TRUNCATION_DETECTED / ANCHOR_MISMATCH,
3 ANCHOR_UNAVAILABLE. `ANCHOR_STALE` is separated from both a pass and a failure
deliberately: honest growth between runs is the common case and must not cry
wolf, while loss must be loud. An unavailable anchor is never a pass.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = REPO_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.activity_log import anchor as anchor_lib  # noqa: E402
from packages.activity_log import witness as witness_lib  # noqa: E402
from packages.activity_log.provenance import (  # noqa: E402
    load_or_create_identity,
)

DEFAULT_PROVENANCE_ROOT = WORKSPACE_ROOT / ".agent-surface" / "provenance"
DEFAULT_IDENTITY_DIR = WORKSPACE_ROOT / ".agent-surface" / "identity"
DEFAULT_ANCHOR_PATH = REPO_ROOT / ".anchors" / "anchor.json"

TAG_PREFIX = "prov-anchor"


def tag_name(anchor: dict) -> str:
    """A tag name carrying the root, safe for git refs.

    Colons are illegal in ref names, so the timestamp is flattened. The root is
    truncated because a ref name has a practical length budget and the full root
    is in the commit message and the file; the prefix is long enough that a
    collision would itself be the news.
    """

    stamp = str(anchor.get("generated_at", "")).replace(":", "-").replace("+00-00", "Z")
    return f"{TAG_PREFIX}-{stamp}-{str(anchor.get('merkle_root', ''))[:24]}"


def commit_message(anchor: dict) -> str:
    """One line, on purpose.

    This string is printed as a shell command for the operator to run, and a
    multi-line `-m` argument does not survive that round trip. It also has to
    reach a third party intact: the whole point of putting the root in the
    message is that GitHub's public events firehose carries message text into
    mirrors the operator cannot rewrite, so the root must be on the first line
    any consumer of that feed will read.
    """

    return (
        f"chore(anchor): provenance merkle root {anchor.get('merkle_root')} "
        f"[packets={anchor.get('packet_count')} "
        f"identities={anchor.get('identity_count')} "
        f"prev={anchor.get('prev_root') or 'genesis'}]"
    )


def _retain_series(series_dir: Path, root: str, payload: bytes) -> Path:
    """Write a retained anchor without ever destroying one already there.

    The series was keyed purely by merkle_root. Two DIFFERENT anchors can share
    a root: the format version and the summary fields are outside the Merkle
    tree, so migrating a v2 anchor over an unchanged packet set produces a v3
    with the same root -- and the write replaced the v2, discarding its
    signature, its metadata and its witness claims. The migration path
    documented that the old anchor "remains as history"; the code deleted it.

    Identical bytes are a no-op (republishing the same anchor is idempotent).
    A genuinely different anchor with the same root is retained beside it.
    """

    # EXCLUSIVE CREATE, not exists()-then-write.
    #
    # The store lock is released by build_anchor() long before this runs, and a
    # publish that requests a witness spends seconds on the network in between,
    # so two invocations can both observe the same name absent and both write
    # it -- one clobbering the other, which is the single thing this function
    # promises never to do. O_CREAT|O_EXCL makes exactly one creator win at the
    # filesystem level, the same primitive claim_singleton and --reserve-slot
    # use. Losing the race is not an error: fall through, compare, and either
    # recognise identical bytes or take the next name.
    candidate = 1
    while True:
        name = f"{root}.json" if candidate == 1 else f"{root}.{candidate}.json"
        path = series_dir / name
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                if path.read_bytes() == payload:
                    return path
            except OSError:
                pass
            candidate += 1
            continue
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
        except OSError:
            # An empty file we created but could not fill is worse than none:
            # the next publish would compare against it and take a new name
            # forever. Remove it and let the caller see the failure.
            path.unlink(missing_ok=True)
            raise
        return path


def _display_path(path: Path) -> str:
    """Repo-relative when possible, absolute otherwise.

    `relative_to` RAISES for a path outside the repository, so any `--anchor`
    pointing elsewhere -- a temp directory in a test, a second store, an
    operator keeping anchors outside the checkout -- crashed publish with a
    traceback after the anchor had already been written. Found by a test that
    used a tmp_path; the earlier runs all used the in-repo default and never
    reached it.
    """

    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def _resolve_identity(identity_dir: Path, allow_new: bool):
    """Refuse to mint a signing identity as a side effect of publishing.

    `load_or_create_identity` creates a key when the directory is empty, so a
    missing or mistyped `--identity-dir` silently minted a fresh AID and signed a
    fresh, internally consistent anchor series -- the exact failure the spec says
    key pinning exists to prevent. Two reviewers flagged it (G9).

    Creating the first identity is legitimate; doing it by accident is not. It
    now requires saying so.
    """

    if not (Path(identity_dir) / "private.key").exists() and not allow_new:
        raise SystemExit(
            f"refusing to mint a new signing identity at {identity_dir}. "
            f"No private.key there, and an anchor signed by a brand-new key is "
            f"a fresh consistent series that attests nothing about the old one. "
            f"Pass --allow-new-identity if this really is the first anchor."
        )
    return load_or_create_identity(identity_dir)


def _publish(args: argparse.Namespace) -> int:
    previous = anchor_lib.load_anchor(args.anchor)

    # ABSENT AND UNREADABLE ARE NOT THE SAME ANSWER.
    #
    # load_anchor returns None for a file that is not there AND for one that is
    # there but corrupt -- invalid UTF-8, malformed JSON, or valid JSON of the
    # wrong shape. That second case was introduced by hardening the loader, and
    # this caller could not tell them apart: it read None as "no predecessor",
    # skipped the whole verify-before-overwriting guard, and wrote a fresh
    # genesis over the pointer. The retained series was never consulted, so
    # continuity with real history was neither checked nor preserved, and the
    # next verify reported a valid disconnected series.
    #
    # Refusing is right because the two cases need opposite handling: an absent
    # anchor is a first publication, an unreadable one is either corruption or
    # tampering and the retained series is still on disk to recover from.
    # --force remains the deliberate override, as it is for a detected loss.
    if previous is None and args.anchor.exists() and not args.force:
        print(
            f"refusing to publish over an unreadable anchor at "
            f"{_display_path(args.anchor)}: the file exists but could not be "
            f"loaded (bad encoding, malformed JSON, or not a JSON object)."
        )
        print(
            "  Publishing now would write a new genesis over it and start a "
            "series disconnected from the retained history, which the next "
            "verify would report as valid."
        )
        series_dir = args.anchor.parent / anchor_lib.SERIES_DIRNAME
        retained = anchor_lib.load_series(series_dir)
        if retained:
            print(
                f"  {len(retained)} retained anchor(s) remain in "
                f"{_display_path(series_dir)} -- restore the pointer from one "
                "of them, or re-run with --force if starting a new series is "
                "intended."
            )
        else:
            print("  Investigate, then re-run with --force if this is intended.")
        return 2

    # VERIFY BEFORE OVERWRITING. Publishing used to build a replacement anchor
    # without ever checking the store against the one it was replacing, so an
    # accidental truncation or interior deletion was laundered into the new
    # baseline: the next verify reported VERIFIED over a store that had lost
    # packets, and the evidence that anything went missing was the anchor being
    # overwritten.
    #
    # This is the actionable half of the standing finding that republishing over
    # a truncated store returns VERIFIED. It does not stop a deliberate
    # operator -- --force exists and they own the key -- but it stops the
    # accident, which is the case that was silently destroying evidence.
    # A SUPERSEDED FORMAT IS A MIGRATION, NOT A LOSS.
    #
    # Bumping ANCHOR_VERSION without a migration path bricked the shipped
    # anchor: the committed one was v2, the verifier accepted only v3, so
    # `verify` returned ANCHOR_UNAVAILABLE before looking at the store and
    # `publish` refused its own preflight because the predecessor was
    # unavailable. The only way forward was --force, which is the flag that
    # exists to overwrite a DETECTED LOSS -- so the documented escape route for
    # a format bump was the one reserved for destroying evidence.
    #
    # An unreadable-by-version predecessor cannot be compared, so no loss can be
    # claimed and none can be ruled out. Publishing proceeds, loudly, and starts
    # a NEW series rather than chaining to a root this build cannot verify:
    # linking to an unverifiable ancestor is the broken-series condition.
    migrating = False
    if previous is not None and previous.get("v") not in anchor_lib.SUPPORTED_VERSIONS:
        # AUTHENTICATE BEFORE BELIEVING THE VERSION.
        #
        # `v` is a field in a file anyone who can write the repository can edit,
        # and this branch acts on it by discarding `previous` -- which skips the
        # entire verify-before-overwriting preflight below. Editing one v3
        # anchor's `v` to garbage was therefore enough to make an ordinary
        # publish sign a fresh genesis over a truncated store and launder the
        # loss, with no --force anywhere.
        #
        # `v` is inside the signed pre-image, so tampering with it breaks the
        # signature: a GENUINE legacy anchor still authenticates under its own
        # signer, and a doctored one does not. That is the difference this
        # branch has to test before it is allowed to throw the predecessor away.
        # PINNED, not merely self-consistent.
        #
        # anchor_signature_problem() with no expected_signer authenticates an
        # anchor against the key the anchor itself names -- which an attacker
        # who can replace the file simply generates. The previous fix closed
        # "edit one field"; this closes "replace the whole file": sign a
        # truncated-store anchor with your own key, declare an unsupported `v`,
        # and the migration path discards the predecessor, skipping both the
        # loss preflight and the signer-continuity check below.
        #
        # The pin is the identity on disk that will sign the replacement. A
        # format migration is the same operator with a new format; a different
        # key as well is a rotation, and has to be stated as one. Read from the
        # aid file rather than resolving the identity here, because resolving
        # can MINT a key on the paths above that deliberately publish nothing.
        expected = _identity_aid_on_disk(args.identity_dir)
        unauthenticated = anchor_lib.anchor_signature_problem(
            previous, expected_signer=expected
        )
        if expected is None:
            unauthenticated = (
                "no local identity to pin against at "
                f"{_display_path(Path(args.identity_dir))}"
            )
        if unauthenticated is not None and not args.force:
            print(
                f"refusing to migrate an anchor that does not authenticate: "
                f"{unauthenticated}."
            )
            print(
                f"  It claims format {previous.get('v')!r}, which this build "
                f"does not verify. An unsupported version in a file that also "
                f"fails its own signature is tampering or corruption, not a "
                f"format bump -- and treating it as one would discard the "
                f"predecessor and skip the loss check entirely."
            )
            series_dir = args.anchor.parent / anchor_lib.SERIES_DIRNAME
            retained = anchor_lib.load_series(series_dir)
            if retained:
                print(
                    f"  {len(retained)} retained anchor(s) remain in "
                    f"{_display_path(series_dir)} to compare against."
                )
            print(
                "  A genuinely old anchor signed under a pre-v2 rule cannot "
                "authenticate here either; re-run with --force if you have "
                "confirmed that is what this is."
            )
            return 2
        migrating = True
        print(
            f"anchor format migration: the current anchor is "
            f"{previous.get('v')!r} and this build verifies "
            f"{sorted(anchor_lib.SUPPORTED_VERSIONS)}."
        )
        print(
            "  It cannot be compared against the store, so no loss is claimed "
            "and none is ruled out. Publishing a new series; the old anchor and "
            "its series files are left in place as history."
        )
        previous = None

    if previous is not None and not args.force:
        prior = anchor_lib.verify_anchor(
            args.provenance_root,
            previous,
            series_dir=args.anchor.parent / anchor_lib.SERIES_DIRNAME,
        )
        if prior["status"] in (
            anchor_lib.TRUNCATION_DETECTED,
            anchor_lib.ANCHOR_MISMATCH,
            anchor_lib.ANCHOR_UNAVAILABLE,
        ):
            print(
                f"refusing to publish: the current anchor reports "
                f"{prior['status']} against this store."
            )
            if prior.get("reason"):
                print(f"  {prior['reason']}")
            findings = prior.get("findings") or {}
            for label in (
                "vanished_identities",
                "head_regressions",
                "missing_anchored_heads",
                "missing_anchored_positions",
            ):
                if findings.get(label):
                    print(f"  {label}: {json.dumps(findings[label])[:400]}")
            print(
                "Publishing now would overwrite the only record that anything "
                "is missing. Investigate, then re-run with --force if the loss "
                "is understood and intended."
            )
            return 2

    try:
        built = anchor_lib.build_anchor(args.provenance_root, previous)
    except anchor_lib.StoreContention as exc:
        # Refusing is the point: an anchor is a signed claim that this exact set
        # was the store. Under sustained writes no such set was ever observed,
        # so there is nothing honest to sign. Publishing is cheap to retry.
        print(f"refusing to anchor a store that will not hold still: {exc}")
        print("Re-run when the provenance hooks are idle.")
        return 4

    # UNCHANGED ROOT IS A NO-OP, NOT A PUBLICATION.
    #
    # The series file is keyed by root, so republishing an unchanged store
    # overwrote the previous entry with an anchor whose prev_root EQUALS its own
    # merkle_root. walk_series then correctly reported a cycle, and every
    # subsequent verify returned ANCHOR_UNAVAILABLE -- permanently, from one
    # redundant publish. Reproduced: publish, publish, verify -> exit 3.
    #
    # A test in test_anchor.py already documented that anchoring an unchanged
    # store twice produces prev_root == merkle_root. Noticing the property and
    # not guarding the caller is how this shipped.
    #
    # BUT THE ROOT IS NOT THE WHOLE ANCHOR. The signer is outside the Merkle
    # tree, so a key rotation over an unchanged store produces a genuinely
    # different anchor that this check called a no-op -- making rotation
    # impossible in precisely the case an operator rotates in: swap the key,
    # re-anchor the same store. When a rotation is being requested, the decision
    # moves below, after the signer is known; the guard is unchanged otherwise.
    def _unchanged_noop() -> int:
        print(
            json.dumps(
                {
                    "status": "unchanged",
                    "merkle_root": built["merkle_root"],
                    "packet_count": built["packet_count"],
                    "note": (
                        "the store has not changed since the current anchor; "
                        "nothing published. Re-anchoring identical content would "
                        "make the anchor its own predecessor and break the series."
                    ),
                },
                indent=2,
            )
        )
        return 0

    # THE PREFLIGHT CHECKED A DIFFERENT SCAN THAN THE ONE BEING SIGNED.
    #
    # verify_anchor() above and build_anchor() here each walk the store
    # separately, and the lock is released between them. A packet deleted in
    # that window passes the preflight and is simply absent from the anchor
    # that gets signed -- which still links to the old root, and the series walk
    # checks signatures and links, not that a descendant covers its predecessor.
    # The replacement then verifies cleanly, laundering exactly the loss the
    # preflight exists to preserve.
    #
    # Re-checked against the SNAPSHOT BEING SIGNED, using the same subset the
    # verifier uses, so no lock has to span the two scans.
    if previous is not None and not args.force:
        dropped = anchor_lib.anchored_leaves(previous) - anchor_lib.anchored_leaves(
            built
        )
        if dropped:
            sample = sorted(dropped)[:10]
            print(
                f"refusing to publish: {len(dropped)} leaf/leaves anchored by the "
                f"current anchor are absent from the snapshot just scanned."
            )
            print(
                "  The preflight and the build are separate scans, so this is a "
                "packet that went missing between them."
            )
            for aid, seq, said in sample:
                print(f"  missing: {aid[:12]}... seq {seq} said {said[:16]}...")
            if len(dropped) > len(sample):
                print(f"  ... and {len(dropped) - len(sample)} more")
            print(
                "Publishing now would sign an anchor that omits them while still "
                "chaining to the anchor that had them. Investigate, then re-run "
                "with --force if the loss is understood and intended."
            )
            return 2

    unchanged_root = previous is not None and built["merkle_root"] == previous.get(
        "merkle_root"
    )
    if unchanged_root and not args.allow_signer_change:
        return _unchanged_noop()

    identity = _resolve_identity(args.identity_dir, args.allow_new_identity)
    rotating = False

    # Signer continuity. If a previous anchor exists, its signer is the implicit
    # pin: changing it mid-series is precisely the rotation attack the spec
    # names, and it should require an explicit statement rather than happening
    # because a key directory moved.
    if previous is not None:
        prior_signer = previous.get("signer")
        if (
            isinstance(prior_signer, str)
            and prior_signer != identity.aid
            and not args.allow_signer_change
        ):
            print(
                f"refusing to change the anchor signer. "
                f"previous={prior_signer} now={identity.aid}. "
                f"A new key can sign a fresh consistent series over any store. "
                f"Pass --allow-signer-change if the rotation is intended."
            )
            return 3
        elif isinstance(prior_signer, str) and prior_signer != identity.aid:
            # A ROTATION STARTS A NEW SERIES.
            #
            # verify pins the signer from the head and checks every ancestor
            # against it, so a series that spans a rotation fails its own
            # default verification on the first ancestor -- the publish command
            # would allow a rotation that verify can never accept. The same
            # reasoning the format-migration path already uses: an ancestor this
            # build cannot verify must not be chained to, it must be superseded.
            # The old series stays on disk as history; it is simply no longer
            # walked from this head.
            rotating = True
            print(
                f"anchor signer rotation: previous={prior_signer} "
                f"now={identity.aid}."
            )
            print(
                "  Starting a NEW series. The previous anchors remain retained "
                "as history, but this head does not chain to them: verify pins "
                "the head's signer for the whole walk, so a series spanning a "
                "rotation could never verify."
            )

    if unchanged_root and not rotating:
        # --allow-signer-change was passed but the key is the same, so this is
        # the redundant republish the guard above exists to stop.
        return _unchanged_noop()

    if rotating:
        # Break the link BEFORE signing, so the rotation is inside the signed
        # bytes rather than an unsigned edit afterwards. The identity check runs
        # after build_anchor, so the anchor already carries the old head's root.
        built["prev_root"] = None
        built["prev_generated_at"] = None

    # Witness BEFORE signing. The root is computed over leaves only, so
    # attaching a witness record does not change it -- but the record must be
    # inside the signed bytes, or an operator could add or remove witness claims
    # after the fact.
    if args.witness:
        stamped = witness_lib.stamp_root(
            built["merkle_root"], timeout=args.witness_timeout
        )
        for failure in stamped.get("failed", []):
            print(f"  calendar unavailable: {failure['calendar']}: {failure['error']}")
        if stamped["proof"] is None:
            print(
                f"WITNESS {stamped['status']}: {stamped.get('reason')}. "
                f"Publishing WITHOUT an external witness."
            )
        else:
            built["witnesses"] = [
                {
                    "kind": witness_lib.WITNESS_KIND,
                    "digest_alg": "sha256",
                    "digest": stamped["digest"],
                    "calendars": stamped["attested"],
                }
            ]

    signed = anchor_lib.sign_anchor(built, identity)

    problem = anchor_lib.anchor_signature_problem(signed)
    if problem is not None:
        # Never write an anchor we cannot ourselves verify: an unverifiable
        # anchor is indistinguishable from a tampered one at read time.
        print(f"refusing to write an anchor that does not verify: {problem}")
        return 3

    args.anchor.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(signed, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")
        + b"\n"
    )

    # RETAIN THE SERIES. Overwriting a single anchor.json left `prev_root`
    # pointing backwards into nothing, so the "anchor series is a hash chain"
    # claim was a field on one file rather than a retained history (G5).
    series_dir = args.anchor.parent / anchor_lib.SERIES_DIRNAME
    series_dir.mkdir(parents=True, exist_ok=True)
    retained = _retain_series(series_dir, signed["merkle_root"], payload)

    # Pointer written last, through a temp file. A crash mid-write used to leave
    # a corrupt anchor.json that load_anchor read as None, which would then
    # publish a fresh genesis over a real series (part of G10).
    # PER-PROCESS staging name. A single shared `anchor.json.tmp` is the same
    # race the retained series had, one file along: two publishes both write it,
    # one replaces the path while the other still holds the inode open and
    # keeps writing -- into the freshly published anchor.json -- and the loser's
    # replace can raise over a file that is no longer there. mkstemp creates
    # exclusively in the destination directory, so the rename is still atomic
    # and same-filesystem.
    args.anchor.parent.mkdir(parents=True, exist_ok=True)
    fd, staging_name = tempfile.mkstemp(
        dir=str(args.anchor.parent), prefix=args.anchor.name + ".", suffix=".tmp"
    )
    staging = Path(staging_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
        os.replace(staging, args.anchor)
    except OSError:
        staging.unlink(missing_ok=True)
        raise

    if args.witness and signed.get("witnesses"):
        proof_file = witness_lib.proof_path(args.anchor.parent, signed["merkle_root"])
        proof_file.parent.mkdir(parents=True, exist_ok=True)
        proof_file.write_bytes(stamped["proof"])
        state = witness_lib.inspect_proof(
            stamped["proof"],
            expected_digest=witness_lib.root_digest(signed["merkle_root"]),
        )
        print(f"  witness: {state['status']} -> {proof_file.name}")
        if state.get("note"):
            print(f"  {state['note']}")
    print(
        json.dumps(
            {
                "wrote": _display_path(args.anchor),
                "retained": _display_path(retained),
                "merkle_root": signed["merkle_root"],
                "packet_count": signed["packet_count"],
                "identity_count": signed["identity_count"],
                "prev_root": signed["prev_root"],
                "signer": signed["signer"],
                "tag": tag_name(signed),
            },
            indent=2,
        )
    )
    if args.print_tag:
        print()
        print("# Not run for you -- publishing is an operator decision.")
        print(f'git add "{_display_path(args.anchor)}"')
        print(f"git commit -m {json.dumps(commit_message(signed))}")
        print(f'git tag "{tag_name(signed)}"')
        print("git push origin HEAD --tags")
    return 0


def _verify(args: argparse.Namespace) -> int:
    stored = anchor_lib.load_anchor(args.anchor)
    # Default the pin to the stored anchor's own signer rather than to None.
    # `--expect-signer` defaulting to None meant the documented "actual root of
    # trust" was off unless the operator remembered to switch it on (G9). This
    # is a weaker pin than an out-of-band one -- it detects a signer change
    # within a retained series, not a series forged wholesale -- but it is the
    # strongest default available without asking the operator for a key.
    pin = args.expect_signer
    if pin is None and not args.no_pin and isinstance(stored, dict):
        pin = stored.get("signer")
    result = anchor_lib.verify_anchor(
        args.provenance_root,
        stored,
        expected_signer=pin,
        series_dir=args.anchor.parent / anchor_lib.SERIES_DIRNAME,
    )
    # Witness state is reported alongside, never folded into, the store verdict.
    # A confirmed witness does not make a truncated store VERIFIED, and a missing
    # witness does not make an intact store a failure -- they answer different
    # questions.
    result["witness"] = _witness_state(args.anchor, stored)
    print(_bounded_json(result, args.max_output))
    return anchor_lib.EXIT_CODES.get(result["status"], 2)


def _identity_aid_on_disk(identity_dir: Path | str) -> str | None:
    """The local signer identifier, WITHOUT creating one.

    load_or_create_identity() mints a key when none exists, which is wrong on
    the preflight paths that may publish nothing at all. The aid file is written
    beside the key at creation, so reading it answers "whose anchors should
    these be" without side effects. None means there is no local identity to
    pin against, which is itself a reason to refuse a migration.
    """

    try:
        aid = (Path(identity_dir) / "aid").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return None
    return aid or None


def _bounded_json(result: dict, limit: int) -> str:
    """Serialize within `limit` characters WITHOUT emitting broken JSON.

    Slicing the serialized document cut it mid-token, so the structured verdict
    became unparseable exactly when a store is damaged enough to produce a lot
    of findings -- the case where a script reading this output is most useful.
    A verdict nobody can parse is not a verdict.

    Diagnostic ARRAYS are shortened instead, longest first, each recording how
    many entries it dropped. The envelope -- status, roots, counts, witness --
    is never trimmed, because that is the part every caller reads.
    """

    def render(document: dict) -> str:
        return json.dumps(document, indent=2, ensure_ascii=False)

    rendered = render(result)
    if limit <= 0 or len(rendered) <= limit:
        return rendered

    trimmed = copy.deepcopy(result)

    def arrays(node, path=()):
        if isinstance(node, dict):
            for key, value in node.items():
                yield from arrays(value, path + (key,))
        elif isinstance(node, list):
            yield path, node

    def resolve(document: dict, path):
        node = document
        for key in path[:-1]:
            node = node[key]
        return node, path[-1]

    while len(rendered) > limit:
        candidates = [
            (len(node), path) for path, node in arrays(trimmed) if len(node) > 1
        ]
        if not candidates:
            break
        candidates.sort(reverse=True)
        _size, path = candidates[0]
        parent, key = resolve(trimmed, path)
        node = parent[key]
        keep = max(1, len(node) // 2)
        dropped = len(node) - keep
        parent[key] = node[:keep]
        notes = trimmed.setdefault("truncated", {})
        label = ".".join(str(part) for part in path)
        notes[label] = notes.get(label, 0) + dropped
        rendered = render(trimmed)

    if len(rendered) > limit:
        # Even the envelope is over budget. Emit the part every caller reads
        # rather than a fragment of the part they do not.
        return render(
            {
                "status": result.get("status"),
                "anchored_root": result.get("anchored_root"),
                "current_root": result.get("current_root"),
                "anchored_packets": result.get("anchored_packets"),
                "current_packets": result.get("current_packets"),
                "truncated": "the full verdict does not fit in --max-output",
            }
        )
    return rendered


def _witness_state(anchor_path: Path, stored: dict | None) -> dict:
    if not isinstance(stored, dict):
        return {"status": witness_lib.WITNESS_ABSENT, "reason": "no anchor"}
    root = stored.get("merkle_root")
    claims = stored.get("witnesses") or []
    proof_file = witness_lib.proof_path(anchor_path.parent, str(root))
    if not proof_file.exists():
        return {
            "status": witness_lib.WITNESS_ABSENT,
            "reason": (
                "the anchor claims a witness but no proof file is present"
                if claims
                else "this anchor was published without an external witness"
            ),
            "claims_in_anchor": len(claims),
        }
    # The sidecar is operator-writable and may be locked, permission-denied, or
    # replaced by a directory. read_bytes() then raises straight through a
    # function whose entire job is to return a structured verdict, so the STORE
    # verdict is lost to a problem with the witness file. Same reasoning as the
    # unreadable-packet path: report it, do not raise over it.
    try:
        proof_bytes = proof_file.read_bytes()
    except OSError as exc:
        return {
            "status": witness_lib.WITNESS_UNAVAILABLE,
            "reason": f"the proof file could not be read: {type(exc).__name__}",
            "proof": proof_file.name,
            "claims_in_anchor": len(claims),
        }
    state = witness_lib.inspect_proof(
        proof_bytes, expected_digest=witness_lib.root_digest(str(root))
    )
    state["proof"] = proof_file.name
    state["claims_in_anchor"] = len(claims)
    return state


def _witness_upgrade(args: argparse.Namespace) -> int:
    stored = anchor_lib.load_anchor(args.anchor)
    if not isinstance(stored, dict):
        print("no anchor to upgrade")
        return 3
    root = str(stored.get("merkle_root"))
    proof_file = witness_lib.proof_path(args.anchor.parent, root)
    if not proof_file.exists():
        print(f"no proof at {proof_file}")
        return 3
    # Sibling of the same reader in _witness_state: an operator-writable sidecar
    # that exists but cannot be read must be reported, not raised over.
    try:
        proof_bytes = proof_file.read_bytes()
    except OSError as exc:
        print(f"cannot read {proof_file}: {type(exc).__name__}")
        return 3
    result = witness_lib.upgrade_proof(proof_bytes, timeout=args.witness_timeout)
    proof = result.pop("proof", None)
    if proof:
        proof_file.write_bytes(proof)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    # Exit 0 requires CONFIRMED, which this code never returns -- verifying a
    # Bitcoin attestation needs block headers the witness layer does not have.
    # An attested-but-unverified proof therefore exits 1, not 0: it is progress,
    # not a witness.
    return 0 if result.get("status") == witness_lib.WITNESS_CONFIRMED else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["publish", "verify", "witness-upgrade"])
    parser.add_argument("--provenance-root", type=Path, default=DEFAULT_PROVENANCE_ROOT)
    parser.add_argument("--identity-dir", type=Path, default=DEFAULT_IDENTITY_DIR)
    parser.add_argument("--anchor", type=Path, default=DEFAULT_ANCHOR_PATH)
    parser.add_argument(
        "--expect-signer",
        default=None,
        help=(
            "Pin the anchor's signer AID. Pinning is the actual root of trust: "
            "without it, a fresh key can sign a fresh consistent series."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Publish even when the current anchor reports a loss against this "
            "store. Overwrites the only record that something is missing."
        ),
    )
    parser.add_argument(
        "--witness",
        action="store_true",
        help=(
            "Request an OpenTimestamps stamp over the root. Requires the "
            "optional `opentimestamps` package; degrades to publishing without "
            "a witness if unavailable."
        ),
    )
    parser.add_argument("--witness-timeout", type=int, default=30)
    parser.add_argument(
        "--allow-new-identity",
        action="store_true",
        help="Permit minting a signing identity. Required for the first anchor.",
    )
    parser.add_argument(
        "--allow-signer-change",
        action="store_true",
        help="Permit signing with a different key than the previous anchor used.",
    )
    parser.add_argument(
        "--no-pin",
        action="store_true",
        help=(
            "Do not pin the signer to the stored anchor's own. Weakens verify "
            "to 'some key signed this'."
        ),
    )
    parser.add_argument(
        "--print-tag",
        action="store_true",
        help="Print the git commands that would publish this anchor. Runs none.",
    )
    parser.add_argument("--max-output", type=int, default=8000)
    args = parser.parse_args(argv)

    if args.command == "publish":
        return _publish(args)
    if args.command == "witness-upgrade":
        return _witness_upgrade(args)
    return _verify(args)


if __name__ == "__main__":
    raise SystemExit(main())
