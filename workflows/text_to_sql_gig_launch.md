# Workflow: Text-to-SQL Fiverr Gig Launch

## Status
**DRAFT** — written 2026-04-08 from the niche research output (`.tmp/niche_brief_2026-04-08.md`).
Has not yet been run end-to-end. Refine after the first execution; expect the FAQ section,
pricing, and review-velocity tactics to need revision based on real Fiverr feedback.

## Objective
Take the user from "no Fiverr presence in this niche" to "live text-to-SQL gig with the
first reviews coming in" within ~2 weeks of execution. The downstream goal is to validate
that buyers will actually pay for custom text-to-SQL builds, not just SaaS subscriptions.

## Required Inputs (ask the user before starting)
1. **OpenAI API key OR Anthropic API key** in `.env` (the demo needs an LLM)
2. **Fiverr seller account** — already created, or willingness to create one (verification
   takes 24–72h, factor that into the timeline)
3. **GitHub account** — public, for the demo repo. Credibility hinges on a public repo.
4. **3–5 people in the user's network** with any kind of database (even SQLite, even a
   personal project) who could be early test buyers at half price for the first reviews
5. **Screen recording tool** — Loom (free tier works) or OBS

If any of these are missing, **stop and ask** before starting.

## Phases

### Phase 1 — Build the demo
**Goal:** a working text-to-SQL agent on the Chinook sample database that you can
screen-record. This is the single artifact that replaces a portfolio.

1. Create the demo directory: `tools/demo_text_to_sql/`
2. Install deps: `pip install fastapi uvicorn jinja2 openai anthropic python-dotenv`
3. Download Chinook SQLite from https://github.com/lerocha/chinook-database (the
   `Chinook_Sqlite.sqlite` file). Save as `tools/demo_text_to_sql/chinook.db`.
4. Write the backend modules:
   - `tools/demo_text_to_sql/db.py` — SQLite connection, schema introspection, query
     execution (read-only)
   - `tools/demo_text_to_sql/llm.py` — sends schema + user question directly to
     Claude (or GPT-4o) with a system prompt constraining output to valid SELECT
     statements. Includes retry logic with backoff for transient API errors (529
     overloaded, rate limits).
   - `tools/demo_text_to_sql/app.py` — FastAPI server with `/api/schema` and
     `/api/query` endpoints, serves the frontend via Jinja2 templates
5. Write the frontend:
   - `tools/demo_text_to_sql/templates/index.html` — Alpine.js + Tailwind CSS SPA
   - `tools/demo_text_to_sql/static/app.js` — chat logic, schema explorer,
     query history, CSV export, theme toggle, "New Query" reset button
   - `tools/demo_text_to_sql/static/brand.css` — shared brand tokens (dark/light)
   - `tools/demo_text_to_sql/static/style.css` — component styles
   - Show the generated SQL openly. Buyers should see "no black box."
6. Smoke-test 8–10 sample questions and iterate until accuracy is >80% on first try.
   Bad demo = no orders. Examples to test:
   - "Top 10 customers by total spend"
   - "Most popular genre by track count"
   - "Average invoice value by country"
   - "Show me the longest tracks"
   - "Which artists have the most albums?"
   - "Monthly revenue trend over the last 2 years"
   - "How many employees report to each manager?" (self-join)
   - "Revenue by genre" (3-table join)
   **Status (2026-04-13):** 10/10 queries passed on first try. Accuracy exceeds target.
7. Push to a public GitHub repo. Suggested name: `text-to-sql-demo` or
   `chat-with-your-database-demo`.
