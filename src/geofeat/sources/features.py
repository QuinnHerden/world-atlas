"""Adapt data/features.yaml's Feature entries to Cards."""

import re

from geofeat.card import Card, Geometry, RenderRef, id_tag
from geofeat.model import FEATURES, Feature, active, load_features
from geofeat.resolve import custom, features_by_id, resolve
from geofeat.spec import RenderSpec

PATH = FEATURES


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def tags(feature: Feature) -> tuple[str, ...]:
    return (f"tier::{feature.tier}", f"category::{_slug(feature.category)}", id_tag("feature", feature.id), "kind::feature")


def answer(feature: Feature) -> str:
    return f"{feature.name} ({', '.join(feature.alt_names)})" if feature.alt_names else feature.name


def geometry(feature: Feature) -> Geometry:
    """The feature's resolved shape, and the context and former shapes its frame names."""
    options = feature.frame
    return (
        resolve(feature),
        tuple(resolve(features_by_id()[other]) for other in options.context),
        custom(options.former).boundary if options.former else None,
    )


def card(feature: Feature) -> Card:
    if feature.uid is None:
        raise ValueError(f"{feature.id}: no uid (run `make ids` and commit)")
    return Card(
        uid=feature.uid,
        kind="feature",
        id=feature.id,
        prompt=feature.type_text,
        answer_lines=(answer(feature),),
        tags=tags(feature),
        tier=feature.tier,
        note=feature.note,
        render=RenderRef(spec=RenderSpec.from_feature(feature), geometry=lambda: geometry(feature)),
    )


def cards() -> list[Card]:
    """One card per active feature, in features.yaml order."""
    return [card(f) for f in active(load_features())]
