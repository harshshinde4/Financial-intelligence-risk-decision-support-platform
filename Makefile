install:
	pip install -e ".[dev]"

run:
	uvicorn financial_ai.api.main:app --reload

test:
	pytest

lint:
	ruff check .

format:
	ruff check . --fix

typecheck:
	mypy src

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f api

db:
	docker compose exec postgres psql -U financial_ai -d financial_ai
