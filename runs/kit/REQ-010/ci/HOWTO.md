# HOWTO — REQ-010 Runtime Execution

## Prerequisites
- Python 3.12 with `pip`
- Docker (for container build)
- Access to on-prem Kubernetes, Kong, Vault, Ory, and Prometheus clusters
- Slack app credentials stored in Vault
- Kafka and Postgres endpoints reachable from cluster

## Local Setup
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r runs/kit/REQ-010/requirements.txt
export PYTHONPATH=$PWD/runs/kit/REQ-010/src
```

## Running Tests
```bash
mkdir -p runs/kit/REQ-010/reports
PYTHONPATH=runs/kit/REQ-010/src pytest -q runs/kit/REQ-010/test --junitxml=runs/kit/REQ-010/reports/junit.xml
```

## Building the Image
```bash
cd runs/kit/REQ-010
docker build -t coffeebuddy/runtime:0.1.0 -f src/Dockerfile .
```

## Kubernetes Deployment
1. Apply ConfigMap/Secrets/Vault policy:
   ```bash
   kubectl apply -f src/infra/kubernetes/configmap.yaml
   vault policy write coffeebuddy-runtime src/infra/vault/policy.hcl
   ```
2. Deploy workload:
   ```bash
   kubectl apply -f src/infra/kubernetes/deployment.yaml
   kubectl apply -f src/infra/kubernetes/service.yaml
   kubectl apply -f src/infra/kubernetes/servicemonitor.yaml
   ```
3. Configure Kong + Ory:
   ```bash
   kubectl apply -f src/infra/kong/service-route.yaml
   kubectl apply -f src/infra/ory/client.yaml
   ```

## Environment Variables
Set via ConfigMap/Secret:
- `SERVICE_NAME`, `SERVICE_ENV`, `SERVICE_PORT`, `SERVICE_VERSION`
- `SLACK_SIGNING_SECRET`, `SLACK_BOT_TOKEN`
- `DATABASE_URL`
- `KAFKA_BROKERS`, `KAFKA_SECURITY_PROTOCOL`
- `VAULT_ADDR`, `VAULT_ROLE`, `VAULT_TOKEN_PATH`
- `ORY_ISSUER_URL`, `ORY_AUDIENCE`, `ORY_CLIENT_ID`
- `METRICS_PATH`, `PROMETHEUS_MULTIPROC_DIR` (optional)

## Enterprise Runner Notes
- Jenkins: add pipeline stage running the LTC command from `ci/LTC.json`.
- Sonar/Mend: not required for this REQ but add scanning stage before deploy if mandated.

## Troubleshooting
- **Readiness failures**: ensure Vault token file exists at `VAULT_TOKEN_PATH` and Kafka broker list non-empty.
- **Metrics scrape issues**: verify `ServiceMonitor` selector matches `app: coffeebuddy`.
- **Import errors**: confirm `PYTHONPATH` includes `runs/kit/REQ-010/src` during local scripts/tests.