# Frontend Redesign — Chat With Your Database

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Streamlit UI with a branded FastAPI + Alpine.js + Tailwind CSS single-page app that feels like a real SaaS product.

**Architecture:** Extract `db.py` and `llm.py` from the current monolithic `app.py`, build a FastAPI server with three endpoints (`GET /`, `GET /api/schema`, `POST /api/query`), and serve a Jinja2 template that loads Alpine.js and Tailwind CSS via CDN. No build step, no Node dependency.

**Tech Stack:** Python 3 / FastAPI / Jinja2 / SQLite / Alpine.js (CDN) / Tailwind CSS (CDN) / Inter + JetBrains Mono (Google Fonts CDN)

---

## File Structure

```
tools/demo_text_to_sql/
├── app.py              # FastAPI server — serves template + API endpoints (REPLACE existing)
├── llm.py              # LLM helpers — generate_sql, provider switching (NEW)
├── db.py               # Database helpers — connection, schema, query execution (NEW)
├── static/
│   ├── brand.css       # Shared brand tokens as CSS custom properties (NEW)
│   ├── style.css       # App-specific component styles (NEW)
│   └── app.js          # Alpine.js app logic — chat, sidebar, theme toggle (NEW)
├── templates/
│   └── index.html      # Single Jinja2 template — loads Alpine + Tailwind via CDN (NEW)
├── chinook.db          # Sample database (EXISTING, unchanged)
tests/
└── demo_text_to_sql/
    ├── test_db.py       # Tests for db.py (NEW)
    ├── test_llm.py      # Tests for llm.py (NEW)
    └── test_app.py      # Tests for FastAPI endpoints (NEW)
```

---

## Task 1: Extract `db.py` — Database Helpers

**Files:**
- Create: `tools/demo_text_to_sql/db.py`
- Create: `tests/demo_text_to_sql/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/demo_text_to_sql/test_db.py`

- [ ] **Step 1: Write failing tests for db.py**

Create `tests/__init__.py` (empty file) and `tests/demo_text_to_sql/__init__.py` (empty file), then create the test file:

```python
# tests/demo_text_to_sql/test_db.py
import os
import sqlite3
import pytest
from tools.demo_text_to_sql.db import get_connection, get_schema, run_query

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
    # Chinook has 11 tables
    assert isinstance(schema, list)
    table_names = [t["name"] for t in schema]
    assert "albums" in table_names or "Album" in table_names


def test_get_schema_includes_columns(db_path):
    conn = get_connection(db_path)
    schema = get_schema(conn)
    # Find the albums/Album table and check it has columns
    albums = next(t for t in schema if t["name"].lower() in ("albums", "album"))
    assert len(albums["columns"]) > 0
    # Each column should have name and type
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
    result = run_query(conn, "SELECT COUNT(*) AS cnt FROM albums")
    assert result["columns"] == ["cnt"]
    assert result["rows"][0][0] > 0


def test_run_query_bad_sql_raises(db_path):
    conn = get_connection(db_path)
    with pytest.raises(sqlite3.OperationalError):
        run_query(conn, "SELECT * FROM nonexistent_table")
```

Add the missing import at the top — update the import line:

```python
from tools.demo_text_to_sql.db import get_connection, get_schema, get_schema_ddl, run_query
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd c:/Workflows/FirstWorkflow && python -m pytest tests/demo_text_to_sql/test_db.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'tools.demo_text_to_sql.db'`

- [ ] **Step 3: Implement db.py**

```python
# tools/demo_text_to_sql/db.py
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
            # col: (cid, name, type, notnull, dflt_value, pk)
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
```

Also create `tools/demo_text_to_sql/__init__.py` (empty file) if it doesn't exist, and `tools/__init__.py` (empty file) if it doesn't exist.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd c:/Workflows/FirstWorkflow && python -m pytest tests/demo_text_to_sql/test_db.py -v`

Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/__init__.py tools/demo_text_to_sql/__init__.py tools/demo_text_to_sql/db.py tests/__init__.py tests/demo_text_to_sql/__init__.py tests/demo_text_to_sql/test_db.py
git commit -m "feat: extract db.py from monolithic app.py with tests"
```

---

## Task 2: Extract `llm.py` — LLM Helpers

**Files:**
- Create: `tools/demo_text_to_sql/llm.py`
- Create: `tests/demo_text_to_sql/test_llm.py`

- [ ] **Step 1: Write failing tests for llm.py**

```python
# tests/demo_text_to_sql/test_llm.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd c:/Workflows/FirstWorkflow && python -m pytest tests/demo_text_to_sql/test_llm.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'tools.demo_text_to_sql.llm'`

- [ ] **Step 3: Implement llm.py**

