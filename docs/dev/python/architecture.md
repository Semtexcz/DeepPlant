---
type: governance
status: active
canonical_for:
  - python-architecture-and-ownership
read_when:
  - python-change
  - new-module
  - architecture-change
update_when:
  - python-engineering-contract-change
depends_on:
  - docs/dev/python/index.md
  - docs/dev/architecture/index.md
  - docs/dev/workflow/conventions.md
decision:
  - docs/dev/decisions/ADR-0002-semantic-model-is-the-core.md
  - docs/dev/decisions/ADR-0003-separate-semantic-and-presentation-models.md
  - docs/dev/decisions/ADR-0004-yaml-is-a-serialization-format.md
evidence: []
superseded_by: null
---

# Python Architecture and Module Ownership

> **Question this document answers:** how should DeepPlant Python modules be
> organized, how should dependencies point, and when should a module be split or
> combined so the code stays cohesive and independently testable?

This document owns the **direction of dependencies**, **module ownership**, and
the **practical criteria for splitting or combining** modules. The current
technical shape is owned by [architecture.md](../architecture/index.md); this page
states the rules new and changed code must follow.

## Preferred direction

Dependencies point toward the independently usable semantic core. Never the
reverse:

```text
CLI / FastAPI / desktop adapters
              ↓
Application and use-case logic
              ↓
Semantic engineering core
```

The semantic core (the domain model) imports nothing consumer-specific: no CLI,
no YAML or file I/O, no rendering, no HTTP, no GUI toolkit (ADR-0002). Each layer
depends only on layers below it.

## Canonical rules

- **Semantic model independence.** Domain objects stay usable from Python and
  from the CLI without a GUI, a network, or a file (ADR-0002, ADR-0004).
- **Capability-oriented packages.** Organize by capability and responsibility,
  not by technical kind. A package owns one cohesive concern; for example the
  delivered layout is `model/` (semantics), `render/` (presentation), `io.py`
  (serialization), `adapters/dexpi/` (one external format), `editor/`
  (application + hosts).
- **Explicit module ownership.** Every module has one clear owner responsibility.
  If two modules would both reasonably change for the same reason, they may be
  one module; if they change for different reasons, they are separate.
- **Framework-specific code at boundaries.** Typer lives only in the CLI entry
  point, FastAPI/Uvicorn only in the editor transport, Qt only in the desktop
  package. Framework imports never leak into the Core or the application layer.
- **Thin entry points.** `__main__.py`, the FastAPI route handlers, and the
  desktop CLI parse input and delegate. They hold no engineering behavior.
- **No unnecessary service/repository/factory layers.** A function that computes,
  a dataclass that carries, and a Pydantic model that validates are usually
  enough. Add a layer only when it removes real complexity or matches an existing
  local pattern.
- **No speculative interfaces or generic abstraction frameworks.** Do not build a
  plugin system, a generic `BaseRepository`, or an abstract "engine" before real
  code needs one.
- **No unrelated code in `utils.py`, `helpers.py`, `common.py`, and the like.** A
  genuinely generic helper belongs in the capability that owns it, or in a small
  named module that describes what it does. A catch-all bucket is a signal that
  ownership was not decided.

## Splitting and combining modules

Do not define a rigid universal directory template. Decide from cohesion,
dependencies, maintainability, and testability:

- **Split** when a module contains **independently maintained responsibilities**
  or lifecycles — the parts change for different reasons, have different
  dependencies, or are separately testable. Issue #106's `model.py → model/`
  split is the reference: shared validation primitives, the physical layer, the
  piping layer, the process graph, and the root aggregate became separate
  modules because each is a distinct responsibility.
- **Combine** when the parts are read together, change together, and share one
  dependency set. Fragmentation that forces a reader to open three files to
  understand one rule is worse than a single cohesive module.
- **Prefer capability boundaries over technical boundaries.** `render/symbols.py`
  owns symbol-pack policy; `editor/application.py` owns the framework-independent
  editor state. A file called `services.py` or `helpers.py` owns nothing.
