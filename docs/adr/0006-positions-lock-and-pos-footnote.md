# 6. positions.lock and the ankc `[^pos]` footnote

Status: accepted, 2026-10-14; amended in P7 (lock format, freeze). Supersedes the drift consequence of [ADR 0004](0004-flat-deck-and-study-order.md). Built in P1 (WS1 in ankcompiler, WS3 here); the lock was frozen in P7 for v2.0.0.

Amended on 2026-10-16 (v3.0.0) by [ADR 0011](0011-refreezing-at-a-major-version.md): the lock declares its major-version series and records each card's block instead of its pass, and the freeze guard works per series (see [Amendment: series](#amendment-series-v300)).

## Context

Anki sets a new card's position once, on first import, and keeps it on every re-import ([ADR 0004](0004-flat-deck-and-study-order.md)). ankc 0.5 numbers new cards 0..N in source order and can't set a position directly.

So the position of every card depends on the whole deck. Adding one card shifts every card after it in a fresh build, while an existing collection keeps the old numbers. The two orders drift apart, and new cards tie with unstudied old ones. With 132 cards this was a small drift. World Atlas adds about 600 cards over several releases, and the order is the curriculum ([ADR 0009](0009-curriculum-order.md)).

## Decision

**Positions are data.** `data/positions.lock` maps each uid to an integer position and to the pass and ring region the card was placed in. It is committed, and append-only once frozen: from then on a retired uid keeps its slot, so no position is ever reused.

- **Format (P7 amendment):** a header line, `draft: true` or `draft: false`, then one line per uid, sorted by uid: `<uid>: <position> pass=<orientation|1|2> region=<NN|->`. An orientation card has no region, written `-`. (Since v3.0.0 a second header line gives the series, and `block=` replaces `pass=`; see [the amendment](#amendment-series-v300).) Any other card records the region the order engine gave it: its own region for a political card, its frame region for a feature.
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

- Adding a card never moves an existing card. Within a series, fresh and existing collections see the same order. A re-freeze at a major version breaks that once, on purpose ([ADR 0011](0011-refreezing-at-a-major-version.md)).
- The lock is the history of the order. The ideal order and the shipped order can differ: a card placed when its neighbours were different keeps its slot.
- Freezing the lock depends on ankc 0.6. Since the P7 freeze, a build with ankc 0.5 fails.
- A frozen card's pass and region are fixed with its position: a later data change moves neither its slot nor its `pass::`/`region::` tags, only the warning shows it. The ring's region numbers can't be renumbered without a migration.
- Existing users' 132 feature cards keep the positions they were imported with (0 to 131). The lock can't change those; see [ADR 0007](0007-rename-and-migration.md).
- The Anki behaviour this relies on (due kept on import, Check Database rewriting dues of 2,000,000 or more) was measured on Anki 26.09.3 desktop in the P1 spike. P6 tests it on AnkiDroid and AnkiMobile before release.

## Amendment: series (v3.0.0)

v3.0.0 re-froze the lock in a new order ([ADR 0011](0011-refreezing-at-a-major-version.md)). What changed here:

- **Format:** two header lines, `draft: true|false` and `series: <N>`, then one line per uid: `<uid>: <position> block=<continents|countries|features|cities> region=<NN|->`. The `pass=` field is gone with the `pass::` tag; deckgen writes `block::` from the entry and `check package` holds it to the entry. A continent and an orientation feature (an ocean, a planetary wind band) have no region; every country, territory, dispute, capital and city has one. A lock with no `series:` line is series 2, v2.0.0's format.
- **Freeze guard, per series:** the rules above apply against the base ref and the newest release tag *of the lock's own series* (`v<N>.*`). A base of an earlier series is only checked to be well formed; one of a later series is an error. The series must equal the newest release's major version or be the next one. A new series is a fresh freeze at stride 500, and only a major version may start one. It may reorder, but must keep every uid of the newest earlier release; uids only ever on main or a branch may go.
- **Release tags:** found with `git tag --merged HEAD`, exact `vX.Y.Z` only, newest by version. Under `strict` (a release build, or `make positions`) a frozen lock also fails when the tags can't be listed or the clone is shallow.
- **Release version:** a release build names its version, `make all RELEASE=1 RELEASE_VERSION=vX.Y.Z`, and fails without one unless a release tag is on `HEAD`. The version's major, and any release tag on `HEAD`, must equal the lock's series. A non-release build whose lock is ahead of the newest release warns that the next release must be vN.0.0.
- **Retired uids:** `check deck` requires every locked uid to belong to a source entry, active or `retired: true` (`check.retired_lock_errors`), so a retired entry can't be deleted while the lock holds its uid. The series-3 lock was regenerated from the active cards, so at v3.0.0 it held no retired uid. Amended 2026-10-16: v3.0.1 retired 55 cards after the freeze, and their uids keep their slots, so the lock now holds 616 uids for 561 cards.

Within a series, nothing above changes: no entry moves, and new uids only fill gaps.
