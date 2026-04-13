"""
Database helpers for the Text-to-SQL demo.
Handles connection, schema introspection, and query execution.
"""

import sqlite3


def get_connection(db_path: str) -> sqlite3.Connection:
    """Open a SQLite connection to the given database file."""
    return sqlite3.connect(db_path, check_same_thread=False)


def get_schema(conn: sqlite3.Connection) -> list[dict]:
    """Return the database schema as a list of tables with their columns.

    Returns:
        [
            {
                "name": "Album",
                "columns": [
                    {"name": "AlbumId", "type": "INTEGER"},
                    {"name": "Title", "type": "NVARCHAR(160)"},
                    ...
                ]
            },
            ...
        ]
    """
    tables = []
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()

    for (table_name,) in rows:
        columns = []
        for col in conn.execute(f"PRAGMA table_info('{table_name}')").fetchall():
            columns.append({"name": col[1], "type": col[2] or "TEXT"})
        tables.append({"name": table_name, "columns": columns})

    return tables


def get_schema_ddl(conn: sqlite3.Connection) -> str:
    """Return the full DDL of every table as a single string (for LLM prompts)."""
    rows = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
    ).fetchall()
    return "\n\n".join(row[0] for row in rows)


def run_query(conn: sqlite3.Connection, sql: str) -> dict:
    """Execute read-only SQL and return columns + rows.

    Returns:
        {"columns": ["col1", "col2"], "rows": [[val1, val2], ...]}

    Raises:
        sqlite3.OperationalError: If the SQL is invalid.
    """
    cursor = conn.execute(sql)
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    rows = [list(row) for row in cursor.fetchall()]
    return {"columns": columns, "rows": rows}
