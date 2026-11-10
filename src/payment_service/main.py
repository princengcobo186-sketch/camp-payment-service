"""HTTP API."""

import logging
import time
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from payment_service.config import Settings, load_settings
from payment_service.domain import Payment, PaymentRequest, process
from payment_service.observability import PAYMENTS, REQUESTS, configure_logging
from payment_service.store import IdempotencyConflictError, InMemoryStore

log = logging.getLogger("payment_service")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()  # raises ConfigError: the process must not start
    configure_logging(settings.log_level)
    store = InMemoryStore()
    app = FastAPI(title="camp-payment-service", version="0.1.0")

    @app.middleware("http")
    async def measure(request: Request, call_next):  # type: ignore[no-untyped-def]
        start = time.perf_counter()
        response = await call_next(request)
        route = getattr(request.scope.get("route"), "path", "unmatched")
        REQUESTS.labels(request.method, route, str(response.status_code)).observe(
            time.perf_counter() - start
        )
        return response

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz() -> dict[str, str]:
        return {"status": "ready", "environment": settings.environment}

    @app.get("/metrics")
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    IdempotencyKey = Annotated[str, Header(min_length=8, max_length=128)]

    @app.post("/payments", status_code=201)
    def create_payment(
        body: PaymentRequest, response: Response, idempotency_key: IdempotencyKey
    ) -> Payment:
        try:
            payment, created = store.create_once(
                idempotency_key,
                body,
                lambda: process(body, settings.max_amount_minor),
            )
        except IdempotencyConflictError:
            raise HTTPException(
                status_code=409,
                detail="Idempotency-Key was already used with a different request body",
            ) from None
        if created:
            PAYMENTS.labels(payment.status.value, payment.currency).inc()
            log.info(
                "payment processed",
                extra={"fields": {"payment_id": payment.id, "status": payment.status.value}},
            )
        else:
            response.status_code = 200  # replay of an earlier request
        return payment

    @app.get("/payments/{payment_id}")
    def get_payment(payment_id: str) -> Payment:
        payment = store.get(payment_id)
        if payment is None:
            raise HTTPException(status_code=404, detail="payment not found")
        return payment

    return app
