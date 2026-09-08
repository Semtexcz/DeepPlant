# examples/process-graph

A small synthetic example proving the root/loadable process-model integration:
a real process graph (`FEED -> PUMP -> PRODUCT`) authored as YAML and loaded by
`load_plant()` through `PlantModel.process`.

```text
FEED.out
   ↓ S-001
PUMP.suction → PUMP.discharge
   ↓ S-002
PRODUCT.in
```

The process graph lives in the YAML `process` section and owns its identity
through the S1–S4 rules on `ProcessModel`. The physical layer is deliberately
empty (`equipment: []`, `connections: []`) in this example: a process step id
(`PUMP`) carries no implied relationship to any `Equipment` id of the same
string, and mixing/splitting or boundary steps stay valid without a physical
realization (ADR-0005). Cross-layer mappings and consistency validation are not
implemented.

Validate it from the repository root:

```bash
uv run deepplant validate examples/process-graph/plant.yaml
```

Expected output (the CLI reports only the physical/topology layer; the process
graph loads and validates but is not yet counted by the CLI):

```text
✓ valid DeepPlant model
✓ plant: demo
✓ equipment: 0
✓ ports: 0
✓ connections: 0
```

See [docs/roadmap.md](../../docs/roadmap.md) and
[docs/architecture.md](../../docs/architecture.md).
