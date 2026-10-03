"""Focused tests for the DeepPlant-owned Process/PFD projection (Issue #75).

The projection is an application/consumer concern: it derives a read-only view
from the semantic ``ProcessModel`` and must keep semantic identity explicit while
keeping framework (Vue Flow) concepts out of the transport shape.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from deepplant import load_plant
from deepplant.editor.projection import (
    KIND_PROCESS_STEP,
    KIND_PROCESS_STREAM,
    ProcessPfdProjection,
    ProcessPfdProjectionError,
    project_process_pfd,
    projection_to_dict,
)
from deepplant.render import ProcessRenderError

REPO_ROOT = Path(__file__).resolve().parents[1]
REALISTIC_EXAMPLE = REPO_ROOT / "examples" / "realistic-process-fragment" / "plant.yaml"

# PS-vessel has engineering function "unspecified" (ADR-0009); the presentation
# boundary supplies its symbol role explicitly, exactly like the committed
# headless diagram. The override is transient and never stored in the model.
VESSEL_OVERRIDES = {"PS-vessel": "vessel"}

EXPECTED_STEP_IDS = [
    "PS-feed",
    "PS-mix",
    "PS-pump",
    "PS-hx",
    "PS-split",
    "PS-vessel",
    "PS-consumer",
]

# stream id -> (source step, source port, target step, target port)
EXPECTED_STREAMS: dict[str, tuple[str, str, str, str]] = {
    "S-001": ("PS-feed", "out_feed", "PS-mix", "in_fresh"),
    "S-002": ("PS-vessel", "out_recycle", "PS-mix", "in_recycle"),
    "S-003": ("PS-mix", "out_mixed", "PS-pump", "suction"),
    "S-004": ("PS-pump", "discharge", "PS-hx", "in_side_A"),
    "S-005": ("PS-hx", "out_side_A", "PS-split", "in"),
    "S-006": ("PS-split", "out_vessel", "PS-vessel", "in"),
    "S-007": ("PS-split", "out_branch", "PS-consumer", "in"),
}

PHYSICAL_IDS = {"T-101", "P-101", "FV-101", "E-101", "V-101"}

# Framework/projection concepts that must never appear in the transport shape.
FORBIDDEN_TRANSPORT_KEYS = {
    "sourceHandle",
    "targetHandle",
    "handle",
    "nodeType",
    "vueFlow",
    "selected",
    "dragging",
    "dimensions",
    "width",
    "height",
}


def _projection() -> ProcessPfdProjection:
    return project_process_pfd(
        load_plant(REALISTIC_EXAMPLE), symbol_role_overrides=VESSEL_OVERRIDES
    )


def _transport_text(payload: dict[str, object]) -> str:
    """JSON text of the transport payload, for framework-key scanning."""
    return json.dumps(payload, ensure_ascii=False)


def test_realistic_fragment_projects_seven_steps_and_seven_streams() -> None:
    projection = _projection()

    assert [step.id for step in projection.steps] == EXPECTED_STEP_IDS
    assert [stream.id for stream in projection.streams] == list(EXPECTED_STREAMS)


def test_projection_carries_explicit_semantic_identity() -> None:
    projection = _projection()

    assert all(step.kind == KIND_PROCESS_STEP for step in projection.steps)
    assert all(stream.kind == KIND_PROCESS_STREAM for stream in projection.streams)
    # Identity is the authored semantic id, never a label, index, or position.
    assert [step.id for step in projection.steps] == EXPECTED_STEP_IDS


def test_stream_endpoints_are_preserved_exactly() -> None:
    projection = _projection()

    actual = {
        stream.id: (
            stream.source.step,
            stream.source.port,
            stream.target.step,
            stream.target.port,
        )
        for stream in projection.streams
    }
    assert actual == EXPECTED_STREAMS


def test_recycle_stream_is_present_and_marked_feedback() -> None:
    projection = _projection()

    recycle = next(stream for stream in projection.streams if stream.id == "S-002")
    assert (recycle.source.step, recycle.target.step) == ("PS-vessel", "PS-mix")
    assert recycle.is_feedback is True
    assert all(stream.is_feedback is False for stream in projection.streams if stream.id != "S-002")


def test_step_semantic_properties_come_from_the_model() -> None:
    projection = _projection()

    pump = next(step for step in projection.steps if step.id == "PS-pump")
    assert pump.function == "pumping"
    assert pump.name == "Feed Pumping"
    assert pump.symbol_role == "pump"
    assert pump.ports == ("suction", "discharge")


def test_ps_vessel_stays_unspecified_while_projected_as_vessel() -> None:
    """Presentation honesty (ADR-0009): the role is resolved, the function is not."""
    projection = _projection()

    vessel = next(step for step in projection.steps if step.id == "PS-vessel")
    assert vessel.function == "unspecified"
    assert vessel.symbol_role == "vessel"
    # The projection never rewrites semantic state to make drawing convenient.
    model = load_plant(REALISTIC_EXAMPLE)
    assert model.process is not None
    semantic_vessel = next(step for step in model.process.steps if step.id == "PS-vessel")
    assert semantic_vessel.function == "unspecified"


def test_unresolvable_function_without_override_fails_honestly() -> None:
    """``unspecified`` has no default role, so it must fail rather than guess."""
    with pytest.raises(ProcessRenderError) as exc_info:
        project_process_pfd(load_plant(REALISTIC_EXAMPLE))

    assert "PS-vessel" in str(exc_info.value)


def test_physical_layer_objects_do_not_leak_into_the_pfd_projection() -> None:
    projection = _projection()
    payload = projection_to_dict(projection)

    step_ids = {step.id for step in projection.steps}
    stream_ids = {stream.id for stream in projection.streams}
    assert step_ids == set(EXPECTED_STEP_IDS)
    assert stream_ids == set(EXPECTED_STREAMS)
    assert step_ids.isdisjoint(PHYSICAL_IDS)
    # No physical topology or piping concept is transported.
    assert {"equipment", "connections", "piping", "ports"}.isdisjoint(payload)


def test_missing_process_model_returns_an_honest_failure(tmp_path: Path) -> None:
    plant_path = tmp_path / "no-process.yaml"
    plant_path.write_text("plant:\n  id: demo\nequipment: []\n", encoding="utf-8")

    with pytest.raises(ProcessPfdProjectionError) as exc_info:
        project_process_pfd(load_plant(plant_path))

    assert "no process model to project" in str(exc_info.value)


def test_transport_shape_is_deepplant_owned_and_framework_free() -> None:
    payload = projection_to_dict(_projection())
    text = _transport_text(payload)

    assert "steps" in payload
    assert "streams" in payload
    assert "validation" in payload
    assert '"kind": "process-step"' in text
    assert '"kind": "process-stream"' in text
    # No framework-only concept is transported; those belong to the adapter.
    for forbidden in sorted(FORBIDDEN_TRANSPORT_KEYS):
        assert f'"{forbidden}"' not in text


def test_projection_is_deterministic() -> None:
    first = projection_to_dict(_projection())
    second = projection_to_dict(_projection())

    assert first == second


def test_step_anchors_reflect_the_canonical_pack_slots() -> None:
    projection = _projection()

    mixing = next(step for step in projection.steps if step.id == "PS-mix")
    assert [anchor.index for anchor in mixing.in_anchors] == [0, 1]
    assert [anchor.index for anchor in mixing.out_anchors] == [0]
    # Anchors live on the canonical 100x100 pack viewBox.
    assert all(anchor.x in {0.0, projection.symbol_size} for anchor in mixing.in_anchors)
    assert all(anchor.x in {0.0, projection.symbol_size} for anchor in mixing.out_anchors)
