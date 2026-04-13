# QueryCraft — Chat With Your Database

A text-to-SQL demo that lets you ask questions about a database in plain English. Type a question, get back the SQL query and results instantly.

Built with FastAPI, Alpine.js, and Tailwind CSS. No complex frameworks — just a clean prompt to a frontier LLM (Claude or GPT-4o) and a lightweight web UI.

## How It Works

```
User question → LLM generates SQL → SQLite executes it → Results displayed
```

1. The frontend sends your natural language question to the `/api/query` endpoint
2. The backend sends the database schema + your question to the LLM with a system prompt constraining output to valid SELECT statements
3. The generated SQL runs against the database (read-only)
4. Results come back as a sortable table with CSV export

## Features

- **Schema Explorer** — browse tables and columns in the sidebar
- **Query History** — replay past questions with one click
- **Sortable Results** — click column headers to sort
- **CSV Export** — download any result set
- **Dark/Light Theme** — toggle in the header
- **SQL Transparency** — view the generated SQL for every query
- **Retry Logic** — automatic retries with backoff for transient API errors

## Quick Start

### Prerequisites

- Python 3.10+
- An API key from [Anthropic](https://console.anthropic.com/) or [OpenAI](https://platform.openai.com/)

### Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/chat-with-your-database-demo.git
cd chat-with-your-database-demo

# Install dependencies
pip install -r requirements.txt

# Add your API key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
# or: echo "OPENAI_API_KEY=sk-..." > .env

# Run the server
python -m uvicorn tools.demo_text_to_sql.app:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### Try These Questions

- "Top 10 customers by total spend"
- "Most popular genre by track count"
- "Monthly revenue trend over the last 2 years"
- "Which artists have the most albums?"
- "How many employees report to each manager?"
- "Show revenue by genre"

## Architecture

```
tools/demo_text_to_sql/
├── app.py              # FastAPI server, routes, request handling
├── db.py               # SQLite connection, schema introspection, query execution
├── llm.py              # LLM integration (Claude / GPT-4o) with retry logic
├── chinook.db          # Sample database (Chinook music store)
├── templates/
│   └── index.html      # Single-page app (Alpine.js + Tailwind CSS)
└── static/
    ├── app.js          # Frontend logic (chat, history, sorting, export)
    ├── brand.css       # Design tokens (colors, typography, spacing)
    └── style.css       # Component styles
```

## Sample Database

This demo uses the [Chinook database](https://github.com/lerocha/chinook-database) — a sample music store with 11 tables covering artists, albums, tracks, customers, invoices, and employees. It's the standard test database for SQL tooling.

## Connecting Your Own Database

To point QueryCraft at a different SQLite database:

```bash
DEMO_DB_PATH=/path/to/your/database.db python -m uvicorn tools.demo_text_to_sql.app:app --reload
```

The schema explorer and LLM prompt adapt automatically — no code changes needed.

## Security

- **Read-only queries only** — the system prompt constrains the LLM to SELECT statements, and the backend enforces this before execution
- **Your data stays local** — only the schema DDL and your question are sent to the LLM provider. Row data never leaves your machine.
- **API keys stay in `.env`** — never committed to the repo

## License

MIT
