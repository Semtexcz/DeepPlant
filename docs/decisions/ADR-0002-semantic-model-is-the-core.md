# ADR-0002: The Semantic Engineering Model Is the Product Core

> Status: Accepted
> Date: 2026-09-07

## Context

DeepPlant is a Git-native semantic engineering platform for process plants.
Consumers will include a CLI, a GUI, renderers, DEXPI adapters, simulation
adapters, and AI agents. The project could be organized around drawings, around
a file/schema format, or around the semantics of the plant itself.

## Options

- Organize around presentation and drawing deliverables.
- Organize around the YAML/schema representation.
- Organize around a semantic domain model that everything depends on.

## Decision

The semantic engineering model is the product core. CLI, GUI, renderers, DEXPI
adapters, simulation adapters, and AI agents depend on it. The domain model must
remain independently usable from Python and from the CLI.

No UI, persistence, network service, or external integration is placed inside
the domain model. The domain model imports nothing consumer-specific.

## Consequences

### Positive

- Validation, diff, and rendering all operate on one source of truth.
- Consumers (renderer, DEXPI, simulators, agents) can be added or replaced
  without reshaping the model.

### Negative

- The domain model must be designed deliberately first; drawing-derived
  shortcuts cannot hide missing semantics.

## Revisit When

A concrete consumer proves this layering blocks a real requirement.

## Related

- [ADR-0003-separate-semantic-and-presentation-models.md](ADR-0003-separate-semantic-and-presentation-models.md)
- [ADR-0004-yaml-is-a-serialization-format.md](ADR-0004-yaml-is-a-serialization-format.md)