```python
# tools/demo_text_to_sql/llm.py
"""
LLM helpers for the Text-to-SQL demo.
Generates SQL from natural language using Anthropic Claude or OpenAI GPT.
"""

SYSTEM_PROMPT = """\
You are a SQL expert. Given the database schema below and a user's question,
generate a single SQLite-compatible SELECT query that answers the question.

Rules:
- Output ONLY the SQL query, nothing else. No markdown, no explanation.
- Use only tables and columns from the schema provided.
- Always use read-only SELECT statements. Never INSERT, UPDATE, DELETE, DROP, etc.
- For ambiguous questions, make a reasonable assumption and proceed.
- Limit results to 50 rows unless the user asks for more.

Schema:
{schema}
"""


def generate_sql(
    question: str,
    schema: str,
    anthropic_key: str = "",
    openai_key: str = "",
) -> str:
    """Send the question + schema to the LLM and return a SQL query string.

    Args:
        question: Natural language question from the user.
        schema: Database DDL string.
        anthropic_key: Anthropic API key (preferred if set).
        openai_key: OpenAI API key (fallback).

    Returns:
        A SQL query string.

    Raises:
        ValueError: If neither API key is provided.
    """
    if not anthropic_key and not openai_key:
        raise ValueError(
            "No API key configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."
        )

    system = SYSTEM_PROMPT.format(schema=schema)

    if anthropic_key:
        raw = _call_anthropic(system, question, anthropic_key)
    else:
        raw = _call_openai(system, question, openai_key)

    return _strip_fences(raw)


def _strip_fences(text: str) -> str:
    """Remove markdown code fences from LLM output."""
    text = text.strip()
    if text.startswith("```sql"):
        text = text[6:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _call_anthropic(system: str, question: str, api_key: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": question}],
    )
    return resp.content[0].text


def _call_openai(system: str, question: str, api_key: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1024,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ],
    )
    return resp.choices[0].message.content
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd c:/Workflows/FirstWorkflow && python -m pytest tests/demo_text_to_sql/test_llm.py -v`

Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/demo_text_to_sql/llm.py tests/demo_text_to_sql/test_llm.py
git commit -m "feat: extract llm.py from monolithic app.py with tests"
```

---

## Task 3: Create `brand.css` — Shared Brand Tokens

**Files:**
- Create: `tools/demo_text_to_sql/static/brand.css`

- [ ] **Step 1: Create the static directory**

```bash
mkdir -p tools/demo_text_to_sql/static
```

- [ ] **Step 2: Write brand.css**

```css
/* brand.css — QueryCraft shared brand tokens
   Import this file into any product for consistent branding.
   Colors switch between dark/light via the [data-theme] attribute on <html>. */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  /* --- Primary palette --- */
  --brand-primary: #5B21B6;
  --brand-primary-vivid: #7C3AED;
  --brand-accent: #D97706;

  /* --- Semantic --- */
  --brand-success: #10B981;
  --brand-error: #EF4444;
  --brand-info: #3B82F6;

  /* --- Typography --- */
  --font-ui: 'Inter', system-ui, -apple-system, sans-serif;
  --font-code: 'JetBrains Mono', ui-monospace, monospace;

  /* --- Spacing (4px base) --- */
  --sp-1: 4px;
  --sp-2: 8px;
  --sp-3: 12px;
  --sp-4: 16px;
  --sp-6: 24px;
  --sp-8: 32px;
  --sp-12: 48px;
  --sp-16: 64px;

  /* --- Radius --- */
  --radius-sm: 6px;   /* buttons, inputs */
  --radius-md: 8px;   /* cards, panels */
  --radius-lg: 12px;  /* modals */
  --radius-pill: 20px; /* pills, badges */

  /* --- Shadows --- */
  --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.1);
  --shadow-elevated: 0 4px 12px rgba(0, 0, 0, 0.15);

  /* --- Logo gradient --- */
  --brand-gradient: linear-gradient(135deg, #7C3AED, #D97706);
}

/* Dark theme (default) */
[data-theme="dark"] {
  --color-bg: #0C0716;
  --color-surface: #150E24;
  --color-border: #2D1F4E;
  --color-text: #FAF5FF;
  --color-text-secondary: #6B7280;
}

/* Light theme */
[data-theme="light"] {
  --color-bg: #FAF5FF;
  --color-surface: #FFFFFF;
  --color-border: #E9D5FF;
  --color-text: #0C0716;
  --color-text-secondary: #6B7280;
}
```

- [ ] **Step 3: Commit**

```bash
git add tools/demo_text_to_sql/static/brand.css
git commit -m "feat: add brand.css with shared QueryCraft brand tokens"
```

---

## Task 4: Create `style.css` — App Component Styles

**Files:**
- Create: `tools/demo_text_to_sql/static/style.css`

- [ ] **Step 1: Write style.css**

