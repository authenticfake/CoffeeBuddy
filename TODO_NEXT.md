# TODO_NEXT

- Implement horizontal scaling guidance for reminder worker (partition assignment, consumer groups) to meet >10 runs/day scenarios.
- Add automated fairness audit dashboard or CLI to visualize runner distribution over time.
- Provide blue/green deployment checklist for Kong + Ory integration to streamline prod cutovers.
- Harden telemetry by exporting structured tracing (OpenTelemetry) beyond current logging + metrics.
- Extend Postman/Newman suite with full E2E script covering admin disable/reset flows.

## Assumptions
- Future sprints will target production readiness for >2 pilot channels and higher reminder throughput.