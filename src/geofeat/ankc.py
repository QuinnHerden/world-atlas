"""The configured ankc: $ANKC (set by the Makefile, default `ankc`), and what its version supports."""

import os
import re
import shlex
import subprocess
from functools import cache


@cache
def ankc_command() -> tuple[str, ...]:
    """The ankc to run. $ANKC may be a command line such as `uv run --with ../ankcompiler ankc`."""
    return tuple(shlex.split(os.environ.get("ANKC") or "ankc"))


@cache
def ankc_version_text() -> str:
    """What `ankc --version` prints, or why it couldn't run."""
    try:
        return subprocess.run([*ankc_command(), "--version"], capture_output=True, text=True).stdout.strip()
    except OSError as exc:
        return str(exc)


def ankc_version() -> tuple[int, int] | None:
    """(major, minor) of the configured ankc, or None if it can't be run or read."""
    match = re.fullmatch(r"(\d+)\.(\d+)\.\d+", ankc_version_text())
    return (int(match.group(1)), int(match.group(2))) if match else None


def writes_pos() -> bool:
    """Whether deckgen writes `[^pos]` footnotes: ankc 0.6 reads them; 0.5 would reject them."""
    version = ankc_version()
    return version is not None and version >= (0, 6)
