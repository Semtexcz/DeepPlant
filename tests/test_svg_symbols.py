"""Deterministic contract tests for the basic process SVG symbol pack.

These tests validate the SVG + anchor contract defined in
``docs/svg-symbols.md`` and decided in ADR-0008, using only the standard
library XML parser. They enforce the *current basic-pack variant* anchor
cardinalities without encoding any semantic-model validation: the domain model
keeps ``ProcessStep.function`` an open string (ADR-0009), a symbol role is a
presentation value resolved at the rendering boundary, and a symbol role is not
a globally canonical SVG asset.
"""

import re
from pathlib import Path
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from deepplant import load_plant

# The canonical asset tree lives inside the installed package so the basic
# pack can be resolved at runtime through importlib.resources. These contract
# tests read the same tree from the source checkout.
BASIC_PACK_DIR = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "deepplant"
    / "assets"
    / "symbols"
    / "process"
    / "basic"
)
REALISTIC_EXAMPLE = (
    Path(__file__).resolve().parents[1] / "examples" / "realistic-process-fragment" / "plant.yaml"
)

SVG_NAMESPACE = "http://www.w3.org/2000/svg"

# Role -> (expected input anchor count, expected output anchor count) for the
# current basic-pack variants only. These are not semantic invariants: another
# pack may realize the same role with different geometry and anchors.
EXPECTED_CARDINALITIES: dict[str, tuple[int, int]] = {
    "source": (0, 1),
    "mixing": (2, 1),
    "pump": (1, 1),
    "heat_exchanger": (1, 1),
    "splitting": (1, 2),
    "vessel": (1, 1),
    "sink": (1, 0),
}

# Roles that the realistic process fragment requires the basic pack to cover.
REQUIRED_PROCESS_ROLES = set(EXPECTED_CARDINALITIES)

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
    return sorted(BASIC_PACK_DIR.glob("*.svg"))


def _root_of(path: Path) -> Element:
    return ElementTree.parse(path).getroot()


def _anchor_circles(root: Element) -> list[Element]:
    groups = [
        element
        for element in root.iter()
        if _local_name(element.tag) == "g" and element.get("id") == ANCHOR_GROUP_ID
    ]
    assert len(groups) == 1, "exactly one deepplant-anchors group is required"
    group = groups[0]
    circles = [child for child in group if _local_name(child.tag) == "circle"]
    assert len(circles) == len(group), "the anchors group must contain only anchor circles"
    return circles


def test_required_basic_pack_directory_exists() -> None:
    assert BASIC_PACK_DIR.is_dir(), "assets/symbols/process/basic must exist"


def test_basic_pack_covers_required_process_roles() -> None:
    # Subset coverage only: the required realistic-fragment roles must be
    # present, but nothing requires the pack to contain exactly those roles.
    # Adding a further valid asset stays green.
    symbol_ids = {path.stem for path in _symbol_paths()}
    assert REQUIRED_PROCESS_ROLES <= symbol_ids


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


def test_exactly_one_unique_anchors_group() -> None:
    for path in _symbol_paths():
        groups = [
            element
            for element in _root_of(path).iter()
            if _local_name(element.tag) == "g" and element.get("id") == ANCHOR_GROUP_ID
        ]
        assert len(groups) == 1, f"exactly one {ANCHOR_GROUP_ID} group is required in {path}"


def test_anchor_ids_are_unique_and_contiguous_per_direction() -> None:
    for path in _symbol_paths():
        circles = _anchor_circles(_root_of(path))

        seen: set[str] = set()
        in_indices: list[int] = []
        out_indices: list[int] = []
        for circle in circles:
            anchor_id = circle.get("id")
            assert anchor_id is not None, path
            match = ANCHOR_ID.fullmatch(anchor_id)
            assert match is not None, (
                f"anchor id {anchor_id!r} must match anchor-in-N/anchor-out-N in {path}"
            )
            assert anchor_id not in seen, f"duplicate anchor id {anchor_id!r} in {path}"
            seen.add(anchor_id)
            index = int(match.group(2))
            if match.group(1) == "in":
                in_indices.append(index)
            else:
                out_indices.append(index)

        for direction, indices in (("in", in_indices), ("out", out_indices)):
            assert indices == list(range(len(indices))), (
                f"{direction} anchor indices must start at 0 and be contiguous in {path}"
            )


