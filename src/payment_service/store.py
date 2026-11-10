"""Payment repository with idempotency.

In-memory for now: state is lost on restart and not shared between replicas, so run one replica
until a Postgres adapter replaces this (tracked for a later phase). The interface is the seam.
"""

import threading
from collections.abc import Callable

from payment_service.domain import Payment, PaymentRequest


class IdempotencyConflictError(Exception):
    """The same Idempotency-Key was reused with a different request body."""


class InMemoryStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._payments: dict[str, Payment] = {}
        self._by_key: dict[str, tuple[PaymentRequest, Payment]] = {}

    def get(self, payment_id: str) -> Payment | None:
        return self._payments.get(payment_id)

    def create_once(
        self, key: str, request: PaymentRequest, make: Callable[[], Payment]
    ) -> tuple[Payment, bool]:
        """Return (payment, created). Replaying a key with the same body returns the original."""
        with self._lock:
            existing = self._by_key.get(key)
            if existing is not None:
                original_request, payment = existing
                if original_request != request:
                    raise IdempotencyConflictError(key)
                return payment, False
            payment = make()
            self._payments[payment.id] = payment
            self._by_key[key] = (request, payment)
            return payment, True
