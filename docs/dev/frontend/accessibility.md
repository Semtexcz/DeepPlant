---
type: governance
status: active
canonical_for:
  - frontend-accessibility-baseline
read_when:
  - frontend-change
  - editor-frontend-work
update_when:
  - accessibility-baseline-change
depends_on:
  - docs/dev/frontend/index.md
  - docs/dev/frontend/vue.md
decision: []
evidence: []
superseded_by: null
---

# Accessibility Baseline

> **Question this document answers:** what accessibility is required in the
> editor frontend as part of normal correctness?

Accessibility is part of frontend correctness, not a later polish pass. This is a
**practical engineering baseline**, not a WCAG certification exercise: apply it
to the surfaces being changed and leave the code at least as accessible as it was.

## Requirements

- **Semantic HTML.** Use real elements (`button`, `a`, `dl`/`dt`/`dd`, headings)
  with the correct roles instead of `div` handlers.
- **Button vs link semantics.** Actions (for example *Fit view*) are `<button
  type="button">`; navigation is a link. Do not use a link as a button or a
  click handler on a non-interactive element.
- **Accessible names.** Every interactive control and landmark region has a
  programmatic name — visible text or `aria-label`.
- **Keyboard interaction.** Everything reachable and operable by pointer must be
  reachable and operable by keyboard, with a sensible order.
- **Visible focus.** Focus indicators must remain visible. Do not remove outlines
  without an equivalent, visible replacement.
- **Focus management.** Move focus deliberately when a surface opens, traps, or
  closes; restore it to a sensible origin.
- **Meaningful alternative text.** Decorative graphics are marked decorative;
  meaningful graphics carry an `alt` that states the meaning, not the pixels.
- **Visible error and validation feedback.** Errors are shown as text, associated
  with what they describe, and never conveyed by color alone.
- **No color-only or pointer-only interaction.** State changes (for example
  selected vs not) must be conveyed by more than color, and must not require a
  pointer.

## What this contract does not do

It does not add runtime accessibility tooling, a WCAG conformance claim, or an
audit. It states the baseline each change must honor and is reviewed through the
[frontend review checklist](index.md#frontend-review-checklist).

## Current state (implemented)

The delivered slice already applies part of this baseline: the canvas and
Inspector regions carry `aria-label`, the symbol image has an `alt`, *Fit view*
is a native button, and the Inspector renders a definition list. These are
partial, not a complete audit; keep them intact and extend them as surfaces grow.
