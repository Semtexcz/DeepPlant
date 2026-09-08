"""Deterministic contract tests for the process SVG symbol assets.

These tests validate the SVG + anchor contract defined in
``docs/svg-symbols.md`` and decided in ADR-0008, using only the standard
library XML parser. They enforce the *current variant* anchor cardinalities
without encoding any semantic-model validation: the domain model keeps
``ProcessStep.type`` an open string.
"""

import re
from pathlib import Path
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from deepplant import load_plant

ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "symbols" / "process"
REALISTIC_EXAMPLE = (
    Path(__file__).resolve().parents[1] / "examples" / "realistic-process-fragment" / "plant.yaml"
)

SVG_NAMESPACE = "http://www.w3.org/2000/svg"

# Symbol id -> (expected input anchor count, expected output anchor count).
# These are properties of the current symbol variants only, not semantic
# invariants.
EXPECTED_CARDINALITIES: dict[str, tuple[int, int]] = {
    "source": (0, 1),
    "mixing": (2, 1),
    "pump": (1, 1),
    "heat_exchanger": (1, 1),
    "splitting": (1, 2),
    "vessel": (1, 1),
    "sink": (1, 0),
}

EXPECTED_PROCESS_TYPES = set(EXPECTED_CARDINALITIES)

ANCHOR_ID = re.compile(r"^anchor-(in|out)-([0-9]+)$")
ANCHOR_GROUP_ID = "deepplant-anchors"
CANONICAL_VIEWBOX = "0 0 100 100"
ALLOWED_ELEMENT_NAMES = {
    "svg",
    "g",
    "path",
    "line",
    "polyline",
    "polygon",
    "rect",
    "circle",
    "ellipse",
}
ALLOWED_COLOR_VALUES = {"currentColor", "none"}


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _symbol_paths() -> list[Path]:
    return sorted(ASSET_DIR.glob("*.svg"))


def _root_of(path: Path) -> Element:
    return ElementTree.parse(path).getroot()


def test_asset_set_matches_current_process_variants() -> None:
    symbol_ids = {path.stem for path in _symbol_paths()}
    assert symbol_ids == EXPECTED_PROCESS_TYPES


def test_assets_are_valid_xml_with_svg_root() -> None:
    for path in _symbol_paths():
        root = _root_of(path)
        assert root.tag == f"{{{SVG_NAMESPACE}}}svg", path
        assert _local_name(root.tag) == "svg", path


def test_canonical_viewbox_and_no_fixed_dimensions() -> None:
    for path in _symbol_paths():
        root = _root_of(path)
        assert root.get("viewBox") == CANONICAL_VIEWBOX, path
        assert "width" not in root.attrib, path
        assert "height" not in root.attrib, path


def _anchor_circles(root: Element) -> list[Element]:
    groups = [
        element
        for element in root.iter()
        if _local_name(element.tag) == "g" and element.get("id") == ANCHOR_GROUP_ID
    ]
    assert len(groups) == 1, "exactly one deepplant-anchors group is required"
    group = groups[0]
    circles = [child for child in group if _local_name(child.tag) == "circle"]
    assert len(circles) == len(group), "the anchors group must contain only circles"
    return circles


def test_anchor_ids_are_unique_ordered_and_match_cardinalities() -> None:
    for path in _symbol_paths():
        root = _root_of(path)
        circles = _anchor_circles(root)
        symbol_id = path.stem

        seen: set[str] = set()
        in_indices: list[int] = []
        out_indices: list[int] = []
        for circle in circles:
            anchor_id = circle.get("id")
            assert anchor_id is not None, path
            match = ANCHOR_ID.fullmatch(anchor_id)
            assert match is not None, f"anchor id '{anchor_id}' must be anchor-in-N/anchor-out-N"
            assert anchor_id not in seen, f"duplicate anchor id '{anchor_id}' in {path}"
            seen.add(anchor_id)
            index = int(match.group(2))
            if match.group(1) == "in":
                in_indices.append(index)
            else:
                out_indices.append(index)

        expected_ins, expected_outs = EXPECTED_CARDINALITIES[symbol_id]
        assert len(in_indices) == expected_ins, path
        assert len(out_indices) == expected_outs, path
        assert in_indices == list(range(expected_ins)), f"in indices must start at 0: {path}"
        assert out_indices == list(range(expected_outs)), f"out indices must start at 0: {path}"

        # Every element id in the document must be the anchors group id or an
        # anchor id inside that group.
        all_ids = {element.get("id") for element in root.iter() if element.get("id") is not None}
        assert all_ids == seen | {ANCHOR_GROUP_ID}, (
            f"anchor ids must live only in the anchors group: {path}"
        )


def test_anchor_coordinates_are_numeric_unrendered_and_inside_viewbox() -> None:
    for path in _symbol_paths():
        root = _root_of(path)
        circles = _anchor_circles(root)
        for circle in circles:
            cx = circle.get("cx")
            cy = circle.get("cy")
            radius = circle.get("r")
            assert cx is not None and cy is not None and radius is not None, path
            assert float(cx) >= 0.0 and float(cx) <= 100.0, f"cx out of viewBox in {path}"
            assert float(cy) >= 0.0 and float(cy) <= 100.0, f"cy out of viewBox in {path}"
            assert float(radius) == 0.0, f"anchors must not render visibly in {path}"
            assert circle.get("fill") == "none", path
            assert circle.get("stroke") == "none", path


def test_only_allowed_svg_elements_and_no_text_or_external_content() -> None:
    for path in _symbol_paths():
        root = _root_of(path)
        for element in root.iter():
            name = _local_name(element.tag)
            assert name in ALLOWED_ELEMENT_NAMES, f"forbidden element <{name}> in {path}"
            assert element.text is None or not element.text.strip(), (
                f"unexpected text content in {path}"
            )
            assert element.tail is None or not element.tail.strip(), (
                f"unexpected tail content in {path}"
            )
            for attribute_name, value in element.attrib.items():
                assert "url(" not in value, f"external reference in {path}"
                assert not value.startswith("data:"), f"embedded data in {path}"
                assert not value.startswith("http:") and not value.startswith("https:"), (
                    f"external URI in {path}"
                )
                assert attribute_name not in {"href", "style", "class", "font-family"}, (
                    f"forbidden attribute '{attribute_name}' in {path}"
                )
                if attribute_name in {"fill", "stroke"}:
                    assert value in ALLOWED_COLOR_VALUES, f"non-themeable color in {path}"


def test_realistic_process_types_have_symbol_assets() -> None:
    model = load_plant(REALISTIC_EXAMPLE)
    assert model.process is not None
    process_types = {step.type for step in model.process.steps}
    assert process_types == EXPECTED_PROCESS_TYPES
    symbol_ids = {path.stem for path in _symbol_paths()}
    assert process_types <= symbol_ids
