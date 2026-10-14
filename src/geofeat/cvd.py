"""Colour-vision-deficiency check: each map beside its deuteranopia and protanopia simulations.

Uses the Machado, Oliveira & Fernandes (2009) matrices at severity 1.0, applied in linear RGB.
"""

import sys

import numpy as np
from PIL import Image

from geofeat.card import load_media, match_keys
from geofeat.model import BUILD
from geofeat.sheet import contact_sheet, out_name, thumbnail
from geofeat.style import (
    AREA_ALPHA, BORDER, CASING, COAST, CONTEXT_EDGE, CONTEXT_TINT_ALPHA, HIGHLIGHT, LAND, OCEAN, OUTLINE_ALPHA,
    WATER_AREA_ALPHA,
)

MACHADO = {
    "deuteranopia": np.array([
        [0.367322, 0.860646, -0.227968],
        [0.280085, 0.672501, 0.047413],
        [-0.011820, 0.042940, 0.968881],
    ]),
    "protanopia": np.array([
        [0.152286, 1.052583, -0.204868],
        [0.114503, 0.786281, 0.099216],
        [-0.003882, -0.048116, 1.051998],
    ]),
}


def _to_linear(srgb: np.ndarray) -> np.ndarray:
    return np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)


def _to_srgb(linear: np.ndarray) -> np.ndarray:
    return np.where(linear <= 0.0031308, linear * 12.92, 1.055 * linear ** (1 / 2.4) - 0.055)


def simulate(rgb: np.ndarray, kind: str) -> np.ndarray:
    """Simulate a deficiency on an (..., 3) array of sRGB values in 0..1."""
    return _to_srgb(np.clip(_to_linear(rgb) @ MACHADO[kind].T, 0, 1))


def _hex(colour: str) -> np.ndarray:
    return np.array([int(colour[i:i + 2], 16) for i in (1, 3, 5)]) / 255


def _contrast(a: np.ndarray, b: np.ndarray) -> float:
    """WCAG contrast ratio between two sRGB colours."""
    la, lb = sorted((float(_to_linear(c) @ [0.2126, 0.7152, 0.0722]) for c in (a, b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _blend(top: str, alpha: float, bottom: str) -> np.ndarray:
    return alpha * _hex(top) + (1 - alpha) * _hex(bottom)


def main() -> None:
    """Contrast of each highlight mark against what it sits on, then the sheet: `cvd [--out NAME.png] [patterns…]`,
    patterns as in geofeat.sheet; every map to build/cvd.png by default."""
    country_fill = _blend(HIGHLIGHT, OUTLINE_ALPHA, LAND)
    context = _blend(CASING, CONTEXT_TINT_ALPHA, LAND)
    marks = [
        ("stroke on land", _hex(HIGHLIGHT), _hex(LAND)),
        ("stroke on ocean", _hex(HIGHLIGHT), _hex(OCEAN)),
        ("stroke vs coast", _hex(HIGHLIGHT), _hex(COAST)),
        ("area fill on land", _blend(HIGHLIGHT, AREA_ALPHA, LAND), _hex(LAND)),
        ("area fill at sea", _blend(HIGHLIGHT, WATER_AREA_ALPHA, OCEAN), _hex(OCEAN)),
        ("country fill vs neighbour", country_fill, _hex(LAND)),
        ("outline on country fill", _hex(HIGHLIGHT), country_fill),
        ("dot on context country", _hex(HIGHLIGHT), context),
        ("context edge vs border", _hex(CONTEXT_EDGE), _hex(BORDER)),
    ]
    for kind in ("normal", *MACHADO):
        sim = (lambda c: c) if kind == "normal" else (lambda c: simulate(c, kind))
        print(f"{kind}: " + ", ".join(f"{name} {_contrast(sim(a), sim(b)):.1f}:1" for name, a, b in marks))

    out, patterns = out_name(sys.argv[1:], "cvd.png")
    keys = sorted(load_media())
    cells = []
    try:
        chosen = match_keys(patterns, keys) if patterns else keys
    except ValueError as exc:
        sys.exit(f"{exc} among the rendered cards")
    for key in chosen:
        image = thumbnail(key)
        rgb = np.asarray(image, dtype=np.float64) / 255
        cells.append((key, image))
        for kind in MACHADO:
            cells.append((kind, Image.fromarray(np.round(simulate(rgb, kind) * 255).astype(np.uint8))))
    contact_sheet(cells, 3, BUILD / out)


if __name__ == "__main__":
    main()
