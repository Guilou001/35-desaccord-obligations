.PHONY: setup test fetch run report
setup:
	uv sync --all-groups
test:
	uv run ruff check .
	uv run pytest
fetch:
	uv run desaccord fetch
run:
	uv run desaccord run
report:
	uv run --group report desaccord report
