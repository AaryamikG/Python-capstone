def test_health_returns_200_with_expected_shape(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert isinstance(body["gemini_configured"], bool)
    assert isinstance(body["chroma_available"], bool)
    assert isinstance(body["sqlite_available"], bool)
