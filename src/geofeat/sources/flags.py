"""data/flags.yaml: World Flags (ADR 0012), one card per flag. The front is the flag, the back the name World Atlas
gives the place. Every World Atlas country has one, and each territory card whose place has an official flag of its
own in common use; data/flags/excluded.yaml says why each other territory has none. Subnationals and disputed areas
are out of scope.

The file lists the flags in study order: by continent (CONTINENTS), and within one in World Atlas's frozen order of
those places, but for the moves that keep look-alikes apart (geofeat.order.flags). Each entry records its continent,
so the card's `continent::` tag and its place in the deck are data, frozen with the card. It is the one World Atlas
uses (`world_continents`): its curriculum region's (geofeat.continents.REGION_CONTINENT), or the continent cards'
where they differ (MEMBERSHIP: Greenland, Aruba and Curaçao are North America, the British Indian Ocean Territory
Africa). A transcontinental state, which the continent cards split, goes with its region: Russia is Europe; Turkey,
Georgia, Azerbaijan and Kazakhstan Asia; Egypt Africa. `make check-data` notes an entry that no longer agrees.

The image is data/flags/<id>.svg, made by geofeat.flagfiles. There is no map to render."""

from functools import cache
from typing import Literal

from pydantic import model_validator
from ruamel.yaml import YAML

from geofeat.card import Card, Text, block_of, block_tag, id_tag
from geofeat.decks import FLAGS
from geofeat.flagfiles import FLAG_DIR, flag_file, lock_errors
from geofeat.model import ROOT, Strict
from geofeat.polities import Id, Uid, Territory, read_countries, read_entries, read_territory_file, unique
from geofeat.sources.political import require_uid

PATH = ROOT / "data/flags.yaml"
EXCLUDED = FLAG_DIR / "excluded.yaml"
CONTINENTS = ("europe", "asia", "africa", "north-america", "south-america", "oceania")  # the deck's order
Continent = Literal["europe", "asia", "africa", "north-america", "south-america", "oceania"]
FLAG_TIER = 1  # not tagged: a companion deck has no tiers


class Flag(Strict):
    id: Id  # the country's or territory's id
    uid: Uid | None = None
    kind: Literal["country", "territory"]
    continent: Continent
    reason: Text | None = None  # a territory's: the flag it has of its own
    retired: bool = False

    @model_validator(mode="after")
    def _reason(self) -> "Flag":
        if (self.kind == "territory") != (self.reason is not None):
            raise ValueError(f"{self.id}: a territory's flag needs a `reason` (its own flag, and its status); a "
                             f"country's has none")
        return self


@cache
def load_flags() -> tuple[Flag, ...]:
    """Every entry, retired ones included, in file order."""
    entries = [Flag.model_validate(e) for e in read_entries(PATH)]
    unique(entries, "flag")
    return tuple(entries)


def active() -> list[Flag]:
    return [f for f in load_flags() if not f.retired]


def excluded() -> dict[str, str]:
    """Territory id -> why it has no card: it flies its sovereign's flag, or has no official flag of its own."""
    if not EXCLUDED.exists():
        return {}
    reasons = YAML(typ="safe").load(EXCLUDED) or {}
    if not isinstance(reasons, dict):
        raise ValueError(f"{EXCLUDED.name}: a map of territory id to reason")
    return reasons


def active_territories() -> list[Territory]:
    return [e for e in read_territory_file() if isinstance(e, Territory) and not e.retired]


@cache
def names() -> dict[str, str]:
    """The name World Atlas gives each country and active territory."""
    return {p.id: p.name for p in (*read_countries(), *active_territories())}


@cache
def world_continents() -> dict[str, str]:
    """Each country's and territory's continent in World Atlas: its region's, or the continent cards' where those
    differ."""
    from geofeat.continents import MEMBERSHIP, REGION_CONTINENT
    from geofeat.countries_ne import state_ids
    from geofeat.curriculum import load_curriculum

    placed = {i: REGION_CONTINENT[r.slug] for r in load_curriculum(state_ids()).regions
              for i in (*r.countries, *r.territories)}
    return placed | {i: c for i, c in MEMBERSHIP.items() if i in placed}


def tags(f: Flag) -> tuple[str, ...]:
    return (id_tag("flag", f.id), f"continent::{f.continent}", "kind::flag", block_tag(block_of("flag")),
            f"{f.kind}::{f.id}")


def card(f: Flag) -> Card:
    if f.id not in names():
        raise ValueError(f"flag {f.id}: not an active World Atlas {f.kind}; retire it in {PATH.name}")
    return Card(uid=require_uid(f.id, f.uid), kind="flag", id=f.id, prompt="Flag", answer_lines=(names()[f.id],),
                tags=tags(f), tier=FLAG_TIER, deck=FLAGS.name, image=flag_file(f.id))


def cards() -> list[Card]:
    """One card per active flag, in file order."""
    return [card(f) for f in active()]


def check() -> list[str]:
    """Every country has a flag and every active territory a flag or a reason for none; no flag is of anything else;
    each continent's flags are listed together, in CONTINENTS order; each image matches its lock entry."""
    try:
        flags = active()
        reasons = excluded()
    except (ValueError, OSError) as exc:
        return [str(exc)]
    countries = {c.id for c in read_countries()}
    territories = {t.id for t in active_territories()}
    kinds = {f.id: f.kind for f in flags}
    errors = [f"{i}: a country with no flag in {PATH.name}" for i in sorted(countries - set(kinds))]
    errors += [f"{i}: a flag of kind {k}, but {i} is not an active World Atlas {k}" for i, k in kinds.items()
               if i not in (countries if k == "country" else territories)]
    errors += [f"{i}: a territory in neither {PATH.name} nor {EXCLUDED.name}" for i in sorted(territories - set(kinds)
                                                                                                 - set(reasons))]
    errors += [f"{i}: in both {PATH.name} and {EXCLUDED.name}" for i in sorted(set(reasons) & set(kinds))]
    errors += [f"{EXCLUDED.name}: {i} is not an active territory" for i in sorted(set(reasons) - territories)]
    errors += [f"{EXCLUDED.name}: {i} needs a reason" for i, why in reasons.items() if not isinstance(why, str) or not why]
    if errors:
        return errors
    order = [f.continent for f in flags]
    grouped = [c for i, c in enumerate(order) if i == 0 or order[i - 1] != c]
    if grouped != [c for c in CONTINENTS if c in order]:
        errors.append(f"{PATH.name} must list the flags continent by continent, in the order {', '.join(CONTINENTS)}; "
                      f"it runs {', '.join(grouped)}")
    return errors + lock_errors([f.id for f in flags])


def continent_notes() -> list[str]:
    """Entries whose recorded continent World Atlas no longer gives the place. The entry keeps it: the card's place in
    the deck is frozen, and moving it to another continent's run would need a new lock series."""
    world = world_continents()
    return [f"{f.id}: recorded in {f.continent}, but World Atlas now places it in {world.get(f.id)}" for f in active()
            if world.get(f.id) != f.continent]