```css
/* style.css — QueryCraft app-specific component styles
   Imports brand tokens from brand.css. App layout, chat, sidebar, etc. */

/* === Base === */

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  font-family: var(--font-ui);
  background: var(--color-bg);
  color: var(--color-text);
  transition: background 0.2s, color 0.2s;
}

/* === Layout === */

.app-layout {
  display: flex;
  height: 100vh;
  flex-direction: column;
}

/* --- Header --- */

.header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--sp-6);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
  flex-shrink: 0;
  z-index: 10;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.logo-mark {
  width: 32px;
  height: 32px;
  background: var(--brand-gradient);
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.logo-text {
  font-weight: 700;
  font-size: 18px;
  letter-spacing: -0.02em;
}

/* Theme toggle */
.theme-toggle {
  background: none;
  border: 1px solid var(--color-border);
  color: var(--color-text);
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: border-color 0.2s;
}

.theme-toggle:hover {
  border-color: var(--brand-primary-vivid);
}

/* --- Main body (sidebar + content) --- */

.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* --- Sidebar --- */

.sidebar {
  width: 280px;
  border-right: 1px solid var(--color-border);
  background: var(--color-surface);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  flex-shrink: 0;
  transition: width 0.2s;
}

.sidebar.collapsed {
  width: 0;
  overflow: hidden;
  border-right: none;
}

.sidebar-section {
  padding: var(--sp-4);
  border-bottom: 1px solid var(--color-border);
}

.sidebar-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
  margin-bottom: var(--sp-3);
}

/* Schema explorer */
.schema-table {
  cursor: pointer;
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  transition: background 0.15s;
}

.schema-table:hover {
  background: var(--color-border);
}

.schema-table.active {
  color: var(--brand-primary-vivid);
}

.schema-columns {
  padding-left: var(--sp-6);
  font-size: 12px;
  color: var(--color-text-secondary);
  font-family: var(--font-code);
}

.schema-column {
  padding: var(--sp-1) 0;
  display: flex;
  justify-content: space-between;
}

.schema-col-type {
  color: var(--brand-primary-vivid);
  font-size: 11px;
}

/* Query history */
.history-item {
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: background 0.15s;
}

.history-item:hover {
  background: var(--color-border);
}

/* --- Main content --- */

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Example questions (empty state) */
.example-questions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
  justify-content: center;
  padding: var(--sp-8) var(--sp-6);
  max-width: 640px;
  margin: auto;
}

.example-pill {
  padding: var(--sp-2) var(--sp-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  background: transparent;
  color: var(--color-text);
  font-size: 13px;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  font-family: var(--font-ui);
}

.example-pill:hover {
  border-color: var(--brand-primary-vivid);
  background: var(--brand-primary);
  color: white;
}

/* Chat thread */
.chat-thread {
  flex: 1;
  overflow-y: auto;
  padding: var(--sp-6);
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

/* User message */
.msg-user {
  align-self: flex-end;
  background: var(--brand-primary);
  color: white;
  padding: var(--sp-3) var(--sp-4);
  border-radius: var(--radius-md);
  max-width: 70%;
  font-size: 14px;
  line-height: 1.5;
}

/* Assistant message */
.msg-assistant {
  align-self: flex-start;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  padding: var(--sp-4);
  border-radius: var(--radius-md);
  max-width: 85%;
  font-size: 14px;
  line-height: 1.5;
  box-shadow: var(--shadow-card);
}

.msg-summary {
  margin-bottom: var(--sp-3);
}

/* SQL toggle */
.sql-toggle {
  background: none;
  border: none;
  color: var(--brand-primary-vivid);
  font-size: 12px;
  cursor: pointer;
  font-weight: 500;
  padding: var(--sp-1) 0;
  font-family: var(--font-ui);
}

.sql-block {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--sp-3);
  margin-top: var(--sp-2);
  font-family: var(--font-code);
  font-size: 13px;
  overflow-x: auto;
  white-space: pre-wrap;
}

/* Results table */
.results-wrapper {
  margin-top: var(--sp-3);
  overflow-x: auto;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.results-table th {
  text-align: left;
  padding: var(--sp-2) var(--sp-3);
  border-bottom: 2px solid var(--color-border);
  font-weight: 600;
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}

.results-table th:hover {
  color: var(--brand-primary-vivid);
}

.sort-arrow {
  font-size: 10px;
  margin-left: 4px;
}

.results-table td {
  padding: var(--sp-2) var(--sp-3);
  border-bottom: 1px solid var(--color-border);
}

.results-table tr:nth-child(even) {
  background: var(--color-bg);
}

.truncation-note {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: var(--sp-2);
}

/* Export CSV button */
.btn-export {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-1);
  background: var(--brand-accent);
  color: white;
  border: none;
  padding: var(--sp-1) var(--sp-3);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  margin-top: var(--sp-2);
  float: right;
  font-family: var(--font-ui);
}

.btn-export:hover {
  opacity: 0.9;
}

/* Error cards */
.msg-error {
  align-self: flex-start;
  border: 1px solid var(--brand-error);
  background: var(--color-surface);
  padding: var(--sp-4);
  border-radius: var(--radius-md);
  max-width: 85%;
  color: var(--brand-error);
  font-size: 14px;
}

.msg-warning {
  align-self: flex-start;
  border: 1px solid var(--brand-accent);
  background: var(--color-surface);
  padding: var(--sp-4);
  border-radius: var(--radius-md);
  max-width: 85%;
  font-size: 14px;
}

.msg-info {
  align-self: flex-start;
  border: 1px solid var(--brand-info);
  background: var(--color-surface);
  padding: var(--sp-4);
  border-radius: var(--radius-md);
  max-width: 85%;
  font-size: 14px;
}

/* No API key onboarding card */
.onboarding-card {
  max-width: 480px;
  margin: auto;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--sp-8);
  text-align: center;
  box-shadow: var(--shadow-elevated);
}

.onboarding-card h2 {
  margin-bottom: var(--sp-4);
}

.onboarding-card code {
  font-family: var(--font-code);
  background: var(--color-bg);
  padding: var(--sp-1) var(--sp-2);
  border-radius: var(--radius-sm);
  font-size: 13px;
}

/* Loading animation */
.loading-dots {
  display: flex;
  gap: 6px;
  align-self: flex-start;
  padding: var(--sp-4);
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: var(--brand-primary-vivid);
  border-radius: 50%;
  animation: pulse 1.4s ease-in-out infinite;
}

.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes pulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}

/* --- Input bar --- */

.input-bar {
  padding: var(--sp-4) var(--sp-6);
  border-top: 1px solid var(--color-border);
  background: var(--color-surface);
  display: flex;
  gap: var(--sp-3);
  flex-shrink: 0;
}

.input-bar input {
  flex: 1;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--sp-3) var(--sp-4);
  color: var(--color-text);
  font-size: 14px;
  font-family: var(--font-ui);
  outline: none;
  transition: border-color 0.2s;
}

.input-bar input:focus {
  border-color: var(--brand-primary-vivid);
}

.input-bar input::placeholder {
  color: var(--color-text-secondary);
}

.btn-send {
  background: var(--brand-primary);
  color: white;
  border: none;
  width: 42px;
  height: 42px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: background 0.2s;
  flex-shrink: 0;
}

.btn-send:hover {
  background: var(--brand-primary-vivid);
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Sidebar toggle (mobile) */
.sidebar-toggle {
  display: none;
  background: none;
  border: none;
  color: var(--color-text);
  font-size: 20px;
  cursor: pointer;
  padding: var(--sp-2);
}

@media (max-width: 768px) {
  .sidebar {
    position: absolute;
    z-index: 5;
    height: calc(100vh - 56px);
    top: 56px;
  }

  .sidebar.collapsed {
    width: 0;
  }

  .sidebar-toggle {
    display: block;
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add tools/demo_text_to_sql/static/style.css
git commit -m "feat: add style.css with all app component styles"
```

