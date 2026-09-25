def test_query_endpoint_returns_manager_answer(client, fake_manager):
    response = client.post("/query", json={"query": "What is our security policy?"})

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "qualitative"
    assert body["answer"] == "Passwords must be 14+ characters."
    assert body["citations"][0]["doc_name"] == "security_policy.md"
    assert fake_manager.handle_query_calls == ["What is our security policy?"]


def test_query_endpoint_rejects_empty_query(client):
    response = client.post("/query", json={"query": ""})
    assert response.status_code == 422


def test_qualitative_endpoint_bypasses_classifier(client, fake_manager):
    response = client.post("/agents/qualitative", json={"query": "password rules?"})

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "qualitative"
    assert body["answer"] == "Passwords must be 14+ characters."
    assert fake_manager.qualitative_agent.queries == ["password rules?"]
    assert fake_manager.classify_calls == []  # classifier was never invoked


def test_quantitative_endpoint_bypasses_classifier(client, fake_manager):
    response = client.post("/agents/quantitative", json={"query": "churn rate?"})

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "quantitative"
    assert body["sql"] == "SELECT 1"
    assert fake_manager.quantitative_agent.queries == ["churn rate?"]


def test_classify_endpoint_does_not_call_sub_agents(client, fake_manager):
    response = client.post("/agents/manager/classify", json={"query": "What is our security policy?"})

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "qualitative"
    assert fake_manager.qualitative_agent.queries == []
    assert fake_manager.quantitative_agent.queries == []
