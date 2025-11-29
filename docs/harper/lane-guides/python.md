## Lane Guide — python

### Tools
- tests: `pytest`, `pytest-asyncio`, Slack SDK stubs.
- lint: `ruff` aligned to org rules.
- types: `mypy` strict optional mode.
- security: `bandit`, `pip-audit` against internal mirror.
- build: `poetry build` or `pip wheel` feeding Docker via internal registry.

### CLI Examples
- Local: `poetry run pytest -q`.
- Containerized: `docker run --rm -v $PWD:/app coffee/python:3.12 bash -c "pip install -r requirements-dev.txt && pytest"`.

### Default Gate Policy
- min coverage: 80% line.
- max criticals: 0 High/Critical from Bandit or SCA.

### Enterprise Runner Notes
- SonarQube: upload via `sonar-scanner` using Python profile.
- Jenkins: pipeline stages for lint → typecheck → tests → coverage; artifacts archived under `/var/lib/jenkins/artifacts`.

### TECH_CONSTRAINTS integration
- air-gap: use internal PyPI mirror, offline Slack SDK wheel cached.
- registries: push images to `registry.corp.local/coffee/python`.