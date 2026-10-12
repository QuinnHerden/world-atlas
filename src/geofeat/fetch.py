"""Fetch pinned Natural Earth files into vendor/ and verify them against data/sources.lock.

Downloads go through `gh api` because the usual CDNs are blocked on some machines.
`--relock` downloads every file at its pinned commit and records its checksums.
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from geofeat.model import LOCK, VENDOR


def _gh(*args: str) -> bytes:
    return subprocess.run(["gh", "api", *args], check=True, capture_output=True).stdout


def _download(entry: dict) -> bytes:
    return _gh("-H", "Accept: application/vnd.github.raw", f"repos/{entry['repo']}/contents/{entry['path']}?ref={entry['commit']}")


def _blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _check_upstream(entry: dict) -> None:
    """A fork's commit is also served under the upstream repo name, so insist the pin is on upstream history."""
    repo, commit = entry["repo"], entry["commit"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        sys.exit(f"{entry['path']}: commit must be a full sha, got {commit!r}")
    branch = json.loads(_gh(f"repos/{repo}"))["default_branch"]
    status = json.loads(_gh(f"repos/{repo}/compare/{commit}...{branch}"))["status"]
    if status not in ("identical", "ahead"):
        sys.exit(f"{entry['path']}: commit {commit} is not on {repo}@{branch} ({status})")


def vendor_path(entry: dict) -> Path:
    return VENDOR / Path(entry["path"]).name


def fetch(entries: list[dict], relock: bool) -> None:
    VENDOR.mkdir(exist_ok=True)
    for entry in entries:
        target = vendor_path(entry)
        if not relock and target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == entry["sha256"]:
            continue
        if relock:
            _check_upstream(entry)
        data = _download(entry)
        actual = {"sha256": hashlib.sha256(data).hexdigest(), "blob": _blob_sha(data)}
        if relock:
            remote_blob = json.loads(_gh(f"repos/{entry['repo']}/contents/{entry['path']}?ref={entry['commit']}"))["sha"]
            if actual["blob"] != remote_blob:
                sys.exit(f"{entry['path']}: download does not match the repo's blob sha")
            entry.update(actual)
        elif actual != {"sha256": entry["sha256"], "blob": entry["blob"]}:
            sys.exit(f"{entry['path']}: checksum mismatch with {LOCK.name}")
        tmp = target.with_suffix(".tmp")
        tmp.write_bytes(data)
        tmp.replace(target)
        print(f"fetched {target.name}")


def main() -> None:
    entries = json.loads(LOCK.read_text())
    relock = sys.argv[1:] == ["--relock"]
    fetch(entries, relock)
    if relock:
        LOCK.write_text(json.dumps(entries, indent=2) + "\n")


if __name__ == "__main__":
    main()