8. Clean README with: what it is, how to run it, architecture diagram, and a link
   back to the Fiverr gig (you'll fill that in after Phase 4).

**Architecture note:** We dropped Vanna in favour of direct LLM calls. Frontier models
(Claude Sonnet, GPT-4o) handle text-to-SQL well enough on clean schemas with just a
system prompt — no RAG training step needed. This simplifies the stack (no ChromaDB
dependency) and means the demo works out of the box with just an API key.

### Phase 2 — Record demo media
**Goal:** 3 pieces of media to upload to the gig listing.

1. **90-second screen capture** of using the chat UI. Show 4–5 questions, including
   one moderately complex join. Loom or OBS, export as MP4.
2. **2–3 still screenshots** of the UI in action (these become Fiverr gig images).
3. **Optional architecture diagram** as PNG — handwritten on a whiteboard or Excalidraw.

Save all to `.tmp/gig_media_<YYYY-MM-DD>/`.

### Phase 3 — Write the gig copy
**Goal:** title, description, packages, FAQ, and tags ready to paste into Fiverr.

Output to `.tmp/gig_copy_<YYYY-MM-DD>.md` with sections:

1. **Three candidate gig titles** (test by sharing with a few peers, pick the one that
   makes the most sense to a non-technical buyer):
   - "I will build a chat-with-your-database AI assistant in Python"
   - "I will turn your SQL database into an AI chatbot you can ask in plain English"
   - "I will build a custom text-to-SQL AI agent for your PostgreSQL/MySQL/MSSQL database"

2. **Gig description** (Fiverr allows 1,200 chars). Structure:
   - **Hook (1–2 lines):** name a specific pain. *"Your team keeps asking 'how many X
     did we sell last quarter?' and waiting on someone who knows SQL to answer. I'll
     fix that."*
   - **Who it's for:** non-technical buyers (CEOs, sales, support, ops) who own data
     but can't query it themselves
   - **What you'll get:** concrete deliverables (a working chat UI, your real schema
     trained, the source code, deployment instructions)
   - **Why me:** SQL engineer first, AI second. You'll see the source code. Your data
     never leaves your environment. (These three lines directly answer the recurring
     Fiverr complaints documented in the niche brief.)
   - **Process:** intake → schema review → build → handoff → 7 days of Q&A

3. **Three packages:**

   | Tier      | Price  | Includes                                                                                                                            | Delivery |
   |-----------|:------:|-------------------------------------------------------------------------------------------------------------------------------------|:--------:|
   | Basic     | $85    | 1 database (PostgreSQL/MySQL/SQLite/MSSQL), ≤5 tables, web chat UI you can run locally, source code                            | 3 days   |
   | Standard  | $245   | Up to 20 tables, multi-table joins, custom prompt templates with your business glossary, basic auth, deployable to your machine     | 5 days   |
   | Premium   | $495   | Production deployment (Docker or your cloud), row-level security, query history + analytics, 30 days of revisions and Q&A           | 10 days  |

   **Note:** These prices are the launch starting point from the niche brief. After
   ~10 reviews, raise everything ~25%.

