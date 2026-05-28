"""Endpoint tests for the balance API."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient


def _create_category(client: TestClient, name: str = "Food") -> dict:
    return client.post("/categories", json={"name": name}).json()


def _create_transaction(
    client: TestClient,
    txn_type: str,
    amount: str,
    txn_date: str,
    category_id: int | None = None,
) -> dict:
    payload = {
        "type": txn_type,
        "amount": amount,
        "description": "test",
        "date": txn_date,
    }
    if category_id is not None:
        payload["category_id"] = category_id
    return client.post("/transactions", json=payload).json()


def test_month_balance_empty(client: TestClient) -> None:
    response = client.get("/balance/month/2026/5")
    assert response.status_code == 200
    body = response.json()
    assert body["income_total"] == "0.00"
    assert body["expense_total"] == "0.00"
    assert body["net"] == "0.00"


def test_month_balance_with_data(client: TestClient) -> None:
    cat = _create_category(client)
    _create_transaction(client, "income", "1000.00", "2026-05-05")
    _create_transaction(client, "expense", "300.00", "2026-05-15", cat["id"])

    response = client.get("/balance/month/2026/5")
    assert response.status_code == 200
    body = response.json()
    assert body["income_total"] == "1000.00"
    assert body["expense_total"] == "300.00"
    assert body["net"] == "700.00"
    assert len(body["by_category"]) == 1
    assert body["by_category"][0]["category"]["name"] == "Food"


def test_month_balance_invalid_month_returns_422(client: TestClient) -> None:
    response = client.get("/balance/month/2026/13")
    assert response.status_code == 422


def test_current_balance(client: TestClient) -> None:
    today = date.today()
    _create_transaction(client, "income", "500.00", today.isoformat())
    response = client.get("/balance/current")
    assert response.status_code == 200
    body = response.json()
    assert body["year"] == today.year
    assert body["month"] == today.month
    assert body["income_total"] == "500.00"


def test_history_with_explicit_range(client: TestClient) -> None:
    _create_transaction(client, "income", "100.00", "2026-04-01")
    _create_transaction(client, "income", "200.00", "2026-05-01")

    response = client.get("/balance/history?from_year=2026&from_month=4&to_year=2026&to_month=5")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["items"][0]["month"] == 5
    assert body["from"]["year"] == 2026
    assert body["from"]["month"] == 4
    assert body["to"]["month"] == 5


def test_history_inverted_range_returns_422(client: TestClient) -> None:
    response = client.get("/balance/history?from_year=2026&from_month=6&to_year=2026&to_month=5")
    assert response.status_code == 422


def test_history_default_range(client: TestClient) -> None:
    response = client.get("/balance/history")
    assert response.status_code == 200
    body = response.json()
    # Default range is 12 months, so 12 items.
    assert len(body["items"]) == 12
