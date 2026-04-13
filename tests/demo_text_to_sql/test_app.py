import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from tools.demo_text_to_sql.app import app
    return TestClient(app)


def test_get_root_returns_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "QueryCraft" in response.text


def test_get_schema_returns_json(client):
    response = client.get("/api/schema")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "name" in data[0]
    assert "columns" in data[0]


@patch("tools.demo_text_to_sql.app.ANTHROPIC_KEY", "sk-ant-test")
@patch("tools.demo_text_to_sql.app.generate_sql")
def test_post_query_success(mock_gen, client):
    mock_gen.return_value = "SELECT 1 AS num"
    response = client.post("/api/query", json={"question": "test question"})
    assert response.status_code == 200
    data = response.json()
    assert "sql" in data
    assert "columns" in data
    assert "rows" in data
    assert "summary" in data


@patch("tools.demo_text_to_sql.app.ANTHROPIC_KEY", "sk-ant-test")
@patch("tools.demo_text_to_sql.app.generate_sql")
def test_post_query_sql_error(mock_gen, client):
    mock_gen.return_value = "SELECT * FROM nonexistent_table_xyz"
    response = client.post("/api/query", json={"question": "bad query"})
    assert response.status_code == 400
    data = response.json()
    assert data["error_type"] == "sql"
    assert "sql" in data


@patch("tools.demo_text_to_sql.app.ANTHROPIC_KEY", "sk-ant-test")
@patch("tools.demo_text_to_sql.app.generate_sql")
def test_post_query_llm_error(mock_gen, client):
    mock_gen.side_effect = Exception("Rate limited")
    response = client.post("/api/query", json={"question": "test"})
    assert response.status_code == 502
    data = response.json()
    assert "detail" in data
    assert "Rate limited" in data["detail"]


@patch("tools.demo_text_to_sql.app.ANTHROPIC_KEY", "sk-ant-test")
@patch("tools.demo_text_to_sql.app.generate_sql")
def test_post_query_timeout(mock_gen, client):
    import asyncio

    original_wait_for = asyncio.wait_for

    async def instant_timeout(coro, *, timeout):
        """Simulate immediate timeout."""
        raise asyncio.TimeoutError()

    with patch("tools.demo_text_to_sql.app.asyncio.wait_for", side_effect=instant_timeout):
        response = client.post("/api/query", json={"question": "slow query"})
    assert response.status_code == 504
    data = response.json()
    assert "timed out" in data["detail"].lower()


def test_post_query_empty_question(client):
    response = client.post("/api/query", json={"question": ""})
    assert response.status_code == 422 or response.status_code == 400
