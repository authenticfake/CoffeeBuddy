## Lane Guide — python

### Tools

- tests: pytest, pytest-asyncio, requests-mock for HTTP, moto or equivalents if cloud mocks are ever needed but avoid non required
- lint: flake8 or ruff, isort for imports, black for formatting
- types: mypy with strictness for core domains, typing-extensions as needed
- security: bandit for static analysis, dependency scanner aligned with internal tooling
- build: docker or Podman for images, pip-tools or uv for lockfiles where allowed

### CLI Examples

- Local:
  - Run tests: `pytest -q`
  - Run type checks: `mypy coffeebuddy`
  - Run lints: `ruff check coffeebuddy`
  - Start dev server: `uvicorn coffeebuddy.app.main:app --reload`
- Containerized:
  - Build image: `docker build -t coffeebuddy:dev .`
  - Run tests in container: `docker run --rm coffeebuddy:dev pytest -q`

### Default Gate Policy

- min coverage: 80% line coverage for new and changed python modules
- max criticals: zero critical or high severity findings from bandit or dependency scanner before merge
- quality: no new mypy errors, lints must pass with no fatal issues

### Enterprise Runner Notes

- SonarQube: configure Python analysis using existing project key, import coverage via XML generated from pytest
- Jenkins or similar CI: use pipeline stages for lint, type-check, tests, coverage, and image build, publish artifacts and reports
- Artifacts: store coverage reports, junit XML, and built images in internal artifact or container registry

### TECH_CONSTRAINTS integration

- air-gap: use internal Python package mirror, pin versions and vendor critical dependencies if external access restricted
- registries: push images only to approved on prem registry, reference via internal DNS in Kubernetes manifests
- tokens: obtain registry and SCM tokens via Vault or CI secret store, never hardcode in repository