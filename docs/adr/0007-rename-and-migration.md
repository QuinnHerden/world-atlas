# 7. Rename to World Atlas, and migration

Status: proposed, 2026-10-14. The deck name is decided; the repo rename (decision 11) and GitHub-only distribution (decision 12) are defaults waiting for the user's confirmation ([open decisions](../world-atlas-plan.md#open-decisions)). Built in P5; tested in P6.

## Context

The deck is called **Geographic Features**, and it becomes **World Atlas** (decided 2026-10-14). Renaming has three costs in Anki:

- ankc derives the deck id from the deck name, and Anki doesn't move existing cards between decks on re-import. After a rename, a user's 132 existing cards stay in the old deck and every new card lands in the new one.
- A note type mismatch on import makes Anki duplicate notes instead of updating them. That is the one way a release can wreck an existing collection.
- Existing users have feature cards at positions 0 to 131, ahead of every new card ([ADR 0006](0006-positions-lock-and-pos-footnote.md)).

## Decision

**Rename once, at the first World Atlas release (v2.0.0).** Every card added after the rename would also need moving, so the first release is the cheapest point.

- **Deck:** `World Atlas`. The Makefile `DECK`, the deck source file and the `.apkg` name change with it.
- **Repo:** rename to `world-atlas` (default, decision 11). GitHub redirects the old URL. Update the remote and the README links.
- **Package:** keep `geofeat`. It's internal, and renaming it is churn no user sees.

**Identity doesn't change.**

- The 166 feature uids stay as they are, retired ones included. A uid freeze test fails the build if any of them changes or disappears.
- The ankc note type (model id and fields) for basic cards doesn't change.

**Migration is README guidance, not a tool.** The README gets a migration section for v1 users:

1. Import the new package.
2. Move the old cards with **Browse > Change Deck** from `Geographic Features` to `World Atlas`, as in the flat-deck migration.
3. Choose a path:
   - **Studied little or nothing:** delete the deck and import fresh, to get the full program order.
   - **Mid-way:** keep going. The ring starts once the earlier features are done, or run region filtered decks in parallel.

No repositioning tool is built (default, decision 8). These users aren't total beginners.

**Distribution:** a GitHub release only, carrying the `.apkg` (about 100 MB) and the guide PDF (default, decision 12).

## Consequences

- Existing notes update in place, with their review history. Only the deck move is manual.
- A user who skips the Change Deck step has two decks. Their old cards still work, just under the old name.
- AnkiWeb's shared-deck limits don't apply while the release is GitHub only.
- P6 tests the v1 to World Atlas upgrade on a device, alongside a fresh import.
