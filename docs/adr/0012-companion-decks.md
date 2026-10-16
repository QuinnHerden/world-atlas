# 12. Companion decks

Status: accepted, 2026-10-16. Amends [ADR 0006](0006-positions-lock-and-pos-footnote.md) (the lock's entries and the freeze guard) and [ADR 0005](0005-card-sources-and-card-dto.md) (a card's deck).

## Context

The user wants to learn the first-level subdivisions of four countries: Italy's 20 regions, the 50 US states and DC, Brazil's 26 states and the Distrito Federal, and Canada's 10 provinces and 3 territories. These cards have the same shape as World Atlas's: an unlabelled map with one place in red, the name on the back and a short note under it. They need the same render pipeline, note model and checks.

They are a different subject, though. A learner may want the US states without the rest of the world, or World Atlas without 111 subdivision cards. They don't belong in World Atlas's ring of regions or its four study blocks.

Two shapes were considered:

- **Subdecks of World Atlas** (`World Atlas::US States`). Anki gathers new cards deck by deck, alphabetically, by default. Studying the parent deck would then need a gather-order setting, and existing users would have to move their cards into a `World Atlas::World` subdeck by hand. Rejected.
- **Separate decks, one package each.** World Atlas stays exactly as it is. Each companion deck is its own top-level deck and its own `.apkg`, imported only by those who want it. Chosen.

## Decision

**One repo, several packages.** `src/geofeat/decks.py` lists the decks: World Atlas and four companion decks.

| Deck | Package | Cards | Positions |
|---|---|---|---|
| World Atlas | `dist/world-atlas.apkg` | 554 | 0–599,999 |
| Italian Regions | `dist/italian-regions.apkg` | 20 | 600,000–649,999 |
| US States | `dist/us-states.apkg` | 51 | 650,000–699,999 |
| Brazilian States | `dist/brazilian-states.apkg` | 27 | 700,000–749,999 |
| Canadian Provinces and Territories | `dist/canadian-provinces.apkg` | 13 | 750,000–799,999 |

- **Data.** `data/subdivisions.yaml` holds one entry per subdivision. Each has a country-prefixed id (`us-georgia`, `br-sao-paulo`, `it-sicilia`, `ca-quebec`), a uid, a name and alternative names (Italy's and Brazil's names are Italian and Portuguese only, with no alternatives: Sicilia, Distrito Federal), the type shown as the prompt (Region, State, Federal district, Province, Territory), the Natural Earth admin-1 rows it is made from, an `expect` box and a note. Italy's regions are dissolved from the province rows by their `region` attribute; the row count is part of the selector, so a change in Natural Earth fails the build. `ne_10m_admin_1_states_provinces` is pinned at the same commit as every other layer.
- **Cards.** A subdivision is `kind: subdivision`, in block `subdivisions`, with the tags `kind::subdivision`, `block::subdivisions`, `country::<country id>` (`country::united-states`) and `id_subdivision_<id>`. There is no `region::` or `tier::` tag. `Card.deck` names its deck, and the card validator holds subdivisions, and only subdivisions, to a companion deck.
- **Checks.** `make check-data` holds each deck to its count (20, 51, 27, 13), requires every outline inside its `expect` box, and requires a country's subdivisions to tile its full outline: no overlap and no gap over 1 km².
- **Study order.** World Atlas's order is unchanged (ADR 0009). A companion deck's order is its order in `data/subdivisions.yaml`. That order is a neighbour walk: each card borders one already seen while any unseen card does. The adjacency graph is built from the admin-1 outlines as the country graph is (ADR 0008): land edges, plus sea edges up to 100 km for a subdivision with no land neighbour (Sicilia, Prince Edward Island). `python -m geofeat.order.companions` generates a walk and prints its jumps and look-alike gaps; `make check-data` fails on a listed order that jumps while it could step. Look-alike pairs (the Dakotas, Alberta and Saskatchewan) are kept 3–10 cards apart where the walk allows, and the rest are reported.
- **Building.** `deckgen` writes one markdown file per deck (`deck/<slug>.md`, its frontmatter naming the deck). `make build` runs `ankc build --deck <name>` once per deck. ankc packages a deck, its subdecks and only the media its cards use, so each package holds only its own cards and maps. ankc names a package after its deck, so each is built in a scratch directory and moved to `dist/<slug>.apkg`.
- **Note type.** Every ankc package uses the same `AnkCompiler-Question_Answer` note type, with a fixed id. Importing a companion package into a collection that already has World Atlas reuses that note type: it adds none, renames none and changes no World Atlas card. `make import-test` checks this.

**One lock, a range per deck.** `data/positions.lock` keeps one entry per card. Each entry now ends in `deck=<slug>`. A line without it, as written before this change, is World Atlas's, so the frozen lock on `origin/main` still parses and compares. A deck's positions stay in its range: the first card is the range's base + 500, and `make positions` places a new uid among its own deck's entries only, never past the range's limit. The ranges keep the positions unique across packages, so one lock and one freeze guard cover all of them.

**A card's deck is frozen, like its position.** Re-importing never moves a card to another deck, so a card that changed deck would sit in the wrong deck in every existing collection. The freeze guard compares whole entries, so a changed `deck=` fails it. `make positions`, `make deck` and `check deck` fail when a locked card's deck no longer matches its data. `check package` holds each package to its own deck: its notes are exactly that deck's cards, every card is in that deck, every due equals the card's lock position, and its media are that deck's maps.

## Consequences

- World Atlas users see no change. Its package, deck, positions and tags are what they were; its lock lines only gain `deck=world-atlas`.
- World Atlas's positions now stop below 600,000, not 1,000,000. Its last card is at 303,500, which leaves room for about 590 more cards at the end of its order before inserts between existing cards are needed.
- `make build` writes five packages. A release ships each one; a learner imports only the decks they want, in any order.
- Each companion deck starts its own new-card queue. Studying several decks at once follows Anki's usual per-deck limits; nothing ties their orders together.
- Moving a subdivision to another deck, or a World Atlas card into a companion deck, is a breaking change. It would need a new lock series (ADR 0011).
- Adding a companion deck means a registry entry with an unused position range, entries in `data/subdivisions.yaml` and a frame for its country ([ADR 0013](0013-subdivision-framing.md)).
