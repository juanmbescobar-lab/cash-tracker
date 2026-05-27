"""Endpoint tests for the transactions API."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _create_category(client: TestClient, name: str = "Food") -> dict:
    return client.post("/categories", json={"name": name}).json()


def test_create_income_without_category_returns_201(
    client: TestClient,
) -> None:
    response = client.post(
        "/transactions",
        json={
            "type": "income",
            "amount": "500.00",
            "description": "Salary",
            "date": "2026-05-23",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "income"
    assert body["amount"] == "500.00"
    assert body["category"] is None


def test_create_expense_with_category_returns_201(client: TestClient) -> None:
    cat = _create_category(client)
    response = client.post(
        "/transactions",
        json={
            "type": "expense",
            "amount": "25.50",
            "description": "Coffee",
            "date": "2026-05-23",
            "category_id": cat["id"],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["category"]["id"] == cat["id"]
    assert body["category"]["name"] == "Food"


def test_create_expense_without_category_returns_422(client: TestClient) -> None:
    response = client.post(
        "/transactions",
        json={
            "type": "expense",
            "amount": "25.50",
            "description": "Coffee",
            "date": "2026-05-23",
        },
    )
    assert response.status_code == 422


def test_create_transaction_negative_amount_returns_422(
    client: TestClient,
) -> None:
    response = client.post(
        "/transactions",
        json={
            "type": "income",
            "amount": "-100.00",
            "description": "x",
            "date": "2026-05-23",
        },
    )
    assert response.status_code == 422


def test_create_transaction_zero_amount_returns_422(client: TestClient) -> None:
    response = client.post(
        "/transactions",
        json={
            "type": "income",
            "amount": "0.00",
            "description": "x",
            "date": "2026-05-23",
        },
    )
    assert response.status_code == 422


def test_create_transaction_with_nonexistent_category_returns_422(
    client: TestClient,
) -> None:
    response = client.post(
        "/transactions",
        json={
            "type": "expense",
            "amount": "10.00",
            "description": "x",
            "date": "2026-05-23",
            "category_id": 9999,
        },
    )
    assert response.status_code == 422
    assert "does not exist" in response.json()["detail"]


def test_get_transaction_returns_200_with_category(client: TestClient) -> None:
    cat = _create_category(client)
    created = client.post(
        "/transactions",
        json={
            "type": "expense",
            "amount": "10.00",
            "description": "Snack",
            "date": "2026-05-23",
            "category_id": cat["id"],
        },
    ).json()
    response = client.get(f"/transactions/{created['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["category"]["name"] == "Food"


def test_get_transaction_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/transactions/9999")
    assert response.status_code == 404


def test_list_transactions_empty(client: TestClient) -> None:
    response = client.get("/transactions")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_list_transactions_ordered_by_date_desc(client: TestClient) -> None:
    cat = _create_category(client)
    for date in ["2026-05-20", "2026-05-23", "2026-05-21"]:
        client.post(
            "/transactions",
            json={
                "type": "expense",
                "amount": "10.00",
                "description": f"On {date}",
                "date": date,
                "category_id": cat["id"],
            },
        )
    response = client.get("/transactions")
    assert response.status_code == 200
    dates = [t["date"] for t in response.json()["items"]]
    assert dates == ["2026-05-23", "2026-05-21", "2026-05-20"]


def test_list_transactions_pagination(client: TestClient) -> None:
    cat = _create_category(client)
    for i in range(5):
        client.post(
            "/transactions",
            json={
                "type": "expense",
                "amount": "10.00",
                "description": f"#{i}",
                "date": "2026-05-23",
                "category_id": cat["id"],
            },
        )
    response = client.get("/transactions?skip=2&limit=2")
    body = response.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2


def test_update_transaction_returns_200(client: TestClient) -> None:
    cat = _create_category(client)
    created = client.post(
        "/transactions",
        json={
            "type": "expense",
            "amount": "10.00",
            "description": "Snack",
            "date": "2026-05-23",
            "category_id": cat["id"],
        },
    ).json()
    response = client.patch(
        f"/transactions/{created['id']}",
        json={"amount": "15.00", "description": "Updated snack"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["amount"] == "15.00"
    assert body["description"] == "Updated snack"


def test_update_transaction_change_category(client: TestClient) -> None:
    cat1 = _create_category(client, "Food")
    cat2 = _create_category(client, "Transport")
    created = client.post(
        "/transactions",
        json={
            "type": "expense",
            "amount": "10.00",
            "description": "x",
            "date": "2026-05-23",
            "category_id": cat1["id"],
        },
    ).json()
    response = client.patch(
        f"/transactions/{created['id']}",
        json={"category_id": cat2["id"]},
    )
    assert response.status_code == 200
    assert response.json()["category"]["name"] == "Transport"


def test_update_expense_remove_category_returns_422(client: TestClient) -> None:
    cat = _create_category(client)
    created = client.post(
        "/transactions",
        json={
            "type": "expense",
            "amount": "10.00",
            "description": "x",
            "date": "2026-05-23",
            "category_id": cat["id"],
        },
    ).json()
    response = client.patch(
        f"/transactions/{created['id']}",
        json={"category_id": None},
    )
    assert response.status_code == 422
    assert "require a category" in response.json()["detail"]


def test_update_transaction_not_found_returns_404(client: TestClient) -> None:
    response = client.patch("/transactions/9999", json={"amount": "10.00"})
    assert response.status_code == 404


def test_delete_transaction_returns_204(client: TestClient) -> None:
    cat = _create_category(client)
    created = client.post(
        "/transactions",
        json={
            "type": "expense",
            "amount": "10.00",
            "description": "x",
            "date": "2026-05-23",
            "category_id": cat["id"],
        },
    ).json()
    response = client.delete(f"/transactions/{created['id']}")
    assert response.status_code == 204
    response = client.get(f"/transactions/{created['id']}")
    assert response.status_code == 404


def test_delete_transaction_not_found_returns_404(client: TestClient) -> None:
    response = client.delete("/transactions/9999")
    assert response.status_code == 404
