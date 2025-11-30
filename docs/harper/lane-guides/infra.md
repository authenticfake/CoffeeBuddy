## Lane Guide — infra

### Tools

- tests: kubeval or kubeconform for manifest validation, kubectl and helm for dry runs
- lint: yamllint, kube-linter or equivalent for Kubernetes best practices
- types: schema validation for Kubernetes resources, OpenAPI for ingress where applicable
- security: trivy or similar for image scanning, Polaris or OPA Gatekeeper for policy checks
- build: docker or Podman for images, Helm or Kustomize for manifests

### CLI Examples

- Local:
  - Validate manifests: `kubeconform -strict -summary k8s/*.yaml`
  - Lint YAML: `yamllint k8s`
  - Helm template: `helm template coffeebuddy ./chart`
- Containerized:
  - Run infra tests: `docker run --rm -v $PWD/k8s:/k8s kubeconform-image ...`
  - Use CI job to apply manifests to dev cluster with `kubectl apply`

### Default Gate Policy

- min coverage: all Kubernetes manifests validated and linted in CI before deployment
- max criticals: zero critical image vulnerabilities and zero high severity policy violations
- reliability: liveness and readiness probes required for all workloads, resource limits defined

### Enterprise Runner Notes

- SonarQube: limited direct infra support, treat manifests as infrastructure as code reviewed via separate tooling
- Jenkins: pipelines for build image, scan image, validate manifests, then deploy to dev and later environments
- Artifacts: store rendered manifests and Helm charts in artifact repositories for traceability

### TECH_CONSTRAINTS integration

- air-gap: base images pulled from internal registries, Kubernetes cluster is on prem only
- registries: all images referenced via internal registry URLs, no public registry at deploy time
- tokens: use Vault or Kubernetes secrets for Slack tokens DB credentials OIDC settings, rotate according to policy