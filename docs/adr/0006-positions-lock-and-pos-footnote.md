# 6. positions.lock and the ankc `[^pos]` footnote

Status: accepted, 2026-10-14; amended in P7 (lock format, freeze). Supersedes the drift consequence of [ADR 0004](0004-flat-deck-and-study-order.md). Built in P1 (WS1 in ankcompiler, WS3 here); the lock was frozen in P7 for v2.0.0.

Amended on 2026-10-15 (v2.1.0): retire and replace, for a political card that must move region (see [the amendment](#amendment-retire-and-replace-v210)).

## Context

Anki sets a new card's position once, on first import, and keeps it on every re-import ([ADR 0004](0004-flat-deck-and-study-order.md)). ankc 0.5 numbers new cards 0..N in source order and can't set a position directly.

So the position of every card depends on the whole deck. Adding one card shifts every card after it in a fresh build, while an existing collection keeps the old numbers. The two orders drift apart, and new cards tie with unstudied old ones. With 132 cards this was a small drift. World Atlas adds about 600 cards over several releases, and the order is the curriculum ([ADR 0009](0009-curriculum-order.md)).

## Decision

**Positions are data.** `data/positions.lock` maps each uid to an integer position and to the pass and ring region the card was placed in. It is committed, and append-only once frozen: from then on a retired uid keeps its slot, so no position is ever reused.

- **Format (P7 amendment):** a header line, `draft: true` or `draft: false`, then one line per uid, sorted by uid: `<uid>: <position> pass=<orientation|1|2> region=<NN|->`. An orientation card has no region, written `-`. Any other card records the region the order engine gave it: its own region for a political card, its frame region for a feature.
- **Why pass and region are recorded:** the guide's sections, and the `pass::` and `region::` tags that filtered decks search on, must agree with the slot each card holds. The lock is the single source for both: the guide takes its sections from the lock instead of recomputing them from the curriculum, and deckgen writes each locked card's `pass::` tag, and its `region::` tag if it has one, from its entry. Features carry no `region::` tag, so their recorded region only places them in the guide. `check package` fails when a note's `pass::` or `region::` tag differs from its entry. When a frozen card's pass or region in the data changes (a curriculum edit, or a feature's frame region shifting with its geometry), the card keeps its slot, section and tags, and `check deck` and `make positions` print a warning naming it. No retirement is needed. Region numbers are therefore identifiers once frozen: renumbering or splitting the ring needs a migration.
- **Initial assignment:** the ideal order from the order engine, with a stride of 500. About 700 cards end near 350,000.
- **New cards:** for each new uid, `pred` is the nearest earlier card in the ideal order that is in the lock. The new uid goes between `lock[pred]` and the next locked value above it. With no `pred`, it goes between 0 and the lowest locked value; with nothing locked above `pred`, new uids go at successive strides of 500 after `lock[pred]`. Several new uids that share a bounded gap are spread evenly through it, in ideal order. The ideal order is used only to place new uids. It never moves a locked one.
- **Bounds:** every position, and so every `due` in the package, is below 1,000,000. Anki's Check Database rewrites dues of 2,000,000 or more (P1 spike, below); 1,000,000 leaves a margin under that.
- **Full gap:** `make positions` fails (`GapExhausted`) when a gap has no room for the uids placed in it, or when a placement after the last locked value would reach 1,000,000. Single inserts at one spot halve a 500 gap each time, so about 8 fit. A deliberate reflow can renumber, but only cards no user has imported, which in practice means before release.
- **Draft until release:** the lock carried `draft: true` until P7. While it is a draft, `make positions` regenerates it from the ideal order at stride 500, so a draft lock never has a full gap, and retired uids drop out of it. A draft is stale, and fails `check deck`, when regenerating would change any position, pass or region.
- **Freeze guard:** P7 set the lock to `draft: false`. Since then, `check data` (and so every build) and `make positions` compare the working lock with the one committed on `origin/main` (`POSITIONS_BASE=<ref>` sets another base) and with the one on the newest `v*` release tag reachable from `HEAD`, which is what users last imported. If the base lock is frozen, the working lock must be frozen too and must keep every base entry as it is: no changed position, pass or region, and no dropped uid. It may only add uids. A draft base always passes. A base header or entry that doesn't parse is an error. If the base ref can't be read, as in a source archive with no git history or a shallow CI checkout, `check data` warns and skips that comparison; it fails under `RELEASE=1`, and `make positions` always fails. CI must check out with full history (or fetch `origin/main`) for the guard to run.
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
- Freezing the lock depends on ankc 0.6. Since the P7 freeze, a build with ankc 0.5 fails.
- A frozen card's pass and region are fixed with its position: a later data change moves neither its slot nor its `pass::`/`region::` tags, only the warning shows it. The ring's region numbers can't be renumbered without a migration.
- Existing users' 132 feature cards keep the positions they were imported with (0 to 131). The lock can't change those; see [ADR 0007](0007-rename-and-migration.md).
- The Anki behaviour this relies on (due kept on import, Check Database rewriting dues of 2,000,000 or more) was measured on Anki 26.09.3 desktop in the P1 spike. P6 tests it on AnkiDroid and AnkiMobile before release.

## Amendment: retire and replace (v2.1.0)

A frozen card's slot, pass and region can't change. A data change only warns, and the card stays where it was (above). That is right for a feature whose frame region drifts, but not for a political card deliberately moved to another region: it would keep the old region's slot and `region::` tag.

So a political card moves by **retire and replace**:

1. Set `retired: true` on the old entry in `territories.yaml` and keep the rest of it, uid included. A retired territory is validated, then dropped: it makes no card and isn't placed. Its lock entry stays as it is, as the freeze guard requires, and since it has no card it takes no number in the guide.
2. Add a new entry with a fresh uid (`make ids`). It may reuse the old `id`.
3. Run `make positions`. It places the new uid by the usual rule, between its `pred`'s slot and the next locked value.

The freeze guard is unchanged: the lock only gains an entry. `check deck` holds the rest: every locked uid must belong to a source entry, active or `retired: true`, so deleting a retired entry fails the build; and a retired territory and the replacement that reuses its id must be locked in different regions, since the `region::` tag is what tells the two notes apart in Browse. Each such move also halves the gap it lands in (250 either side of Greenland), so about 7 more inserts fit there before `GapExhausted`.

Greenland, v2.1.0: the old card, `24rdGoHY6W` at 250500 in region 19, is retired. The new card, `zjAlvxD9jl`, is at 21750 in region 02, between Iceland (21500) and the GIUK Gap (22000).

For users the replacement is a new note. An upgraded collection keeps the old card, with its review history, until the user deletes it; the history doesn't carry over to the new card. The README's [Retired cards](../../README.md#retired-cards) section says how to find it.
