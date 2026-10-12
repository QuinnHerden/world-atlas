PY := uv run python -m geofeat
DECK := Geographic Features

.PHONY: all fetch ids check-data render deck check build sheet clean

all: build

ids:
	$(PY).ids

fetch:
	$(PY).fetch

check-data: fetch
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
	$(PY).sheet

clean:
	rm -rf build deck dist