4. **8–10 FAQ entries** (these matter — they convert):
   - "What database types do you support?" (PostgreSQL, MySQL, SQLite, MSSQL, others on request)
   - "Will my data leave my server?" (No. The agent runs in your environment. Only
     the schema and your example questions are shared with the LLM provider.)
   - "What if my schema changes?" (Re-training takes ~30 minutes. I'll document the process.)
   - "Do I need to know SQL?" (No. That's the whole point. But you'll see the SQL
     the AI generates, so a technical reviewer can verify it.)
   - "Can you deploy this to my cloud?" (Premium tier yes — AWS, Azure, GCP, or your
     own server via Docker.)
   - "What LLM does this use? Can I swap it for Claude or a local model?" (Default is
     OpenAI GPT-4. Yes, swappable to Anthropic Claude, or local Llama via Ollama —
     Standard tier and up.)
   - "What if the AI gets a query wrong?" (The architecture shows the SQL before
     running it, so you can catch errors. I also train it with example Q&A pairs from
     your real data to drive accuracy up.)
   - "Do I need an OpenAI / Anthropic account?" (Yes — you'll need an API key. Setup
     takes 5 minutes; I'll walk you through it.)
   - "How accurate is it?" (Depends on schema complexity. Out of the box, frontier
     LLMs hit 70–85% on clean schemas. With proper training on your data,
     85–95% is achievable. I'll measure accuracy on your sample questions during
     handoff.)
   - "Can you build this for [specific vertical]?" (Yes — accounting, e-commerce,
     SaaS, healthcare, real estate, manufacturing. The harder the schema, the more
     value Standard/Premium provide.)

5. **Tags:** text-to-sql, ai-chatbot, sql-database, openai, vanna-ai, database-automation,
   ai-assistant, postgresql, mysql, business-intelligence

### Phase 4 — List the gig
1. Verify Fiverr seller account (identity verification, payout setup)
2. Create the gig with copy from Phase 3 + media from Phase 2
3. Drop the GitHub demo repo URL in the FAQ section (Fiverr restricts external links
   in the main description but allows them in FAQ)
4. Submit for review — Fiverr typically approves in 24h
5. Once live, paste the gig URL back into the GitHub demo repo's README

### Phase 5 — First reviews (review velocity)
**Goal:** 4–5 reviews in 2 weeks to escape "new seller" purgatory and unlock impressions.

1. Identify 3–5 people in your network with any database (even SQLite, even a side
   project) who could plausibly use the demo
2. Offer them the Basic tier at $40 in exchange for honest feedback. Don't promise a
   5-star review — Fiverr can flag explicit review-trading. Frame it as a beta test.
3. Deliver in 1–2 days with white-glove care (over-communicate, over-document)
4. Fiverr's review prompt fires automatically on order completion. Ask for their
   honest take.
5. Track which gig title variant performed best for impressions (Fiverr surfaces this
   in seller analytics after ~7 days of activity)

### Phase 6 — Iterate (after 30 days)
1. Re-run `workflows/fiverr_niche_research.md` to refresh the market picture
2. Look at which questions buyers actually ask in the inquiry phase → add them to FAQ
3. Look at which package buyers actually choose → adjust pricing if everyone picks
   Basic (price too low) or nobody picks Premium (gap too wide)
4. Look at which tags drive impressions → adjust tags
5. Update *this workflow* with what you learned. The launch tactics should refine
   over time the same way the research workflow does.

## Tools used
- **FastAPI** — backend server with REST endpoints for schema and query
- **Alpine.js + Tailwind CSS** — lightweight frontend SPA (no build step)
- **Anthropic Claude API or OpenAI API** — the LLM generating SQL from natural language
- **Chinook SQLite database** — public sample data for the demo
- **Loom or OBS** — screen recording
- **GitHub** — public demo repo for credibility

No Python tools to build for `tools/` yet. The demo itself lives in
`tools/demo_text_to_sql/` because it's reusable artifact, not because it's an
orchestration helper.

## Outputs
- `tools/demo_text_to_sql/` — committed demo code (the portfolio piece)
- `.tmp/gig_media_<date>/` — recorded video + screenshots
- `.tmp/gig_copy_<date>.md` — finalized gig copy ready to paste
- A live Fiverr gig with the first reviews coming in
- A public GitHub repo linked from the gig FAQ

## Edge cases & lessons learned
- **Direct LLM calls beat Vanna for clean schemas.** We dropped Vanna's RAG pipeline
  because Claude Sonnet and GPT-4o hit 100% accuracy on Chinook with just a system
  prompt. No training step, no ChromaDB. For messier real-world schemas, consider
  adding few-shot examples to the system prompt before reaching for a framework.
- **Anthropic 529 overloaded errors are common.** Added retry logic (3 attempts, 5s/10s
  backoff, 45s deadline) in `llm.py`. Without retries the demo looks broken during
  API load spikes.
- **Fiverr is sensitive to explicit review trading.** Frame early-customer outreach
  as a beta test, not a review-for-money exchange.
- **The half-price-to-network move works once.** After the first 5 reviews, charge
  full price or you train your network to expect discounts.
- **Don't promise on-prem deployment in Basic.** That's a Premium-only deliverable
  or scope creep destroys the hours/dollar economics.
- **API key cost is the buyer's responsibility.** Make this explicit in the FAQ so
  there's no surprise — they need their own OpenAI / Anthropic account.
