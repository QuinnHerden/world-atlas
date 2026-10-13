"""Paths shared by the climate tools. Downloads live outside git, in $CLIMATE_DATA (default build/climate-data)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("CLIMATE_DATA", ROOT / "build/climate-data"))
GEOMETRY = ROOT / "geometry"
NE_50M_LAND = ROOT / "vendor/ne_50m_land.geojson"
NE_10M_LAND = ROOT / "vendor/ne_10m_land.geojson"
