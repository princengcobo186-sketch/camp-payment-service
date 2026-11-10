import pytest
from pydantic import ValidationError

from payment_service.domain import PaymentRequest, PaymentStatus, process


def req(**kw):
    return PaymentRequest(**{"amount_minor": 1000, "currency": "USD", "reference": "o-1", **kw})


def test_capture():
    p = process(req(), max_amount_minor=5000)
    assert p.status is PaymentStatus.CAPTURED and p.failure_reason is None


def test_over_limit_declined():
    p = process(req(amount_minor=5001), max_amount_minor=5000)
    assert (p.status, p.failure_reason) == (PaymentStatus.FAILED, "amount_exceeds_limit")


def test_unsupported_currency_declined():
    p = process(req(currency="JPY"), max_amount_minor=5000)
    assert p.failure_reason == "unsupported_currency"


@pytest.mark.parametrize("amount", [0, -1, 10**12 + 1])
def test_bad_amounts_rejected(amount):
    with pytest.raises(ValidationError):
        req(amount_minor=amount)


def test_float_amount_rejected():
    with pytest.raises(ValidationError):
        req(amount_minor=10.5)


@pytest.mark.parametrize("cur", ["usd", "US", "USDX", ""])
def test_malformed_currency_rejected(cur):
    with pytest.raises(ValidationError):
        req(currency=cur)


def test_unknown_field_rejected():
    with pytest.raises(ValidationError):
        PaymentRequest(amount_minor=1, currency="USD", reference="x", card_number="4111")
