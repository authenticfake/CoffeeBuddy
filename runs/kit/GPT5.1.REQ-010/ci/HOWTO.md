# HOWTO — REQ-010 Runtime Execution & CI

This document explains how to run, test, and integrate the CoffeeBuddy
runtime service introduced in REQ-010.

## Prerequisites

- Python 3.12 available on your PATH.
- Recommended: virtual environment (venv).
- Network access to Vault and Ory for full readiness behavior in
  non-test environments (not required for unit tests).
- For Kubernetes deployment:
  - Access to a cluster.
  - Ability to create Deployments, Services, and Kong resources.
  - Existing Vault and Ory endpoints reachable from the cluster.

## Local environment setup

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

pip install -r runs/kit/REQ-010/requirements.txt
```

Common issues:

- If `python` points to a different version, use `python3.12` explicitly.
- Ensure your shell is using the virtual environment before running
  commands (check `which python` / `where python`).

## Running the service locally

```bash
export COFFEEBUDDY_ENVIRONMENT=dev
export COFFEEBUDDY_HTTP_PORT=8080
# Optional: configure Vault and Ory if you want readiness to succeed
# export VAULT_ADDR="https://vault.internal:8200"
# export VAULT_TOKEN="..."
# export ORY_BASE_URL="https://ory.internal"

uvicorn coffeebuddy.infrastructure.runtime.app:create_app --factory --host 0.0.0.0 --port 8080
```

Endpoints:

- `http://localhost:8080/health/live`
- `http://localhost:8080/health/ready`
- `http://localhost:8080/metrics`

## Running tests

From the repository root:

```bash
source .venv/bin/activate
pip install -r runs/kit/REQ-010/requirements.txt

pytest -q runs/kit/REQ-010/test
```

The LTC (`runs/kit/REQ-010/ci/LTC.json`) declares:

- Tool: `pytest`
- Case: `tests` running `pytest -q runs/kit/REQ-010/test` with `cwd="."`.

## Enterprise CI / Runner Integration

Most enterprise CI tools (Jenkins, GitLab CI, Azure DevOps, etc.) can
execute the same commands defined in `LTC.json`:

1. Ensure Python 3.12 and pip are available in the agent/container.
2. Install dependencies:

   ```bash
   pip install -r runs/kit/REQ-010/requirements.txt
   ```

3. Run tests:

   ```bash
   pytest -q runs/kit/REQ-010/test
   ```

4. Optionally enable JUnit and coverage reporting:

   ```bash
   pytest --junitxml=reports/junit-REQ-010.xml --cov=coffeebuddy --cov-report=xml:reports/coverage-REQ-010.xml runs/kit/REQ-010/test
   ```

Configure your CI to collect:

- `reports/junit-REQ-010.xml` (test results)
- `reports/coverage-REQ-010.xml` (coverage)

These paths match the `reports` section of `LTC.json`.

## Kubernetes deployment

1. Build and push the CoffeeBuddy image:

   ```bash
   docker build -t registry.internal/coffeebuddy:REQ-010 .
   docker push registry.internal/coffeebuddy:REQ-010
   ```

2. Edit `runs/kit/REQ-010/src/coffeebuddy/infrastructure/runtime/k8s/deployment.yaml`:

   - Set `image: registry.internal/coffeebuddy:REQ-010`.
   - Ensure environment variable sources (`Secret`, `ConfigMap`) exist.

3. Apply manifests:

   ```bash
   kubectl apply -f runs/kit/REQ-010/src/coffeebuddy/infrastructure/runtime/k8s/deployment.yaml
   ```

4. (Optional) Deploy Kong route config:

   ```bash
   kubectl apply -f runs/kit/REQ-010/src/coffeebuddy/infrastructure/runtime/kong/route.yaml
   ```

5. Verify pods:

   ```bash
   kubectl get pods -l app=coffeebuddy
   kubectl describe pod <pod-name>
   ```

Readiness and liveness probes are configured to use
`/health/ready` and `/health/live` respectively.

## Prometheus & Observability

The deployment manifest includes annotations:

