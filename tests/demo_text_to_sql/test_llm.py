import pytest
from unittest.mock import patch, MagicMock
from tools.demo_text_to_sql.llm import generate_sql, SYSTEM_PROMPT


FAKE_SCHEMA = "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);"


def test_system_prompt_contains_schema_placeholder():
    assert "{schema}" in SYSTEM_PROMPT


def test_system_prompt_formats_with_schema():
    formatted = SYSTEM_PROMPT.format(schema=FAKE_SCHEMA)
    assert FAKE_SCHEMA in formatted
    assert "{schema}" not in formatted


@patch("tools.demo_text_to_sql.llm._call_anthropic")
def test_generate_sql_uses_anthropic_when_key_set(mock_anthropic):
    mock_anthropic.return_value = "SELECT * FROM users"
    result = generate_sql("show all users", FAKE_SCHEMA, anthropic_key="sk-ant-test")
    mock_anthropic.assert_called_once()
    assert result == "SELECT * FROM users"


@patch("tools.demo_text_to_sql.llm._call_openai")
def test_generate_sql_uses_openai_when_no_anthropic_key(mock_openai):
    mock_openai.return_value = "SELECT * FROM users"
    result = generate_sql(
        "show all users", FAKE_SCHEMA, anthropic_key="", openai_key="sk-openai-test"
    )
    mock_openai.assert_called_once()
    assert result == "SELECT * FROM users"


def test_generate_sql_raises_when_no_keys():
    with pytest.raises(ValueError, match="API key"):
        generate_sql("show all users", FAKE_SCHEMA, anthropic_key="", openai_key="")


@patch("tools.demo_text_to_sql.llm._call_anthropic")
def test_generate_sql_strips_markdown_fences(mock_anthropic):
    mock_anthropic.return_value = "```sql\nSELECT 1\n```"
    result = generate_sql("test", FAKE_SCHEMA, anthropic_key="sk-ant-test")
    assert result == "SELECT 1"
