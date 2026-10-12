"""Give every feature a permanent Anki uid, minted by `ankc gen chunk`, written back into features.yaml."""

import re
import subprocess

from ruamel.yaml import YAML

from geofeat.model import FEATURES

UID_RE = re.compile(r"\[\^uid\]: *([A-Za-z0-9]{10})")


def mint() -> str:
    out = subprocess.run(["ankc", "gen", "chunk"], check=True, capture_output=True, text=True).stdout
    return UID_RE.search(out).group(1)


def main() -> None:
    yaml = YAML()
    yaml.width = 4096
    entries = yaml.load(FEATURES)
    missing = [entry for entry in entries if not entry.get("uid")]
    for entry in missing:
        entry.insert(list(entry.keys()).index("id") + 1, "uid", mint())
    if missing:
        yaml.dump(entries, FEATURES)
    print(f"minted {len(missing)} uid(s)")


if __name__ == "__main__":
    main()
