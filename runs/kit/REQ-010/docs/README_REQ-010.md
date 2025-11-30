# Runtime Integration (REQ-010)

## Purpose
Provides the CoffeeBuddy runtime shell required for on-prem Kubernetes deployment, including health/metrics endpoints, configuration bindings for Vault, Ory, Postgres, Kafka, and Kong, plus deployment manifests.

## Key Components
| Path | Description |
| --- | --- |
| `coffeebuddy/infrastructure/runtime/config.py` | Environment-driven configuration loader with validation |
| `coffeebuddy/infrastructure/runtime/app.py` | FastAPI factory exposing `/health/live`, `/health/ready`, and `/metrics` |
| `coffeebuddy/infrastructure/runtime/probes.py` | Probe registry and default environment readiness probe |
| `coffeebuddy/infrastructure/runtime/container.py` | Wires config, readiness probes, and metrics registry |
| `src/Dockerfile` + `scripts/docker-entrypoint.sh` | Production container image definition |
| `src/infra/kubernetes/*.yaml` | Deployment, Service, ServiceMonitor, ConfigMap, Ingress for Kong |
| `src/infra/kong/service-route.yaml` | Kong declarative configuration for Slack route |
| `src/infra/vault/policy.hcl` | Vault policy binding for CoffeeBuddy secrets |
| `src/infra/ory/client.yaml` | Ory rule enabling authenticated ingress traffic |

## Configuration
Set the following environment variables (typically via ConfigMap/Secrets):

- Core: `SERVICE_NAME`, `SERVICE_ENV`, `SERVICE_PORT`, `SERVICE_VERSION`
- Slack: `SLACK_SIGNING_SECRET`, `SLACK_BOT_TOKEN`, `SLACK_APP_ID`
- Database: `DATABASE_URL`, `DATABASE_POOL_MIN`, `DATABASE_POOL_MAX`
- Kafka: `KAFKA_BROKERS`, `KAFKA_SECURITY_PROTOCOL`, `KAFKA_SASL_USERNAME`, `KAFKA_SASL_PASSWORD`
- Vault: `VAULT_ADDR`, `VAULT_ROLE`, `VAULT_TOKEN_PATH`, `VAULT_SECRET_PATHS`
- Ory: `ORY_ISSUER_URL`, `ORY_AUDIENCE`, `ORY_CLIENT_ID`
- Metrics: `METRICS_PATH`, `PROMETHEUS_MULTIPROC_DIR`, `METRICS_ENABLE_PROCESS`

## Health & Metrics
- `/health/live`: process-level heartbeat
- `/health/ready`: readiness based on registered probes
- `/metrics`: Prometheus-compatible metrics (service info + process collectors)

## Deployment Flow
1. Build container via provided `Dockerfile`.
2. Apply `ConfigMap`, `Secrets`, `Vault` policy, and `ServiceAccount`.
3. Deploy Kubernetes manifests (Deployment, Service, ServiceMonitor).
4. Configure Kong ingress route and Ory/OIDC rule.
5. Point Slack slash-command + interaction URLs at Kong host.