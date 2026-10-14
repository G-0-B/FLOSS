"""The brainstorming companion's bootstrap page (spec LSI-C1).

`skill-corpus/superpowers-brainstorming/scripts/server.cjs` serves a page that
stores the session key in `sessionStorage` from inside a `<script>` element.
CodeQL (`js/reflected-xss`, high) reported the reflection on PR #41. The key is
only reachable after it has been compared against the secret token, so this is
hardening: the embedded JSON must not be able to close the script element or
the string literal, whatever the value.

The function is evaluated from the shipped source with `node`. It is not
exported from the module, and importing the module would run its start-up code,
so the test extracts `bootstrapPage` from the file and calls it. The tests skip
when `node` is not installed.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER = (
    REPO_ROOT / "skill-corpus" / "superpowers-brainstorming" / "scripts" / "server.cjs"
)
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="node is not installed")

_RENDER = r"""
const fs = require('fs');
const src = fs.readFileSync(process.env.SERVER_PATH, 'utf8');
const found = src.match(/function bootstrapPage\(key\) \{[\s\S]*?\n\}\n/);
if (!found) { console.error('bootstrapPage not found'); process.exit(3); }
const bootstrapPage = new Function(found[0] + '; return bootstrapPage;')();
process.stdout.write(bootstrapPage(process.env.BOOTSTRAP_KEY));
"""


def render(key: str) -> str:
    result = subprocess.run(
        [NODE, "-e", _RENDER],
        env={**os.environ, "SERVER_PATH": str(SERVER), "BOOTSTRAP_KEY": key},
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def stored_value(html: str) -> str:
    """The key as the page's own script would read it back."""
    found = re.search(r"sessionStorage\.setItem\('brainstorm-session-key', (.+)\);", html)
    assert found, html
    return json.loads(found.group(1))


def test_a_key_cannot_close_the_script_element():
    """Spec LSI-C1 b. `JSON.stringify` leaves `</script>` alone, so a value
    containing it ended the element and the rest ran as markup."""
    key = "</script><script>window.__pwned = 1</script><!--"

    html = render(key)

    assert html.count("<script>") == 1
    assert html.count("</script>") == 1
    assert "<!--" not in html
    assert stored_value(html) == key


def test_line_separators_are_escaped():
    """Spec LSI-C1 b. U+2028 and U+2029 are legal in JSON but were line
    terminators in JavaScript string literals before ES2019, and some consumers
    still treat them so."""
    key = "a b c"

    html = render(key)

    assert " " not in html
    assert " " not in html
    assert stored_value(html) == key


def test_an_ordinary_key_round_trips():
    """A guard: the token the server really uses is unchanged by the escaping."""
    key = "0f3a9c1d4b7e82a65c0d9e1f2a3b4c5d"

    html = render(key)

    assert stored_value(html) == key
    assert "location.replace('/')" in html
