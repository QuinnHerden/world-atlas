"""A companion deck's map (ADR 0013): one subdivision on its whole country, drawn on a frame fixed per country, so
every card of a deck shares the main map.

- The country's subdivisions (the subject and the render job's `context`) are drawn with their borders, and the
  country's land border, in dark grey; the other countries recede into a flat grey-blue near the sea's value; and
  relief is toned down on the country so the borders read.
- The subject has World Atlas's country highlight (a faint red fill under a red outline); one smaller than SMALL_PX
  across also gets a red ring with a white halo.
- Repositioned parts (the US's Alaska and Hawaii) are drawn north up in boxes of their own in a corner, with a thin
  grey frame.
- Every card but the largest has a detail inset in its country's corner: the subject in its true place, north up and true to shape (on
  an equirectangular projection centred on it), with its neighbours, at least INSET_ZOOM times the main map's scale.
  Leader lines run from the subject on the main map, or in its box, to the inset.

Reads the basemap layers through geofeat.render and nothing else; the geometry comes in the job.
"""

from dataclasses import dataclass
from functools import cache
from typing import Literal

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import shapely
from pyproj import Geod, Transformer
from shapely import unary_union
from shapely.geometry import LineString, box
from shapely.geometry.base import BaseGeometry

from geofeat import render as r
from geofeat.frame import ASPECT, Equirectangular, Frame, centre, project
from geofeat.ne import layer
from geofeat.spec import RenderSpec
from geofeat.style import CASING, LAND, OCEAN

BBox = tuple[float, float, float, float]  # lon/lat: west, south, east, north
Corner = Literal["bottom-left", "bottom-right", "top-right"]

SUBDIVISION_BORDER = "#5F5A52"  # dark grey, lighter than the subject's outline
SUBDIVISION_BORDER_PX = 2.0  # at 1600 wide: about 0.5 px on a 390 px phone, under the coast's 2.4 px
SMALL_PX = 33  # 8 px on a 390 px phone: a subject smaller than this across is ringed
# Other countries' land: an opaque grey-blue a step off the ocean's, over their relief, borders and rivers, so the
# country is the lightest, warmest land on the map; their coasts show only as the faint half line on the sea side
FOREIGN = "#C9D0D4"
RELIEF_TONE = 0.55  # land colour over the country's relief
BOX_FRAME = "#9A958C"
BOX_FRAME_PX = 1.5

INSET_SHARE = 0.35  # the inset's share of the card's width
INSET_ZOOM = 1.5  # the inset's scale is at least this many times the main map's (or the box's)
INSET_FILL = 0.45  # the subject's share of the inset's width, on the 16:9 measure: room for its neighbours
SMALL_FILL = 0.18  # a small subject's inset widens, for context, until it is this share of the inset's width...
SMALL_INSET_M = 250_000  # ...but not past this
TIGHT_FILL = 0.8  # a subject over this share of the inset, on the 16:9 measure, is reported as a named exception
MARGIN_PX = 24
INSET_GROUP_M = 120_000  # parts this close belong to the subject's body, which the inset frames
LAND_BORDER_DEG = 0.02  # the country's edge this close to foreign land is a land border (Natural Earth's layers differ)
LAKE_KM2 = 1_000.0  # lakes this large are cut out of the subdivisions (Natural Earth's admin-1 holds the Great Lakes)


@dataclass(frozen=True)
class Box:
    """Parts of the country drawn in a frame of their own: those whose representative point is in `region`, which
    is also what the box shows, north up, on an equirectangular projection centred on it."""

    region: BBox
    rect: tuple[float, float, float, float]  # x, y (from the bottom left), width and height in px at 1600 × 900


@dataclass(frozen=True)
class CountryFrame:
    projection: str  # a proj4 string; see `crs`
    hold: BBox  # the lon/lat box the main frame is fitted to (16:9 round its projected bounds)
    corner: Corner  # where the detail inset goes; the boxes take the bottom left
    boxes: tuple[Box, ...] = ()
    clip: BBox | None = None  # parts are cut to this box first (Alaska's Aleutians stop at 180°)


