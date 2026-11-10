# camp-payment-service

A payment processing microservice for the CAMP platform: application code, automated tests,
the container build, and the Helm chart that describes how it runs. It has no cloud-provider
dependencies; where and which version it runs is decided in
[camp-k8s-gitops](https://github.com/princengcobo186-sketch/camp-k8s-gitops).

| Repository | Owns |
|---|---|
| [camp-infra-live](https://github.com/princengcobo186-sketch/camp-infra-live) | AWS foundations, the Argo CD install and its root Application |
| [camp-k8s-gitops](https://github.com/princengcobo186-sketch/camp-k8s-gitops) | Desired cluster state per environment |
| **camp-payment-service** (this) | Application code, tests, container image, Helm chart |

## Stack

Python + FastAPI, managed with `uv`. Container image built once per commit, scanned, and
pushed to Amazon ECR with an immutable tag. Promotion between environments reuses that exact
image and never rebuilds.

## Design guardrails

- Money is stored as integer minor units; currency is validated at the API edge.
- `POST /payments` requires an `Idempotency-Key`, so retries never double-charge.
- No real card data. The payment provider is a fake adapter, which keeps the service out of PCI scope.
- Configuration comes from the environment and fails closed when required values are missing.
- Structured JSON logs, Prometheus `/metrics`, and liveness/readiness probes ship with the code.

## Status

Phase 0 (foundations). The service, Dockerfile and chart land in Phase 1. Plan:
[camp-infra-live/docs/platform-plan.md](https://github.com/princengcobo186-sketch/camp-infra-live/blob/main/docs/platform-plan.md).
