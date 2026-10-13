"""Westerlies and trade winds: streamlines of the annual-mean ICOADS surface wind from fixed seeds.

usage: trace_winds.py   (writes $CLIMATE_DATA/westerlies.json and trades.json, plus preview PNGs)
Seed positions are a drawing choice. Every third point is kept, plus the last.
"""
import json

from common import DATA
from wind import preview, streamline

WESTERLY_SEEDS = [(150, 37), (-178, 41), (-152, 44), (-72, 37), (-48, 43), (-26, 49),
                  (-178, -45), (-148, -47), (-118, -46), (-55, -44), (-25, -43), (5, -43), (35, -44), (65, -44), (95, -44),
                  (125, -45), (152, -47)]
TRADE_SEEDS = [(-22, 23), (-44, 21), (-124, 23), (-146, 21), (-168, 19), (172, 18), (152, 17),
               (6, -21), (-16, -19), (-84, -21), (-106, -19), (-128, -18), (-150, -18), (-172, -18), (104, -21), (84, -21), (64, -20)]


def thin(line: list[tuple[float, float]]) -> list[list[float]]:
    return [[round(a, 1), round(b, 1)] for a, b in line[::3] + ([line[-1]] if (len(line) - 1) % 3 else [])]


westerlies = []
for lon, lat in WESTERLY_SEEDS:
    line = [(a, b) for a, b in streamline(lon, lat, 0, 1900, step_km=100) if a <= 179.5]
    westerlies.append(thin(line))
json.dump(westerlies, open(DATA / "westerlies.json", "w"))
preview(0, (-180, -65, 180, 65), DATA / "westerlies.png", lines=westerlies, stride=2, slp=False)

trades = []
for lon, lat in TRADE_SEEDS:
    cut = []
    for a, b in streamline(lon, lat, 0, 1800, step_km=100):
        a = (a + 180) % 360 - 180
        if abs(b) < 6 or (cut and abs(a - cut[-1][0]) > 180):  # stop near the equator or at the 180 deg wrap
            break
        cut.append((a, b))
    trades.append(thin(cut))
json.dump(trades, open(DATA / "trades.json", "w"))
preview(0, (-180, -40, 180, 40), DATA / "trades.png", lines=trades, stride=2, slp=False)
for line in westerlies + trades:
    print(line[0], line[-1], len(line))