# The main frames. Each projection is north up at the frame's centre: equirectangular (ADR 0003) for Italy, the US and
# Brazil, and Lambert conformal conic for Canada, the projection of Statistics Canada's maps, which keeps the Arctic
# islands' shapes where an equirectangular frame would stretch Ellesmere Island to over twice its width.
FRAMES = {
    # Italy's inset is over the Balkans, top right: bottom right would cover the toe of Calabria, bottom left Sardinia
    "italy": CountryFrame("+proj=eqc +lon_0=12.6 +lat_ts=41.5 +units=m", (6.0, 35.2, 19.2, 47.4), "top-right"),
    # The US frame reaches south to 17°N and east to 52°W: the Alaska and Hawaii boxes sit over Mexico and the Pacific
    # in the bottom left, and the inset's left edge is east of Florida, its top south of Cape Hatteras.
    "united-states": CountryFrame(
        "+proj=eqc +lon_0=-89 +lat_ts=37 +units=m", (-126.0, 17.2, -52.0, 50.4), "bottom-right",
        boxes=(Box((-180.0, 51.0, -129.0, 71.6), (MARGIN_PX, MARGIN_PX, 360, 262)),
               Box((-160.6, 18.7, -154.6, 22.4), (MARGIN_PX + 360 + 16, MARGIN_PX, 200, 128))),
        clip=(-180.0, -90.0, 0.0, 90.0)),
    "brazil": CountryFrame("+proj=eqc +lon_0=-54 +lat_ts=-14 +units=m", (-75.0, -34.6, -33.0, 6.2), "bottom-left"),
    # Canada's frame reaches east to 40°W, so the inset sits over Greenland and Baffin Bay, top right, clear of Baffin
    # Island; every other corner would cover British Columbia, the Maritimes or Newfoundland.
    "canada": CountryFrame("+proj=lcc +lon_0=-96 +lat_0=62 +lat_1=49 +lat_2=77 +units=m", (-141.0, 41.5, -40.0, 83.2),
                           "top-right"),
}
GEOD = Geod(ellps="WGS84")


def crs(proj4: str) -> ccrs.Projection:
    params = dict(p.lstrip("+").split("=") for p in proj4.split() if "=" in p)
    if params["proj"] == "eqc":
        return Equirectangular(float(params["lon_0"]), float(params["lat_ts"]))
    return ccrs.LambertConformal(central_longitude=float(params["lon_0"]), central_latitude=float(params["lat_0"]),
                                 standard_parallels=(float(params["lat_1"]), float(params["lat_2"])))


def _edge_points(bbox: BBox, n: int = 40) -> tuple[np.ndarray, np.ndarray]:
    w, s, e, n_ = bbox
    lons, lats = np.linspace(w, e, n), np.linspace(s, n_, n)
    return (np.concatenate([lons, lons, np.full(n, w), np.full(n, e)]),
            np.concatenate([np.full(n, s), np.full(n, n_), lats, lats]))


def fit(projection: ccrs.Projection, bbox: BBox) -> tuple[float, float, float, float]:
    """The 16:9 extent (x0, x1, y0, y1) round a lon/lat box's projected bounds."""
    xs, ys = Transformer.from_crs("EPSG:4326", projection.proj4_init, always_xy=True).transform(*_edge_points(bbox))
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    w = max(x1 - x0, (y1 - y0) * ASPECT)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return cx - w / 2, cx + w / 2, cy - w / ASPECT / 2, cy + w / ASPECT / 2


def lonlat_bounds(projection: ccrs.Projection, extent: tuple[float, float, float, float]) -> BBox:
    """The lon/lat window (lon0, lon1, lat0, lat1, as render.py takes it) round an extent, padded 2°. Longitudes are
    unwrapped round the projection's centre, so a window across 180° is cut there."""
    x0, x1, y0, y1 = extent
    xs, ys = _edge_points((x0, y0, x1, y1))
    lons, lats = Transformer.from_crs(projection.proj4_init, "EPSG:4326", always_xy=True).transform(xs, ys)
    lon_0 = projection.proj4_params.get("lon_0", 0)
    lons = lon_0 + (np.asarray(lons) - lon_0 + 180) % 360 - 180
    return (max(lons.min() - 2, -180), min(lons.max() + 2, 180), max(np.min(lats) - 2, -90), min(np.max(lats) + 2, 90))


@cache
def _large_lakes() -> BaseGeometry:
    """Every lake over LAKE_KM2."""
    lakes = layer("10m_lakes").geometry
    return shapely.make_valid(unary_union([g for g in lakes if abs(GEOD.geometry_area_perimeter(g)[0]) / 1e6 >= LAKE_KM2]))


