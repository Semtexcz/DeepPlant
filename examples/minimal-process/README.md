# examples/minimal-process

The first executable DeepPlant semantic model: a small, deliberately minimal
process fragment written as YAML and loadable by the DeepPlant CLI.

```yaml
plant:
  id: demo
  name: Minimal Process

equipment:
  - id: T-101
    type: tank
    name: Feed Tank

  - id: P-101
    type: pump
    name: Feed Pump
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
```

The example drives the minimal domain model only: `PlantModel -> Plant` plus
`list[Equipment]`. Fields are limited to what this fragment needs. Ports,
connections, and a full equipment taxonomy are deliberately out of scope for
now; see [docs/roadmap.md](../../docs/roadmap.md).

