---
type: governance
status: active
canonical_for:
  - engineering-computation-documentation
read_when:
  - python-change
  - engineering-calculation-change
  - python-review
update_when:
  - python-engineering-contract-change
depends_on:
  - docs/dev/python/index.md
  - docs/dev/python/testing.md
  - docs/dev/workflow/standards.md
decision:
  - docs/dev/decisions/ADR-0012-process-step-single-classification-axis.md
  - docs/dev/decisions/ADR-0013-qualified-engineering-quantity-boundary.md
evidence: []
superseded_by: null
---

# Scientific and Engineering Computation

> **Question this document answers:** how must engineering and numerical
> computation be documented and justified so a reviewer can trust the result,
> reproduce it, and see that it respects the physics?

DeepPlant is engineering software, not merely a CRUD application. Any code that
computes, transforms, or validates an engineering quantity carries a higher
documentation and testing obligation than ordinary data plumbing. This document
owns **how engineering computation is documented**; [testing.md](testing.md) owns
**how it is tested**.

## Document the computation

Any function or method that performs a non-trivial engineering or numerical
computation documents, next to the code:

- **The equation or rule**, in a readable form, and its **source** (a reference, a
  contract rule id such as S1–S4 or P1–P5, or an explicit DeepPlant decision). If
  a formula is reproduced, cite where it comes from. If it is a DeepPlant-authored
  model, say so.
- **Assumptions** the computation relies on (idealised behaviour, steady state, a
  fixed tolerance, an ordering, an independence).
- **Physical units** of every input and output. Store canonical state and name the
  represented unit (ADR-0013); never leave a bare number whose unit is a guess.
- **Validity range** where the rule only holds in a domain (a range of ratios, a
  positive magnitude, a supported subset), and what happens outside it.
- **Numerical method** when the result is computed rather than read: the algorithm,
  its convergence or termination criterion, and its stability assumptions.
- **Tolerance** where a comparison or an approximated value is involved, and why
  that tolerance is the right one.
- **Edge cases** and how they are handled (empty graph, single node, zero length,
  disconnected input, a degenerate cycle).
- **Conservation laws and physical invariants** where relevant — mass/energy
  balance, flow continuity, direction consistency — and how the code preserves
  them. A violation is a defect, not a rounding detail.
- **Determinism and reproducibility**: why two runs produce the same output. Where
  ordering could vary (sets, dict iteration, floating-point summation order),
  make the result deterministic and say how.

## Units and values

- An engineering value is a magnitude **and** its represented unit. Do not accept
  or emit a bare number where the unit matters.
- Prefer canonical, explicit units and record the represented unit rather than
  silently converting. `10 bar` and `1 MPa` are distinct canonical representations
  under canonical-state equality even when physically equivalent (ADR-0013).
- Do not invent engineering values to make an example look complete. A realistic
  example may legitimately carry no DN, piping class, or fluid code until the
  model supports it.

## Reference validation

- Where an independent **analytical** solution, a hand computation, a published
  closed form, or an independently produced reference value exists, validate
  against it — not merely against the code's own output.
- Pin the reference value in the test with its **provenance** (where it came from)
  and an **explicit tolerance**.
- A self-consistent implementation is not evidence of correctness. If no
  independent reference exists, say so, and test the **invariants** the result
  must satisfy (monotonicity, conservation, symmetry, bounds) instead.

## Reference tests versus behavioural tests

Not every function needs an analytical reference. Decide by the nature of the
computation:

- **Analytical/reference test required** when the function computes an engineering
  result with an independent ground truth (a geometric relation, a balance, a
  closed-form value, a documented formula). Test the value against the reference
  within a stated tolerance.
- **Invariant test sufficient** when there is no independent closed form but there
  are properties that must hold (continuity/conservation, monotonicity, ordering,
  idempotence, round-trip). Test the properties, with explicit tolerances where a
  tolerance applies.
- **Ordinary behavioural test sufficient** when the code is structural or
  presentational: it selects, maps, orders, serialises, or routes. Test the
  observable behavior, as in [testing.md](testing.md).

When in doubt, ask: "could a correct implementation and a subtly wrong one produce
the same output that this test would still pass?" If yes, the test is too weak for
an engineering result.

## Determinism

- Rendering, layout, routing, canonical YAML, and DEXPI export are deterministic
  by contract; their outputs are pinned by golden or determinism tests.
- Any set/dict-driven ordering that reaches an output is sorted or otherwise made
  stable, and the reason is documented.
- Floating-point comparisons use an explicit tolerance; never compare computed
  floats for exact equality.

## Standards licensing

- Follow [workflow/standards.md](../workflow/standards.md) and ADR-0007. Reference
  restricted standards (ISO, ISA, IEC) **by identifier only**; never reproduce or
  redistribute their normative content, and do not feed restricted content to AI
  tools.
- Openly licensed specifications (DEXPI 2.0, CC BY 4.0) may be used with the
  required attribution.
- Do not claim standards compliance from visual similarity or a secondary source;
  conformance that depends on restricted normative content needs human
  verification against an authorised copy.

## Related

- [index.md](index.md) — the contract home and review checklist.
- [testing.md](testing.md) — how engineering and numerical behavior is tested.
- [workflow/standards.md](../workflow/standards.md) — the standards-usage policy.
- [contracts/index.md](../../contracts/index.md) — the current engineering contracts.
