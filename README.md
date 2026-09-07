# DeepPlant

DeepPlant is a Git-native semantic engineering platform for process plants and
the first product implementing the idea of **Engineering as Code**: engineering
intent is expressed as a semantic model that can be validated, versioned,
diffed, and rendered.

This repository currently contains the project foundation only: a minimal Python
CLI package, durable documentation, and architectural ADRs. The semantic domain
model, the YAML schema, renderers, DEXPI, and the interactive editor are planned
but not implemented.

Selected profile: `script-shared` (Python CLI package). Governance: `lightweight`.
Workflow mode: `pr`.

## Product Principles

- The semantic engineering model is the product core; CLI, GUI, renderers, and
  adapters depend on it.
- Presentation data (symbols, coordinates, routing) stays separate from
  engineering semantics.
- YAML is a serialization format, not the domain model.
- Connectivity follows `Component -> Ports -> Connections`.

See [docs/product.md](docs/product.md) for the product view and
[docs/roadmap.md](docs/roadmap.md) for the roadmap.

## Quick Start

```bash
make setup
make check
make build
```

`make check` is validation-only. Use `make format` for formatting changes and
edit durable project docs explicitly when project knowledge changes.

Run the CLI:

```bash
make run
uv run deepplant version
```





## Workflow

Reusable agent skills are available under `.agents/skills/` for orientation,
implementation, verification, review, documentation updates, ADRs, conventional
commits, and learning capture. `.codex/` contains thin Codex adapters that
delegate to those canonical skills.

Start with enough context to work safely:

```bash
sed -n '1,220p' project/brief.md
sed -n '1,220p' docs/architecture.md
make validate-agent-skills
make check
```

Build the smallest useful vertical slice, learn from it, then refine the brief,
architecture notes, ADRs, or the roadmap when the learning is durable.

## Navigation

| Need | Open |
|---|---|
| Product brief | [docs/product.md](docs/product.md) |
| Roadmap | [docs/roadmap.md](docs/roadmap.md) |
| Current architecture | [docs/architecture.md](docs/architecture.md) |
| Project brief | [project/brief.md](project/brief.md) |
| Workflow | [docs/workflow.md](docs/workflow.md) |
| Quality gates | [docs/quality.md](docs/quality.md) |
| Decisions | [docs/decisions/index.md](docs/decisions/index.md) |
| Agent instructions | [AGENTS.md](AGENTS.md) |
| Example area | [examples/minimal-process/README.md](examples/minimal-process/README.md) |
