"""Payment model and the fake payment provider.

Money is always integer minor units (cents). There are no floats anywhere in the money path.
No real card data is accepted or stored, which keeps this service out of PCI scope.
"""

import uuid
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# ISO 4217 subset this service supports.
SUPPORTED_CURRENCIES = frozenset({"USD", "EUR", "GBP", "ZAR", "SEK"})

Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


class PaymentStatus(StrEnum):
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"


class PaymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    amount_minor: int = Field(gt=0, le=10**12, description="Amount in minor units, e.g. cents")
    currency: Currency
    reference: str = Field(min_length=1, max_length=64, description="Merchant order reference")


class Payment(BaseModel):
    id: str
    amount_minor: int
    currency: str
    reference: str
    status: PaymentStatus
    failure_reason: str | None = None


def process(request: PaymentRequest, max_amount_minor: int) -> Payment:
    """Fake provider: deterministic, so tests and demos are reproducible."""
    status = PaymentStatus.CAPTURED
    reason = None
    if request.currency not in SUPPORTED_CURRENCIES:
        status, reason = PaymentStatus.FAILED, "unsupported_currency"
    elif request.amount_minor > max_amount_minor:
        status, reason = PaymentStatus.FAILED, "amount_exceeds_limit"

    return Payment(
        id=str(uuid.uuid4()),
        amount_minor=request.amount_minor,
        currency=request.currency,
        reference=request.reference,
        status=status,
        failure_reason=reason,
    )
