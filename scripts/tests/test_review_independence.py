"""Panel-size accounting for scripts/review_independence.py.

PR41 review findings against the independence measurement itself:

1. `phi()` returns NaN for a reviewer whose vector is CONSTANT -- raised
   nothing, or raised everything -- and says so in its own comment.
   `kish_neff()` drops those pairs from the mean but the reviewer stayed in
   `k`, which sits in the numerator and in the `(k - 1)` term. The guard
   excluded only the raised-nothing half, so a reviewer who raised every
   finding in the union inflated n_eff and flattered the panel. That is the
   more likely half in practice: a broad automated reviewer against a narrow
   union produces exactly it.
2. The refusal branch printed "the formula returns a finite number that is
   meaningless" and then returned 0, so a refusal and a measurement were
   indistinguishable to anything reading the exit code.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "review_independence.py"


def load_module():
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    spec = importlib.util.spec_from_file_location("review_independence", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _review(label: str, keys: list[str]) -> dict:
    """A record with the shape load_review() produces, not a two-key stub.

    report() reads label/harness/tools/saw_prior/self_reported as well as
    findings, so a stub raises KeyError from the reporting section long after
    the accounting under test has already run.
    """
    return {
        "label": label,
        "path": Path(f"{label}.json"),
        "harness": "test",
        "self_reported": None,
        "saw_prior": False,
        "tools": [],
        "findings": [{"_key": key} for key in keys],
        "predicted_majority": None,
        "expects_to_be_alone": None,
    }


def test_a_reviewer_who_raised_everything_is_excluded(capsys):
    """Constant is constant. phi is NaN against every other reviewer, so this
    one contributes nothing to the mean while still counting in k."""
    module = load_module()

    reviews = [
        _review("everything", ["a", "b", "c"]),
        _review("narrow-1", ["a"]),
        _review("narrow-2", ["b"]),
    ]

    module.report(reviews, None)
    err = capsys.readouterr().err

    assert "excluding everything" in err
    assert "raised all 3 findings in the union" in err


def test_a_reviewer_who_raised_nothing_is_still_excluded(capsys):
    """The half that was already guarded must keep working."""
    module = load_module()

    reviews = [
        _review("silent", []),
        _review("narrow-1", ["a", "b"]),
        _review("narrow-2", ["b", "c"]),
    ]

    module.report(reviews, None)

    assert "excluding silent" in capsys.readouterr().err


def test_exclusion_is_iterated_because_it_can_create_new_constants(capsys):
    """Removing a reviewer removes the keys only IT raised, which can leave a
    survivor constant. One pass fixed the reviewer in front of it and left the
    panel it had just created unexamined."""
    module = load_module()

    # `wide` raises everything; once it goes, `only-x` is left raising every
    # key still in the union.
    reviews = [
        _review("wide", ["x", "y"]),
        _review("only-x", ["x"]),
        _review("also-x", ["x"]),
    ]

    code = module.report(reviews, None)
    err = capsys.readouterr().err

    assert "excluding wide" in err
    assert "excluding only-x" in err or "excluding also-x" in err
    assert code == 2, "a panel with no measurable variance must not report n_eff"


def test_the_refusal_reaches_the_exit_code(capsys):
    """The branch printed 'meaningless' and returned 0, so nothing reading the
    exit code could tell a refusal from a measurement."""
    module = load_module()

    # Near-disjoint reviewers are anti-correlated by construction, which is the
    # negative-mean-phi case the tool refuses on.
    reviews = [
        _review("a", ["k1", "k2", "k3"]),
        _review("b", ["k4", "k5", "k6"]),
        _review("c", ["k1", "k4", "k7"]),
    ]

    code = module.report(reviews, None)
    out = capsys.readouterr().out

    if "REFUSING" in out or "meaningless" in out:
        assert code == 2, "a refusal that exits 0 is advisory only"
    else:
        assert code == 0


def test_a_measurable_panel_still_reports(capsys):
    """Fail-closed must not refuse every corpus."""
    module = load_module()

    reviews = [
        _review("a", ["k1", "k2", "k3", "k4"]),
        _review("b", ["k1", "k2", "k3", "k5"]),
        _review("c", ["k1", "k2", "k6", "k7"]),
    ]

    code = module.report(reviews, None)
    out = capsys.readouterr().out

    assert code == 0
    assert "n_eff" in out
