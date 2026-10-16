"""`make build`'s packaging: one `ankc build` per deck (geofeat.decks), each written to dist/<slug>.apkg. ankc names a
package after its deck ("Canadian Provinces and Territories" would be canadian-provinces-and-territories.apkg), so each
is built in a scratch directory and moved to its slug."""

import shutil
import subprocess
import tempfile
from pathlib import Path

from geofeat.ankc import ankc_command
from geofeat.decks import DECKS
from geofeat.model import DECK, ROOT

DIST = ROOT / "dist"


def main() -> None:
    DIST.mkdir(exist_ok=True)
    for old in DIST.glob("*.apkg"):
        old.unlink()
    for deck in DECKS:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run([*ankc_command(), "build", "--deck", deck.name, "--path", str(DECK), "--output", tmp], check=True)
            built = list(Path(tmp).glob("*.apkg"))
            if len(built) != 1:
                raise SystemExit(f"ankc build --deck {deck.name!r} wrote {len(built)} packages")
            shutil.move(built[0], DIST / f"{deck.slug}.apkg")
        print(f"built dist/{deck.slug}.apkg")


if __name__ == "__main__":
    main()