@cache
def _water(bounds: BBox) -> BaseGeometry:
    """The large lakes in a lon/lat window (lon0, lon1, lat0, lat1)."""
    lon0, lon1, lat0, lat1 = bounds
    return shapely.clip_by_rect(_large_lakes(), lon0, lat0, lon1, lat1)


def _in(part: BaseGeometry, region: BBox) -> bool:
    point = part.representative_point()
    return region[0] <= point.x <= region[2] and region[1] <= point.y <= region[3]


@dataclass(frozen=True)
class Panel:
    """One map on the card: the main frame or a box. `px` is its rectangle on the card (x, y, w, h)."""

    projection: ccrs.Projection
    extent: tuple[float, float, float, float]
    px: tuple[float, float, float, float]

    @property
    def metres_per_px(self) -> float:
        return (self.extent[1] - self.extent[0]) / self.px[2]

    def to_card(self, g: BaseGeometry) -> BaseGeometry:
        """Projected geometry in card px."""
        x0, _, y0, _ = self.extent
        scale = self.px[2] / (self.extent[1] - self.extent[0])
        return shapely.transform(g, lambda c: (c - [x0, y0]) * scale + [self.px[0], self.px[1]])


def _ground_scale(projection: ccrs.Projection, lon: float, lat: float) -> float:
    """Projected metres per ground metre at a point, east-west (equirectangular and conformal maps are north up, and
    this is the scale the inset's 16:9 width is compared at)."""
    to = Transformer.from_crs("EPSG:4326", projection.proj4_init, always_xy=True)
    dlon = 0.01
    (xa, xb), _ = to.transform([lon - dlon, lon + dlon], [lat, lat])
    return abs(xb - xa) / GEOD.inv(lon - dlon, lat, lon + dlon, lat)[2]


@dataclass(frozen=True)
class Inset:
    projection: ccrs.Projection
    extent: tuple[float, float, float, float]
    # "whole": the subject and its neighbours; "tight": too large for neighbours at INSET_ZOOM, so it fills over
    # TIGHT_FILL of the inset; "cropped": too large to show whole, so the card has no inset
    fit: Literal["whole", "tight", "cropped"]


def _body(shape: BaseGeometry) -> BaseGeometry:
    """The largest group of a projected subject's parts within INSET_GROUP_M of each other: what the inset frames.
    Outlying islands (Lampedusa) don't size it."""
    parts = shapely.get_parts(shape)
    groups = shapely.get_parts(unary_union(shapely.buffer(parts, INSET_GROUP_M / 2, quad_segs=4)))
    return max((unary_union([p for p in parts if g.intersects(p)]) for g in groups), key=lambda m: m.area)


def inset_window(subject: BaseGeometry, panel: Panel) -> Inset:
    """The detail inset's frame: an equirectangular projection centred on the subject's main body, `INSET_FILL` of it
    the subject (a small one's inset is widened for context until it is SMALL_FILL of the width, up to SMALL_INSET_M), and
    never wider than the main map (or box) scale allows: INSET_ZOOM times larger. A subject that fits but fills over
    TIGHT_FILL of it is "tight"; one that can't fit whole is "cropped", and its card has no inset (`fit`)."""
    lon, lat = centre(subject)
    local = Equirectangular(lon, lat)
    body = _body(project(subject, local))
    bx0, by0, bx1, by1 = body.bounds
    long = max(bx1 - bx0, (by1 - by0) * ASPECT)
    width = max(long / INSET_FILL, min((bx1 - bx0) / SMALL_FILL, SMALL_INSET_M))
    ground_mpp = panel.metres_per_px / _ground_scale(panel.projection, lon, lat)  # main map, ground metres per px
    widest = ground_mpp * INSET_SHARE * r.WIDTH_PX / INSET_ZOOM
    fit_ = "whole" if long / widest <= TIGHT_FILL else "tight" if long <= widest else "cropped"
    width = min(width, widest)
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    return Inset(local, (cx - width / 2, cx + width / 2, cy - width / ASPECT / 2, cy + width / ASPECT / 2), fit_)


