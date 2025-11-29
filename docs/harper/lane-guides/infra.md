## Lane Guide — infra

### Tools
- tests: `pytest` for infra helpers, `kubectl` conformance scripts.
- lint: `yamllint`, `kubeval` for manifests.
- types: not applicable; enforce schema via JSONSchema.
- security: `trivy config` for manifests, `vault-scan` for policy.
- build: `helm template` or `kustomize build` packaging into GitOps repo.

### CLI Examples
- Local: `kubectl apply --dry-run=client -f k8s/`.
- Containerized: `docker run --rm -v $PWD:/infra registry.corp.local/ops/cli bash -c "kubeval k8s/*.yaml"`.

### Default Gate Policy
- min coverage: all manifests validated; probes defined.
- max criticals: 0 High from Trivy config/vault scans.

### Enterprise Runner Notes
- SonarQube: infra configs tracked as IaC project with policy checks.
- Jenkins: infra lane uses service account to apply to dev cluster; artifacts stored under `infra-manifests.zip`.

### TECH_CONSTRAINTS integration
- air-gap: kubectl context targets on-prem clusters only; Vault only accessible via internal mesh.
- registries: images sourced from `registry.corp.local` mirrors, Kong/Ory/Vault references pre-approved.