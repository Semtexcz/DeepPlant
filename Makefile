.PHONY: setup dev run test format format-check lint typecheck api-schema api-generate api-check e2e e2e-production check build image-build image-inspect prod-up prod-status prod-smoke prod-down docs validate-docs validate-agent-skills down

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
COREPACK_HOME ?= $(abspath .corepack)
PNPM ?= corepack pnpm
FRONTEND_PNPM = mkdir -p $(COREPACK_HOME) && cd frontend && COREPACK_HOME=$(COREPACK_HOME) $(PNPM)
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



check: validate-docs validate-agent-skills format-check lint typecheck test


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

	@test -f README.md
	@test -f AGENTS.md
	@test -f docs/architecture.md
	@test -f docs/product.md
	@test -f docs/workflow.md
	@test -f docs/quality.md
	@test -f project/brief.md


validate-agent-skills:
	PYTHONDONTWRITEBYTECODE=1 python tools/agent.py validate-skills



down:

	@true

