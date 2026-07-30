.PHONY: format lint policy test verify

NOX := uv tool run --from 'nox[uv]==2026.4.10' nox -f noxfile.py

format:
	uv run --frozen ruff format .

lint:
	$(NOX) -s lint

policy:
	$(NOX) -s policy

test:
	$(NOX) -s tests

verify:
	$(NOX) -s verify