---

## Task 5: Create `index.html` — Jinja2 Template

**Files:**
- Create: `tools/demo_text_to_sql/templates/index.html`

- [ ] **Step 1: Create templates directory**

```bash
mkdir -p tools/demo_text_to_sql/templates
```

- [ ] **Step 2: Write index.html**

```html
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>QueryCraft — Chat With Your Database</title>

  <!-- Tailwind CSS (CDN, utilities only — component styles in style.css) -->
  <script src="https://cdn.tailwindcss.com"></script>

  <!-- Brand + app styles -->
  <link rel="stylesheet" href="/static/brand.css">
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>

<div class="app-layout" x-data="app()" x-init="init()">

  <!-- ===== Header ===== -->
  <header class="header">
    <div class="header-brand">
      <button class="sidebar-toggle" @click="sidebarOpen = !sidebarOpen">&#9776;</button>
      <div class="logo-mark"></div>
      <span class="logo-text">QueryCraft</span>
    </div>
    <button class="theme-toggle" @click="toggleTheme()" :title="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'">
      <span x-text="theme === 'dark' ? '&#9788;' : '&#9789;'"></span>
    </button>
  </header>

  <!-- ===== Body (sidebar + main) ===== -->
  <div class="app-body">

    <!-- Sidebar -->
    <aside class="sidebar" :class="{ collapsed: !sidebarOpen }">

      <!-- Schema Explorer -->
      <div class="sidebar-section">
        <div class="sidebar-title">Schema Explorer</div>
        <template x-for="table in schema" :key="table.name">
          <div>
            <div class="schema-table"
                 :class="{ active: highlightedTable === table.name }"
                 @click="table._open = !table._open">
              <span x-text="table._open ? '&#9660;' : '&#9654;'"></span>
              <span x-text="table.name"></span>
            </div>
            <div class="schema-columns" x-show="table._open" x-transition>
              <template x-for="col in table.columns" :key="col.name">
                <div class="schema-column">
                  <span x-text="col.name"></span>
                  <span class="schema-col-type" x-text="col.type"></span>
                </div>
              </template>
            </div>
          </div>
        </template>
      </div>

      <!-- Query History -->
      <div class="sidebar-section">
        <div class="sidebar-title">Query History</div>
        <template x-for="(item, idx) in history" :key="idx">
          <div class="history-item" @click="replayQuestion(item)" x-text="item"></div>
        </template>
        <div x-show="history.length === 0" style="font-size: 12px; color: var(--color-text-secondary);">
          No queries yet
        </div>
      </div>
    </aside>

    <!-- Main content -->
    <main class="main-content">

      <!-- Chat thread -->
      <div class="chat-thread" x-ref="chatThread">

        <!-- No API key warning -->
        <template x-if="!hasApiKey">
          <div class="onboarding-card">
            <h2>Welcome to QueryCraft</h2>
            <p style="margin-bottom: 16px; color: var(--color-text-secondary);">
              To get started, add your API key to the <code>.env</code> file:
            </p>
            <p><code>ANTHROPIC_API_KEY=sk-ant-...</code></p>
            <p style="margin-top: 8px; color: var(--color-text-secondary); font-size: 13px;">
              or <code>OPENAI_API_KEY=sk-...</code>
            </p>
          </div>
        </template>

        <template x-if="hasApiKey">
          <div style="display: contents;">

            <!-- Example questions (shown when no messages) -->
            <div class="example-questions" x-show="messages.length === 0" x-transition>
              <template x-for="q in exampleQuestions" :key="q">
                <button class="example-pill" @click="submitQuestion(q)" x-text="q"></button>
              </template>
            </div>

            <!-- Messages -->
            <template x-for="(msg, idx) in messages" :key="idx">
              <div>
                <!-- User message -->
                <template x-if="msg.role === 'user'">
                  <div class="msg-user" x-text="msg.content"></div>
                </template>

                <!-- Assistant message (success) -->
                <template x-if="msg.role === 'assistant' && !msg.error">
                  <div class="msg-assistant">
                    <div class="msg-summary" x-text="msg.summary"></div>

                    <!-- SQL toggle -->
                    <button class="sql-toggle" @click="msg._showSql = !msg._showSql"
                            x-text="msg._showSql ? '&#9660; Hide SQL' : '&#9654; View SQL'"></button>
                    <div class="sql-block" x-show="msg._showSql" x-transition x-text="msg.sql"></div>

                    <!-- Results table -->
                    <template x-if="msg.columns && msg.columns.length > 0">
                      <div class="results-wrapper">
                        <table class="results-table">
                          <thead>
                            <tr>
                              <template x-for="(col, ci) in msg.columns" :key="ci">
                                <th @click="sortColumn(msg, ci)">
                                  <span x-text="col"></span>
                                  <span class="sort-arrow"
                                        x-show="msg._sortCol === ci"
                                        x-text="msg._sortAsc ? '&#9650;' : '&#9660;'"></span>
                                </th>
                              </template>
                            </tr>
                          </thead>
                          <tbody>
                            <template x-for="(row, ri) in msg._displayRows" :key="ri">
                              <tr>
                                <template x-for="(cell, ci) in row" :key="ci">
                                  <td x-text="cell"></td>
                                </template>
                              </tr>
                            </template>
                          </tbody>
                        </table>
                        <div class="truncation-note" x-show="msg.rows.length > 50"
                             x-text="'Showing 50 of ' + msg.rows.length + ' rows'"></div>
                        <button class="btn-export" @click="exportCsv(msg)">&#8681; Export CSV</button>
                      </div>
                    </template>

                    <!-- Empty results -->
                    <template x-if="msg.columns && msg.columns.length === 0 && !msg.error">
                      <div class="msg-info" style="margin-top: 8px;">No results found for that query.</div>
                    </template>
                  </div>
                </template>

                <!-- Error message -->
                <template x-if="msg.role === 'assistant' && msg.error === 'sql'">
                  <div class="msg-error">
                    <div>The generated query didn't work. Try rephrasing your question.</div>
                    <button class="sql-toggle" @click="msg._showSql = !msg._showSql"
                            x-text="msg._showSql ? '&#9660; Hide SQL' : '&#9654; View failed SQL'"
                            style="color: var(--brand-error);"></button>
                    <div class="sql-block" x-show="msg._showSql" x-transition x-text="msg.sql"></div>
                  </div>
                </template>

                <template x-if="msg.role === 'assistant' && msg.error === 'llm'">
                  <div class="msg-warning">
                    <span x-text="'Couldn\'t generate a query — ' + msg.detail"></span>
                  </div>
                </template>
              </div>
            </template>

            <!-- Loading indicator -->
            <div class="loading-dots" x-show="loading">
              <span></span><span></span><span></span>
            </div>

          </div>
        </template>
      </div>

      <!-- Input bar -->
      <div class="input-bar" x-show="hasApiKey">
        <input type="text"
               x-model="question"
               @keydown.enter.prevent="submitQuestion(question)"
               :disabled="loading"
               placeholder="Ask a question about your data...">
        <button class="btn-send" @click="submitQuestion(question)" :disabled="loading || !question.trim()">
          <span x-show="!loading">&#10148;</span>
          <span x-show="loading" style="font-size: 14px;">&#8987;</span>
        </button>
      </div>

    </main>
  </div>
</div>

<!-- Alpine.js (CDN) -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
<!-- App logic -->
<script src="/static/app.js"></script>

</body>
</html>
```

