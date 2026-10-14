PY := uv run python -m geofeat
DECK := Geographic Features
IDS ?=
# The ankc to build with; a command line works, e.g. ANKC="uv run --with ../ankcompiler ankc". 0.6+ gets [^pos].
ANKC ?= ankc
export ANKC

.PHONY: all test fetch ids check-data positions adjacency render deck check build sheet phone pairs cvd guide clean

all: build

ids:
	$(PY).ids

fetch:
	$(PY).fetch

test:
	uv run python -m unittest discover -s tests

check-data: test fetch
	$(PY).check data

# The only writer of data/positions.lock; commit the result. Not part of `make all`.
positions: check-data
	$(PY).positions

# The country adjacency graph (ADR 0008) and its report; cached in build/adjacency.json.
adjacency: fetch
	$(PY).adjacency

render: check-data
	$(PY).jobs

deck: render
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
	$(PY).sheet $(IDS)

phone:
	$(PY).sheet --phone $(IDS)

pairs: render
	$(PY).sheet --pairs

cvd: render
	$(PY).cvd $(IDS)

guide: render
	uv run --group guide python -m geofeat.guide

clean:
	rm -rf build deck dist