class _Drawing:
    """Draws the country on one panel's axes."""

    def __init__(self, fig, panel: Panel, spec: RenderSpec, subject: BaseGeometry, parts: list[BaseGeometry],
                 background: str = OCEAN) -> None:
        self.panel, self.spec = panel, spec
        x, y, w, h = panel.px
        self.ax = fig.add_axes([x / r.WIDTH_PX, y / r.HEIGHT_PX, w / r.WIDTH_PX, h / r.HEIGHT_PX],
                               projection=panel.projection)
        self.ax.set_facecolor(background)
        self.ax.spines["geo"].set_visible(False)
        self.ax.set_extent(panel.extent, crs=panel.projection)
        self.bounds = lonlat_bounds(panel.projection, panel.extent)
        self.water = _water(self.bounds)
        self.country = shapely.make_valid(unary_union(parts))
        self.subject, self.parts = subject, parts

    def project(self, g: BaseGeometry) -> BaseGeometry:
        return project(g, self.panel.projection)

    def draw(self) -> None:
        ax, crs_ = self.ax, self.panel.projection
        frame_ = Frame(crs_, self.panel.extent, inset=False)
        r._basemap(ax, self.spec, frame_, self.bounds, clear=self.country, res="10m")
        lon0, lon1, lat0, lat1 = self.bounds
        window = box(lon0, lat0, lon1, lat1)
        land = unary_union(list(r._clip(layer("10m_land"), self.bounds)))
        land = shapely.make_valid(land).intersection(window)
        country = self.country.difference(self.water)
        ax.add_geometries([self.project(country.intersection(window))], crs_, facecolor=LAND, alpha=RELIEF_TONE,
                          edgecolor="none", zorder=1.15)
        foreign = land.difference(self.country.buffer(0.01)).difference(self.water)
        if not foreign.is_empty:
            ax.add_geometries([self.project(foreign)], crs_, facecolor=FOREIGN, edgecolor="none", zorder=1.55)
        dry = land.difference(self.water)
        inner = unary_union([p.boundary for p in self.parts]).difference(self.country.boundary.buffer(1e-6))
        # The country's land border is drawn as its internal borders are, over the basemap's: the edge of the country
        # that runs along another country's land (US-Canada, Italy-France), not its coast
        abroad = self.country.boundary.intersection(foreign.buffer(LAND_BORDER_DEG)) if not foreign.is_empty else None
        lines = unary_union([inner, abroad]) if abroad is not None else inner
        ax.add_geometries([self.project(lines.intersection(dry))], crs_, facecolor="none", edgecolor=SUBDIVISION_BORDER,
                          linewidth=r.pt_full(SUBDIVISION_BORDER_PX), zorder=1.6)

    def subject_shape(self) -> BaseGeometry:
        return self.project(self.subject.difference(self.water))

    def across_px(self) -> float:
        x0, y0, x1, y1 = self.subject_shape().bounds
        return max(x1 - x0, y1 - y0) / self.panel.metres_per_px

    def draw_subject(self, ring: bool) -> BaseGeometry:
        """The subject in World Atlas's country highlight (render._country: a faint red fill under a red outline with a
        white casing), and its ring when small and `ring`. Returns what the leader lines point at, in card px: the
        subject's body (its parts within INSET_GROUP_M of each other), so a far island (Trindade, Espírito Santo's)
        doesn't pull them out to sea."""
        ax, crs_ = self.ax, self.panel.projection
        shape = self.subject_shape()
        across = self.across_px()
        r._country(ax, self.spec, self.subject.difference(self.water), Frame(crs_, self.panel.extent, inset=False),
                   ring=False)
        body = _body(shape) if not shape.is_empty else shape
        target = self.panel.to_card(body.convex_hull)
        if ring and across < SMALL_PX:
            x0, y0, x1, y1 = body.bounds
            size_px = max(r.RING_PX * r.SCALE, across + 2 * r.SMALL_RING_CLEAR_PX)
            r._ring(ax, (x0 + x1) / 2, (y0 + y1) / 2, crs_, size=r.pt_full(size_px))
            target = target.centroid.buffer(size_px / 2 + 4 * r.SCALE)
        return target


def _frame_box(ax, panel: Panel, colour: str, width_px: float) -> None:
    x, y, w, h = panel.px
    ring = box(x, y, x + w, y + h).exterior
    xs, ys = np.array(ring.coords).T
    ax.plot(xs, ys, color=colour, lw=r.pt_full(width_px), solid_joinstyle="miter", zorder=8)