- [ ] **Step 3: Commit**

```bash
git add tools/demo_text_to_sql/templates/index.html
git commit -m "feat: add index.html Jinja2 template with full chat UI layout"
```

---

## Task 6: Create `app.js` — Alpine.js App Logic

**Files:**
- Create: `tools/demo_text_to_sql/static/app.js`

- [ ] **Step 1: Write app.js**

```javascript
/* app.js — QueryCraft Alpine.js application logic */

function app() {
  return {
    // State
    theme: localStorage.getItem('qc-theme') || 'dark',
    sidebarOpen: window.innerWidth > 768,
    schema: [],
    messages: [],
    history: [],
    question: '',
    loading: false,
    hasApiKey: true, // assume true, updated on first query or schema load
    highlightedTable: '',

    exampleQuestions: [
      'Top 10 customers by total spend',
      'Most popular genre',
      'Monthly revenue trend',
      'Which artists have the most albums?',
      'Average invoice by country',
    ],

    // Lifecycle
    init() {
      document.documentElement.setAttribute('data-theme', this.theme);
      this.fetchSchema();
    },

    // Theme
    toggleTheme() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', this.theme);
      localStorage.setItem('qc-theme', this.theme);
    },

    // Schema
    async fetchSchema() {
      try {
        const res = await fetch('/api/schema');
        if (!res.ok) throw new Error('Failed to load schema');
        const data = await res.json();
        // Add _open flag for tree toggle
        this.schema = data.map(t => ({ ...t, _open: false }));
      } catch (e) {
        console.error('Schema load failed:', e);
      }
    },

    // Chat
    async submitQuestion(q) {
      q = q.trim();
      if (!q || this.loading) return;

      // Add user message
      this.messages.push({ role: 'user', content: q });
      this.history.push(q);
      this.question = '';
      this.loading = true;
      this.scrollToBottom();

      try {
        const res = await fetch('/api/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: q }),
        });

        const data = await res.json();

        if (!res.ok) {
          // Determine error type
          if (data.detail && data.detail.includes('API key')) {
            this.hasApiKey = false;
            this.messages.push({
              role: 'assistant',
              error: 'llm',
              detail: data.detail,
            });
          } else if (data.error_type === 'sql') {
            this.messages.push({
              role: 'assistant',
              error: 'sql',
              sql: data.sql || '',
              _showSql: false,
            });
          } else {
            this.messages.push({
              role: 'assistant',
              error: 'llm',
              detail: data.detail || 'Unknown error',
            });
          }
        } else {
          // Success
          const msg = {
            role: 'assistant',
            summary: data.summary,
            sql: data.sql,
            columns: data.columns,
            rows: data.rows,
            _showSql: false,
            _sortCol: null,
            _sortAsc: true,
            _displayRows: (data.rows || []).slice(0, 50),
          };
          this.messages.push(msg);

          // Highlight queried table
          this.highlightTable(data.sql);
        }
      } catch (e) {
        this.messages.push({
          role: 'assistant',
          error: 'llm',
          detail: 'Network error — could not reach the server.',
        });
      }

      this.loading = false;
      this.scrollToBottom();
    },

    replayQuestion(q) {
      this.question = q;
      this.submitQuestion(q);
    },

    // Table sorting (client-side)
    sortColumn(msg, colIdx) {
      if (msg._sortCol === colIdx) {
        msg._sortAsc = !msg._sortAsc;
      } else {
        msg._sortCol = colIdx;
        msg._sortAsc = true;
      }

      const sorted = [...msg.rows].sort((a, b) => {
        const va = a[colIdx];
        const vb = b[colIdx];
        if (va == null) return 1;
        if (vb == null) return -1;
        if (typeof va === 'number' && typeof vb === 'number') {
          return msg._sortAsc ? va - vb : vb - va;
        }
        const sa = String(va).toLowerCase();
        const sb = String(vb).toLowerCase();
        if (sa < sb) return msg._sortAsc ? -1 : 1;
        if (sa > sb) return msg._sortAsc ? 1 : -1;
        return 0;
      });

      msg._displayRows = sorted.slice(0, 50);
    },

    // CSV export
    exportCsv(msg) {
      const escape = (val) => {
        const s = String(val == null ? '' : val);
        return s.includes(',') || s.includes('"') || s.includes('\n')
          ? '"' + s.replace(/"/g, '""') + '"'
          : s;
      };

      const header = msg.columns.map(escape).join(',');
      const rows = msg.rows.map(r => r.map(escape).join(','));
      const csv = [header, ...rows].join('\n');

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'query-results.csv';
      a.click();
      URL.revokeObjectURL(url);
    },

    // Highlight queried table in sidebar
    highlightTable(sql) {
      if (!sql) return;
      const upper = sql.toUpperCase();
      for (const table of this.schema) {
        if (upper.includes(table.name.toUpperCase())) {
          this.highlightedTable = table.name;
          return;
        }
      }
      this.highlightedTable = '';
    },

    // Auto-scroll
    scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.chatThread;
        if (el) el.scrollTop = el.scrollHeight;
      });
    },
  };
}
```

