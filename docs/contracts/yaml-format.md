---
type: contract
status: active
canonical_for:
  - yaml-format-contract
read_when:
  - authoring-plant-yaml
  - serialization-change
  - loader-change
depends_on:
  - docs/contracts/plant-model.md
  - docs/contracts/process-model.md
  - docs/contracts/physical-piping.md
  - docs/dev/architecture/index.md
decision:
  - docs/dev/decisions/ADR-0004-yaml-is-a-serialization-format.md
  - docs/dev/decisions/ADR-0006-process-model-root-integration.md
evidence: []
superseded_by: null
---

# YAML Format Contract

> **Question this document answers:** what is the authored YAML document shape,
> and what do load and save guarantee?
>
> Implemented in `src/deepplant/io.py`. YAML is a serialization format, never the
> domain model (ADR-0004). Field-level meaning lives in
> [plant-model.md](plant-model.md), [process-model.md](process-model.md), and
> [physical-piping.md](physical-piping.md).

## Document shape

One plant document is a single top-level mapping. Keys are optional except
`plant`, and there is no `version` key yet:

| Key | Value | Contract |
|---|---|---|
| `plant` | mapping | [plant-model.md](plant-model.md) |
| `equipment` | sequence | [plant-model.md](plant-model.md) |
| `connections` | sequence | [plant-model.md](plant-model.md) |
| `piping` | mapping or `null` | [physical-piping.md](physical-piping.md) |
| `process` | mapping or `null` | [process-model.md](process-model.md) |

```yaml
plant:
  id: demo
  name: Minimal Process

equipment:
  - id: T-101
    type: tank
    ports:
      - id: outlet
  - id: P-101
    type: pump
    ports:
      - id: suction

connections:
  - id: C-001
    source:
      component: T-101
      port: outlet
    target:
      component: P-101
      port: suction

piping:            # optional
  lines: []

process:           # optional
  steps: []
  streams: []
```

## Load rules

`load_plant(path: str | Path) -> PlantModel`

1. The file must be readable UTF-8 text; otherwise `PlantLoadError` with
   `cannot read plant file '<path>': <reason>`.
2. The text must be valid YAML; otherwise `PlantLoadError` with
   `invalid YAML in '<path>': <first line of the YAML error>`.
3. The document must be a non-empty mapping; an empty document reports
   `invalid DeepPlant model in '<path>': empty document`, and any other top-level
   type reports `top level must be a mapping, got <type>`.
4. The mapping is validated through Pydantic into typed models. Structural
   failures (unknown fields, blank semantic strings, duplicate ids, unresolvable
   references) raise `PlantLoadError` whose message is
   `invalid DeepPlant model in '<path>': <dotted location>: <message>` per
   failing field, joined with `; `.
5. `load_plant` never returns a partially validated model, and it never raises a
   raw Pydantic or PyYAML error for a user-authored file: every expected failure
   is a `PlantLoadError` with a concise message, so callers such as the CLI can
   report errors without tracebacks.

## Save rules

`save_plant(model: PlantModel, path: str | Path) -> None`

1. Output is canonical **semantic** YAML: `load_plant(save_plant(model))` is
   semantically equal to `model`.
2. Serialization is canonical, not textual. Comments, blank lines, quoting
   style, anchors, aliases, and key order in the original file are deliberately
   not preserved.
3. `None`-valued optional fields are omitted; `process: None` is written as a
   missing `process` key; an explicitly present empty `ProcessModel` stays
   present.
4. Keys follow Pydantic model declaration order (`sort_keys=False`), so output is
   deterministic; text is UTF-8 with `allow_unicode=True` and ends with a
   newline.
5. An unwritable destination raises `PlantSaveError` with
   `cannot write plant file '<path>': <reason>`.

## Compatibility and change rules

- There is **no schema version field and no migration tooling**. YAML from an
  earlier pre-1.0 shape fails loudly instead of being reinterpreted, because
  models forbid unknown fields.
- Documented pre-1.0 breaking changes so far: `Connection.id` became required
  (C1, ADR-0011) and `ProcessStep.type` was replaced by `ProcessStep.function`
  (ADR-0009).
- Authoring is expected to be Git-reviewed: ids are authored and stable, not
  positional, so text diffs stay small and no sibling is renumbered by an
  insertion.

## Deliberately not provided

A CLI save/format command, a schema file or external schema validation service,
document versioning and automated migration, multi-document YAML files,
JSON/other serialization formats, comment preservation, and format
auto-repair. Each needs its own evidence and Issue.

## Related

- [cli.md](cli.md) — how errors surface to users.
- [architecture.md](../dev/architecture/index.md) — module boundary (`io.py` owns YAML).
- [ADR-0004](../dev/decisions/ADR-0004-yaml-is-a-serialization-format.md).
