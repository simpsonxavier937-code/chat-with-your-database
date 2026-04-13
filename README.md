# QueryCraft — Chat With Your Database

Ask questions about your data in plain English. QueryCraft translates natural language into SQL, runs it against your database, and shows you the results — no SQL knowledge required.

![Python](https://img.shields.io/badge/python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## What It Does

- **Natural language to SQL** — Type a question like "top 10 customers by total spend" and get accurate SQL + results
- **Schema explorer** — Browse your tables and columns in the sidebar
- **Query history** — Replay previous questions with one click
- **CSV export** — Download any result set
- **Dark/light mode** — Automatic theme switching
- **No black box** — Every generated query is visible and inspectable

## How It Works

```
User question
    ↓
Schema + question sent to LLM (Claude or GPT-4o)
    ↓
LLM generates a SELECT query
    ↓
Query executes against your database (read-only)
    ↓
Results displayed in a sortable table
```

Your data stays in your environment. Only the database schema and your question are sent to the LLM provider.

## Quick Start

**1. Clone and install**

```bash
git clone https://github.com/YOUR_USERNAME/chat-with-your-database.git
cd chat-with-your-database
pip install -r requirements.txt
```

**2. Add your API key**

Copy the example env file and add your key:

```bash
cp .env.example .env
```

Then edit `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Or use OpenAI instead:

```
OPENAI_API_KEY=sk-...
```

**3. Run it**

```bash
python -m uvicorn app:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Using Your Own Database

By default, QueryCraft runs against the included [Chinook](https://github.com/lerocha/chinook-database) sample database (a music store with artists, albums, customers, and invoices).

To point it at your own SQLite database:

```bash
DEMO_DB_PATH=/path/to/your/database.db python -m uvicorn app:app --reload
```

For PostgreSQL, MySQL, or MSSQL support, [contact me on Fiverr](FIVERR_GIG_URL) — I'll build a custom deployment for your stack.

## Example Questions

These all work out of the box with the included Chinook database:

| Question | What it tests |
|----------|--------------|
| Top 10 customers by total spend | JOIN + GROUP BY + ORDER |
| Most popular genre by track count | Aggregation |
| Average invoice value by country | GROUP BY on a single table |
| Which artists have the most albums? | Simple JOIN |
| Monthly revenue trend over the last 2 years | Date functions (`strftime`) |
| Total revenue by genre, top 5 | 3-table JOIN (Genre → Track → InvoiceLine) |
| What percentage of tracks are longer than 5 minutes? | CASE + arithmetic |
| Show playlists with more than 3 genres | Multi-JOIN + HAVING |

## Architecture

```
app.py          FastAPI server — routes, request handling, timeout management
db.py           Database helpers — connection, schema introspection, query execution
llm.py          LLM integration — prompt construction, Claude/GPT-4o API calls
templates/      Jinja2 HTML template
static/         Alpine.js app logic, Tailwind + custom CSS
chinook.db      Sample SQLite database (Chinook music store)
```

All queries are read-only (`SELECT` only). Write operations are blocked at the application layer.

## Tech Stack

- **Backend:** Python, FastAPI, SQLite
- **Frontend:** Alpine.js, Tailwind CSS, Jinja2
- **LLM:** Anthropic Claude Sonnet or OpenAI GPT-4o (configurable)

## License

MIT