- [ ] **Step 2: Commit**

```bash
git add tools/demo_text_to_sql/static/app.js
git commit -m "feat: add app.js with Alpine.js chat, sidebar, theme, and export logic"
```

---

## Task 7: Create FastAPI `app.py` — Server & Endpoints

**Files:**
- Replace: `tools/demo_text_to_sql/app.py`
- Create: `tests/demo_text_to_sql/test_app.py`

- [ ] **Step 1: Write failing tests for FastAPI endpoints**

```python
# tests/demo_text_to_sql/test_app.py
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    # Import here so env vars and mocks are set up first
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


@patch("tools.demo_text_to_sql.app.generate_sql")
def test_post_query_sql_error(mock_gen, client):
    mock_gen.return_value = "SELECT * FROM nonexistent_table_xyz"
    response = client.post("/api/query", json={"question": "bad query"})
    assert response.status_code == 400
    data = response.json()
    assert data["error_type"] == "sql"
    assert "sql" in data


@patch("tools.demo_text_to_sql.app.generate_sql")
def test_post_query_llm_error(mock_gen, client):
    mock_gen.side_effect = Exception("Rate limited")
    response = client.post("/api/query", json={"question": "test"})
    assert response.status_code == 502
    data = response.json()
    assert "detail" in data


def test_post_query_empty_question(client):
    response = client.post("/api/query", json={"question": ""})
    assert response.status_code == 422 or response.status_code == 400


@patch("tools.demo_text_to_sql.app.generate_sql")
def test_post_query_timeout(mock_gen, client):
    import asyncio
    def slow(*args, **kwargs):
        import time
        time.sleep(35)
    mock_gen.side_effect = slow
    # The 30s timeout should trigger before the function returns
    response = client.post("/api/query", json={"question": "slow query"})
    assert response.status_code == 504
    assert "timed out" in response.json()["detail"].lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd c:/Workflows/FirstWorkflow && python -m pytest tests/demo_text_to_sql/test_app.py -v`

