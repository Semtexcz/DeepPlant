---
type: guidance
status: active
canonical_for:
  - authoring-plant-yaml
read_when:
  - authoring-plant-yaml
  - using-deepplant
update_when:
  - yaml-format-change
  - user-documentation-change
depends_on:
  - docs/contracts/yaml-format.md
  - docs/contracts/plant-model.md
  - docs/contracts/process-model.md
  - docs/contracts/physical-piping.md
decision: []
evidence: []
superseded_by: null
---

# Author a Plant Model as YAML

> **Question this page answers:** how do I write a DeepPlant model file that
> validates?

A DeepPlant model is one YAML file. This page covers the workflow and the shape
you need most often. The exact field rules stay in the contracts linked at the
end.

## The smallest model

`examples/minimal-process/plant.yaml` is the smallest complete model:

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
  - id: C-001
    source:
      component: T-101
      port: outlet
    target:
      component: P-101
      port: suction
```

## What the pieces mean

- **`plant`** — the root object. `id` is required, `name` is optional.
- **`equipment`** — the physical inventory. Each item has an `id`, a `type` (any
  non-empty string; there is no fixed equipment taxonomy), an optional `name`,
  and its own `ports`.
- **`ports`** — named connection points that **belong to their equipment**. Port
  ids are local to the equipment that owns them, so `T-101.suction` and
  `P-101.suction` are different points.
- **`connections`** — directed adjacency between two ports. Each connection needs
  its own `id` and references a `component` (an equipment id) plus a `port` that
  the component actually owns.

```text
T-101.outlet  ──Connection C-001──▶  P-101.suction
```

## Rules that matter while authoring

- **Ids are authored and stable.** Nothing is generated from list position, so you
  can insert a new item anywhere and Git shows only the added lines. Reusing an
  `equipment` or `connection` id, or repeating a port id on the same equipment, is
  an error.
- **Ports belong to equipment.** A connection cannot reference a port on another
  item, and cannot reference a port that does not exist.
- **Unknown fields fail.** Every model forbids extra fields, so a typo becomes a
  validation error instead of silently ignored data.
- **Blank values fail.** Ids, types, and references must be non-empty.
- **`process` and `piping` are optional.** A model with only `plant`, `equipment`,
  and `connections` is complete.

## Optional submodels

Two optional top-level keys extend the same file:

- **`process`** — the process graph: `steps` (each with an engineering `function`
  and ports) and `streams` between step ports. `process: {}` is valid and means an
  explicitly empty process model.
- **`piping`** — physical piping realization: `lines` containing `segments`, each
  listing `realizations` that reference existing `connection` ids. Piping
  references connections; it never restates endpoints.

Add them only when you actually have the data. The
[realistic process fragment](../../../examples/realistic-process-fragment/plant.yaml)
shows both in use.

## Workflow

1. Copy the smallest example and edit it.
2. Validate as you go (see [validate-a-model.md](validate-a-model.md)):

   ```bash
   uv run deepplant validate path/to/plant.yaml
   ```

3. If validation fails, read the file path, the field location, and the reason —
   [diagnose-validation-errors.md](diagnose-validation-errors.md).
4. Commit the file. Ids stay stable, so diffs stay readable.

## Where the exact rules live

This page cannot stay authoritative on field-level rules, and it does not try.
Use the contracts:

- [yaml-format.md](../../contracts/yaml-format.md) — document shape, load/save
  guarantees, and error messages
- [plant-model.md](../../contracts/plant-model.md) — `Plant`, `Equipment`, `Port`,
  `Connection`
- [process-model.md](../../contracts/process-model.md) — `ProcessStep`,
  `ProcessStream`
- [physical-piping.md](../../contracts/physical-piping.md) — piping lines,
  segments, realizations

There is no schema-version field, no JSON format, no auto-formatting command, and
no migration tooling.
