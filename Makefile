
.PHONY: install run test lint format typecheck up down logs db

install:
	pip install -e ".[dev]"

run:
	python -m uvicorn financial_ai.api.main:app --reload

test:
	python -m pytest

lint:
	python -m ruff check src tests scripts

format:
	python -m ruff format src tests scripts

typecheck:
	python -m mypy src

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f api

db:
	docker compose exec postgres psql -U financial_ai -d financial_ai
