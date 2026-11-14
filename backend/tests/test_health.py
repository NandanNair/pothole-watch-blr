def test_health_returns_ok(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_ok_when_database_is_reachable(client) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
