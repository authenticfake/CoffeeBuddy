## Lane Guide — python

### Tools
- tests: `pytest` with coverage plugin (`pytest-cov`)
- lint: `ruff` (PEP8 + import sorting)
- types: `mypy --strict`
- security: `bandit -r src`
- build: `poetry build` or `pip wheel` within internal registry context

### CLI Examples
- Local: `poetry run pytest && poetry run ruff check . && poetry run mypy`
- Containerized: `docker compose run --rm app bash -lc "pytest && ruff check . && mypy"`

### Default Gate Policy
- min coverage: 80%
- max criticals: 0 Bandit HIGH findings, 0 Ruff errors

### Enterprise Runner Notes
- SonarQube: upload coverage via `sonar-scanner -Dsonar.python.coverage.reportPaths=coverage.xml`
- Jenkins: use shared library `py-ci` with stages lint → test → scan; artifacts stored in Nexus

### TECH_CONSTRAINTS integration
- air-gap: use internal PyPI mirror (`https://pypi.corp.local/simple`)
- registries: container builds push to `harbor.corp.local/coffeebuddy/python` with signed images