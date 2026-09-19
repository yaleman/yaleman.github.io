[private]
default:
    just --list

check: lint typing biome

lint:
    uv run ruff check generate.py tests

typing:
    uv run ty check

biome:
    npx --yes @biomejs/biome lint site/search.js site/style.css

test:
    uv run pytest
