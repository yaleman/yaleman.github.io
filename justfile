[private]
default:
    just --list

check: lint mypy biome

lint:
    uv run ruff check generate.py tests

mypy:
    uv run ty check
    uv run mypy --strict generate.py tests

biome:
    npx --yes @biomejs/biome lint site/search.js site/style.css

test:
    uv run pytest
