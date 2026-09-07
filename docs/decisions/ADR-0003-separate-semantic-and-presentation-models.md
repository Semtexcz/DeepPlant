# ADR-0003: Keep Semantic and Presentation Models Separate

> Status: Accepted
> Date: 2026-09-07

## Context

PFD/P&ID deliverables need sheets, symbols, coordinates, routing, and labels. It
is tempting to store x/y positions and symbol choices directly on equipment
objects so that rendering is trivial.

## Options

- Store drawing data on the engineering objects.
- Derive a separate presentation model from the semantic model for each drawing.

## Decision

Engineering semantics and presentation data stay strictly separate. Semantic
information includes `Plant`, `Equipment`, `Port`, `Connection`, `Pipeline`,
`Instrument`, properties, and relationships. Presentation information includes
sheet, symbol, x/y position, rotation, geometry, routing, and labels.

Drawing coordinates and SVG-specific concepts are never embedded in core
engineering objects. Renderers map from the semantic model to a presentation
model they own.

## Consequences

### Positive

- The semantic model stays stable and reusable for non-drawing consumers
  (validation, DEXPI, simulators).
- Multiple presentations of the same model remain possible.

### Negative

- Renderers must maintain layout and geometry logic instead of borrowing it from
  the model.

## Revisit When

A concrete rendering requirement forces semantics and presentation to share
state in a way this boundary cannot express.

## Related

- [ADR-0002-semantic-model-is-the-core.md](ADR-0002-semantic-model-is-the-core.md)