- **Keep the public surface at the package `__init__`.** A capability package
  re-exports its public names (see [conventions.md](conventions.md#package-level-re-exports));
  internal modules stay private implementation. The #106 refactor preserved the
  public API exactly and pinned it with `tests/test_public_api.py`.
- **Testability is a splitting signal.** If a unit can only be exercised through
  a framework or a filesystem, that is a boundary mistake, not a testing problem.

Line-count responses to this: the sizes in
[index.md](index.md#size-and-cohesion-policy) are cohesion signals, not a target.
Split for cohesion, not to reach a number.

## Pythonic SOLID

SOLID is a set of **design heuristics, not a mandatory architectural pattern.**
Apply it pragmatically, consistently with Python's philosophy of simplicity,
readability, duck typing, composition, and explicit dependencies. It is not an
instruction to add five layers, repositories, services, factories, abstract base
classes, or dependency-injection everywhere.

### S — Single Responsibility Principle

A module, function, or class should have one cohesive reason to change. Organize
by capability and responsibility, not by arbitrary LOC thresholds. Prefer
extracting genuinely independent responsibilities over fragmenting cohesive code.
**Module cohesion matters more than having many small files.**

### O — Open/Closed Principle

Prefer small, stable extension points where **actual variation exists**. Use
composition, callbacks, registries, or `Protocol` when justified. Do not create
plugin frameworks, abstract factories, or inheritance hierarchies for
hypothetical future extensions. A simple edit to an existing implementation is
perfectly acceptable when no genuine extension boundary exists.

### L — Liskov Substitution Principle

Substitutable implementations must preserve behavioral contracts, invariants, and
expected error semantics. Prefer composition or structural typing where
inheritance does not represent a genuine substitutable relationship. Do not
introduce inheritance solely for code reuse. Be especially careful with semantic
engineering types that look similar but are not interchangeable (see the examples
below).

### I — Interface Segregation Principle

Prefer small, focused interfaces at **real** architectural boundaries. Use Python
`Protocol` or callable types when multiple implementations or testing needs
justify them. Do not introduce an interface for every class or function. Plain
functions and concrete dependencies are the default.

### D — Dependency Inversion Principle

High-level engineering rules must not depend on FastAPI, Typer, Qt, HTTP, or
persistence infrastructure. Keep dependency direction toward the independently
usable semantic core. Introduce abstractions only where a real boundary needs to
support substitution. **Dependency inversion does not imply dependency-injection
containers or mandatory interface layers.**

### Pythonic implementation guidance

- **Duck typing and structural typing.** Reach for `Protocol` when you need a
  shape, not a lineage. Most DeepPlant call sites just call a concrete function.
- **Composition over unnecessary inheritance.** Subclass only to express a real
  substitutable relationship; otherwise hold an instance.
- **Functions versus classes.** Use a function unless you genuinely need to carry
  state, group related operations, or satisfy a framework contract.
- **`Protocol` versus ABC.** Prefer `Protocol` for structural boundaries; an ABC
  is justified only when you need shared implementation or a genuine taxonomy.
- **Dataclasses and immutable values.** `@dataclass(frozen=True)` for internal,
  framework-free value carriers (for example `editor.application.EditorProjectionView`).
- **Explicit dependency passing versus DI frameworks.** Pass what a unit needs as
  a parameter or constructor argument. There is no container in DeepPlant.
- **Practicality beats purity.** A slightly "impure" but obvious solution that a
  reviewer reads in one pass beats a "pure" one that hides behavior.
- **YAGNI.** Do not build for a hypothetical future requirement.

## DeepPlant-specific examples

Short, realistic illustrations. These are guidance, not code to add.

### A real architectural boundary requiring abstraction

The editor must expose a loaded project to two hosts — the FastAPI transport
(`editor/api.py`) and the native desktop host (`editor/desktop_qt/`) — without
either host re-implementing engineering behavior. The real boundary is the
framework-independent `EditorApplication`: both hosts depend on it, and neither
transport leaks into it. This is dependency inversion doing genuine work, and it
is achieved with an explicit object plus functions, **not** with an abstract
factory or a registered provider interface.

### A simple concrete implementation that needs no abstraction

`deepplant.io.load_plant` is a plain function returning `PlantModel`. It has one
caller-visible contract, one implementation, and no variation. Wrapping it in a
`PlantLoaderProtocol`, a `LoaderFactory`, and a `LoaderRegistry` "for testability"
would add three indirections and remove none. Tests call the function directly.
This is the default shape; abstraction here would be premature.

### Two engineering concepts that must remain distinct

`ProcessPort` and the physical `Port` are structurally similar — both are named
connection points with an id — but they are **not** interchangeable. The boundary
between the process graph and the physical realization is owned by
[ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md)
(Process ↔ Physical Realization Boundary); the process-side objects are owned by
the [process-model contract](../../contracts/process-model.md) and the
physical/plant-side objects by the
[plant-model contract](../../contracts/plant-model.md). A `ProcessPort` belongs to
a `ProcessStep` in the process graph; a physical `Port` belongs to `Equipment`.
Reusing one type for both, or letting either substitute for the other, would
silently collapse two engineering layers (LSP/ISP applied to semantics). They stay
distinct types with distinct owners, even though the compiler would accept a
shared base.

## Related

- [index.md](index.md) — the contract home, review checklist, and size policy.
- [conventions.md](conventions.md) — design, Pydantic boundaries, and the Ruff review.
- [architecture.md](../architecture/index.md) — the current technical shape.
- [decisions/index.md](../decisions/index.md) — the ADRs that own each boundary.
