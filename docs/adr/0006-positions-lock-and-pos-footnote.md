# 6. positions.lock and the ankc `[^pos]` footnote

Status: proposed, 2026-10-14. Supersedes the drift consequence of [ADR 0004](0004-flat-deck-and-study-order.md). Built in P1 (WS1 in ankcompiler, WS3 here); the lock is frozen in P7.

## Context

Anki sets a new card's position once, on first import, and keeps it on every re-import ([ADR 0004](0004-flat-deck-and-study-order.md)). ankc 0.5 numbers new cards 0..N in source order and can't set a position directly.

So the position of every card depends on the whole deck. Adding one card shifts every card after it in a fresh build, while an existing collection keeps the old numbers. The two orders drift apart, and new cards tie with unstudied old ones. With 132 cards this was a small drift. World Atlas adds about 600 cards over several releases, and the order is the curriculum ([ADR 0009](0009-curriculum-order.md)).

## Decision

**Positions are data.** `data/positions.lock` maps each uid to an integer position. It is committed and append-only. A retired uid keeps its slot, so no position is ever reused.

- **Initial assignment:** the ideal order from the order engine, with a stride of 500. About 700 cards end near 350,000.
- **New cards:** a new uid takes the midpoint between the locked positions of its neighbours in the ideal order. The ideal order is used only to place new uids. It never moves a locked one.
- **Bounds:** every position is below 1,000,000. Anki's Check Database renumbers new cards at or above that value (read from the desktop source; tested on devices in P6).
- **Full gap:** a stride of 500 allows about 8 midpoint inserts at one spot. When a gap runs out, the build fails. A deliberate reflow can renumber, but only cards no user has imported, which in practice means before release.
- **Draft until release:** the lock carries `draft: true` until P7. While it is a draft, it can be regenerated. At P7 it is frozen, and a check fails on any change to an existing entry compared with `origin/main`.
- **Make target:** `make positions` places new uids and writes the lock.

**ankc 0.6 writes the position.** A new optional footnote, `[^pos]: <int>`, sits beside `[^uid]` and `[^type]` and sets the card's new-card due. Its rules:

- All or none: if any note in a package has `[^pos]`, every note must.
- 0 ≤ pos < 1,000,000, and positions are unique.
- Every card of one note shares the note's position.
- A package with no `[^pos]` builds exactly as in 0.5.
- `ankc check` validates these rules, `ankc uid --fix` keeps the footnote, and note model ids don't change.

deckgen writes `[^pos]` on every card. `check deck` requires ankc 0.6.x, and `check package` asserts that each card's due equals `positions.lock[uid]` instead of following source order.

**Rejected fallback:** rewriting `cards.due` in the built `.apkg`. It works, but it puts a packaging concern in this repo and bypasses `ankc check`.

## Consequences

- Adding a card never moves an existing card. Fresh and existing collections see the same order, and the README no longer needs Reposition instructions.
- The lock is the history of the order. The ideal order and the shipped order can differ: a card placed when its neighbours were different keeps its slot.
- The build depends on an ankc release. WS3 merges only after ankc 0.6 is released.
- Existing users' 132 feature cards keep the positions they were imported with (0 to 131). The lock can't change those; see [ADR 0007](0007-rename-and-migration.md).
- The Anki behaviour this relies on (due kept on import, the 1,000,000 cap) comes from the desktop source. P6 tests it on AnkiDroid and AnkiMobile before release.
