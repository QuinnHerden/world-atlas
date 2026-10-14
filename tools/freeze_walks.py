"""Freeze the current neighbour walks into data/curriculum.yaml (`Region.walk`), once the user has approved them on
the walk maps (`make walks`).

usage: uv run python tools/freeze_walks.py --all
       uv run python tools/freeze_walks.py REGION [REGION ...]   (a slug or a number: western-europe, 1)

A region's current walk is its frozen walk if it has one, else the generated one, so freezing again is a no-op. Only
the `walk` lines change; every other line of the file is kept as written. Commit the result.
"""

import argparse
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from ruamel.yaml import YAML

from geofeat import adjacency
from geofeat.countries_ne import state_ids
from geofeat.curriculum import CURRICULUM, Curriculum, load_curriculum
from geofeat.order.engine import walks

AFTER = ("countries", "pockets", "territories", "disputes")  # `walk` goes after the last of these present
WIDTH = 120
REGION = re.compile(r"^  - number: \d+")
KEY = re.compile(r"^    ([a-z_]+):")


def select(curriculum: Curriculum, names: Sequence[str]) -> list[str]:
    """The slugs of the regions named by slug or number."""
    by_name = {r.slug: r.slug for r in curriculum.regions} | {str(r.number): r.slug for r in curriculum.regions}
    if unknown := [n for n in names if n not in by_name]:
        raise ValueError(f"unknown regions: {', '.join(unknown)}")
    return list(dict.fromkeys(by_name[n] for n in names))


def walk_lines(nodes: Sequence[str]) -> list[str]:
    """`walk: [...]` as the file writes its lists: flow style, wrapped under the first item."""
    head = "    walk: ["
    indent = " " * len(head)
    lines, line = [], head
    for i, node in enumerate(nodes):
        item = node + ("]" if i == len(nodes) - 1 else ",")
        if line not in (head, indent) and len(line) + 1 + len(item) > WIDTH:
            lines.append(line + "\n")
            line = indent
        line += item if line in (head, indent) else " " + item
    return lines + [line + "\n"]


def _keys(lines: list[str], start: int, end: int) -> dict[str, tuple[int, int]]:
    """Each key of the region in lines[start:end] with its line span, continuation lines included."""
    out: dict[str, tuple[int, int]] = {}
    for i in range(start, end):
        if m := KEY.match(lines[i]):
            j = i + 1
            while j < end and lines[j].startswith("     ") and lines[j].strip():
                j += 1
            out[m.group(1)] = (i, j)
    return out


def freeze(text: str, frozen: Mapping[str, Sequence[str]]) -> str:
    """curriculum.yaml's text with `walk` set for each region slug in `frozen`, every other line as it was."""
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if REGION.match(line)]
    regions = {}
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else next(
            (i for i in range(start + 1, len(lines)) if lines[i].strip() and not lines[i].startswith(" ")), len(lines))
        keys = _keys(lines, start, end)
        slug = lines[keys["slug"][0]].split(":", 1)[1].split("#")[0].strip().strip("'\"")
        regions[slug] = keys
    if unknown := sorted(set(frozen) - set(regions)):
        raise ValueError(f"unknown regions: {', '.join(unknown)}")
    edits = []
    for slug, nodes in frozen.items():
        keys = regions[slug]
        insert_at = max(keys[k][1] for k in AFTER if k in keys)
        span = keys.get("walk") or (insert_at, insert_at)
        edits.append((span, walk_lines(nodes)))
    for (a, b), new in sorted(edits, reverse=True):  # bottom up, so earlier spans stay valid
        lines[a:b] = new
    return "".join(lines)


def main(argv: Sequence[str] | None = None, path: Path = CURRICULUM) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("regions", nargs="*", help="region slugs or numbers")
    parser.add_argument("--all", action="store_true", help="freeze every region")
    args = parser.parse_args(argv)
    if args.all == bool(args.regions):
        parser.error("name the regions to freeze, or pass --all")
    states = state_ids()
    curriculum = load_curriculum(states, path)
    try:
        slugs = [r.slug for r in curriculum.regions] if args.all else select(curriculum, args.regions)
    except ValueError as exc:
        parser.error(str(exc))
    current = walks(curriculum, adjacency.neighbours(adjacency.graph()))
    by_slug = {r.slug: current[r.number] for r in curriculum.regions}
    text = freeze(path.read_text(), {s: by_slug[s].nodes for s in slugs})
    written = Curriculum.model_validate(YAML(typ="safe").load(text))
    errors = written.check(states)
    errors += [f"{r.slug}: walk did not round-trip" for r in written.regions
               if r.slug in slugs and tuple(r.walk) != by_slug[r.slug].nodes]
    if errors:
        sys.exit("; ".join(errors))
    path.write_text(text)
    for s in slugs:
        state = "already frozen" if by_slug[s].frozen else "frozen"
        print(f"{s}: {state}: {' → '.join(by_slug[s].nodes)}")


if __name__ == "__main__":
    main()
