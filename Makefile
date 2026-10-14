PY := uv run python -m geofeat
DECK := World Atlas
# Card key patterns for render, sheet, phone and cvd: keys or globs, e.g. IDS="country:france city:*"; a bare id is a
# feature. `make render IDS=...` renders only those cards and deletes nothing (a pilot); unset, every card.
IDS ?=
# OUT=name.png: sheet, phone or cvd to one named file in build/.
OUT ?=
# Each pattern single-quoted, so the shell neither globs nor interprets it.
QIDS = $(foreach p,$(IDS),'$(p)')
# RELEASE=1: check-data (and everything after it) also fails while any note has an open verify item.
RELEASE ?=
$(if $(filter-out 1,$(RELEASE)),$(error RELEASE must be 1 or unset))
# The ankc to build with; a command line works, e.g. ANKC="uv run --with ../ankcompiler ankc". 0.6+ gets [^pos].
ANKC ?= ankc
export ANKC

.PHONY: all test fetch ids check-data positions adjacency walks render deck check build sheet phone review pairs cvd guide verify-report clean

all: build

ids:
	$(PY).ids

fetch:
	$(PY).fetch

test:
	uv run python -m unittest discover -s tests

check-data: test fetch
	$(PY).check data $(if $(filter 1,$(RELEASE)),--release)

# Every open verify item (a note's claim to recheck before release), by card.
verify-report:
	$(PY).check verify-report

# The only writer of data/positions.lock; commit the result. Not part of `make all`.
positions: check-data
	$(PY).positions

# The country adjacency graph (ADR 0008) and its report; cached in build/adjacency.json.
adjacency: fetch
	$(PY).adjacency

# Each region's walk map and card list for review (build/walks-NN.png/.txt, build/walks-ring.png). Freeze approved
# walks with `uv run python tools/freeze_walks.py --all` (or REGION ...), then commit data/curriculum.yaml.
walks: check-data
	uv run python tools/walk_maps.py

render: check-data
	$(PY).jobs $(QIDS)

deck: render
	@test -z "$(IDS)" || { echo "IDS renders only some cards; unset it for deck, check, build and all" >&2; exit 1; }
	$(PY).deckgen

check: deck
	$(PY).check deck

build: check
	mkdir -p dist
	rm -f dist/*.apkg
	$(ANKC) build --deck "$(DECK)" --path deck --output dist
	$(PY).check package
	@ls dist/*.apkg

sheet:
	$(PY).sheet $(if $(OUT),--out '$(OUT)') $(QIDS)

phone:
	$(PY).sheet --phone $(if $(OUT),--out '$(OUT)') $(QIDS)

# One phone-size sheet per ring region, in study order (build/review-NN.png), and build/review-orientation.png.
review:
	$(PY).sheet --review

pairs: render
	$(PY).sheet --pairs

cvd: render
	$(PY).cvd $(if $(OUT),--out '$(OUT)') $(QIDS)

# The PDF guide in study order (build/<deck>-guide.pdf); REGION=NN writes one ring region's (build/<deck>-guide-NN.pdf).
guide: render
	uv run --group guide python -m geofeat.guide $(if $(REGION),--region '$(REGION)')

clean:
	rm -rf build deck dist
