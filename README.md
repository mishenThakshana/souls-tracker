# Souls Tracker

A native Android app (Kotlin + Jetpack Compose) for tracking 100% completion in souls games.
Elden Ring is the first entry. The base game and *Shadow of the Erdtree* are kept as separate tabs.

## Features

- The full Elden Ring checklist (2,709 base-game steps and 907 DLC steps), in the guide's walkthrough order and grouped into its area sections.
- Tap a step's ⓘ to see its notes from the checklist and a map crop of its location:
  - **Red dot**: the exact datamined position of the item, grace, boss or NPC.
  - **Red ring**: the general area named in the step's Location column. This is used for steps without a fixed spot, such as merchant purchases, events and ghosts.
- Steps the guide flags for a later playthrough get an **NG+** badge.
- Search across item, location and notes. The filter button opens a sheet with Remaining/Done and category filters. Sections can be collapsed.
- The header hides while you scroll down the list and comes back when you scroll up.
- Progress is saved on the device with DataStore. You can reset each tab separately.
- The guide's general tips are behind the 💡 button.

## Build

Requires JDK 17 and the Android SDK (platform 35).

```sh
./gradlew :app:assembleDebug     # development
./gradlew :app:assembleRelease   # app/build/outputs/apk/release/app-release.apk (~5 MB)
```

Release builds are signed with `keystore/souls-tracker-release.jks`, using the passwords in `keystore.properties`. Both are git-ignored. Back them up: Android only installs an update over an existing install if it's signed with the same key.

## Adding another game

1. Put `checklist.json` (same schema as `app/src/main/assets/eldenring/checklist.json`) and its map tiles under `app/src/main/assets/<gameId>/`.
2. Add a `Game` to `GameCatalog` in `data/Models.kt`.

## Regenerating Elden Ring data

The scripts in `tools/` rebuild the app's assets from the source spreadsheet. Python 3 needs `openpyxl` and `Pillow`.

```sh
git clone --depth 1 https://github.com/jw-ofs/elden-ring-map.git /tmp/jw          # map tiles
git clone --depth 1 https://github.com/EthanShoeDev/elden-ring-compass.git /tmp/compass  # datamined positions
G=/tmp/compass/packages/data/src/generated

python3 tools/dump_checklist.py "Elden Ring Checklist.xlsx" raw.json
python3 tools/extract.py $G index.json          # project graces/bosses/NPCs/item placements to map pixels
python3 tools/match.py raw.json index.json matched.json
python3 tools/pack_tiles.py /tmp/jw/ctiles matched.json app/src/main/assets/eldenring/tiles
python3 tools/export_app_data.py matched.json app/src/main/assets/eldenring/checklist.json
```

`match.py` looks up each step's item name in the datamined data. When there are several candidates, it uses the step's Location and the previous step to choose one. If there is no confident match, it falls back to that location's area. It also anchors a few map landmarks that aren't graces to their nearest grace, using the Fextralife wiki.

`pack_tiles.py` bundles only the 290 zoom-5 map tiles that some step's crop touches, about 3.7 MB. The app cuts each step's crop from these tiles and draws the red marker when the info box opens (`MapCropRenderer.kt`).

## Credits

- Checklist: the community "Elden Ring Checklist" spreadsheet by zaraxeon.
- Map tiles and positions: datamined by [elden-ring-compass](https://github.com/EthanShoeDev/elden-ring-compass), with tiles as packaged by [jw-ofs/elden-ring-map](https://github.com/jw-ofs/elden-ring-map).
- *Elden Ring* and its assets are © FromSoftware / Bandai Namco. This is an unofficial fan project for personal use.
