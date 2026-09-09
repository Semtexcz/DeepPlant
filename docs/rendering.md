---
type: rendering
status: active
source_of_truth_for:
  - headless-process-renderer
read_when:
  - renderer-implementation
  - presentation-work
update_when:
  - renderer-behavior-change
  - renderer-api-change
  - layout-heuristic-change
---

# Basic Headless Process Renderer

`deepplant.render` renders a semantic [`ProcessModel`](architecture.md) into a
complete standalone SVG process/PFD diagram. It is the first end-to-end
presentation slice:

```text
YAML
→ PlantModel
→ ProcessModel
→ ProcessStep.function → presentation policy → symbol roles
→ basic symbol pack
→ layout
→ anchor assignment
→ stream routing
→ standalone SVG
```

This is **not** frontend work: no HTML, JavaScript, Vue/React, canvas
libraries, browser runtime, drag/drop, zoom/pan, or manual diagram editing.

## Purpose

The renderer proves that the semantic `ProcessModel`, the pack-aware SVG
symbol contract ([svg-symbols.md](svg-symbols.md), ADR-0008), and
`ProcessStream` topology are sufficient to generate a readable standalone
process diagram. It is deliberately small and deterministic; it is not a
general automatic diagramming tool.

## Public API

```python
from deepplant import render_process_svg, ProcessRenderError

svg: str = render_process_svg(
    model.process,
    symbol_pack="basic",
    symbol_role_overrides={"PS-vessel": "vessel"},  # optional, transient
)
```

- Returns a complete standalone SVG document (valid XML/SVG, deterministic
  viewBox, `currentColor` engineering line style, UTF-8-safe text, trailing
  newline, no external resources).
- Repeated rendering of the same `ProcessModel` is byte-for-byte identical.
- `symbol_role_overrides` is an optional read-only mapping keyed by
  `ProcessStep.id`; each value is the presentation symbol role to draw for
  that step in this render call. It is a transient presentation override (ADR
  -0009): it exists only at the rendering boundary and is never stored on the
  semantic model, in YAML, or in a view file.
- `ProcessRenderError(ValueError)` is raised for an unknown pack, a step whose
  engineering function has no resolvable symbol role (and no override supplies
  one), an invalid override (unknown step id, blank or non-filename-safe role,
  role missing from the selected pack), a broken pack asset/anchor contract, or
  a step whose stream incidence exceeds the pack variant's anchor capacity.
- No CLI command and no file-saving helper exist yet.

## Symbol-role resolution (presentation policy)

Symbol roles are presentation semantics, not canonical engineering data
(ADR-0009). For each step the renderer resolves one role with this
deterministic precedence:

1. an explicit `symbol_role_overrides[step.id]` entry;
2. the renderer's default `ProcessStep.function` -> symbol-role policy:
   `source → source`, `sink → sink`, `mixing → mixing`,
   `splitting_material → splitting`, `pumping → pump`,
   `heat_exchange → heat_exchanger`;
3. otherwise a `ProcessRenderError` naming the step id, the engineering
   function, the selected symbol pack, and the missing presentation policy.

`unspecified` is a legal engineering function (semantic uncertainty) but has
no default role; without an explicit override its rendering is a presentation
error, not a semantic-model error. The realistic fragment's `PS-vessel` uses
exactly this: semantic `function: unspecified` + a per-step override to the
`vessel` symbol role.

## ProcessModel-only scope

The input domain is `ProcessModel` → `ProcessStep[]` (each owning
`ProcessPort[]`) + `ProcessStream[]`. The renderer never reads `Equipment`,
`Port`, `Connection`, valves, nozzles, pipes, instruments, or signals.
`FV-101` (physical, no `ProcessStep`) therefore stays out of the generated
process diagram, and no process↔physical mappings exist.

## Pack-aware lookup and runtime packaging

The renderer resolves each step's **symbol role** from its engineering
function (see "Symbol-role resolution" above; ADR-0009) — a role is never read
directly from the semantic model. The renderer then selects the explicitly
requested **symbol pack** and reads that pack's `<role>.svg` asset plus its
ordered `anchor-in-N` / `anchor-out-N` slots. Only the built-in `basic` pack is
supported in this first implementation; unknown packs fail loudly instead of
silently substituting a different symbol.

The canonical asset copy ships inside the installed package
(`src/deepplant/assets/symbols/process/basic/`) and is resolved at runtime
through `importlib.resources`, so the renderer works from a source checkout
and from an installed wheel. The built wheel is verified to contain the
`basic` pack SVGs (a CI packaging check after `make check`). There is no
plugin/entry-point/pack-registry framework yet.

At runtime the renderer validates the contract invariants it relies on before
composing a diagram: the asset has an SVG root, the canonical
`viewBox="0 0 100 100"`, no fixed `width`/`height`, exactly one
`deepplant-anchors` group, and every anchor has a unique `anchor-in-N` /
`anchor-out-N` id with numeric coordinates inside the local viewBox and
contiguous indices per direction. Anchor order is defined by the numeric
anchor id, never by XML child order. Visible geometry may use any top-level
element the symbol contract permits (`g`, `path`, `line`, `polyline`,
`polygon`, `rect`, `circle`, `ellipse`); the anchors group is removed and all
other permitted top-level geometry is treated as visible symbol content.

