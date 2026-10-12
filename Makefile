PY := uv run python -m geofeat
DECK := Geographic Features
IDS ?=

.PHONY: all test fetch ids check-data render deck check build sheet pairs cvd clean

all: build

ids:
	$(PY).ids

fetch:
	$(PY).fetch

test:
	uv run python -m unittest discover -s tests

check-data: test fetch
	$(PY).check data

render: check-data
	$(PY).render

deck: render
	$(PY).deckgen

check: deck
	$(PY).check deck

build: check
	mkdir -p dist
	rm -f dist/*.apkg
	ankc build --deck "$(DECK)" --path deck --output dist
	$(PY).check package
	@ls dist/*.apkg

sheet:
	$(PY).sheet $(IDS)

pairs: render
	$(PY).sheet --pairs

cvd: render
	$(PY).cvd $(IDS)

clean:
	rm -rf build deck dist
