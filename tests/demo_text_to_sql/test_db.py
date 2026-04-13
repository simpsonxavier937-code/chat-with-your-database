# tests/demo_text_to_sql/test_db.py
import os
import sqlite3
import pytest
from tools.demo_text_to_sql.db import get_connection, get_schema, get_schema_ddl, run_query

CHINOOK_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "tools", "demo_text_to_sql", "chinook.db"
)


@pytest.fixture
def db_path():
    """Return the path to the Chinook test database."""
    assert os.path.exists(CHINOOK_PATH), f"Chinook DB not found at {CHINOOK_PATH}"
    return CHINOOK_PATH


def test_get_connection_returns_sqlite_connection(db_path):
    conn = get_connection(db_path)
    assert isinstance(conn, sqlite3.Connection)


def test_get_schema_returns_all_tables(db_path):
    conn = get_connection(db_path)
    schema = get_schema(conn)
    assert isinstance(schema, list)
    table_names = [t["name"] for t in schema]
    assert "albums" in table_names or "Album" in table_names


def test_get_schema_includes_columns(db_path):
    conn = get_connection(db_path)
    schema = get_schema(conn)
    albums = next(t for t in schema if t["name"].lower() in ("albums", "album"))
    assert len(albums["columns"]) > 0
    col = albums["columns"][0]
    assert "name" in col
    assert "type" in col


def test_get_schema_ddl_returns_string(db_path):
    conn = get_connection(db_path)
    ddl = get_schema_ddl(conn)
    assert isinstance(ddl, str)
    assert "CREATE TABLE" in ddl


def test_run_query_returns_columns_and_rows(db_path):
    conn = get_connection(db_path)
    result = run_query(conn, "SELECT 1 AS num, 'hello' AS greeting")
    assert result["columns"] == ["num", "greeting"]
    assert result["rows"] == [[1, "hello"]]


def test_run_query_against_chinook(db_path):
    conn = get_connection(db_path)
    result = run_query(conn, "SELECT COUNT(*) AS cnt FROM Album")
    assert result["columns"] == ["cnt"]
    assert result["rows"][0][0] > 0


def test_run_query_rejects_non_select(db_path):
    conn = get_connection(db_path)
    with pytest.raises(ValueError, match="SELECT"):
        run_query(conn, "DROP TABLE Album")


def test_run_query_bad_sql_raises(db_path):
    conn = get_connection(db_path)
    with pytest.raises(sqlite3.OperationalError):
        run_query(conn, "SELECT * FROM nonexistent_table")