Expected: FAIL — the existing `app.py` is a Streamlit app, not FastAPI.

- [ ] **Step 3: Replace app.py with FastAPI server**

Overwrite `tools/demo_text_to_sql/app.py` with:

```python
# tools/demo_text_to_sql/app.py
"""
QueryCraft — Chat With Your Database
FastAPI server that serves the frontend and provides API endpoints
for schema introspection and natural-language-to-SQL queries.
"""

import asyncio
import os
import sqlite3
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, field_validator

from tools.demo_text_to_sql.db import get_connection, get_schema, get_schema_ddl, run_query
from tools.demo_text_to_sql.llm import generate_sql

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

DB_PATH = os.environ.get(
    "DEMO_DB_PATH",
    os.path.join(os.path.dirname(__file__), "chinook.db"),
)

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(__file__)

_conn = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = get_connection(DB_PATH)
    return _conn


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: open DB connection
    _get_conn()
    yield
    # Shutdown: close connection
    global _conn
    if _conn:
        _conn.close()
        _conn = None


app = FastAPI(title="QueryCraft", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class QueryRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the single-page app."""
    has_key = bool(ANTHROPIC_KEY or OPENAI_KEY)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "has_api_key": has_key},
    )


@app.get("/api/schema")
async def api_schema():
    """Return the database schema as JSON."""
    conn = _get_conn()
    return get_schema(conn)


@app.post("/api/query")
async def api_query(body: QueryRequest):
    """Accept a natural language question, generate SQL, execute it, return results.
    
    Entire operation is wrapped in a 30-second timeout.
    """
    conn = _get_conn()

    if not ANTHROPIC_KEY and not OPENAI_KEY:
        return JSONResponse(
            status_code=502,
            content={"detail": "No API key configured. Add ANTHROPIC_API_KEY or OPENAI_API_KEY to .env."},
        )

    # Generate SQL
    schema_ddl = get_schema_ddl(conn)
    try:
        sql = await asyncio.wait_for(
            asyncio.to_thread(
                generate_sql,
                question=body.question,
                schema=schema_ddl,
                anthropic_key=ANTHROPIC_KEY,
                openai_key=OPENAI_KEY,
            ),
            timeout=30.0,
        )
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=504,
            content={"detail": "Request timed out after 30 seconds. Try a simpler question."},
        )
    except Exception as e:
        return JSONResponse(
            status_code=502,
            content={"detail": f"LLM error: {e}"},
        )

    # Execute SQL
    try:
        result = run_query(conn, sql)
    except sqlite3.OperationalError as e:
        return JSONResponse(
            status_code=400,
            content={"error_type": "sql", "sql": sql, "detail": str(e)},
        )

    # Build summary
    row_count = len(result["rows"])
    if row_count == 0:
        summary = "No results found for that query."
    else:
        summary = f"Found {row_count} result{'s' if row_count != 1 else ''}."

    return {
        "sql": sql,
        "columns": result["columns"],
        "rows": result["rows"],
        "summary": summary,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd c:/Workflows/FirstWorkflow && python -m pytest tests/demo_text_to_sql/test_app.py -v`

Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/demo_text_to_sql/app.py tests/demo_text_to_sql/test_app.py
git commit -m "feat: replace Streamlit app.py with FastAPI server and API endpoints"
```

---

## Task 8: Add Dependencies & Run Script

**Files:**
- Modify: `tools/demo_text_to_sql/` (may need a `requirements.txt` or update existing one)

- [ ] **Step 1: Check for existing requirements file**

```bash
ls tools/demo_text_to_sql/requirements.txt 2>/dev/null; ls requirements.txt 2>/dev/null
```

- [ ] **Step 2: Create requirements.txt at project root (if none exists)**

```
# Core app
fastapi>=0.110
uvicorn[standard]>=0.29
jinja2>=3.1
python-dotenv>=1.0

