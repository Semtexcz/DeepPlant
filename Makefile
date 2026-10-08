.PHONY: setup dev run test format format-check lint typecheck typecheck-desktop architecture-check symbol-gallery frontend-install frontend-lint frontend-typecheck frontend-test frontend-build frontend-check frontend-e2e package-editor verify-packaged-editor api-schema api-generate api-check e2e e2e-production check build image-build image-inspect prod-up prod-status prod-smoke prod-down docs validate-docs validate-agent-skills down

PROJECT_TYPE := script
RUNTIME_LEVEL := shared
GOVERNANCE := lightweight
WORKFLOW_MODE := pr
PROJECT_SLUG := deepplant
HOST ?= 127.0.0.1
PORT ?= 8000
PROD_BACKEND_PORT ?= 8000
PROD_FRONTEND_PORT ?= 3000
BACKEND_IMAGE ?= $(PROJECT_SLUG)-backend:production
FRONTEND_IMAGE ?= $(PROJECT_SLUG)-frontend:production
COMPOSE ?= docker compose
# The editor application pins its package manager in apps/editor/package.json
# (`packageManager`). `pnpm` is used directly; `corepack enable` makes the pinned
# version available when only Corepack is installed.
PNPM ?= pnpm
FRONTEND_DIR ?= apps/editor
FRONTEND_PNPM = cd $(FRONTEND_DIR) && $(PNPM)
PNPM_INSTALL_FLAGS ?=
OPENAPI_SCHEMA ?= artifacts/openapi.json

setup:

	uv sync


dev:

	uv run python -m deepplant


run:

	uv run python -m deepplant


test:

	uv run pytest


lint:

	uv run ruff check .


format:

	uv run ruff format .


format-check:

	uv run ruff format --check .


typecheck:

	uv run pyright


# Deterministic Python architecture and size guardrails (Issue #108): a small,
# repository-owned, standard-library checker over src/deepplant/** and tests/**.
# Soft-limit findings are informative; hard-limit and import-boundary
# violations fail with a non-zero exit code.
architecture-check:

	uv run python tools/architecture_check.py


# Generated developer symbol gallery (Issue #121). Renders every definition in the
# canonical `deepplant.symbols` registry through the production renderer into the
# ignored build directory, so a developer can inspect geometry, anchors, asset
# provenance, and standards state in a static local page. Derived artifact only:
# never canonical geometry, never committed, and never part of packaging or
# runtime.
symbol-gallery:

	uv run python tools/generate_symbol_gallery.py


# Desktop-specific strict type check (Issue #93 review). The default `typecheck`
# excludes the src/deepplant/editor/desktop_qt/ package because the fast `dev`
# environment deliberately does not install PySide6. The native packaging jobs do
# install the `desktop` group, so they run this config, which mirrors the
# canonical strict settings but keeps every module (including the desktop_qt
# package) in scope.
typecheck-desktop:

	uv run --group dev --group desktop pyright --project pyrightconfig.desktop.json


frontend-install:

	$(FRONTEND_PNPM) install --frozen-lockfile $(PNPM_INSTALL_FLAGS)


# Frontend lint is the canonical ESLint gate for `apps/editor/` (flat config in
# `apps/editor/eslint.config.js`). It enforces Vue/TypeScript correctness rules,
# forbids explicit `any`, and implements the hard size/cohesion limits from
# `docs/dev/frontend/architecture.md`. It does not replace `frontend-typecheck`.
frontend-lint: frontend-install

	$(FRONTEND_PNPM) run lint


frontend-typecheck: frontend-install

	$(FRONTEND_PNPM) run typecheck


frontend-test: frontend-install

	$(FRONTEND_PNPM) run test


# Production SPA bundle (`vite build`). This is a separate production-build
# verification and is intentionally outside the fast default local confidence
# gate (`frontend-check`/`check`). Beyond the TypeScript contract that
# `frontend-typecheck` already proves, a production build can also catch build
# configuration, module resolution, asset, plugin, or bundling failures. It is
# exercised by `make frontend-e2e` and the packaging jobs; run it explicitly
# (or through `make frontend-e2e`) when a change concerns the shipped SPA.
frontend-build: frontend-install

	$(FRONTEND_PNPM) run build


# Default frontend confidence gate: lint, typecheck, tests. Fast enough for the
# normal inner loop. It deliberately excludes the production build, which is the
# separate `frontend-build` target above.
frontend-check: frontend-lint frontend-typecheck frontend-test


# Browser/system E2E: the real local `deepplant ui` CLI serving the production
# build, driven by a real Chromium browser (see docs/dev/frontend/testing.md).
# Separate from `frontend-check`/`check`: it builds the production SPA and needs a
# Chromium binary, so it is kept out of the fast default gate. Install Chromium
# once with `cd apps/editor && pnpm exec playwright install chromium`.
frontend-e2e: frontend-build

	$(FRONTEND_PNPM) run e2e


