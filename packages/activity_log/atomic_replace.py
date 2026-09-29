"""os.replace with a bounded retry for transient Windows handle contention.

Stdlib-only on purpose, so lean consumers can import it without pulling in the
provenance extras.

On Windows, os.replace is MoveFileExW(MOVEFILE_REPLACE_EXISTING). It fails
with ERROR_ACCESS_DENIED whenever another process holds any open handle on the
destination, whatever share mode that handle uses, and with
ERROR_SHARING_VIOLATION when a handle on the source lacks FILE_SHARE_DELETE.
Both surface as PermissionError. File watchers and scanners open freshly
written files briefly, so a tight rewrite loop loses that race now and then.
Measured on the workspace that the PR41 audit ran in (2026-09-29): about 0.5%
of replaces under the watched tree failed, none failed outside it, and the
first retry after a 0.5 ms pause succeeded every time.

The retry budget covers holds of that kind with a wide margin and nothing
more. A hold that outlasts it is not transient, so the final attempt's error
propagates unchanged. POSIX rename does not have this failure mode and is left
alone.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

_IS_WINDOWS = os.name == "nt"

# Pauses before each retry: five retries, about 0.3 s in total.
_RETRY_DELAYS_SECONDS = (0.01, 0.02, 0.04, 0.08, 0.16)


def replace_with_retry(src: Path | str, dst: Path | str) -> None:
    """Atomically replace ``dst`` with ``src``, as :func:`os.replace` does."""
    if _IS_WINDOWS:
        for delay in _RETRY_DELAYS_SECONDS:
            try:
                os.replace(src, dst)
                return
            except PermissionError:
                time.sleep(delay)
    os.replace(src, dst)
