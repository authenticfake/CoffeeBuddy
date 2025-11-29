## TODO_NEXT
- Harden autoscaling: add HPA guidance for API deployment and KEDA (or equivalent) for reminder workers to keep latency consistent under surges.
- Ship automated Postman/OpenAPI export in CI artifacts so downstream testers do not rely on manual curl steps.
- Extend observability with alert runbooks (error budget, Kafka lag dashboards) to streamline on-call readiness.
- Provide redaction tooling for audit/data reset verification reports to simplify compliance reviews.
- Document blue/green rollout plus rollback scripts for multi-cluster deployments.