# Standalone Editor packaging (Issue #85). The canonical operation is the
# cross-platform Python driver; these wrappers are developer convenience only,
# because Windows CI calls the driver directly and must not need GNU Make.
# The `desktop` group supplies PySide6/Qt WebEngine (Issue #93); it is never part
# of `make setup`/`check`. Deliberately outside `check`: packaging is slow and
# platform-specific.
package-editor:

	uv run --group package --group desktop python tools/package_editor.py all


verify-packaged-editor:

	uv run --group package --group desktop python tools/package_editor.py verify


api-schema:

	@true


api-generate: api-schema

	@true


api-check: api-schema

	@true


e2e:

	@true


e2e-production:

	@true



# The single canonical local confidence gate. Run it once before finalizing a
# pull request, not after every edit. It is deliberately a developer-confidence
# gate, not a release/distribution gate: the heavy or platform-specific checks
# stay outside it --
#   frontend-build           production SPA bundle
#   frontend-e2e             Playwright/Chromium system tests over the real CLI
#   package-editor           Windows installer / Linux AppImage + desktop verify
#   verify-packaged-editor   native packaged-app verification
#   typecheck-desktop        strict PySide6 type check (desktop group)
#   build                    release wheel/sdist (`uv build`)
# CI runs this gate plus those stronger jobs asynchronously.
check: validate-docs validate-agent-skills format-check lint typecheck test architecture-check frontend-check


build:

	rm -rf dist
	uv build


image-build:

	@true


image-inspect:

	@true


prod-up:

	@true


prod-status:

	@true


prod-smoke:

	@true


prod-down:

	@true


docs:

	@echo "Project docs live under docs/ and project/brief.md."




validate-docs:

	@test -f VISION.md
	@test -f README.md
	@test -f AGENTS.md
	@test -f docs/dev/architecture/index.md
	@test -f docs/dev/planning/index.md
	@test -f docs/dev/planning/roadmap.md
	@test -f docs/dev/planning/direction.md
	@test -f docs/dev/planning/product.md
	@test -f docs/dev/planning/strategy.md
	@test -f docs/dev/workflow/index.md
	@test -f docs/dev/workflow/quality.md
	@test -f docs/index.md
	@test -f docs/dev/workflow/conventions.md
	@test -f docs/dev/workflow/documentation-migration.md
	@test -f docs/contracts/index.md
	@test -f docs/contracts/plant-model.md
	@test -f docs/contracts/process-model.md
	@test -f docs/contracts/physical-piping.md
	@test -f docs/contracts/yaml-format.md
	@test -f docs/contracts/cli.md
	@test -f docs/dev/reference/dexpi-process-adapter.md
	@test -f docs/dev/decisions/index.md
	@test -f docs/dev/research/index.md
	@test -f docs/dev/workflow/standards.md
	@test -f docs/dev/reference/standards-registry.md
	@test -f docs/dev/research/standards-licensing-evidence.md
	@test -f docs/dev/research/standalone-editor-distribution.md
	@test -f docs/dev/research/editor-desktop-host.md
	@test ! -e docs/standards.md
	@test -f docs/dev/history/implementation-slices.md
	@test -f docs/dev/history/gate-decisions.md
	@test -f docs/contracts/rendering.md
	@test -f docs/dev/reference/svg-symbols.md
	@test -f docs/dev/reference/symbol-library.md
	@test -f docs/dev/reference/mvp-symbol-coverage.md
	@test -f docs/dev/reference/symbol-seed-geometry.md
	@test -f docs/dev/workflow/packaging.md
	@test -f docs/dev/frontend/index.md
	@test -f docs/dev/frontend/architecture.md
	@test -f docs/dev/frontend/vue.md
	@test -f docs/dev/frontend/typescript.md
	@test -f docs/dev/frontend/styling.md
	@test -f docs/dev/frontend/testing.md
	@test -f docs/dev/frontend/accessibility.md
	@test -f docs/dev/frontend/design-to-code.md
	@test -f docs/dev/python/index.md
	@test -f docs/dev/python/architecture.md
	@test -f docs/dev/python/conventions.md
	@test -f docs/dev/python/typing.md
	@test -f docs/dev/python/errors.md
	@test -f docs/dev/python/scientific-computation.md
	@test -f docs/dev/python/testing.md
	@test -f .agents/skills/frontend-engineering/SKILL.md
	@test -f .agents/skills/python-engineering/SKILL.md
	@test -f docs/user/index.md
	@test -f docs/user/getting-started.md
	@test -f docs/user/concepts/what-is-deepplant.md
	@test -f docs/user/how-to/author-plant-yaml.md
	@test -f docs/user/how-to/validate-a-model.md
	@test -f docs/user/how-to/diagnose-validation-errors.md
	@test -f docs/user/how-to/render-process-svg.md
	@test -f docs/user/how-to/install-the-editor.md
	@test -f docs/user/reference/index.md
	@test -f project/brief.md


validate-agent-skills:
	PYTHONDONTWRITEBYTECODE=1 python tools/agent.py validate-skills



down:

	@true

