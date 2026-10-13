# 1. Type vocabulary and families

Status: accepted, 2026-10-13

## Context

Each card shows a type word above the map ("Strait", "River"). By the end of phase 3 the deck used 32 words for 166 cards, and 12 of them covered one or two cards each. Words that rare teach little about "what kind of thing" and make the vocabulary harder to keep consistent.

Separately, the sibling-pair check flagged nesting only when two cards had the identical word. A Plain inside a Steppe was therefore "fine", and so was a Coastal pass beside a Mountain pass, even though on the map those pairs look alike.

## Decision

**23 shown words.** Every word covers at least 3 cards, with these exceptions:

| Word | Cards | Why it stays |
|---|---|---|
| Isthmus | 2 | It tells the Isthmus of Kra apart from the Malay Peninsula, which contains it. |
| Valley | 2 | The user merged Rift valley into Valley. |
| Sea route | 1 | The user's name for the Northern Sea Route. |
| Cape | 2 | No honest merge exists: Cape Horn isn't on a peninsula, and neither cape is an island. |

**Merges:**

| Old word | New word |
|---|---|
| Naval chokepoint | Strait |
| Mountain pass, Coastal pass | Pass |
| Rift valley | Valley |
| Basin, Steppe | Plain |
| Shipping route | Sea route |
| Gulf | Sea |
| Archipelago | Island |
| Prevailing winds, Monsoon | Wind system |
| Pressure belt, Storm belt | Climate belt |

**Qualifier.** `qualifier` adds only the season a climate map shows ("Wind system, July"). "Monsoon" isn't used as a qualifier, because it would give away part of the answer.

**Region category.** Region is used in one category only (Regions, Rifts & Deltas), so the Sahel moved there from Deserts, Plateaus & Plains.

**Families.** Each word has a coarse family (`model.FAMILY`):

| Family | Words |
|---|---|
| water body | Ocean, Sea, Lake |
| river | River |
| sea passage | Strait, Canal, Sea route |
| land passage | Pass, Corridor |
| relief | Mountain range, Plateau |
| lowland | Plain, Desert, Valley, Delta |
| region | Region |
| landmass | Peninsula, Isthmus, Cape |
| island | Island |
| climate | Ocean current, Wind system, Climate belt |

The family drives two things:

1. **Pair check.** When one highlight covers another (cover ≥ 0.9), the check flags the pair if both are in the same family, regardless of word. A real nesting is resolved with `{feature: …, subtract: true}` or a reasoned `allow_nested`.
2. **Land clip.** Area features in a land family (land passage, relief, lowland, region, landmass) are clipped to Natural Earth 10m land when resolved.

Island is a family of its own. NE draws some island groups as sea-area envelopes (the Spratlys), and clipping those to land would leave only specks.

## Consequences

- Re-typing a card usually changes only the note text. The map re-renders when the new word moves it into or out of a land family (the land clip changes its geometry, and the render hash records this, including through `{feature:}` references), or changes its fill opacity or close-up borders.
- Moving the Sahel to another category leaves an already-imported card in its old subdeck; see the tier note in the README.
- The vocabulary is 23 words, above the 15–18 first estimated. The ≥3 rule keeps every word that covers 3 or more cards. Fewer words would mean merging informative ones, for example Delta into Plain, Corridor into Pass, or Canal and Sea route into one word.
- Switching the pair check to families surfaced three nestings: Singapore in the Malay Peninsula, now subtracted; Barents in the Arctic Ocean, allowed; and the Zagros in the Iranian Plateau, allowed.
