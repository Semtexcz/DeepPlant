---
type: architecture
status: draft
source_of_truth_for:
  - current-architecture
read_when:
  - architecture-change
  - new-module
  - ready-for-development
update_when:
  - module-boundary-change
  - runtime-component-change
---

# Architecture

Project type: `script`. Runtime level: `shared`.
Governance: `lightweight`.

This document describes the architecture now and the durable target principles
that shape it. Nothing under "Target Architecture" is implemented yet.

## Current Architecture

The system is a Python CLI package.

```text
tests -> src/deepplant/__main__.py (Typer CLI) -> package code
```

- Python >= 3.12, managed with `uv`.
- Runtime dependencies: Typer (CLI), Pydantic v2, PyYAML.
- Dev toolchain: pytest + pytest-cov, Ruff, Pyright (strict).
- The CLI exposes only `--help` and `version`.
- `make run` executes the package module; `make test`, `make lint`,
  `make typecheck`, and `make build` verify the local package lifecycle.

No service runtime, browser runtime, container runtime, database, or external
infrastructure exists in this profile.

## Target Architecture (Principles Only)

The semantic engineering model is the product core; everything else depends on it:

```text
CLI
GUI
renderers
DEXPI adapters
simulation adapters
AI agents
        ↓
semantic domain model
```

Dependency direction is inward: consumers may depend on the domain model; the
domain model depends on nothing consumer-specific. The domain model must remain
usable directly from Python and from the CLI.

Stated constraints:

- Semantic model vs presentation model: engineering semantics (`Plant`,
  `Equipment`, `Port`, `Connection`, `Pipeline`, `Instrument`, properties,
  relationships) and presentation (`sheet`, `symbol`, x/y position, rotation,
  geometry, routing, labels) are strictly separate. Drawing coordinates and SVG
  concepts never live on core engineering objects.
- YAML is a serialization format, not the domain model:

  ```text
  YAML
   ↓
  Pydantic validation / parsing
   ↓
  DeepPlant domain model
   ↓
  validation / rendering / adapters
  ```

- The future connectivity model uses generic `Component -> Ports -> Connections`
  relationships (e.g. `P-101.discharge -> connection -> L-101.inlet`), not
  hard-coded `pump connected to pipe` fields.

Do not create packages for `model/`, `rendering/`, `dexpi/`, or `simulation/`
until real code needs them.

## Current Quality Gates

```bash
make validate-docs
make validate-agent-skills

make check
```

## Possible Future Extensions

Do not treat this list as implemented architecture. Add any item only when a
concrete requirement and ADR justify it:

- semantic model packages and the YAML schema
- rendering and the SVG symbol specification
- DEXPI and simulator adapters
- interactive editor
- database or durable persistence
- cache, queue, broker, or background worker
- public deployment, Kubernetes, or service mesh

## Related

- [product.md](product.md)
- [roadmap.md](roadmap.md)
- [workflow.md](workflow.md)
- [quality.md](quality.md)
- [decisions/index.md](decisions/index.md)
