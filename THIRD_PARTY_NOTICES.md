# Third-party notices and provenance

This index records known non-original inputs and points to the detailed record
where one exists. It is not a complete inventory of every dependency's licence.
Contributors must disclose new material before it is accepted.

## DEXPI 2.0 fixtures

The synthetic XML fixtures under
[`tests/fixtures/dexpi/2.0.0/`](tests/fixtures/dexpi/2.0.0/) use DEXPI 2.0
class identifiers, enumeration literals, and XML envelope structure reported
under CC BY 4.0. The XML instances themselves were authored for DeepPlant.
The directory's [attribution record](tests/fixtures/dexpi/2.0.0/ATTRIBUTION.md)
identifies the upstream sources, licence, attribution, modifications, and
limitations. Verify any future reuse against the upstream terms; do not infer
that every DEXPI-associated work is covered by CC BY 4.0.

## DeepPlant-original assets

The packaged `basic` process SVG symbols are documented as DeepPlant-original,
non-normative fallback assets in
[`src/deepplant/assets/symbols/process/basic/README.md`](src/deepplant/assets/symbols/process/basic/README.md).
That record is the per-asset provenance source and does not claim standards
compliance.

The brand logo artwork in [`assets/brand/logo/`](assets/brand/logo/) is
project-authored. Its horizontal wordmark paths were generated from Inter Bold,
then converted to vector outlines; the SVGs have no runtime font dependency.
Inter is distributed under the SIL Open Font License 1.1. The [asset
record](assets/brand/logo/README.md) links the Inter project and licence and
states the variants and distribution terms.

## Engineering Editor frontend dependencies (Issue #75)

The local editor SPA under [`apps/editor/`](apps/editor/) is built with the
following direct dependencies. They are build/dev-time dependencies of the SPA;
the Python wheel does not bundle or redistribute any JavaScript, and the built
`apps/editor/dist` output is not committed.

| Dependency | Declared range | Licence | Why it is needed now |
|---|---|---|---|
| `vue` | `^3.5.43` | MIT | SPA foundation selected by the reuse-first frontend architecture (Issue #70). |
| `@vue-flow/core` | `^1.48.2` | MIT | Interactive canvas candidate selected by Issue #70; used only behind the DeepPlant projection/adapter boundary. |
| `vite` | `^8.3.2` | MIT | Frontend dev server and production bundler. |
| `typescript` | `~5.9.3` | Apache-2.0 | Strict TypeScript checking. Pinned to the 5.x line because `vue-tsc` does not support the TypeScript 7 package layout yet. |
| `vue-tsc` | `^3.3.12` | MIT | Type checking of `.vue` single-file components. |
| `vitest` | `^5.0.3` | MIT | Frontend unit tests for the adapter and the selection → Inspector mapping. |
| `@vitejs/plugin-vue` | `^6.0.9` | MIT | Vue SFC support for Vite. |
| `pnpm` | pinned `10.20.0` in `apps/editor/package.json` | MIT | Package manager; a build-time tool, not distributed or linked. |

Deliberately **not** added: Reka UI, Dockview, Monaco, ELK/elkjs, Pinia,
shadcn-vue, Tailwind, jsdom, a browser E2E framework, or any third-party
engineering symbol asset. The engineering symbols remain the DeepPlant-original
`basic` pack (see above), served from the Python package.

## Engineering Editor frontend lint tooling (Issue #80)

The canonical frontend lint gate (`apps/editor/eslint.config.js`, run by
`pnpm lint` / `make frontend-lint`) is built from the following direct
**dev-only** dependencies. Like the SPA dependencies above, they are build/dev
time only: the Python wheel bundles no JavaScript and `apps/editor/dist` is not
committed.

| Dependency | Declared range | Licence | Why it is needed now |
|---|---|---|---|
| `eslint` | `^10.12.0` | MIT | The lint engine; flat-config based, one of the four independent frontend gates. |
| `@eslint/js` | `^10.0.1` | MIT | ESLint's own recommended JavaScript correctness rules. |
| `typescript-eslint` | `^8.71.0` | MIT | TypeScript parser plus lint rules; enforces the explicit-`any` ban and unused-code checks. |
| `eslint-plugin-vue` | `^10.11.1` | MIT | Vue 3 SFC correctness rules (`flat/essential`); also brings the Vue parser. |
| `globals` | `^17.13.0` | MIT | Standard browser and node global definitions for the linted files. |

`eslint-plugin-vue` requires `vue-eslint-parser` (MIT) and
`@typescript-eslint/parser` (MIT, provided by `typescript-eslint`) as peers; they
are resolved transitively and are not separately declared.

Deliberately **not** added by Issue #80: Prettier (the gate enforces correctness,
not a second formatter) and UnoCSS (the selected canonical styling direction — see
[`docs/dev/frontend/styling.md`](docs/dev/frontend/styling.md) — whose integration
and CSS migration are deferred to #81, so no unused dependency is recorded).

## Standards, vendors, and unresolved boundaries

The repository contains project-authored standards summaries and references;
it does not redistribute restricted ISO, IEC, or ISA standards content. DEXPI,
COMOS, and AVEVA are mentioned as interoperability references or future
integration targets. No COMOS or AVEVA proprietary files are included here.

Future schemas, symbols, vendor formats, industrial project material,
documentation, screenshots, datasets, generated data, or copied examples need
item-level provenance and a redistribution-compatible licence before inclusion.
Where ownership, licence scope, or derivation is unclear, the item remains
unresolved and must not be described as owned by DeepPlant or its maintainer.
