# 11. Re-freezing the study order at a major version

Status: accepted, 2026-10-16 (v3.0.0); amended 2026-10-16 when versioning restarted at v1.0.0 ([Amendment](#amendment-versioning-restarted-at-v100)): the v3.0.0 named here is now the pre-release `archive/v3.0.0`, and its series 3 is series 1. Amends [ADR 0006](0006-positions-lock-and-pos-footnote.md) (the lock's format and the freeze guard) and [ADR 0009](0009-curriculum-order.md) (the study order).

## Context

v2.0.0 froze `data/positions.lock` ([ADR 0006](0006-positions-lock-and-pos-footnote.md)). Its order interleaves every kind of card: once round a ring of 21 regions, each country followed 2–3 cards later by its capital, with its territories, cities and the features it frames worked in around it ([ADR 0009](0009-curriculum-order.md)).

After using it, the user decided that the interleaved order was harder to follow than learning the map in layers: the political map first, then the physical map, then the cities, each as a block of its own. In the same change Greenland moves from North & Central America (region 19) to Nordic & Baltic (region 02), right after Iceland.

A frozen lock can't take either change. Every existing entry keeps its position, its block and its region, and the guard fails a build that changes one. Inserting new uids doesn't help: reordering means moving nearly every card.

Two facts about Anki set the limits:

- Re-importing a note never changes an existing card's `due`. A collection that imported v2 keeps v2's queue positions whatever v3 ships.
- A fresh import takes each card's `due` from the package, so a new lock does reach new users.

## Decision

**v3.0.0 re-freezes the lock.** The order is rebuilt in four blocks (ADR 0009) and the lock is regenerated from it at stride 500, as a new series. The ring order is still built and the blocks are cut from it.

| Block | Cards | Positions | First and last card |
|---|---|---|---|
| Continents | 7 | 500–3,500 | Europe … Antarctica |
| Countries, territories and disputed areas | 235 | 4,000–121,000 | Portugal … Bahamas |
| Physical features | 132 | 121,500–187,000 | Atlantic Ocean … Lake Titicaca |
| Capitals and cities | 233 | 187,500–303,500 | Lisbon … Nassau |

Greenland keeps its v2 card and uid (`24rdGoHY6W`) and is card 23, at 11,500, in region 02, right after Iceland. It stays in North America on the continent cards.

**The lock declares its series.** Its first two lines are `draft: true|false` and `series: N`, where `N` is the major version whose order it freezes. v3.0.0's lock is `series: 3`. A lock with no `series:` line is series 2, v2.0.0's format; `parse` accepts only the current format, and the guard reads the old one only to check it is well formed. Each entry records its block instead of its pass: `<uid>: <position> block=<block> region=<NN|->`.

**The freeze guard works per series** (`positions.guard`):

- Against the lock on the base ref (`origin/main`) and on the newest release tag of the same series (`v3.*`): the rules of ADR 0006, unchanged. A frozen base of the same series must stay frozen and keep every entry; the working lock may only add uids.
- A base of an earlier series isn't compared entry by entry. It is checked to be a well-formed lock of its own format, and the new lock must keep every uid of the newest earlier release (`dropped_released`): users hold those notes. A uid only ever on main or a branch may go.
- A base of a later series is an error: a series never goes back.
- `series_errors` holds the series to the release tags. It may equal the major version of the newest release merged into `HEAD`, or be exactly the next one (a fresh freeze). It may not be lower, and it may not skip a major version. Release tags are found with `git tag --merged HEAD`, exact `vX.Y.Z` only, newest by version.
- A release build names its version: `make all RELEASE=1 RELEASE_VERSION=vX.Y.Z`. The version's major, and any release tag on `HEAD`, must equal the lock's series, so a `v2.x` release can't ship a series-3 lock. A release build with no version and no tag on `HEAD` fails. A non-release build whose lock is ahead of the newest release warns that the next release must be vN.0.0.
- In a release build or `make positions`, a frozen lock fails when the tags can't be listed or the clone is shallow.

**To re-freeze**, in a future major version N:

1. Replace the lock with a header of `draft: true` and `series: N`.
2. Run `make positions`. A draft lock is regenerated from the study order at stride 500.
3. Set `draft: false` and commit.
4. Build with `make all RELEASE=1 RELEASE_VERSION=vN.0.0` and release as vN.0.0.

**This is not an exception mechanism.** No entry can change within a series: the guard within a series is ADR 0006's, unchanged. A new series is a whole new freeze, not an edit to the old one. It is tied to a semver major version and checked against the release tags, and it can't go back or skip a version. Breaking the order is possible, but only as a declared, versioned break.

## Consequences

- New users get the four-block order from a fresh import.
- An upgraded v2 collection keeps v2's interleaved queue. Re-importing updates every note's maps and tags (`block::`, `region::`) in place and keeps review history, but no `due` changes. A user who wants the new order either deletes the deck and imports fresh (losing review history), or repositions the unstudied cards block by block in **Browse** ([README](../../README.md#upgrading-from-a-pre-release)). Repositioning puts the blocks in v3 order but keeps v2's relative order within each block, which is close to v3's but not the same.
- Within series 3, ADR 0006's promise holds again: adding a card never moves an existing one, and fresh and upgraded v3 collections see the same order.
- The `pass::` tags are gone. A filtered deck that searched them must search `block::` instead. That is a breaking change, and part of why this is a major version.
- Region numbers stay identifiers. A series-3 card's `region::` tag comes from its lock entry, as before.
- Every future reorder costs existing users the same choice. A re-freeze should be rare and carry a real gain.

## Amendment: versioning restarted at v1.0.0

Versioning restarted at v1.0.0; earlier releases archived as `archive/v1.0.0`–`archive/v3.0.0` and treated as pre-release. This is a documented one-off, not a mechanism. Its constants in `positions.py` (`FIRST_SERIES`, `RESTARTED_FROM`, `ARCHIVE_PREFIX`) are permanent; a later re-freeze changes only the lock's `series:`.

- **Tags.** Each old release tag became an annotated `archive/vX.Y.Z` tag at the same commit, and the `vX.Y.Z` tags and their GitHub releases were deleted. The next release is v1.0.0. A clone that fetched the old tags keeps them until `git fetch --prune --prune-tags origin` (or `git tag -d v1.0.0 v2.0.0 v3.0.0`); until then the guard fails it.
- **Series.** The lock's header is `series: 1`. Its entries are archived v3.0.0's, unchanged: series 1 continues the series 3 order under a new number. Within series 1, positions are append-only, as before. A later re-freeze starts series 2 at v2.0.0, as above.
- **The guard** (`positions.guard`) changes in three ways; nothing else is relaxed:
  - Every lock must keep every uid of every archived release it can see (`dropped_released` over the `archive/vX.Y.Z` tags merged into `HEAD`), so users of the pre-releases keep their notes. `archive/v1.0.0` has no lock; its uids are in `archive/v2.0.0`'s.
  - A series-1 lock is held entry by entry to the newest archived series-3 lock (`archive/v3.0.0`), as if they were one series. Until the first `vX.Y.Z` tag exists, the base ref may still hold that series-3 lock and is compared the same way. Once v1.0.0 is tagged, a series-3 base is an error again ("a series never goes back").
  - With no `vX.Y.Z` tag yet, the lock must be series 1, and the oldest release (tag or `RELEASE_VERSION`) must be v1.x. A frozen series-1 lock, or any frozen lock while no `vX.Y.Z` tag exists, needs the archive tags: without them a release build or `make positions` fails, and any other build warns.
- **Why.** The old numbers carried pre-release churn (a rename, a re-freeze) that users of the first public release shouldn't have to read past. Archiving the tags rather than deleting them keeps the history and lets the guard go on protecting the uids those builds shipped.
