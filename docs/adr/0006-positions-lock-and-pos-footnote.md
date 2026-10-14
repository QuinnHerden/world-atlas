# 6. positions.lock and the ankc `[^pos]` footnote

Status: proposed, 2026-10-14. Supersedes the drift consequence of [ADR 0004](0004-flat-deck-and-study-order.md). Built in P1 (WS1 in ankcompiler, WS3 here); the lock is frozen in P7.

## Context

Anki sets a new card's position once, on first import, and keeps it on every re-import ([ADR 0004](0004-flat-deck-and-study-order.md)). ankc 0.5 numbers new cards 0..N in source order and can't set a position directly.

So the position of every card depends on the whole deck. Adding one card shifts every card after it in a fresh build, while an existing collection keeps the old numbers. The two orders drift apart, and new cards tie with unstudied old ones. With 132 cards this was a small drift. World Atlas adds about 600 cards over several releases, and the order is the curriculum ([ADR 0009](0009-curriculum-order.md)).

## Decision

**Positions are data.** `data/positions.lock` maps each uid to an integer position. It is committed, and append-only once frozen: from then on a retired uid keeps its slot, so no position is ever reused.

- **Initial assignment:** the ideal order from the order engine, with a stride of 500. About 700 cards end near 350,000.
- **New cards:** for each new uid, `pred` is the nearest earlier card in the ideal order that is in the lock. The new uid goes between `lock[pred]` and the next locked value above it. With no `pred`, it goes between 0 and the lowest locked value; with nothing locked above `pred`, new uids go at successive strides of 500 after `lock[pred]`. Several new uids that share a bounded gap are spread evenly through it, in ideal order. The ideal order is used only to place new uids. It never moves a locked one.
- **Bounds:** every position, and so every `due` in the package, is below 1,000,000. Anki's Check Database rewrites dues of 2,000,000 or more (P1 spike, below); 1,000,000 leaves a margin under that.
- **Full gap:** `make positions` fails (`GapExhausted`) when a gap has no room for the uids placed in it, or when a placement after the last locked value would reach 1,000,000. Single inserts at one spot halve a 500 gap each time, so about 8 fit. A deliberate reflow can renumber, but only cards no user has imported, which in practice means before release.
- **Draft until release:** the lock carries `draft: true` until P7. While it is a draft, `make positions` regenerates it from the ideal order at stride 500, so a draft lock never has a full gap, and retired uids drop out of it. At P7 it is frozen; a check that fails on any change to an existing entry compared with `origin/main` is added then.
- **Make target:** `make positions` is the only writer of the lock. It places new uids (or regenerates a draft) and writes the file; the result is committed. It isn't part of `make all`, and `check deck` fails on an active uid the lock doesn't hold.

**ankc 0.6 writes the position.** A new optional footnote, `[^pos]: <int>`, sits beside `[^uid]` and `[^type]` and sets the card's new-card due. Its rules:

- All or none: if any note in a package has `[^pos]`, every note must.
- 0 ≤ pos < 1,000,000, and positions are unique.
- Every card of one note shares the note's position.
- A package with no `[^pos]` builds exactly as in 0.5.
- `ankc check` validates these rules, `ankc uid --fix` keeps the footnote, and note model ids don't change.

**ankc gate.** `check deck` accepts ankc `>=0.5,<0.7`. With 0.6, deckgen writes `[^pos]` on every card and `check package` asserts that each card's due equals `positions.lock[uid]`. With 0.5, deckgen writes no `[^pos]` and `check package` asserts that dues follow the ideal order, as before. A frozen lock (`draft: false`) requires 0.6: deckgen and `check deck` fail with 0.5, and `check package` always compares dues with the lock.

**Spike evidence (P1).** Anki 26.09.3 desktop kept the imported dues exactly. Check Database rewrote dues of 2,000,000 or more.

**Rejected fallback:** rewriting `cards.due` in the built `.apkg`. It works, but it puts a packaging concern in this repo and bypasses `ankc check`.

## Consequences

- Adding a card never moves an existing card. Fresh and existing collections see the same order, and the README no longer needs Reposition instructions.
- The lock is the history of the order. The ideal order and the shipped order can differ: a card placed when its neighbours were different keeps its slot.
- Freezing the lock depends on ankc 0.6. Until the lock is frozen, a build with ankc 0.5 still works, with positions following the ideal order.
- Existing users' 132 feature cards keep the positions they were imported with (0 to 131). The lock can't change those; see [ADR 0007](0007-rename-and-migration.md).
- The Anki behaviour this relies on (due kept on import, Check Database rewriting dues of 2,000,000 or more) was measured on Anki 26.09.3 desktop in the P1 spike. P6 tests it on AnkiDroid and AnkiMobile before release.
