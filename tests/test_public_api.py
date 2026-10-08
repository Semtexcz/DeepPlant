"""Compatibility evidence for the public Python import surfaces (Issue #106).

The Python structural refactor reorganized several core modules into
capability packages. These tests protect the *public* import contracts that must
survive that reorganization: the package-level surfaces
(``deepplant``, ``deepplant.model``, ``deepplant.render``,
``deepplant.adapters.dexpi``), the declared ``__all__`` of each, and the identity
of the re-exported objects. They deliberately assert nothing about the internal
module layout, so a further internal move stays green as long as the public
surface is intact.
"""

from __future__ import annotations

import deepplant
import deepplant.adapters.dexpi
import deepplant.model
import deepplant.render
import deepplant.symbols


def test_model_package_reexports_its_public_surface() -> None:
    expected = {
        "Connection",
        "Equipment",
        "PipingLine",
        "PipingModel",
        "PipingRealization",
        "PipingSegment",
        "Plant",
        "PlantModel",
        "Port",
        "PortRef",
        "ProcessModel",
        "ProcessPort",
        "ProcessRef",
        "ProcessStep",
        "ProcessStream",
    }
    assert set(deepplant.model.__all__) == expected
    for name in expected:
        # The submodel objects are the same objects the top level re-exports.
        assert getattr(deepplant.model, name) is getattr(deepplant, name)


def test_render_package_reexports_its_public_surface() -> None:
    expected = {
        "ProcessPfdAnchor",
        "ProcessPfdLayout",
        "ProcessPfdStepPlacement",
        "ProcessPfdStreamPlacement",
        "ProcessRenderError",
        "compute_process_pfd_layout",
        "read_process_symbol_svg",
        "render_process_svg",
    }
    assert set(deepplant.render.__all__) == expected
    assert deepplant.render.render_process_svg is deepplant.render_process_svg
    assert deepplant.render.ProcessRenderError is deepplant.ProcessRenderError


def test_symbol_library_reexports_its_public_surface() -> None:
    expected = {
        "CANONICAL_VIEW_BOX",
        "SYMBOLS",
        "AssetProvenance",
        "Circle",
        "Line",
        "Polygon",
        "StandardsReference",
        "SymbolAnchor",
        "SymbolDefinition",
        "SymbolDefinitionError",
        "SymbolRegistry",
        "render_symbol_svg",
    }
    assert set(deepplant.symbols.__all__) == expected
    for name in expected:
        assert hasattr(deepplant.symbols, name)


def test_dexpi_adapter_reexports_its_public_surface() -> None:
    expected = {
        "DEXPI_CORE_MODEL_URI",
        "DEXPI_INSPECTION_DATE",
        "DEXPI_LICENCE",
        "DEXPI_PROCESS_MODEL_URI",
        "DEXPI_SOURCE_URL",
        "DEXPI_TARGET_REVISION",
        "DEXPI_TARGET_TAG",
        "DEXPI_TARGET_VERSION",
        "DexpiExportError",
        "DexpiImportError",
        "export_dexpi_process",
        "import_dexpi_process",
        "import_dexpi_process_xml",
        "validate_dexpi_xml_structure",
    }
    assert set(deepplant.adapters.dexpi.__all__) == expected
    for name in expected:
        assert hasattr(deepplant.adapters.dexpi, name)


def test_deepplant_top_level_public_surface_is_unchanged() -> None:
    assert set(deepplant.__all__) == {
        "__version__",
        "Connection",
        "Equipment",
        "PipingLine",
        "PipingModel",
        "PipingRealization",
        "PipingSegment",
        "Plant",
        "PlantLoadError",
        "PlantModel",
        "PlantSaveError",
        "Port",
        "PortRef",
        "ProcessModel",
        "ProcessPort",
        "ProcessRef",
        "ProcessRenderError",
        "ProcessStep",
        "ProcessStream",
        "load_plant",
        "render_process_svg",
        "save_plant",
    }