def test_anchors_live_inside_the_anchors_group() -> None:
    for path in _symbol_paths():
        root = _root_of(path)
        circles = _anchor_circles(root)
        group_anchor_ids = {circle.get("id") for circle in circles}
        document_anchor_ids: set[str] = set()
        for element in root.iter():
            element_id = element.get("id")
            if element_id is not None and ANCHOR_ID.fullmatch(element_id):
                document_anchor_ids.add(element_id)
        assert document_anchor_ids == group_anchor_ids, (
            f"every anchor id must live inside {ANCHOR_GROUP_ID} in {path}"
        )


def test_current_basic_variant_anchor_counts_remain_expected() -> None:
    paths_by_role = {path.stem: path for path in _symbol_paths()}
    for role, (expected_ins, expected_outs) in EXPECTED_CARDINALITIES.items():
        circles = _anchor_circles(_root_of(paths_by_role[role]))
        counts = {"in": 0, "out": 0}
        for circle in circles:
            match = ANCHOR_ID.fullmatch(circle.get("id") or "")
            assert match is not None, f"unexpected anchor in {paths_by_role[role]}"
            counts[match.group(1)] += 1
        assert counts["in"] == expected_ins, f"input count for {role!r} in basic pack"
        assert counts["out"] == expected_outs, f"output count for {role!r} in basic pack"


def test_anchor_coordinates_are_numeric_and_inside_viewbox() -> None:
    for path in _symbol_paths():
        for circle in _anchor_circles(_root_of(path)):
            cx = circle.get("cx")
            cy = circle.get("cy")
            assert cx is not None, f"anchor missing cx in {path}"
            assert cy is not None, f"anchor missing cy in {path}"
            assert 0.0 <= float(cx) <= 100.0, f"cx out of viewBox in {path}"
            assert 0.0 <= float(cy) <= 100.0, f"cy out of viewBox in {path}"


def test_anchors_are_visually_hidden_without_requiring_exact_radius() -> None:
    for path in _symbol_paths():
        for circle in _anchor_circles(_root_of(path)):
            # Invisibility comes from no fill and no stroke. The radius is not
            # prescribed by the contract: r="0", r="1", or no radius all pass.
            assert circle.get("fill") == "none", f"anchor fill must be none in {path}"
            assert circle.get("stroke") == "none", f"anchor stroke must be none in {path}"


def test_unrelated_svg_element_ids_are_allowed() -> None:
    # pump.svg intentionally carries an unrelated geometry-group id (pump-body)
    # and hidden anchors with a nonzero radius; both must satisfy the contract.
    path = BASIC_PACK_DIR / "pump.svg"
    root = _root_of(path)
    unrelated_ids: list[str] = []
    for element in root.iter():
        element_id = element.get("id")
        if (
            element_id is not None
            and element_id != ANCHOR_GROUP_ID
            and not ANCHOR_ID.fullmatch(element_id)
        ):
            unrelated_ids.append(element_id)
    assert unrelated_ids, "fixture must retain an unrelated geometry id"
    _anchor_circles(root)


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
                    f"forbidden attribute {attribute_name!r} in {path}"
                )
                if attribute_name in {"fill", "stroke"}:
                    assert value in ALLOWED_COLOR_VALUES, f"non-themeable color in {path}"


def test_realistic_process_roles_are_covered_by_basic_pack() -> None:
    # The basic pack covers *symbol roles*, which the renderer resolves from
    # engineering functions through its default presentation policy (ADR-0009)
    # plus the explicit PS-vessel override used for the committed diagram.
    resolved_roles_by_step = {
        "PS-feed": "source",
        "PS-mix": "mixing",
        "PS-pump": "pump",
        "PS-hx": "heat_exchanger",
        "PS-split": "splitting",
        "PS-vessel": "vessel",  # explicit presentation override, not a function
        "PS-consumer": "sink",
    }
    symbol_ids = {path.stem for path in _symbol_paths()}
    assert set(resolved_roles_by_step.values()) <= symbol_ids

    # The semantic model itself stores engineering functions, never roles.
    model = load_plant(REALISTIC_EXAMPLE)
    assert model.process is not None
    assert {step.function for step in model.process.steps} == {
        "source",
        "mixing",
        "pumping",
        "heat_exchange",
        "splitting_material",
        "unspecified",
        "sink",
    }