# LLM providers (need at least one)
anthropic>=0.25
openai>=1.12

# Testing
pytest>=8.0
httpx>=0.27
```

- [ ] **Step 3: Install dependencies**

Run: `cd c:/Workflows/FirstWorkflow && pip install -r requirements.txt`

- [ ] **Step 4: Run the full test suite**

Run: `cd c:/Workflows/FirstWorkflow && python -m pytest tests/ -v`

Expected: All tests from Tasks 1, 2, and 7 pass (19 tests total).

- [ ] **Step 5: Verify the app starts**

Run: `cd c:/Workflows/FirstWorkflow && python -m uvicorn tools.demo_text_to_sql.app:app --host 127.0.0.1 --port 8000`

Expected: Server starts, visit `http://127.0.0.1:8000` to see the QueryCraft UI. Ctrl+C to stop.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt
git commit -m "feat: add requirements.txt with FastAPI, uvicorn, and test dependencies"
```

---

## Task 9: End-to-End Manual Verification

- [ ] **Step 1: Start the server**

```bash
cd c:/Workflows/FirstWorkflow && python -m uvicorn tools.demo_text_to_sql.app:app --host 127.0.0.1 --port 8000
```

- [ ] **Step 2: Verify dark mode (default)**

Open `http://127.0.0.1:8000` in a browser. Confirm:
- Dark background (`#0C0716`)
- Purple + gold gradient logo mark
- "QueryCraft" wordmark in header
- Sidebar with Schema Explorer showing Chinook tables (all collapsed)
- Example question pills visible in main area

- [ ] **Step 3: Verify light mode toggle**

Click the theme toggle button. Confirm:
- Background switches to light (`#FAF5FF`)
- Cards switch to white
- Toggle persists after page reload (check `localStorage`)

- [ ] **Step 4: Test example question flow**

Click "Top 10 customers by total spend" pill. Confirm:
- User message appears right-aligned with purple background
- Loading dots animate
- Assistant response appears with summary, collapsible SQL, and results table
- Example pills fade out
- Query appears in sidebar history
- Relevant table highlighted in schema explorer

- [ ] **Step 5: Test table sorting**

Click a column header in the results table. Confirm:
- Rows re-sort ascending (arrow up shown)
- Click same header again: sorts descending
- Click different header: sorts ascending by that column

- [ ] **Step 6: Test CSV export**

Click "Export CSV" button. Confirm a `.csv` file downloads with correct data.

- [ ] **Step 7: Test error handling**

Type an intentionally confusing query like "asdfghjkl gibberish nonsense". Confirm:
- If LLM generates invalid SQL: red error card with collapsible failed SQL
- Input re-enables for retry

- [ ] **Step 8: Test sidebar collapse (responsive)**

Resize the browser window below 768px wide. Confirm:
- Sidebar collapses
- Hamburger menu icon appears in header
- Clicking it toggles sidebar overlay

- [ ] **Step 9: Commit any fixes from verification**

If any fixes were needed during verification:

```bash
git add -A
git commit -m "fix: address issues found during manual verification"
```
