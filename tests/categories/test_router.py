"""Endpoint tests for the categories API."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_category_returns_201(client: TestClient) -> None:
    response = client.post("/categories", json={"name": "Food"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Food"
    assert body["description"] is None
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body


def test_create_category_with_description(client: TestClient) -> None:
    response = client.post(
        "/categories",
        json={"name": "Transport", "description": "Daily commute"},
    )
    assert response.status_code == 201
    assert response.json()["description"] == "Daily commute"


def test_create_category_duplicate_name_returns_409(client: TestClient) -> None:
    client.post("/categories", json={"name": "Food"})
    response = client.post("/categories", json={"name": "Food"})
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_category_empty_name_returns_422(client: TestClient) -> None:
    response = client.post("/categories", json={"name": ""})
    assert response.status_code == 422


def test_create_category_name_too_long_returns_422(client: TestClient) -> None:
    response = client.post("/categories", json={"name": "x" * 101})
    assert response.status_code == 422


def test_get_category_returns_200(client: TestClient) -> None:
    created = client.post("/categories", json={"name": "Food"}).json()
    response = client.get(f"/categories/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Food"


def test_get_category_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/categories/9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_list_categories_empty(client: TestClient) -> None:
    response = client.get("/categories")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["skip"] == 0
    assert body["limit"] == 50


def test_list_categories_with_items(client: TestClient) -> None:
    for name in ["Food", "Transport", "Entertainment"]:
        client.post("/categories", json={"name": name})
    response = client.get("/categories")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3
    # Ordered alphabetically by name
    assert [c["name"] for c in body["items"]] == [
        "Entertainment",
        "Food",
        "Transport",
    ]


def test_list_categories_pagination(client: TestClient) -> None:
    for i in range(5):
        client.post("/categories", json={"name": f"Cat{i:02d}"})
    response = client.get("/categories?skip=2&limit=2")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert body["skip"] == 2
    assert body["limit"] == 2


def test_list_categories_limit_too_high_returns_422(client: TestClient) -> None:
    response = client.get("/categories?limit=500")
    assert response.status_code == 422


def test_update_category_returns_200(client: TestClient) -> None:
    created = client.post("/categories", json={"name": "Food"}).json()
    response = client.patch(
        f"/categories/{created['id']}",
        json={"description": "All food expenses"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Food"
    assert body["description"] == "All food expenses"


def test_update_category_not_found_returns_404(client: TestClient) -> None:
    response = client.patch("/categories/9999", json={"name": "x"})
    assert response.status_code == 404


def test_update_category_to_existing_name_returns_409(client: TestClient) -> None:
    client.post("/categories", json={"name": "Food"})
    other = client.post("/categories", json={"name": "Transport"}).json()
    response = client.patch(f"/categories/{other['id']}", json={"name": "Food"})
    assert response.status_code == 409


def test_delete_category_returns_204(client: TestClient) -> None:
    created = client.post("/categories", json={"name": "Food"}).json()
    response = client.delete(f"/categories/{created['id']}")
    assert response.status_code == 204
    assert response.content == b""

    # Verify it's actually gone
    response = client.get(f"/categories/{created['id']}")
    assert response.status_code == 404


def test_delete_category_not_found_returns_404(client: TestClient) -> None:
    response = client.delete("/categories/9999")
    assert response.status_code == 404


def test_delete_category_with_transactions_returns_409(
    client: TestClient,
) -> None:
    cat = client.post("/categories", json={"name": "Food"}).json()
    client.post(
        "/transactions",
        json={
            "type": "expense",
            "amount": "10.00",
            "description": "Coffee",
            "date": "2026-05-23",
            "category_id": cat["id"],
        },
    )
    response = client.delete(f"/categories/{cat['id']}")
    assert response.status_code == 409
    assert "transactions still reference" in response.json()["detail"]
