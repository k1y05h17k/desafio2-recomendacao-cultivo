UV ?= uv
RUN ?= $(UV) run --locked

.DEFAULT_GOAL := quality
.NOTPARALLEL:
.PHONY: up down lint typecheck security test quality pipeline docs

up:
	$(if $(wildcard docker-compose.yml),,$(error docker-compose.yml ausente: TASK-025))
	docker compose up -d --build lab

down:
	$(if $(wildcard docker-compose.yml),,$(error docker-compose.yml ausente: TASK-025))
	docker compose down

lint:
	$(if $(wildcard pyproject.toml),,$(error pyproject.toml ausente: TASK-003))
	$(RUN) ruff check src tests
	$(RUN) ruff format --check src tests

typecheck:
	$(if $(wildcard pyproject.toml),,$(error pyproject.toml ausente: TASK-003))
	$(RUN) mypy src

security:
	$(if $(wildcard uv.lock),,$(error uv.lock ausente: TASK-003))
	$(RUN) bandit -c pyproject.toml -r src $(wildcard scripts)
	$(UV) export --quiet --locked --no-emit-project --format requirements-txt -o .cache/requirements-audit.txt
	$(RUN) pip-audit --strict --disable-pip --require-hashes -r .cache/requirements-audit.txt

test:
	$(if $(wildcard pyproject.toml),,$(error pyproject.toml ausente: TASK-003))
	$(RUN) pytest --cov=cultivo --cov-report=term-missing

quality: lint typecheck security test

pipeline:
	$(if $(wildcard notebooks/00_entrega_parcial.ipynb),,$(error notebook ausente: criado pelo docs-writer na TASK-015; Prompt 13 nao executa etapas posteriores))
	$(RUN) jupyter nbconvert --to notebook --execute --inplace notebooks/00_entrega_parcial.ipynb

docs:
	$(error exportacao nao implementada: formato e destino devem ser definidos pelo docs-writer)
