# DeepPlant

DeepPlant is a Git-native semantic engineering platform for process plants and
the first product implementing the idea of **Engineering as Code**: engineering
intent is expressed as a semantic model that can be validated, versioned,
diffed, and rendered.

This repository currently ships the project foundation plus executable semantic
vertical slices: a minimal `PlantModel`/`Plant`/`Equipment` domain model, the
topology slice (`Port`, `Connection`, reference validation), the standalone
process-domain model (`ProcessModel` with `ProcessStep[]`/`ProcessStream[]` —
mixing, splitting, and recycle are legal), YAML load/save into typed Pydantic
models, strict structural validation, a `deepplant validate` command, the SVG +
anchor `basic` symbol-pack contract, a headless read-only process renderer
(`render_process_svg()`) that derives standalone PFD-style SVG from a
`ProcessModel`, and a narrow DEXPI 2.x Process import/export adapter spike
(`deepplant.adapters.dexpi`; evidence and limits in
[docs/dexpi-process-spike.md](docs/dexpi-process-spike.md)). Import preflight
pins the DEXPI 2.0.0 Core/Process model URIs and global XML `Object@id`
uniqueness; export covers the deliberately symmetric canonical subset
(including material-port-only `pumping` after ADR-0009). `ProcessStep.function`
is canonical engineering semantics (ADR-0009); symbol roles are resolved at the
rendering boundary by a default presentation policy or explicit per-step
overrides, never stored in the semantic model. Full DEXPI, other
adapters (COMOS, AVEVA), the interactive editor, and P&ID rendering are planned
but not implemented.

Selected profile: `script-shared` (Python CLI package). Governance: `lightweight`.
Workflow mode: `pr`.

## Product Principles

- The semantic engineering model is the product core; CLI, GUI, renderers, and
  adapters depend on it.
- Presentation data (symbols, coordinates, routing) stays separate from
  engineering semantics; a `ProcessStep` states its engineering `function`,
  never its drawing role (ADR-0009).
- YAML is a serialization format, not the domain model.
- Connectivity follows `Component -> Ports -> Connections`.

DeepPlant is an experimental Git-native semantic engineering platform for
process plants. Its semantic model is intended to become the authoritative
system of record for DeepPlant-managed engineering intent and project state,
with PFD/P&ID views, engineering checks, simulations, and external exchange
handled as derived views, computations, or adapters.

See [VISION.md](VISION.md) for where DeepPlant is going,
[docs/architecture.md](docs/architecture.md) for what exists,
[docs/roadmap.md](docs/roadmap.md) for sequencing reasoning, and the
[DeepPlant Roadmap GitHub Project](https://github.com/users/Semtexcz/DeepPlant/projects/2)
for the strategic capability map. Planning governance is defined in
[docs/planning.md](docs/planning.md).

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

## License

DeepPlant is licensed under the GNU Affero General Public License, version 3
only (`AGPL-3.0-only`). See [LICENSE](LICENSE) for the full license text.

## Navigation

| Need | Open |
|---|---|
| Vision | [VISION.md](VISION.md) |
| Strategic planning | [docs/planning.md](docs/planning.md) |
| Product brief | [docs/product.md](docs/product.md) |
| Roadmap | [docs/roadmap.md](docs/roadmap.md) |
| Current architecture | [docs/architecture.md](docs/architecture.md) |
| Headless process renderer | [docs/rendering.md](docs/rendering.md) |
| DEXPI 2.x Process adapter spike | [docs/dexpi-process-spike.md](docs/dexpi-process-spike.md) |
| Project brief | [project/brief.md](project/brief.md) |
| Workflow | [docs/workflow.md](docs/workflow.md) |
| Quality gates | [docs/quality.md](docs/quality.md) |
| Standards & asset provenance | [docs/standards.md](docs/standards.md) |
| Decisions | [docs/decisions/index.md](docs/decisions/index.md) |
| Agent instructions | [AGENTS.md](AGENTS.md) |
| Example area | [examples/minimal-process/README.md](examples/minimal-process/README.md) |