def _leaders(target: BaseGeometry, inset_px: BaseGeometry) -> list[BaseGeometry]:
    """The two tangents from the subject to the inset's far corners, stopped short of the subject."""
    if inset_px.intersects(target):
        return []
    corners = {tuple(p) for p in np.round(np.array(inset_px.exterior.coords), 6)}
    pts = [tuple(p) for p in np.round(np.array(unary_union([target, inset_px]).convex_hull.exterior.coords), 6)]
    lines = [LineString([a, b]) for a, b in zip(pts, pts[1:]) if (a in corners) != (b in corners)]
    return [line.difference(target.buffer(r.LEADER_GAP_PX)) for line in lines]


def layout(spec: RenderSpec, geometry: BaseGeometry, context: tuple[BaseGeometry, ...]) -> dict:
    """Everything decided before drawing: the main panel, the boxes and their parts, the subject's panel, the inset's
    window and rectangle. Exposed so the checks can report the inset rules without rendering."""
    cf = FRAMES[spec.country_frame]
    parts = [geometry, *context]
    if cf.clip:
        clip = box(*cf.clip)
        parts = [p.intersection(clip) for p in parts]
    subject = parts[0]
    projection = crs(cf.projection)
    main = Panel(projection, fit(projection, cf.hold), (0, 0, r.WIDTH_PX, r.HEIGHT_PX))
    boxes = []
    for b in cf.boxes:
        lon, lat = (b.region[0] + b.region[2]) / 2, (b.region[1] + b.region[3]) / 2
        p = Equirectangular(lon, lat)
        x0, x1, y0, y1 = fit(p, b.region)
        bw, bh = b.rect[2], b.rect[3]
        w = max(x1 - x0, (y1 - y0) * bw / bh)  # the box's own aspect
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        boxes.append((Panel(p, (cx - w / 2, cx + w / 2, cy - w * bh / bw / 2, cy + w * bh / bw / 2), b.rect),
                      [q for q in parts if _in(q, b.region)]))
    home = next((panel for panel, members in boxes if any(m is subject for m in members)), main)
    window = inset_window(subject, home)
    iw = INSET_SHARE * r.WIDTH_PX
    ih = iw / ASPECT
    ix = MARGIN_PX if cf.corner == "bottom-left" else r.WIDTH_PX - iw - MARGIN_PX
    iy = r.HEIGHT_PX - ih - MARGIN_PX if cf.corner == "top-right" else MARGIN_PX
    return {"frame": cf, "parts": parts, "subject": subject, "main": main, "boxes": boxes, "home": home,
            "inset": window, "inset_px": (ix, iy, iw, ih)}


def render_country(spec: RenderSpec, geometry: BaseGeometry, context: tuple[BaseGeometry, ...]) -> bytes:
    plan = layout(spec, geometry, context)
    parts, subject, main = plan["parts"], plan["subject"], plan["main"]
    boxed = {id(q) for _, members in plan["boxes"] for q in members}
    fig = plt.figure(figsize=(r.WIDTH_PX / r.DPI, r.HEIGHT_PX / r.DPI), dpi=r.DPI, facecolor=OCEAN)

    drawing = _Drawing(fig, main, spec, subject, [q for q in parts if id(q) not in boxed])
    drawing.draw()
    target = drawing.draw_subject(ring=True) if id(subject) not in boxed else None
    for panel, members in plan["boxes"]:
        box_drawing = _Drawing(fig, panel, spec, subject, members)
        box_drawing.draw()
        if any(m is subject for m in members):
            target = box_drawing.draw_subject(ring=True)

    window = plan["inset"]
    ix, iy, iw, ih = plan["inset_px"]
    if window.fit != "cropped":  # a subject the inset can't hold whole is large enough to read on the main map
        inset_drawing = _Drawing(fig, Panel(window.projection, window.extent, (ix, iy, iw, ih)), spec, subject, parts)
        inset_drawing.draw()
        inset_drawing.draw_subject(ring=False)

    overlay = fig.add_axes([0, 0, 1, 1])  # plain axes in card px, over every panel
    overlay.set_xlim(0, r.WIDTH_PX)
    overlay.set_ylim(0, r.HEIGHT_PX)
    overlay.set_axis_off()
    overlay.patch.set_alpha(0)
    for panel, _ in plan["boxes"]:
        _frame_box(overlay, panel, CASING, BOX_FRAME_PX + 2 * r.CASING_PX)
        _frame_box(overlay, panel, BOX_FRAME, BOX_FRAME_PX)
    if window.fit != "cropped":
        inset_px = box(ix, iy, ix + iw, iy + ih)
        r._link_stroke(overlay, unary_union([inset_px.exterior, *_leaders(target, inset_px)]))
    return r.png(fig)
