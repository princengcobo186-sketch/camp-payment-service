# Local developer workflow. Nothing here needs cloud credentials.
CLUSTER   ?= camp
IMAGE     ?= camp/payment-service
LOCAL_TAG ?= local

.PHONY: help sync lint test chart-check build kind-load dev run
help:           ## list targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'

sync:           ## install pinned dependencies
	uv sync --frozen

lint:           ## ruff + mypy
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy

test:           ## unit + integration tests with coverage gate
	uv run pytest

chart-check:    ## helm lint + security posture + schema rejection checks
	./scripts/chart-check.sh

build:          ## build the container image locally
	docker build -t $(IMAGE):$(LOCAL_TAG) .

kind-load: build ## load the image into the Kind cluster (create it with camp-infra-live/scripts/kind-up.sh)
	kind load docker-image $(IMAGE):$(LOCAL_TAG) --name $(CLUSTER)

dev: kind-load  ## build, load, and restart the pod so Argo's local app runs the new image
	kubectl --context kind-$(CLUSTER) -n payments rollout restart deploy/payment-service

run:            ## run the service on :8080 without a container
	APP_ENV=local uv run python -m payment_service
