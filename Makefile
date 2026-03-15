.PHONY: setup lint test ingest enrich score validate build pipeline serve

setup:
	uv sync --all-extras

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest -v

ingest:
	uv run python -m pipeline.ingest

enrich:
	uv run python -m pipeline.enrich

score:
	uv run python -m pipeline.score

validate:
	uv run python -m pipeline.validate

build:
	uv run python -m pipeline.build

pipeline: ingest enrich score validate build

serve:
	cd site && python -m http.server 8888
