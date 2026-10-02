---
type: guidance
status: active
canonical_for:
  - diagnosing-validation-errors
read_when:
  - diagnose-validation-error
  - authoring-plant-yaml
  - using-deepplant
update_when:
  - loader-change
  - user-documentation-change
depends_on:
  - docs/contracts/yaml-format.md
  - docs/contracts/plant-model.md
  - docs/contracts/cli.md
decision: []
evidence: []
superseded_by: null
---

# Diagnose Validation Errors

> **Question this page answers:** validation failed — what does the message mean,
> and how do I fix it?

## How to read the message

Every failure is one line on standard error, and the exit code is `1`:

```text
✗ invalid DeepPlant model in 'my-plant.yaml': connections[0].source: unknown component 'T-999'
```

Three parts matter:

| Part | Example | Meaning |
|---|---|---|
| File path | `'my-plant.yaml'` | which file failed |
| Location | `connections[0].source` | dotted path to the offending value |
| Reason | `unknown component 'T-999'` | what is wrong |

The location uses list indices too, for example `equipment.0.colour` (the first
equipment item) or `piping.lines[0].segments[0]`. Some messages have no location
because the problem is document-wide, such as `empty document` or
`duplicate equipment id(s): T-101`. When several fields fail, they are joined with
`; `.

Expected errors like these never print a traceback — they are reported as a single
concise message.

## Failure classes

### Unreadable file

```text
✗ cannot read plant file 'my-plant.yaml': No such file or directory
```

The path is wrong, or the file cannot be read. Check the path and re-run.

### Invalid YAML

```text
✗ invalid YAML in 'my-plant.yaml': while parsing a flow sequence
```

The file is not valid YAML — usually an unbalanced bracket, a stray tab, or a
missing colon. The message quotes the first line of the YAML parser's report.

### Empty or non-mapping document

```text
✗ invalid DeepPlant model in 'my-plant.yaml': empty document
✗ invalid DeepPlant model in 'my-plant.yaml': top level must be a mapping, got list
```

The document must be a single, non-empty mapping. An empty file, or a file whose
top level is a list or a scalar, is rejected.

### Unknown field

```yaml
equipment:
  - id: T-101
    type: tank
    colour: blue
```

```text
✗ invalid DeepPlant model in 'my-plant.yaml': equipment.0.colour: Extra inputs are not permitted
```

Models forbid extra fields, so a misspelled or unsupported key fails. Remove the
field, or correct its name. Here `equipment.0` is the first equipment item.

### Blank semantic value

```yaml
plant:
  id: "   "
```

```text
✗ invalid DeepPlant model in 'my-plant.yaml': plant.id: String should have at least 1 character
```

Ids, types, and references must be non-empty. Whitespace-only values are trimmed
and then rejected.

### Duplicate id

```text
✗ invalid DeepPlant model in 'my-plant.yaml': duplicate equipment id(s): T-101
✗ invalid DeepPlant model in 'my-plant.yaml': equipment.0: equipment 'T-101' has duplicate port id(s): outlet
```

Ids are unique: equipment and connection ids across the plant, port ids within the
equipment that owns them, piping line ids within the piping model, and segment ids
within their line.

### Unknown reference

```text
✗ invalid DeepPlant model in 'my-plant.yaml': connections[0].source: unknown component 'T-999'
```

A connection names equipment that does not exist. Check the `component` value
against the `equipment` list.

### Port not owned by the referenced component

```text
✗ invalid DeepPlant model in 'my-plant.yaml': connections[0].source: component 'T-101' has no port 'drain'
```

The equipment exists, but it does not declare that port. Add the port to the
equipment, or fix the port id. Port ids are local to their equipment, so a port
that exists on another item is still not owned by this one.

### Other structural or reference failures

The same message shape covers piping and process problems, for example:

```text
✗ invalid DeepPlant model in 'my-plant.yaml': piping.lines[0].segments[0].realizations[0].connection: unknown connection 'C-999'
✗ invalid DeepPlant model in 'my-plant.yaml': process: streams[0].target: unknown step 'PS-b'
✗ invalid DeepPlant model in 'my-plant.yaml': plant: Field required
```

`plant: Field required` means the `plant` key itself is missing from the document.

## Fix-and-recheck loop

1. Read the **location** to find the exact value.
2. Read the **reason** to see which rule it breaks.
3. Fix the YAML.
4. Re-run `uv run deepplant validate <path>`.

## Where the exact rules live

This page lists the common classes, not every rule. The authoritative statements
are:

- [yaml-format.md](../../contracts/yaml-format.md) — load rules and message format
- [plant-model.md](../../contracts/plant-model.md) — identity and reference rules
- [physical-piping.md](../../contracts/physical-piping.md) — piping rules
- [process-model.md](../../contracts/process-model.md) — process rules
- [cli.md](../../contracts/cli.md) — exit codes
