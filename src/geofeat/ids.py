"""Give every entry in the card sources a permanent Anki uid, minted by `ankc gen chunk` and written back into
its YAML file."""

import re
import subprocess
from collections import Counter
from pathlib import Path

from ruamel.yaml import YAML

from geofeat.ankc import ankc_command
from geofeat.sources import PATHS

UID_RE = re.compile(r"\[\^uid\]: *([A-Za-z0-9]{10})")


def mint() -> str:
    out = subprocess.run([*ankc_command(), "gen", "chunk"], check=True, capture_output=True, text=True).stdout
    return UID_RE.search(out).group(1)


def _yaml() -> YAML:
    yaml = YAML()
    yaml.width = 4096
    return yaml


def mint_missing(paths: list[Path]) -> int:
    """Mint every missing uid, retired entries included, and return the count. An entry that makes one card has a
    `uid`, inserted after its `id`. One that makes several (a country and its capital) has `uids:`, a map from card
    kind to uid; each empty slot there is filled, and a kind left out gets no card."""
    yaml = _yaml()
    total = 0
    for path in paths:
        entries = yaml.load(path)
        count = 0
        for entry in entries:
            if "uids" in entry:
                for kind in [k for k, v in entry["uids"].items() if not v]:
                    entry["uids"][kind] = mint()
                    count += 1
            elif not entry.get("uid"):
                entry.insert(list(entry.keys()).index("id") + 1, "uid", mint())
                count += 1
        if count:
            yaml.dump(entries, path)
        total += count
    return total


def uids(entry: dict) -> list[str]:
    return [u for u in [entry.get("uid"), *(entry.get("uids") or {}).values()] if u]


def duplicate_uids(paths: list[Path]) -> list[str]:
    """Uids that appear more than once across the sources, retired entries included: a uid is never reused."""
    counts = Counter(u for path in paths for entry in YAML(typ="safe").load(path) for u in uids(entry))
    return sorted(uid for uid, n in counts.items() if n > 1)


def main() -> None:
    print(f"minted {mint_missing(list(PATHS))} uid(s)")


if __name__ == "__main__":
    main()
