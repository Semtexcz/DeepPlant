---
type: governance
status: active
canonical_for:
  - python-testing-strategy
read_when:
  - python-change
  - python-test-change
  - python-review
update_when:
  - python-engineering-contract-change
depends_on:
  - docs/dev/python/index.md
  - docs/dev/python/scientific-computation.md
  - docs/dev/workflow/quality.md
decision: []
evidence: []
superseded_by: null
---

# Python Testing

> **Question this document answers:** how should DeepPlant's Python tests be
> organized, and what must they prove, so behavior — not implementation — stays
> pinned?

The Python suite runs through `make test` (`uv run pytest`) and is part of
`make check`. Issue #106 reorganized `tests/` by capability; that structure is the
practical reference.

## Organization by capability

Mirror the production package layout so it is obvious where a test belongs:

```text
tests/model/            semantic model (physical, process, piping)
tests/render/           renderer, symbols, layout
tests/adapters/dexpi/   DEXPI import/export
tests/editor/           editor application, transport, projection, desktop
tests/                  cross-cutting: public API, CLI, io, round-trip, packaging
```

A test lives next to the capability it exercises. Cross-cutting or
repository-wide checks (`test_public_api.py`, `test_cli.py`, `test_io.py`,
`test_roundtrip.py`, packaging tests) stay at the `tests/` root.

## Test layers

- **Unit.** One cohesive rule or function, no transport, no framework. Domain
  rules are unit-tested independently of the CLI and any transport.
- **Integration.** A real chain within the process, without a browser or the
  network: for example `load → model` or `model → projection → envelope`.
- **System/end-to-end.** The real product path where one exists. In Python this
  means the CLI and the boundary routes driven through their real entry points;
  browser E2E lives in the frontend suite, not here.

Keep each layer small. Do not test framework internals.

## What to assert

- **Observable behavior**, not implementation. Assert the returned value, the
  raised error and its message, the emitted document, the exit code — not that a
  private method was called.
- **Round-trip invariants.** `load_plant(save_plant(model))` is semantically equal
  to `model`; DEXPI export has a semantic round-trip. Pin these explicitly.
- **Deterministic outputs.** Canonical YAML, rendered SVG, layout, and DEXPI
  export are deterministic; pin them with golden or determinism tests.
- **Error paths.** Every fail-closed rule has negative coverage: unknown fields,
  blank semantic strings, duplicate ids, unresolvable references, wrong version
  URIs, unsupported external content. Assert the specific message where it is
  part of the contract.
- **Regressions.** A defect fix adds a test that fails before the fix and passes
  after it. The test names the behavior that broke, not the code change.

## Fixtures, isolation, and parameterization

- **Fixtures** build the smallest state a test needs, and each test owns or resets
  its own state. Use `tmp_path` for filesystem work; never write into the source
  tree. An example fixture loads the canonical example or a small synthetic model.
- **Isolation** means one test cannot affect another: no shared mutable module
  state, no fixed port, no ordering dependency, no leftover file.
- **Parameterize** repeated cases with `@pytest.mark.parametrize` instead of
  copy-pasted near-identical tests. Each parameter set reads as one behavior with
  its input and expected outcome.
- Do not make tests depend on execution order or on a previous test's side effect.

## Reference and numerical validation

See [scientific-computation.md](scientific-computation.md) for when a reference
test is required versus when an invariant or behavioral test is sufficient.

- Pin a reference value with its **provenance** and an **explicit tolerance**;
  never compare computed floats for exact equality.
- Where no independent closed form exists, assert the invariants the result must
  satisfy (conservation, monotonicity, ordering, bounds, round-trip).
- Keep the tolerance as small as the method justifies; a loose tolerance hides a
  real regression.

## External systems and determinism

- External systems appear only as **repository fixtures**. The suite runs
  **offline**, with no network access at test time.
- Fixtures that originate from an external specification carry their attribution
  and licence recording (see [workflow/standards.md](../workflow/standards.md));
  restricted standards content is never committed.
- Every output the contract calls deterministic is tested for that property.

## Mocks

- Prefer a real object or a small local fake over a mock. Reach for
  `monkeypatch` or a stub only at a genuine boundary you cannot exercise directly
  (an environment variable, `Path.home`, a socket that must be controlled).
- Do not mock the thing under test, and do not assert on mock call choreography
  that merely mirrors the implementation.
- A mock is a boundary tool, not a test strategy. If a design needs heavy mocking
  to test, the design or the boundary is wrong.

## Anti-patterns to avoid

- A test that restates the implementation (`assert x == x + 0`) and would pass
  even if the behavior were wrong.
- Snapshotting a large object to avoid deciding what matters. Assert the
  properties that matter.
- Tests that depend on wall-clock time, network, a fixed port, or execution order.
- Weakening or deleting a test to make a change pass; fix the behavior instead.

## Related

- [index.md](index.md) — the contract home and review checklist.
- [scientific-computation.md](scientific-computation.md) — engineering-computation rules.
- [quality.md](../workflow/quality.md) — the test gates and CI expectations.
- [history/implementation-slices.md](../history/implementation-slices.md) — how the suite grew.