Pack-local geometry is copied into the composed document with duplicate-prone
`id` attributes removed (the safe symbol contract forbids functional
internal/external references, so dropping ids is safe). The composed diagram
carries machine-readable debug/test attributes such as
`data-deepplant-step="PS-pump"` and `data-deepplant-stream="S-004"`; semantic
ids are never required to be valid XML ids.

## Anchor assignment

Input/output role is derived from topology: `stream.target` → incoming,
`stream.source` → outgoing. No `ProcessPort.direction` exists on the semantic
model. For each step, incoming and outgoing streams are sorted by
`(semantic port declaration order, stream id)` and mapped deterministically
onto `anchor-in-N` / `anchor-out-N`. Multiple streams may legally share one
`ProcessPort`; the stream-id tie-breaker keeps such cases stable.

## Layout heuristic

A deliberately simple deterministic layered layout runs entirely inside the
renderer; no coordinates are ever written back into YAML or Pydantic models.

1. A deterministic iterative DFS classifies feedback (back) edges. It first
   starts from every step with zero total incoming `ProcessStream` incidence
   (in declaration order), then starts any remaining unvisited steps in
   declaration order. Incoming incidence is semantic and computed before
   classification, so a back edge never makes a downstream node look like a
   root. It visits outgoing streams in stable `(port order, stream id)` order
   and marks a stream whose target is still on the DFS stack as a back edge.
2. The remaining forward graph is acyclic. A heap-based topological pass
   assigns each step to a **layer (column)** by longest forward path, so
   normal process progression reads left-to-right. Within one layer, rows are
   ordered from each step's incoming forward connections where available:
   upstream row, upstream output-port order, then stream id; target
   declaration order and step id are deterministic fallbacks. This preserves
   the branch order implied by upstream output ports/anchors (so the first
   split output targets the upper row) without claiming optimal crossing
   minimisation.
3. Each symbol canvas occupies a deterministic grid cell. Layout constants
   (gaps, margins, lane spacing, label offsets) are renderer-internal
   presentation geometry.

This heuristic is intentionally not a general optimal graph-layout algorithm.

## Stream routing heuristic

Ordinary forward streams use orthogonal routes (`horizontal → vertical →
horizontal`); adjacent same-row steps get a straight line. Bends run only in
the empty gutters between symbol columns. Streams spanning more than one
column travel on a horizontal "street" below the endpoint rows so they do not
pass through intermediate symbols. No collision-avoidance optimisation or
routing search exists; line crossings between streams are allowed.

Feedback streams (recycle) are distinguished **geometrically**, never by a
semantic kind: they leave the source output anchor to the right, drop to a
dedicated return lane below all steps and labels, run left, rise in the gutter
left of the target, and enter the target input anchor. Multiple feedback
streams get separate lanes in a stable order
(`(source step declaration order, source port order, stream id)`).

Direction is shown with small self-contained arrowhead polygons at every
stream target (no `<marker>`, no external CSS).

## Labels

Every step shows its `ProcessStep.id` (bold) and, when present, its
`ProcessStep.name` below the symbol. Every stream shows its `ProcessStream.id`
near its longest horizontal run. Stream names are currently omitted to keep
the MVP readable; physical equipment tags are never invented.

## Known limitations and visual status

- The `basic` glyphs are non-normative fallback geometry; the full fragment
  exposes their proportions for later improvement (e.g. mixing/splitting
  apex geometry, pump/hx/vessel strokes).
- Rows/columns are not balanced across layers; long or dense graphs can
  produce empty space, stream crossings, and bus-line overlaps.
- Labels use a single generic sans-serif without collision detection; long
  names can reach into nearby gutters.
- Feedback lanes are always drawn below the diagram; a feedback edge among
  late columns can look long.
- Streams never pass through symbols by construction of the routing, but no
  crossing minimisation is attempted.
- Layout/routing constants are heuristic and may change without an ADR.

## Explicitly deferred

Frontend/interactive viewing, manual positioning, saved diagram coordinates,
zoom/pan, multiple sheets, title blocks, physical/P&ID rendering, standards
aligned or company packs, custom pack loading, DEXPI graphics, simulation,
routing optimisation/crossing minimisation, automatic standards compliance,
and any persistence of presentation data in the semantic model. **Persistent
presentation configuration is deferred**: the renderer's per-call
`symbol_role_overrides` establishes the presentation boundary as executable
evidence; a future slice may persist per-step view configuration separately
from semantic YAML, without reintroducing the conflation this boundary removes
(ADR-0009).

## Related

- [svg-symbols.md](svg-symbols.md) — the SVG + anchor contract consumed here.
- [architecture.md](architecture.md) — current architecture.
- [roadmap.md](roadmap.md) — slice sequence.
- [ADR-0003](decisions/ADR-0003-separate-semantic-and-presentation-models.md),
  [ADR-0008](decisions/ADR-0008-process-svg-symbol-and-anchor-contract.md),
  [ADR-0009](decisions/ADR-0009-separate-process-function-from-symbol-role.md).

