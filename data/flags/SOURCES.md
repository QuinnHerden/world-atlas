# Flag sources

World Flags' images, `data/flags/<id>.svg`, are sanitised copies of public-domain SVGs. `sources.lock` pins each one: its upstream file, the download's sha256 (and git blob sha or Commons sha1), and the sha256 of the sanitised file committed here. `python -m geofeat.flagfiles` rebuilds them from the pins; see [CONTRIBUTING.md](../../CONTRIBUTING.md#update-a-flag).

## hampusborgos/country-flags (208 flags)

[github.com/hampusborgos/country-flags](https://github.com/hampusborgos/country-flags) at commit `c09927e63705529bbf59ca6684cd9b23225dddad` (2026-03-10), `svg/<iso code>.svg`, by Hampus Nilsson and contributors. Its README says the files were taken from Wikimedia Commons, corrected against each country's or territory's flag legislation where Commons differed, and are in the public domain, as flags are; `package.json` gives the licence as `PD`. The repo has no LICENSE file. Every flag except the nine below comes from it.

## Wikimedia Commons (9 flags)

Where the set above is out of date, shows a flag other than the one in use, or has the state flag with arms where the national flag has none, the file comes straight from Wikimedia Commons. Each is marked public domain on its file page. Commons serves only a file's latest upload, so these pins hold until the file is next re-uploaded there.

| Card | Commons file | Upload pinned | Why not the set above |
|---|---|---|---|
| Afghanistan | [Flag of the Taliban.svg](https://commons.wikimedia.org/wiki/File:Flag_of_the_Taliban.svg) | 2026-03-31 | The set has the Islamic Republic's tricolour; the flag in use since 2021 is the Islamic Emirate's, the white flag with the shahada. |
| Kyrgyzstan | [Flag of Kyrgyzstan.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Kyrgyzstan.svg) | 2026-03-31 | The set has the sun with wavy rays, replaced in December 2023 by straight rays. |
| New Caledonia | [Flag of FLNKS.svg](https://commons.wikimedia.org/wiki/File:Flag_of_FLNKS.svg) | 2026-03-30 | The set has the French tricolour. Since 2010 the Kanak (FLNKS) flag has been flown officially beside it. |
| Martinique | [Flag-of-Martinique.svg](https://commons.wikimedia.org/wiki/File:Flag-of-Martinique.svg) | 2023-03-14 | The set has the French tricolour. The Assembly of Martinique adopted this flag in 2023. |
| Vatican | [Flag of Vatican City (2023–present).svg](https://commons.wikimedia.org/wiki/File:Flag_of_Vatican_City_(2023%E2%80%93present).svg) | 2024-10-17 | The set predates the flag as redrawn under the 2023 flag law. |
| Bolivia | [Flag of Bolivia.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Bolivia.svg) | 2023-10-30 | The set has the state flag with the arms; the civil and national flag is the plain tricolour. |
| Costa Rica | [Flag of Costa Rica.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Costa_Rica.svg) | 2023-10-30 | As Bolivia: the set has the state flag with the arms. |
| Peru | [Flag of Peru.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Peru.svg) | 2013-11-11 | As Bolivia: the set has the state flag with the arms. |
| Venezuela | [Flag of Venezuela.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Venezuela.svg) | 2024-03-09 | As Bolivia: the set has the state flag with the arms. |

## What sanitising changes

`geofeat.flagfiles.sanitise` drops titles, descriptions, comments and editor metadata, and gives the root a `width` and `height` from its `viewBox` (or a `viewBox` from its size), at a height of 400, so each flag keeps its own aspect ratio. It refuses scripts, `foreignObject`, images, links, animation, event attributes, references outside the file and CSS that imports or points elsewhere. The drawing itself is unchanged.

Flags may be subject to laws on their use that are separate from copyright.
