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
    _get_conn()
    yield
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
        request,
        "index.html",
        {"has_api_key": has_key},
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
            timeout=45.0,
        )
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=504,
            content={"detail": "Request timed out after 45 seconds. Try a simpler question."},
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
