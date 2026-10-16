"""The decks one build makes: World Atlas and its companion decks, each its own package. A companion deck holds one
country's first-level subdivisions (data/subdivisions.yaml), one card each. Every deck owns a range of new-card
positions in the one data/positions.lock, so a position says which deck a card is in. See
docs/adr/0012-companion-decks.md."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DeckInfo:
    name: str  # the Anki deck
    slug: str  # deck/<slug>.md, dist/<slug>.apkg and the lock's `deck=`
    base: int  # new-card positions in [base, limit); the first is base + positions.STRIDE
    limit: int
    country: str | None = None  # a companion deck: the country (countries.yaml id) whose subdivisions it holds
    prefix: str | None = None  # a companion deck's subdivision id prefix: it-sicilia
    cards: int | None = None  # a companion deck's active subdivisions; `make check-data` holds the data to it
    entry: str | None = None  # where a companion deck's neighbour walk starts
    # pairs of subdivisions that look alike, kept LOOKALIKE_GAP cards apart where the walk allows
    lookalikes: tuple[tuple[str, str], ...] = ()


WORLD = DeckInfo("World Atlas", "world-atlas", 0, 600_000)
COMPANIONS = (
    DeckInfo("Italian Regions", "italian-regions", 600_000, 650_000, "italy", "it", 20, "it-valle-d-aosta",
             (("it-abruzzo", "it-molise"), ("it-molise", "it-basilicata"), ("it-umbria", "it-marche"))),
    DeckInfo("US States", "us-states", 650_000, 700_000, "united-states", "us", 51, "us-maine",
             (("us-vermont", "us-new-hampshire"), ("us-north-dakota", "us-south-dakota"), ("us-wyoming", "us-colorado"),
              ("us-north-carolina", "us-south-carolina"), ("us-mississippi", "us-alabama"), ("us-arizona", "us-new-mexico"),
              ("us-kansas", "us-nebraska"), ("us-rhode-island", "us-delaware"))),
    DeckInfo("Brazilian States", "brazilian-states", 700_000, 750_000, "brazil", "br", 27, "br-roraima",
             (("br-mato-grosso", "br-mato-grosso-do-sul"), ("br-alagoas", "br-sergipe"),
              ("br-paraiba", "br-rio-grande-do-norte"), ("br-acre", "br-rondonia"))),
    DeckInfo("Canadian Provinces and Territories", "canadian-provinces", 750_000, 800_000, "canada", "ca", 13,
             "ca-british-columbia",
             (("ca-alberta", "ca-saskatchewan"), ("ca-saskatchewan", "ca-manitoba"), ("ca-new-brunswick", "ca-nova-scotia"),
              ("ca-yukon", "ca-northwest-territories"))),
)
DECKS = (WORLD, *COMPANIONS)
BY_NAME = {d.name: d for d in DECKS}
BY_SLUG = {d.slug: d for d in DECKS}
BY_COUNTRY = {d.country: d for d in COMPANIONS}


def deck_of_position(position: int) -> DeckInfo | None:
    return next((d for d in DECKS if d.base <= position < d.limit), None)
