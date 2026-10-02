---
type: evidence
status: historical
canonical_for:
  - dexpi-2-plant-pid-presentation-and-graphics-evidence
read_when:
  - interoperability-work
  - dexpi-version-pinning
  - presentation-boundary-work
  - renderer-work
update_when:
  - dexpi-model-change
  - presentation-contract-change
  - adapter-change
depends_on: []
decision: []
evidence: []
superseded_by: null
---

# DEXPI 2.x Plant / P&ID Presentation and Graphics Evidence

## Outcome card

- **Question investigated:** what does DEXPI Plant/P&ID evidence show about
  diagram/graphics constructs, and where do those constructs belong relative to
  DeepPlant semantics?
- **Status:** historical evidence (investigation complete; no persistent view or
  P&ID rendering design is authorized or implemented).
- **Inspection scope and date:** official DEXPI `V2.0.0` Core/Diagram and
  Plant/Diagram definitions plus the official Reference P&ID instance, inspected
  2026-09-21 — the same inspection whose shared release pin, sources, and method
  are recorded in the sibling
  [physical semantic-boundary evidence](plant-pid-semantic-boundary.md#1-targeted-dexpi-release-pinned).
- **Conclusions:**
  1. DEXPI diagram/graphics constructs are **presentation concerns** and do not
     become canonical engineering semantics merely because DEXPI contains them.
  2. Coordinates, graphical representation, labels, shape usage, and drawing
     metadata stay separate from the conceptual engineering objects.
  3. A future importer must decide explicitly how to handle drawing data outside
     the semantic model; this evidence neither selects that behaviour nor designs
     persistent views.
- **Resulting ADRs:** ADR-0003 (the semantic/presentation boundary this evidence
  independently corroborates); ADR-0010 recorded the Plant/P&ID consequence.
- **Current contracts operationalizing the result:**
  [contracts/rendering.md](../../../contracts/rendering.md) and
  [dev/reference/svg-symbols.md](../../reference/svg-symbols.md) own presentation
  today; no Plant/P&ID presentation contract exists.
- **Conditions for revisiting:** a concrete renderer, import, or persistent-view
  requirement with separately scoped evidence.

> This document is the presentation/graphics part of the former monolithic DEXPI
> Plant/P&ID semantic-mapping spike (Issue #19), decomposed by durable
> responsibility. It records only what the inspected evidence shows about
> diagram/graphics constructs and where that evidence places the boundary; it
> changes no renderer, designs no persistent view, and implements no P&ID
> rendering.
>
> The shared DEXPI release pin, inspected-source inventory, evidence levels, and
> methodology are recorded once in the sibling
> [physical semantic-boundary evidence](plant-pid-semantic-boundary.md#1-targeted-dexpi-release-pinned)
> and are not duplicated here. Section numbering follows the original spike, so
> this document is that spike's §10.

## 10. Presentation and graphics

*(confirmed by model/schema; counts confirmed by official instance)*

DEXPI keeps graphics out of the conceptual objects and inside the same document:

```text
Core.EngineeringModel.Diagram         → Core.Diagram.Diagram
Core.EngineeringModel.ShapeCatalogues → Core.Diagram.ShapeCatalogue (composes Shape)
Core.ConceptualModel.MetaData         → Core.Diagram.MetaData

Core.Diagram.*  primitives and representation:
    GraphicalElement, GraphicalPrimitive, NodePosition, Point, Color, Stroke,
    Ellipse, EllipseArc, Polygon, PolyLine, Text, TextTemplate,
    AttributeRepresentation, ConnectorLine, GraphicsGroup, RepresentationGroup,
    Border, Static, Label, LiteralText, Symbol (→ PipeFlowArrow,
    PipeSlopeSymbol, InsulationSymbol, CustomSymbol), Shape, ShapeUsage

Core.Diagram.ShapeUsage       (an element of a RepresentationGroup)
    IsMirrored (Boolean, required), Position (Point, required),
    Rotation, ScaleX, ScaleY, Shape (reference, required)

Plant.Diagram.*  plant-layer labels and positions:
    EquipmentBarLabel, EquipmentTagNameLabel, NozzleStandardLabel, FittingLabel,
    SafetyValveOrFittingLabel, PipingClassBreakLabel, PipingNodePosition
        (superTypes DIAGRAM.NodePosition; reference property Node → Piping.PipingNode),
    ProcessInstrumentationFunctionLabel, SignalConveyingFunctionLabel, ValveLabel,
    ActuatingSystemNumberLabel, InsulationLabel, PipingNetworkSystemLabel,
    PipingNetworkSegmentLabel, FailActionLabel, ReducerLabel,
    InstrumentationNodePosition, SignalHigh*/SignalLow*Label, SafetyRelevanceLabel,
    PlantMetaData, CustomLabel, OffPageConnector*Label, NoteIdentifierLabel…
```

Structural facts:

- **No geometry, position, colour, or label lives on the conceptual classes.**
  `Nozzle`, `Pipe`, `PipingNetworkSegment`, `CentrifugalPump`, and
  `ProcessInstrumentationFunction` have no coordinate or symbol properties.
  Position belongs to `ShapeUsage`/`NodePosition`; labels are `Diagram.Label`
  subclasses.
- `PipingNodePosition` is a `DIAGRAM.NodePosition` that **references** a semantic
  `PipingNode`: the graphical position is a separate object pointing at the
  semantic object, not a field on it.
- `PlantMetaData` (block name/number, creator, revision, confidentiality…) is a
  **`Core.Diagram`** construct reachable through `Core.ConceptualModel.MetaData`.
  It is drawing metadata, not plant data.
- The official instance is dominated by graphics objects alongside the semantic
  ones: 954 `Core/Diagram.Point`, 486 `Color`, 245 `Text`, 190 `PolyLine`,
  185 `RepresentationGroup`, 62 `ShapeUsage`, 65
  `Plant/Diagram.PipingNodePosition`, 19 `Plant/Diagram.NozzleStandardLabel`,
  8 `ValveLabel`, 5 `EquipmentBarLabel`, 8 `PipeFlowArrow`, 35 `ConnectorLine`.

**Finding G1.** DEXPI's own information model **independently corroborates
ADR-0003**. A standard designed for P&ID exchange separates `ConceptualModel`
from `Diagram`, keeps engineering objects free of coordinates and symbols, and
places drawing metadata in the graphical layer. DeepPlant's stricter file-level
separation (no graphics at all in semantic YAML) is a superset of the same
boundary, not a deviation from the domain.

**Finding G2.** DEXPI has no presentation construct that DeepPlant must treat as
semantic. `NozzleStandardLabel` exists because the *drawing* labels a nozzle; it
carries no engineering meaning DeepPlant would have to store. Likewise
`ShapeCatalogue`/`Shape` (with `SymbolRegistrationNumber`) is asset cataloguing —
the concern DeepPlant already handles as symbol packs with provenance
([dev/reference/svg-symbols.md](../../reference/svg-symbols.md), ADR-0007/ADR-0008), not as model data.

**Finding G3.** `PlantMetaData` is the expected home of drawing-level facts in an
imported file. A future importer must decide explicitly whether to discard it
(lossy, documented) or surface it outside the semantic model; it must not become
a `PlantModel` field.

## 11. Concept classification matrix (presentation rows)

Legend — "New semantic concept required?": **not now** = evidence recorded, no implementation authorized; **candidate** = evidence-justified future canonical concept in a distinct layer; **no** = not a canonical concern.

Rows decomposed from the former mixed matrix. The physical and instrumentation
rows are owned by
[plant-pid-semantic-boundary.md](plant-pid-semantic-boundary.md) and
[plant-pid-instrumentation.md](plant-pid-instrumentation.md).

| DEXPI Plant/P&ID concept | Current DeepPlant concept? | New semantic concept required? | Adapter-only? | Presentation-only? |
|---|---|---|---|---|
| `Core.Diagram.*` primitives, `ShapeUsage`, `ShapeCatalogue` | – | no | no | **yes** |
| `Plant/Diagram.*` labels, `PipingNodePosition`, `InstrumentationNodePosition`, `PlantMetaData` | – | no | no | **yes** |

### Validity limits

The shared release pin, source list, evidence levels, and general validity limits
of this investigation are recorded in the sibling
[physical semantic-boundary evidence](plant-pid-semantic-boundary.md#13-evidence-gaps-and-threats-to-validity)
and are not restated here. Specific to this evidence: the graphics counts and
label classes come from the single official `V2.0.0` Reference P&ID instance, so
they establish a semantic/presentation boundary rather than a complete catalogue
of DEXPI diagram constructs. No DeepPlant view model, persistent layout, or P&ID
renderer is designed or authorized here.

