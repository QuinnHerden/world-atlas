# Device test checklist

Run this by hand before a release, once each on Anki desktop, AnkiDroid (Android) and AnkiMobile (iOS). `make import-test` already checks the same behaviour in the desktop engine; this confirms it on real devices, and the mobile apps must pass before we rely on the positions lock. Build `dist/world-atlas.apkg` with `make all`, then record pass or fail per app in the table at the end.

The card names, counts and positions below come from the v3.0.1 data (554 cards) and its series-3 `positions.lock`. If the data has changed since, take the current values from the output of `make import-test`, which prints the first 16 new cards, the region 05 list and the position range.

**Mobile differences.** Menu names vary between versions, so look for the nearest match.

- **Import:** open or share the `.apkg` into the app. On AnkiDroid you can also use the deck list's menu → Import; on AnkiMobile, open the file from Files or the share sheet.
- **Filtered deck:** desktop **Tools → Create Filtered Deck**; AnkiDroid, in the deck list's menu (Create filtered deck); AnkiMobile, the deck list's Add/+ button (Filtered deck).
- **Check Database:** desktop **Tools → Check Database**; AnkiDroid, in the main menu (Check database); AnkiMobile, under Settings or Tools.

## 1. Fresh import order

1. Use a profile with no World Atlas or Geographic Features deck.
2. Import `world-atlas.apkg` with the default options. Expect one deck, `World Atlas`, with no subdecks and 554 cards, all new.
3. Set **New cards/day** to 20 or more and start studying. A card's front shows a type word and a map; the back names it. Expect the first 16 new cards in this order:
   1 Europe, 2 Africa, 3 Asia, 4 Oceania, 5 North America, 6 South America, 7 Antarctica, 8 Portugal, 9 Spain, 10 Andorra, 11 France, 12 Monaco, 13 Luxembourg, 14 Belgium, 15 Netherlands, 16 United Kingdom.

To check the order without studying, open **Browse** and sort by Due.

## 2. Check Database keeps the order

New-card positions run from 500 to 303,500, below the 2,000,000 threshold at which Anki rewrites new-card dues.

1. Run Check Database.
2. Expect the first new card is still Europe, and **Browse** sorted by Due shows the same order as before.

## 3. Upgrade from Geographic Features

Use a profile with the old v1 `Geographic Features` deck (physical features only, possibly in subdecks like `Geographic Features::<Category>::Tier <n>`) and some cards studied.

1. In **Browse**, search `deck:"Geographic Features"`. Note the card count, and the due date and interval of one studied card.
2. Import `world-atlas.apkg` with the defaults (**Update notes: If newer**).
3. Expect the feature notes updated in place, not duplicated: the same search gives the same count, with no duplicate notes. A feature card now has tags such as `kind::feature`, and its back shows the note under the answer.
4. Expect the noted card to keep its due date and interval, and to stay in `Geographic Features`. The 430 new cards land in `World Atlas`.
5. Follow the README steps: search `deck:"Geographic Features"`, select all, **Cards → Change Deck** → `World Atlas`. Expect the cards to move with their scheduling unchanged.
6. Delete the empty old decks.

The retired v1 notes (34 in the headless test) move along with the rest. This is expected; see [Retired cards](../README.md#retired-cards).

## 4. Filtered deck by region

1. Create a filtered deck with search `deck:"World Atlas" tag:region::05 is:new`, order "Order due", limit 9999.
2. Expect 11 cards (region 05, Eastern Europe) in this order, the countries and disputed areas first, then the capitals and cities: Moldova, Transnistria, Ukraine, Crimea, Belarus, Russia, Chișinău, Kyiv, Minsk, Moscow, Saint Petersburg. No features appear, because features have no region tag.
3. Empty the filtered deck. Expect the cards back in `World Atlas` with their order intact: on a fresh profile the first new card is still Europe.

## 5. Night mode

1. Turn on night or dark mode in the app.
2. Expect the type word and answer text readable, and the map in its normal light colours, not inverted or tinted.
3. Expect the note under the answer (below the thin rule, smaller and dimmer) still readable in night mode: dimmed, not lost against the dark background.
4. On AnkiDroid, check whether any night-mode colour or "invert images" option changes the map, and record what it does.

## 6. Phone readability

Do this on both phones; desktop is optional. Find each card in **Browse** by its tag and preview it at normal phone width, without zooming.

| Card | Tag | Expect |
|---|---|---|
| Kaliningrad Oblast, exclave (37) | `id_subdivision_kaliningrad` | A solid red outline between Poland and Lithuania, with the rest of Russia off to the east |
| Crimea, dispute (64) | `id_dispute_crimea` | A dashed red outline on the peninsula in the Black Sea (dashed means disputed) |
| Europe, continent (1) | `id_continent_europe` | Europe filled red on a world map, islands included |
| Kyoto (510) | `id_city_kyoto` | On its region's frame with a detail inset round its dot (no close-dot frame since Osaka was retired); the dot reads against the coast and Lake Biwa |
| Pretoria (479) and Cape Town (480) | `id_capital_south-africa`, `id_city_cape-town` | Each on its region's frame with a detail inset round its dot. Record whether the inland and the coastal dot read clearly |

For every card: the dot or outline is visible without zooming, the answer text fits, the note under it wraps and reads at phone width, and nothing is cropped.

## Results

| Check | Desktop | AnkiDroid | AnkiMobile |
|---|---|---|---|
| 1. Fresh import order | | | |
| 2. Check Database keeps the order | | | |
| 3. Upgrade from Geographic Features | | | |
| 4. Filtered deck by region | | | |
| 5. Night mode | | | |
| 6. Phone readability | (optional) | | |
