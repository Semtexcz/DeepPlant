# examples/realistic-process-fragment

A **synthetic** process fragment, written as public YAML and loaded through the
production semantic model. It encodes the realistic fragment documented in
[docs/process-fragment-prototype.md](../../docs/process-fragment-prototype.md)
to prove the current model can represent fresh feed, mixing, a pump, a heat
exchanger, splitting, a vessel, a downstream boundary, and recycle — without
inventing schema to make the fixture fit.

Process topology:

```text
                                     ┌──→ downstream consumer
                                     │
PS-feed ── S-001 ──→ PS-mix ── S-003 ──→ PS-pump ── S-004 ──→ PS-hx ── S-005 ──→ PS-split
                      ↑                                                            │
                      └─────────────────── S-002 recycle ◀─── PS-vessel ◀── S-006 ──┘
```

Concretely (process layer):

| Stream | Source | Target |
|---|---|---|
| S-001 fresh feed | `PS-feed.out_feed` | `PS-mix.in_fresh` |
| S-002 recycle | `PS-vessel.out_recycle` | `PS-mix.in_recycle` |
| S-003 mixed feed | `PS-mix.out_mixed` | `PS-pump.suction` |
| S-004 pump discharge | `PS-pump.discharge` | `PS-hx.in_side_A` |
| S-005 exchanger outlet | `PS-hx.out_side_A` | `PS-split.in` |
| S-006 vessel feed | `PS-split.out_vessel` | `PS-vessel.in` |
| S-007 branch | `PS-split.out_branch` | `PS-consumer.in` |

## What this example demonstrates

- The production boundary works end to end:
  `YAML → load_plant() → PlantModel → ProcessModel` and back through the
  canonical serializer (`save_plant()`).
- **Process and physical layers are intentionally distinct.** The process graph
  (`ProcessStep` / `ProcessPort` / `ProcessStream`) and the physical bootstrap
  layer (`Equipment` / `Port` / `Connection`) are each independently valid.
  No `ProcessStep ↔ Equipment` mapping, no `ProcessPort ↔ Port` mapping, and no
  `ProcessStream ↔ Connection` mapping exists; ids in the two namespaces imply
  nothing about each other.
- **Not every ProcessStep maps to Equipment.** `PS-mix` and `PS-split` are
  process functions (mixing and splitting) with no required physical equipment
  counterpart at this PFD abstraction.
- **Not every Equipment appears as a ProcessStep.** `FV-101` is a physical
  flow control valve on the pump discharge, between `P-101` and `E-101`. It is
  transparent at this PFD abstraction and therefore has no process step.
- **Recycle is an ordinary cycle.** S-002 returns from `PS-vessel` to `PS-mix`;
  no recycle-specific stream kind, flag, or metadata is used.
- **Mixing and splitting are explicit `ProcessStep`s** (2 in → 1 out and
  1 in → 2 out respectively) rather than implicit shared-port branching.

The physical/bootstrap layer contains `T-101`, `P-101`, `FV-101`, `E-101`, and
`V-101`. Its `Connection`s represent only physical relationships that are
genuinely direct and known. The only represented physical chain is:

```text
P-101.discharge → FV-101.inlet
FV-101.outlet   → E-101.process_inlet
```

These real physical paths are intentionally **not** represented as direct
`Connection`s, because the physical tees / piping realization does not yet
exist in the production model:

```text
T-101 → mixing point → P-101
E-101 → splitting point → V-101
V-101 → recycle piping → mixing point
```

For this fixture, **absence of `Connection` ≠ absence of real physical
connectivity**. The physical graph is deliberately incomplete, not
approximately continuous. `V-101.recycle_outlet` is therefore unconnected in
the bootstrap graph (the mixing tee / recycle-piping realization is not
modeled), while the recycle itself is fully represented in the process layer as
`S-002`. This fixture exists to validate the semantic model, not to hide the
open physical-piping questions.

Validate it from the repository root:

```bash
uv run deepplant validate examples/realistic-process-fragment/plant.yaml
```

Expected output (the CLI reports the physical/bootstrap layer counts):

```text
✓ valid DeepPlant model
✓ plant: demo
✓ equipment: 5
✓ ports: 9
✓ connections: 2
```

See [docs/roadmap.md](../../docs/roadmap.md) and
[docs/architecture.md](../../docs/architecture.md).

## Generated process diagram

[`process.svg`](process.svg) is a **generated artifact** produced by the basic
headless read-only process renderer from the process layer of this example. It
is committed so pull requests can review the visual result of a semantic
change, and a determinism/golden test
([`tests/test_render.py`](../../tests/test_render.py)) fails if renderer output
ever drifts from the committed file.

It was generated with the public renderer API (no CLI command exists yet):

```python
from deepplant import load_plant, render_process_svg

model = load_plant("examples/realistic-process-fragment/plant.yaml")
svg = render_process_svg(model.process, symbol_pack="basic")
with open("examples/realistic-process-fragment/process.svg", "w", encoding="utf-8") as handle:
    handle.write(svg)
```

The diagram is derived from the semantic `ProcessModel` only: the physical
bootstrap layer (`T-101`, `P-101`, `FV-101`, `E-101`, `V-101`) is intentionally
absent, mixing/splitting stay explicit process functions, and the recycle
(`S-002`) renders on a dedicated return lane below the process without any
recycle-specific semantic kind. See [docs/rendering.md](../../docs/rendering.md)
for the layout/routing heuristics and their limitations.

