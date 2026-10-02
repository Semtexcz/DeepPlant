# ADR-0004: YAML Is a Serialization Format, Not the Domain Model

> Status: Accepted
> Date: 2026-09-07

## Context

DeepPlant stores plant models as YAML. YAML is easy to read and edit, which
makes it tempting to treat the YAML document structure as the in-memory model
and to couple code directly to the file shape.

## Options

- Use YAML documents as the in-memory model.
- Treat YAML as the external serialization and keep a dedicated domain model.

## Decision

YAML is a serialization format, not the internal domain model. The intended flow
is:

```text
YAML
 ↓
Pydantic validation / parsing
 ↓
DeepPlant domain model
 ↓
validation / rendering / adapters
```

Pydantic v2 validates the serialized representation at the boundary. The domain
model is a separate representation that code, validation, and adapters depend
on.

## Consequences

### Positive

- The file format can evolve without reshaping the domain model, and vice versa.
- The domain model stays usable from Python and CLI without file I/O.

### Negative

- Two representations (YAML schema and domain model) must be kept consistent by
  deliberate mapping.

## Revisit When

The mapping cost between the YAML schema and the domain model outweighs the
independence it provides.

## Related

- [ADR-0002-semantic-model-is-the-core.md](ADR-0002-semantic-model-is-the-core.md)