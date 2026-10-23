"""The decks one build makes: World Atlas and its companion decks, each its own package. A subdivision deck holds one
country's first-level subdivisions (data/subdivisions.yaml), one card each; World Flags holds the flag of every World
Atlas country and of the territories with a flag of their own (data/flags.yaml). Every deck owns a range of new-card
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
    # pairs of cards (subdivision ids, or flag ids) that look alike, kept LOOKALIKE_GAP cards apart: where the walk
    # allows in a subdivision deck, always within a continent in World Flags
    lookalikes: tuple[tuple[str, str], ...] = ()
    block: str | None = None  # a companion deck's one study block (geofeat.card.BLOCKS); World Atlas has four


WORLD = DeckInfo("World Atlas", "world-atlas", 0, 600_000)
SUBDIVISION_DECKS = (
    DeckInfo("Italian Regions", "italian-regions", 600_000, 650_000, "italy", "it", 20, "it-valle-d-aosta",
             (("it-abruzzo", "it-molise"), ("it-molise", "it-basilicata"), ("it-umbria", "it-marche")), "subdivisions"),
    DeckInfo("US States", "us-states", 650_000, 700_000, "united-states", "us", 51, "us-maine",
             (("us-vermont", "us-new-hampshire"), ("us-north-dakota", "us-south-dakota"), ("us-wyoming", "us-colorado"),
              ("us-north-carolina", "us-south-carolina"), ("us-mississippi", "us-alabama"), ("us-arizona", "us-new-mexico"),
              ("us-kansas", "us-nebraska"), ("us-rhode-island", "us-delaware")), "subdivisions"),
    DeckInfo("Brazilian States", "brazilian-states", 700_000, 750_000, "brazil", "br", 27, "br-roraima",
             (("br-mato-grosso", "br-mato-grosso-do-sul"), ("br-alagoas", "br-sergipe"),
              ("br-paraiba", "br-rio-grande-do-norte"), ("br-acre", "br-rondonia")), "subdivisions"),
    DeckInfo("Canadian Provinces and Territories", "canadian-provinces", 750_000, 800_000, "canada", "ca", 13,
             "ca-british-columbia",
             (("ca-alberta", "ca-saskatchewan"), ("ca-saskatchewan", "ca-manitoba"), ("ca-new-brunswick", "ca-nova-scotia"),
              ("ca-yukon", "ca-northwest-territories")), "subdivisions"),
)
# Flags that look alike, by country or territory id. Pairs on one continent are kept LOOKALIKE_GAP cards apart; pairs
# across continents are far apart already and are listed for the report (`python -m geofeat.order.flags`).
FLAG_LOOKALIKES: tuple[tuple[str, str], ...] = (
    # Europe
    ("monaco", "poland"), ("netherlands", "luxembourg"), ("slovenia", "slovakia"), ("slovakia", "russia"),
    ("slovenia", "russia"), ("serbia", "russia"), ("norway", "iceland"), ("romania", "moldova"), ("italy", "ireland"),
    ("belgium", "germany"), ("austria", "latvia"),
    # Asia
    ("qatar", "bahrain"), ("jordan", "palestine"), ("syria", "iraq"), ("iraq", "yemen"), ("syria", "yemen"),
    ("kuwait", "united-arab-emirates"), ("china", "vietnam"), ("iran", "tajikistan"),
    # Africa
    ("senegal", "mali"), ("guinea", "mali"), ("senegal", "guinea"), ("senegal", "cameroon"), ("kenya", "south-sudan"),
    # North America
    ("honduras", "nicaragua"), ("nicaragua", "el-salvador"), ("honduras", "el-salvador"), ("puerto-rico", "cuba"),
    # South America
    ("venezuela", "ecuador"), ("venezuela", "colombia"), ("colombia", "ecuador"), ("argentina", "uruguay"),
    # Oceania
    ("australia", "new-zealand"),
    # across continents
    ("romania", "chad"), ("indonesia", "monaco"), ("indonesia", "poland"), ("ireland", "cote-divoire"),
    ("haiti", "liechtenstein"), ("egypt", "syria"), ("egypt", "iraq"), ("egypt", "yemen"), ("india", "niger"),
    ("liberia", "united-states"), ("malaysia", "united-states"), ("thailand", "costa-rica"), ("tunisia", "turkey"),
    ("cyprus", "kosovo"), ("samoa", "taiwan"), ("sudan", "palestine"),
)
# 800,000-949,999: 217 cards at a stride of 500 need 108,500; the rest is room to append, and 950,000 up is left for
# another deck below positions.LIMIT
FLAGS = DeckInfo("World Flags", "world-flags", 800_000, 950_000, lookalikes=FLAG_LOOKALIKES, block="flags")
COMPANIONS = (*SUBDIVISION_DECKS, FLAGS)
DECKS = (WORLD, *COMPANIONS)
BY_NAME = {d.name: d for d in DECKS}
BY_SLUG = {d.slug: d for d in DECKS}
BY_COUNTRY = {d.country: d for d in SUBDIVISION_DECKS}
COMPANION_BLOCKS = frozenset(d.block for d in DECKS if d.block)


def deck_of_position(position: int) -> DeckInfo | None:
    return next((d for d in DECKS if d.base <= position < d.limit), None)