- `prometheus.io/scrape: "true"`
- `prometheus.io/port: "8080"`
- `prometheus.io/path: "/metrics"`

Ensure your Prometheus operator or scraping configuration honors these
annotations.

## Troubleshooting

- **Import errors (`ModuleNotFoundError: coffeebuddy...`)**
  - Ensure you run commands from the repository root so that Python can
    resolve the `runs/kit/REQ-010/src` tree via the default module
    search path.
  - Alternatively, set `PYTHONPATH`:

    ```bash
    export PYTHONPATH="$PWD/runs/kit/REQ-010/src:${PYTHONPATH:-}"
    ```

- **Readiness always failing (`vault`/`ory` unavailable)**
  - Check that `VAULT_ADDR` / `ORY_BASE_URL` are set and reachable from
    the pod.
  - Verify TLS and internal DNS configuration for these hosts.

- **Metrics not scraped**
  - Confirm that the Prometheus deployment is configured to read pod
    annotations.
  - Ensure network policies (if any) allow Prometheus to reach the
    CoffeeBuddy pods on port 8080.

- **Timeouts on health endpoints**
  - The HTTP clients for Vault and Ory use a 2-second timeout. Under
    abnormal conditions you may see timeouts; Kubernetes will use these
    failures for readiness decisions. Investigate underlying network or
    service issues.

```

---

**KIT Iteration Log**

- **Targeted REQ-ID(s)**: REQ-010 (runtime integration with Kubernetes, Kong, Vault, Ory, Prometheus). This is the foundational infra REQ per PLAN batch 1.
- **In/Out of scope**:
  - In scope: ASGI app factory, health endpoints, metrics endpoint, Vault/Ory health wiring, example K8s + Kong manifests, basic tests.
  - Out of scope: DB/Kafka wiring, Slack endpoints, detailed logging/metrics (covered by later REQs).
- **How to run tests**:
  - `pip install -r runs/kit/REQ-010/requirements.txt`
  - `pytest -q runs/kit/REQ-010/test`
- **Prerequisites**:
  - Python 3.12
  - Optional: access to Kubernetes, Kong, Vault, Ory, Prometheus for runtime validation (not required for unit tests).
- **Dependencies and mocks**:
  - Production paths use real `httpx` HTTP clients for Vault/Ory.
  - Tests inject fake `VaultClient` and `OryClient` implementations via the `create_app` factory to avoid network calls.
- **Product Owner Notes**:
  - Readiness currently requires both Vault and Ory to be healthy. If future requirements call for softer degradation (e.g., treat Ory as optional for some endpoints), we can extend the readiness logic while keeping the existing client abstractions.
- **RAG citations**:
  - SPEC.md: used for understanding health, Vault, Ory, and Prometheus requirements.
  - PLAN.md (REQ-010 section): guided module placement under `coffeebuddy.infrastructure.runtime` and clarified that this REQ owns runtime/Kubernetes/Kong/Vault/Ory/Prometheus glue.
  - TECH_CONSTRAINTS.yaml: confirmed Python 3.12 runtime and Prometheus observability expectations.

```json
{
  "index": [
    {
      "req": "REQ-010",
      "src": [
        "runs/kit/REQ-010/src/coffeebuddy/__init__.py",
        "runs/kit/REQ-010/src/coffeebuddy/infrastructure/__init__.py",
        "runs/kit/REQ-010/src/coffeebuddy/infrastructure/runtime/__init__.py",
        "runs/kit/REQ-010/src/coffeebuddy/infrastructure/runtime/settings.py",
        "runs/kit/REQ-010/src/coffeebuddy/infrastructure/runtime/clients.py",
        "runs/kit/REQ-010/src/coffeebuddy/infrastructure/runtime/app.py",
        "runs/kit/REQ-010/src/coffeebuddy/infrastructure/runtime/k8s/deployment.yaml",
        "runs/kit/REQ-010/src/coffeebuddy/infrastructure/runtime/kong/route.yaml"
      ],
      "tests": [
        "runs/kit/REQ-010/test/infrastructure/test_runtime_app.py"
      ]
    }
  ]
}