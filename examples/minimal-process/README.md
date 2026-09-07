# examples/minimal-process

The first executable DeepPlant semantic model: a small, deliberately minimal
process fragment written as YAML and loadable by the DeepPlant CLI. It drives the
first semantic topology slice: equipment owns named ports, and a top-level
connection references two of those ports.

```yaml
plant:
  id: demo
  name: Minimal Process

equipment:
  - id: T-101
    type: tank
    name: Feed Tank
    ports:
      - id: outlet

  - id: P-101
    type: pump
    name: Feed Pump
    ports:
      - id: suction
      - id: discharge

connections:
  - source:
      component: T-101
      port: outlet
    target:
      component: P-101
      port: suction
```

This represents one semantic connection through explicit typed objects:

```text
T-101.outlet
      ↓
  Connection
      ↓
P-101.suction
```

Validate it from the repository root:

```bash
uv run deepplant validate examples/minimal-process/plant.yaml
```

Expected output:

```text
✓ valid DeepPlant model
✓ plant: demo
✓ equipment: 2
✓ ports: 3
✓ connections: 1
```

A connection is semantic topology only: it is not yet a pipe, stream, signal, or
other physical engineering object. Port identity is local to its equipment; the
connection endpoints reference equipment ids and the port ids they own. Invalid
references (an unknown component or a port the component does not own) fail
validation. See [docs/architecture.md](../../docs/architecture.md) and
[docs/roadmap.md](../../docs/roadmap.md).
