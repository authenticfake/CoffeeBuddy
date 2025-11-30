## Lane Guide — infra

### Tools
- tests: `pytest` for infra modules plus `tox` profile `infra`
- lint: `ruff` for Python infra code, `yamllint` for manifests
- types: `mypy` on `infra.platform`
- security: `trivy config` for Kubernetes specs, `trivy fs` for images
- build: `docker build -f Dockerfile` with hardened base image

### CLI Examples
- Local: `poetry run pytest tests/infra && trivy fs . && kubectl apply --dry-run=client -f k8s/`
- Containerized: `docker compose run --rm infra bash -lc "pytest tests/infra && trivy config k8s"`

### Default Gate Policy
- min coverage: 80% on infra modules
- max criticals: 0 Trivy HIGH/CRITICAL, 0 failing readiness probes

### Enterprise Runner Notes
- SonarQube: import infra repo using Python + YAML analyzers
- Jenkins: pipeline stages `vault-smoke`, `ory-smoke`, `k8s-probes`; artifacts stored in Artifactory with signed manifests

### TECH_CONSTRAINTS integration
- air-gap: base images from `harbor.corp.local/python-secure`; kubectl and helm binaries mirrored internally
- registries: Vault secret paths accessible via on-prem endpoints; Ory tokens fetched from internal IdP only