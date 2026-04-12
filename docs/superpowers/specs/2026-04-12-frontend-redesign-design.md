# Frontend Redesign — Chat With Your Database

**Date:** 2026-04-12
**Status:** Approved
**Scope:** Replace the Streamlit UI with a custom FastAPI + Alpine.js + Tailwind CSS frontend

## Context

The current `tools/demo_text_to_sql/app.py` is a Streamlit app that serves as both a Fiverr portfolio demo and a product buyers interact with. It uses stock Streamlit defaults — no branding, generic layout, limited interactivity. The goal is to rebuild it as a modern, branded single-page app that feels like a real SaaS product.

**Primary audience:** Both Fiverr buyers evaluating the gig (need to be impressed in 30 seconds) and end users querying their databases daily.

## 1. Brand Identity

A reusable brand system for this and all future products. Saved separately as `brand.css`.

### Color Palette — Purple + Warm Gold

| Token | Value | Usage |
|-------|-------|-------|
| Primary | `#5B21B6` | Buttons, active states, primary actions |
| Primary Vivid | `#7C3AED` | Hover states, gradients, lighter emphasis |
| Accent (Gold) | `#D97706` | Highlights, badges, export buttons, secondary CTAs |
| Dark | `#0C0716` | Dark mode background, headings |
| Dark Surface | `#150E24` | Dark mode cards, input backgrounds |
| Dark Border | `#2D1F4E` | Dark mode borders |
| Light | `#FAF5FF` | Light mode background |
| Light Surface | `#FFFFFF` | Light mode cards, input backgrounds |
| Light Border | `#E9D5FF` | Light mode borders |
| Text Primary (dark) | `#FAF5FF` | Headings and body text on dark backgrounds |
| Text Primary (light) | `#0C0716` | Headings and body text on light backgrounds |
| Text Secondary | `#6B7280` | Placeholder text, secondary labels |
| Success | `#10B981` | Successful queries |
| Error | `#EF4444` | Query failures, validation errors |
| Info | `#3B82F6` | Informational messages |

### Logo Mark

Gradient square (`linear-gradient(135deg, #7C3AED, #D97706)`) with 8px border-radius. Paired with "QueryCraft" wordmark in Inter Bold.

### Typography

- **Headings & UI:** Inter (Google Fonts CDN)
- **Code/SQL:** JetBrains Mono (Google Fonts CDN)

### Spacing

4px base unit: `4, 8, 12, 16, 24, 32, 48, 64`

### Border Radius

- Cards/panels: `8px`
- Buttons/inputs: `6px`
- Modals: `12px`
- Pills/badges: `20px`

### Shadows

- Cards: `0 1px 3px rgba(0,0,0,0.1)`
- Elevated (dropdowns, modals): `0 4px 12px rgba(0,0,0,0.15)`

### Design Principles

- **Reliable** — consistent spacing, predictable interactions, clear feedback on every action
- **Intuitive** — obvious affordances, no guessing what's clickable
- **Elegant** — restraint over decoration, whitespace as a design element

## 2. Layout & Page Structure

Single-page app with three zones:

### Header Bar (fixed top, ~56px)

- Left: logo mark + "QueryCraft" wordmark
- Right: dark/light mode toggle

### Sidebar (collapsible, left, ~280px expanded)

- **Schema Explorer:** tree view of tables → expandable columns with types. All collapsed by default. Subtle purple highlight on the table currently being queried.
- **Query History:** scrollable list of past questions. Click to replay.
- Collapses to icon-only on small screens.

### Main Area (center)

- **Example Questions (empty state):** 5-6 clickable pill-shaped chips. Clicking auto-submits. Fade out after first message sent. Chips: "Top 10 customers by total spend", "Most popular genre", "Monthly revenue trend", "Which artists have the most albums?", "Average invoice by country".
- **Chat Thread:** vertically scrolling messages.
- **Input Bar (fixed bottom of main area):** full-width text input + purple send button. Enter submits, Shift+Enter for newline. Disabled with spinner while loading.

## 3. Architecture

### File Structure

```
tools/demo_text_to_sql/
├── app.py              # FastAPI server (replaces Streamlit app.py)
├── llm.py              # LLM helpers (generate_sql, provider switching)
├── db.py               # Database helpers (connection, schema, query execution)
├── static/
│   ├── brand.css       # Shared brand tokens — reusable across future products
│   ├── style.css       # App-specific component styles
│   └── app.js          # Alpine.js app logic (chat, sidebar, theme toggle)
├── templates/
│   └── index.html      # Single Jinja2 template (loads Alpine + Tailwind via CDN)
└── chinook.db          # Sample database (already exists)
```

### Key Decisions

- `brand.css` separated from `style.css` so future products import only brand tokens
- `llm.py` and `db.py` extracted from current monolithic `app.py` — same logic, cleaner separation
- Alpine.js and Tailwind CSS loaded via CDN — no build step, no Node dependency
- FastAPI serves the template and API endpoints

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | Serve the HTML page |
| `GET` | `/api/schema` | Return database schema as JSON |
| `POST` | `/api/query` | Accept natural language question, return `{ sql, columns, rows, summary }` |

### Data Flow

1. User types a question → JS sends `POST /api/query`
2. FastAPI calls `llm.py` to generate SQL → calls `db.py` to execute → returns JSON
3. Alpine.js reactively renders the response in the chat thread
4. Query added to history (Alpine local state, no backend persistence)

## 4. Component Details

### Dark/Light Mode Toggle

- Defaults to dark mode (better for screenshots/demos)
- Toggle in header, persists to `localStorage`
- CSS variables swap between palettes

### Schema Explorer

- Fetches from `GET /api/schema` on page load
- Tree: table name → expandable column list with types
- All tables collapsed by default
- Purple highlight on table currently being queried (parsed from generated SQL)

### Example Questions

- 5-6 clickable outlined pill buttons
- Clicking fills input and auto-submits
- Hardcoded for Chinook demo
- Fade out after first message

### Chat Messages

- **User messages:** right-aligned, purple background, white text
- **Assistant messages:** left-aligned, surface card with subtle border
  - Natural language summary
  - "View SQL" toggle — collapsed by default, syntax-highlighted in JetBrains Mono
  - Results table — striped rows, sortable column headers (click to toggle ascending/descending, client-side sort on the returned data), capped at 50 rows with truncation note
  - "Export CSV" button — small, gold accent, bottom-right of results table

### Input Bar

- Fixed to bottom of main area
- Full-width input + purple send button (arrow icon)
- Enter submits, Shift+Enter for newline
- Disabled with loading spinner while waiting

### Loading State

- Pulsing purple dot animation in chat thread
- Input bar disabled during loading

## 5. Error Handling

### LLM Errors (API key missing, rate limit, timeout)

Gold-accented warning card in chat: "Couldn't generate a query — [specific reason]." Input re-enables for retry.

### SQL Execution Errors

Error card with collapsible block showing the failed SQL. Message: "The generated query didn't work. Try rephrasing your question." No stack traces.

### Empty Results

Informational message: "No results found for that query" with SQL still viewable. Not styled as an error.

### No API Key Configured

Centered onboarding card instead of chat: "To get started, add your ANTHROPIC_API_KEY or OPENAI_API_KEY to the .env file" with setup instructions. This is the first thing a buyer sees after cloning.

### Long-Running Queries

30-second timeout on FastAPI endpoint. If exceeded, cancel and show timeout message.
