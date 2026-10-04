.PHONY: setup dev run test format format-check lint typecheck frontend-install frontend-typecheck frontend-test frontend-build frontend-check api-schema api-generate api-check e2e e2e-production check build image-build image-inspect prod-up prod-status prod-smoke prod-down docs validate-docs validate-agent-skills down

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


frontend-install:

	$(FRONTEND_PNPM) install --frozen-lockfile $(PNPM_INSTALL_FLAGS)


frontend-typecheck: frontend-install

	$(FRONTEND_PNPM) run typecheck


frontend-test: frontend-install

	$(FRONTEND_PNPM) run test


frontend-build: frontend-install

	$(FRONTEND_PNPM) run build


frontend-check: frontend-typecheck frontend-test frontend-build


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



check: validate-docs validate-agent-skills format-check lint typecheck test frontend-check


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
	@test ! -e docs/standards.md
	@test -f docs/dev/history/implementation-slices.md
	@test -f docs/contracts/rendering.md
	@test -f docs/dev/reference/svg-symbols.md
	@test -f docs/user/index.md
	@test -f docs/user/getting-started.md
	@test -f docs/user/concepts/what-is-deepplant.md
	@test -f docs/user/how-to/author-plant-yaml.md
	@test -f docs/user/how-to/validate-a-model.md
	@test -f docs/user/how-to/diagnose-validation-errors.md
	@test -f docs/user/how-to/render-process-svg.md
	@test -f docs/user/reference/index.md
	@test -f project/brief.md


validate-agent-skills:
	PYTHONDONTWRITEBYTECODE=1 python tools/agent.py validate-skills



down:

	@true

