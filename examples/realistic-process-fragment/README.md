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
- **Not every Equipment appears as a ProcessStep.** `FV-101` (recycle flow
  control valve) is a physical inline item that is transparent at this PFD
  abstraction and therefore has no process step.
- **Recycle is an ordinary cycle.** S-002 returns from `PS-vessel` to `PS-mix`;
  no recycle-specific stream kind, flag, or metadata is used.
- **Mixing and splitting are explicit `ProcessStep`s** (2 in → 1 out and
  1 in → 2 out respectively) rather than implicit shared-port branching.

The physical layer contains `T-101`, `P-101`, `FV-101`, `E-101`, and `V-101`
with ports and a few partial connections. It is intentionally **not** a
physical piping model: physical mixing/splitting tees, routing downstream of
`FV-101.outlet`, nozzles, and the second `E-101` side are not modeled, and no
`ProcessStream ↔ piping` mapping is implied. This fixture exists to validate
the semantic model, not to hide those open questions.

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
✓ connections: 4
```

See [docs/roadmap.md](../../docs/roadmap.md) and
[docs/architecture.md](../../docs/architecture.md).
