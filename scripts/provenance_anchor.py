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
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = REPO_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.activity_log import anchor as anchor_lib  # noqa: E402
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


def _publish(args: argparse.Namespace) -> int:
    previous = anchor_lib.load_anchor(args.anchor)
    built = anchor_lib.build_anchor(args.provenance_root, previous)
    identity = load_or_create_identity(args.identity_dir)
    signed = anchor_lib.sign_anchor(built, identity)

    problem = anchor_lib.anchor_signature_problem(signed)
    if problem is not None:
        # Never write an anchor we cannot ourselves verify: an unverifiable
        # anchor is indistinguishable from a tampered one at read time.
        print(f"refusing to write an anchor that does not verify: {problem}")
        return 3

    args.anchor.parent.mkdir(parents=True, exist_ok=True)
    args.anchor.write_bytes(
        json.dumps(signed, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")
        + b"\n"
    )
    print(
        json.dumps(
            {
                "wrote": str(args.anchor.relative_to(REPO_ROOT).as_posix()),
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
        print(f'git add "{args.anchor.relative_to(REPO_ROOT).as_posix()}"')
        print(f"git commit -m {json.dumps(commit_message(signed))}")
        print(f'git tag "{tag_name(signed)}"')
        print("git push origin HEAD --tags")
    return 0


def _verify(args: argparse.Namespace) -> int:
    stored = anchor_lib.load_anchor(args.anchor)
    result = anchor_lib.verify_anchor(
        args.provenance_root, stored, expected_signer=args.expect_signer
    )
    print(json.dumps(result, indent=2, ensure_ascii=False)[: args.max_output])
    return anchor_lib.EXIT_CODES.get(result["status"], 2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["publish", "verify"])
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
        "--print-tag",
        action="store_true",
        help="Print the git commands that would publish this anchor. Runs none.",
    )
    parser.add_argument("--max-output", type=int, default=8000)
    args = parser.parse_args(argv)

    if args.command == "publish":
        return _publish(args)
    return _verify(args)


if __name__ == "__main__":
    raise SystemExit(main())
