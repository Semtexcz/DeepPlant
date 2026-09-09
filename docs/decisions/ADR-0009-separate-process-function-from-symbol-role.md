# ADR-0009: Separate Process Function from Presentation Symbol Role

> Status: Accepted
> Date: 2026-09-09

## Context

The DEXPI 2.x Process adapter spike
([docs/dexpi-process-spike.md](../dexpi-process-spike.md)) proved a canonical
model correction with executable evidence: `ProcessStep.type` conflated two
concepts. It was used as both the canonical engineering classification of a
step and the presentation symbol role consumed by the renderer and the `basic`
symbol pack (ADR-0008). DEXPI ProcessStep classes are engineering functions,
but DeepPlant's `type` values (`pump`, `heat_exchanger`, `vessel`, …) were
presentation roles. As a result `heat_exchanger` and `vessel` had no honest
DEXPI mapping or export, reverse `pumping` could not be asserted, and the
realistic fragment had to call its vessel step a "Process Vessel" — a
physical/presentation description — without evidence of its engineering
function.

The target architecture keeps four concepts distinct:

```text
ProcessStep.function          canonical engineering semantics
        ↓  presentation policy
symbol role                   presentation category
        ↓  selected symbol pack
pack-local SVG asset
```

## Decision

1. **`ProcessStep.function` is canonical engineering semantics.** It is the
   engineering process function performed by the step (`source`, `sink`,
   `mixing`, `splitting_material`, `pumping`, `heat_exchange`, …). The
   vocabulary is deliberately open and DeepPlant-native; no closed Python Enum
   is introduced.
2. **`ProcessStep.type` is removed.** The breaking pre-1.0 migration is direct
   (`type` → `function`); no alias, `legacy_type`, or second permanent field is
   added. Because semantic models use `extra="forbid"`, stale YAML containing
   `type:` fails explicitly rather than acquiring an ambiguous meaning. No
   migration framework is built.
3. **Function vocabulary is open.** Any non-empty string is legal, including
   `unspecified`, which means: the `ProcessStep` exists semantically but its
   engineering function has not yet been specified.
4. **Symbol role is presentation semantics and is not stored in
   `ProcessStep`.** A function such as `pumping` may be drawn as the symbol
   role `pump` in one pack and differently elsewhere; roles live at the
   rendering boundary.
5. **A default presentation policy may map known engineering functions onto
   symbol roles.** The renderer owns the current default policy
   (`pumping → pump`, `heat_exchange → heat_exchanger`,
   `splitting_material → splitting`, etc.). It is presentation policy, not
   engineering semantics.
6. **Per-step presentation overrides may be supplied to a renderer.** A
   transient, read-only `symbol_role_overrides` mapping (keyed by
   `ProcessStep.id`) exists only for a render call; it is never stored in
   `ProcessStep`, `ProcessModel`, `PlantModel`, or YAML.
7. **Symbol pack realizes symbol role as graphical assets.** The
   role → pack → SVG + anchor contract of ADR-0008 remains in force.
8. **Unknown/unspecified engineering functions remain valid semantic model
   content.** They may require explicit presentation information to render.
9. **Failure to resolve a graphical role is a presentation error, not a
   semantic-model error.** The renderer raises `ProcessRenderError` naming the
   step id, engineering function, selected symbol pack, and reason; it never
   silently falls back to an arbitrary symbol.
10. **Persistent view/presentation configuration is deferred.** No
    `ProcessView`, `PresentationModel`, `view.yaml`, diagram coordinates, or
    presentation database is introduced by this decision; the renderer API
    override is the executable evidence for the boundary. A future slice may
    persist presentation configuration separately from semantic YAML.

DEXPI evidence for this decision is documented in
[docs/dexpi-process-spike.md](../dexpi-process-spike.md): the type-vocabulary
conflation finding (§9), the export-feasibility analysis (§12), and the
resulting reverse `pumping` round-trip are the executable basis.


## Consequences

### Positive

- A `ProcessStep` can state honest engineering semantics without lying to make
  a diagram convenient: the realistic fragment declares
  `PS-vessel` `function: unspecified` while the committed SVG still draws it
  as a `vessel` through an explicit per-step presentation override. Semantic
  uncertainty does not force presentation uncertainty, and drawing a vessel
  does not pretend we know its engineering process function.
- DEXPI import maps DEXPI step classes onto DeepPlant-native functions
  (`Pumping → function="pumping"`,
  `SplittingMaterial → function="splitting_material"`), and reverse export is
  an engineering-classification assertion for the symmetric subset, including
  material-port-only `pumping`.
- Renderer and model are decoupled: a new function does not require a new
  symbol, and a new symbol pack does not change the semantic model.
- A semantic model may be valid but not renderable without additional
  presentation policy. That is desirable: semantic validity
  (`!=` presentation completeness), the same category as the renderer's
  existing missing-anchor/missing-symbol errors.

### Negative

- `type`-based YAML and Python construction break intentionally (pre-1.0
  correction). Renderer callers must now reason about resolved roles rather
  than reading a role from the step.
- Every further step classification must be chosen with the function/role
  distinction in mind; documentation must keep the two vocabularies apart.

## Deferred

- Persistent presentation/view configuration (per-step symbol-role overrides,
  pack selection, saved layout) beyond the renderer-call override.
- A process-function ontology/hierarchy; storage, reaction, separation, and
  other engineering-function families stay open strings until real instances
  provide evidence.
- DEXPI mappings for `heat_exchange`, storage, reaction, and separation
  functions; each requires semantic review before any claim.
- Equipment realization mapping (`ProcessStep != Equipment`): a `pumping`
  function may later be realized by one pump, several pumps, an ejector,
  gravity, or another physical solution.

## Revisit When

A concrete rendering requirement forces persisted per-step presentation
configuration (then design the boundary deliberately, without returning
presentation data to the semantic model), or real engineering instances show
that an open function string is no longer sufficient (then design a
function vocabulary/ontology from that evidence).

## Related

- [ADR-0003-separate-semantic-and-presentation-models.md](ADR-0003-separate-semantic-and-presentation-models.md)
- [ADR-0005-process-model-container.md](ADR-0005-process-model-container.md)
- [ADR-0008-process-svg-symbol-and-anchor-contract.md](ADR-0008-process-svg-symbol-and-anchor-contract.md)
  (partially superseded: only the `ProcessStep.type` → symbol-role coupling;
  the role → pack → SVG + anchor contract remains in force)
- [../svg-symbols.md](../svg-symbols.md), [../rendering.md](../rendering.md),
  [../architecture.md](../architecture.md),
  [../dexpi-process-spike.md](../dexpi-process-spike.md)
