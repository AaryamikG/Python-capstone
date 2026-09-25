def test_openapi_schema_lists_all_routes(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/health" in paths
    assert "/query" in paths
    assert "/agents/qualitative" in paths
    assert "/agents/quantitative" in paths
    assert "/agents/manager/classify" in paths


def test_docs_ui_is_served(client):
    response = client.get("/docs")
    assert response.status_code == 200
