import pytest
from fastapi.testclient import TestClient

from payment_service.config import Settings
from payment_service.main import create_app

BODY = {"amount_minor": 2500, "currency": "ZAR", "reference": "order-1"}
KEY = {"Idempotency-Key": "key-12345678"}


@pytest.fixture
def client():
    return TestClient(create_app(Settings("local", "WARNING", 1_000_000)))


def test_create_and_fetch(client):
    r = client.post("/payments", json=BODY, headers=KEY)
    assert r.status_code == 201
    assert r.json()["status"] == "CAPTURED"
    assert client.get(f"/payments/{r.json()['id']}").json() == r.json()


def test_idempotent_replay_returns_same_payment(client):
    first = client.post("/payments", json=BODY, headers=KEY)
    second = client.post("/payments", json=BODY, headers=KEY)
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]


def test_key_reuse_with_different_body_conflicts(client):
    client.post("/payments", json=BODY, headers=KEY)
    r = client.post("/payments", json={**BODY, "amount_minor": 1}, headers=KEY)
    assert r.status_code == 409


def test_idempotency_key_required(client):
    assert client.post("/payments", json=BODY).status_code == 422


def test_invalid_body_rejected(client):
    r = client.post("/payments", json={**BODY, "amount_minor": -5}, headers=KEY)
    assert r.status_code == 422


def test_unknown_payment_404(client):
    assert client.get("/payments/nope").status_code == 404


def test_probes_and_metrics(client):
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").json()["environment"] == "local"
    client.post("/payments", json=BODY, headers=KEY)
    metrics = client.get("/metrics").text
    assert "payments_total" in metrics and "http_request_duration_seconds" in metrics


def test_app_refuses_to_start_without_config(monkeypatch):
    from payment_service.config import ConfigError

    monkeypatch.delenv("APP_ENV", raising=False)
    with pytest.raises(ConfigError):
        create_app()
