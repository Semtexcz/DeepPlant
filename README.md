# DeepPlant

DeepPlant is a Git-native semantic engineering platform for process plants and the
first product implementing the idea of **Engineering as Code**: engineering intent
is expressed as a semantic model that can be validated, versioned, diffed, and
rendered.

This repository ships the project foundation plus executable semantic vertical
slices: the physical/plant model (`PlantModel`/`Plant`/`Equipment`, `Port`,
identified `Connection`), the physical piping-realization layer (`PipingModel`
with line → segment → realization over identified connections; ADR-0011), the
standalone process-domain model (`ProcessModel` with `ProcessStep`/`ProcessStream`),
YAML load/save into typed Pydantic models with strict structural validation, a
`deepplant validate` CLI, the SVG + anchor `basic` symbol-pack contract, a headless
read-only process renderer (`render_process_svg()`), and a narrow DEXPI 2.0.0
Process import/export adapter (`deepplant.adapters.dexpi`; supported subset,
directions, and limits in
[docs/dev/reference/dexpi-process-adapter.md](docs/dev/reference/dexpi-process-adapter.md)).
Full DEXPI, other vendor adapters (COMOS, AVEVA), the interactive editor,
engineering rules, and P&ID rendering are planned but not implemented.

Selected profile: `script-shared` (Python CLI package). Governance: `lightweight`.
Workflow mode: `pr`.

## Where to Start

```text
I want to use DeepPlant
    → start here: docs/user/getting-started.md
    → user documentation: docs/user/index.md

I want to develop, extend, or understand DeepPlant internals
    → developer documentation: docs/dev/index.md
```

[docs/index.md](docs/index.md) routes by audience and by knowledge authority. The
long-term thesis is in [VISION.md](VISION.md); the strategic capability map is the
[DeepPlant Roadmap GitHub Project](https://github.com/users/Semtexcz/DeepPlant/projects/2).

## Product Principles

- The semantic engineering model is the product core; CLI, GUI, renderers, and
  adapters depend on it.
- Presentation data (symbols, coordinates, routing) stays separate from
  engineering semantics; a `ProcessStep` states its engineering `function`, never
  its drawing role (ADR-0009).
- YAML is a serialization format, not the domain model.
- Connectivity follows `Component -> Ports -> Connections`; piping realization
  references identified connections instead of restating endpoints (ADR-0011).

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
uv run deepplant validate examples/minimal-process/plant.yaml
```

New to DeepPlant? [docs/user/getting-started.md](docs/user/getting-started.md)
takes you from a checkout to a first validated model using only the CLI and the
bundled examples.

## Workflow

Reusable agent skills live under `.agents/skills/` (orientation, implementation,
verification, review, documentation, ADRs, conventional commits, learning
capture); `.codex/` holds thin adapters that delegate to them.

Start from the smallest relevant context, not the whole repository — use the
task-to-context table in [docs/dev/index.md](docs/dev/index.md) and
[AGENTS.md](AGENTS.md):

```bash
make validate-agent-skills
make check
```

Build the smallest useful vertical slice, learn from it, then refine the brief,
architecture notes, ADRs, or the roadmap when the learning is durable.

## License

DeepPlant is licensed under the GNU Affero General Public License, version 3
only (`AGPL-3.0-only`). Commercial use under AGPL is permitted subject to its
terms; AGPL is not a non-commercial licence. See [LICENSE](LICENSE) for the
full license text.

Where the Project Owner has sufficient rights, alternative commercial
licensing may be offered separately in the future. This does not change rights
already granted under AGPL. Contributions are governed by
[CONTRIBUTING.md](CONTRIBUTING.md) and [CLA.md](CLA.md); see
[COMMERCIAL-LICENSING.md](COMMERCIAL-LICENSING.md) for the concise policy.
Provenance is indexed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), and
project identity is addressed in [TRADEMARKS.md](TRADEMARKS.md).

## Navigation

| Need | Open |
|---|---|
| Documentation router | [docs/index.md](docs/index.md) |
| New user: first validated model | [docs/user/getting-started.md](docs/user/getting-started.md) |
| User documentation | [docs/user/index.md](docs/user/index.md) |
| Developer / agent documentation | [docs/dev/index.md](docs/dev/index.md) |
| Current contracts (model, YAML, CLI, renderer, DEXPI) | [docs/contracts/index.md](docs/contracts/index.md) |
| Current architecture (boundary map) | [docs/dev/architecture/index.md](docs/dev/architecture/index.md) |
| Current state, next direction, evidence gaps | [docs/dev/planning/roadmap.md](docs/dev/planning/roadmap.md) |
| Long-term capability progression | [docs/dev/planning/direction.md](docs/dev/planning/direction.md) |
| Decisions | [docs/dev/decisions/index.md](docs/dev/decisions/index.md) |
| Evidence and research | [docs/dev/research/index.md](docs/dev/research/index.md) |
| Implementation history | [docs/dev/history/implementation-slices.md](docs/dev/history/implementation-slices.md) |
| Documentation conventions | [docs/dev/workflow/conventions.md](docs/dev/workflow/conventions.md) |
| Project brief | [project/brief.md](project/brief.md) |
| Agent instructions | [AGENTS.md](AGENTS.md) |
