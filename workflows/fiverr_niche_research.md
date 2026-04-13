# Workflow: Fiverr Niche Research (AI Automation)

## Status
**Reusable, recurring workflow.** Re-run on demand (monthly cadence recommended) to
refresh the market picture and adjust positioning. Each run produces dated output files
in `.tmp/` so you can compare runs over time.

## How to invoke
Tell Claude: *"Run the Fiverr niche research workflow."* Claude should:
1. Check `.tmp/` for the most recent run and note what's changed since
2. Pull current user profile / project state from memory (don't re-ask if known)
3. Execute Phases 1–5 below
4. Produce a fresh `niche_brief_<YYYY-MM-DD>.md`
5. Update the "Edge Cases & Lessons Learned" section with anything new it discovered

## Objective
Identify the most promising sub-niche(s) on Fiverr for an "AI automation / workflow builder"
service offering. Output a ranked shortlist of niches with evidence-backed positioning,
pricing guidance, and a differentiation angle the user can lead with.

## Required Inputs (ask the user before starting)
1. **Background & skills** — What can the user actually deliver today? (tools they know:
   n8n, Make, Zapier, OpenAI API, Claude API, Python, web scraping, etc.)
2. **Time available** — Hours per week for delivery + how fast they can turn around an order.
3. **Starting price comfort** — Are they OK starting at $25 gigs to build reviews, or do they
   want to launch premium ($200+) from day one?
4. **Existing portfolio** — Any past automations, case studies, or screenshots they can show?
5. **Hard nos** — Any niches/industries they refuse to work in (crypto, adult, etc.)?

If the user hasn't provided these yet, **stop and ask** before doing research. Generic
research without these inputs produces generic recommendations.

## Phases

### Phase 1 — Map the AI automation landscape on Fiverr
Use `WebSearch` and `WebFetch` to investigate:
- Fiverr categories that house AI automation work:
  - "AI Services" → "AI Agents", "AI Applications", "Chatbots", "Data Analysis & Reports"
  - "Programming & Tech" → "Automation", "Chatbots", "Web Scraping", "APIs & Integrations"
  - "Business" → "Virtual Assistant" (where AI VAs increasingly compete)
- For each relevant sub-category, capture:
  - Top 5–10 gig titles (verbatim)
  - Price range across Basic / Standard / Premium tiers
  - Number of reviews on top sellers (proxy for demand & seniority)
  - Common deliverables (what's actually being sold)
- Write findings to `.tmp/fiverr_landscape_<YYYY-MM-DD>.md`

**Anti-bot note:** Fiverr is hostile to scraping. Prefer Google search results
(`site:fiverr.com "ai automation"`) and direct WebFetch of public gig URLs. If pages
return JS-only shells or block fetches, fall back to asking the user to paste URLs of
gigs they want analyzed. Do **not** build a heavy scraper for v1 — escalate to building
a tool only if this becomes a recurring bottleneck.

### Phase 2 — Demand signals (where are buyers expressing pain?)
Look for unmet needs and frustration in public buyer-side discussions:
- Reddit: r/Fiverr, r/freelance, r/automation, r/nocode, r/SideProject, r/Entrepreneur,
  r/smallbusiness — search "automate", "AI", "workflow", "Zapier", "n8n", "expensive"
- Reddit is blocked by Claude Code's `WebFetch` (confirmed 2026-04-08 — error: "unable
  to fetch from www.reddit.com"). The JSON endpoint approach does NOT work via WebFetch.
  Workarounds: (a) `site:reddit.com` queries via `WebSearch` — Google indexes Reddit
  thoroughly and returns titles + snippets; (b) a future Python tool using Reddit's
  official API (free, requires app registration) if Reddit data becomes a recurring
  bottleneck.
- Twitter/X via WebSearch for "looking for someone to automate" / "need an AI to"
- Upwork public job listings (parallel market) — what AI automation jobs are getting posted?
- Capture: 10–20 specific buyer pains, each with a source URL and a 1-line summary
- Write to `.tmp/demand_signals_<YYYY-MM-DD>.md`

### Phase 3 — Competitor deep dive
Pick the top 5 sellers in the 2–3 most promising sub-niches from Phase 1. For each:
- Gig title, tagline, profile blurb
- Package structure (Basic/Standard/Premium prices + what's included)
- Delivery time
- Number of reviews + average rating
- Recurring praise in reviews (what they're doing right)
- Recurring complaints (what buyers wish were different)
- Their differentiator / hook
- Write to `.tmp/competitors_<YYYY-MM-DD>.md`

### Phase 4 — Gap analysis
Cross-reference Phase 2 (what buyers want) against Phase 3 (what's being sold):
- Where is demand high but supply weak/expensive/slow?
- Which buyer pains are NO top seller addressing in their gig copy?
- Are there pricing inefficiencies (e.g., everyone charging $500 for something a smart
  AI workflow could deliver in 30 minutes)?
- Any underserved verticals (legal, real estate, e-commerce, healthcare admin)?

### Phase 5 — Ranked recommendations
Produce a final brief with **3–5 niche options**, ranked by opportunity score.
For each option include:
- **Niche name** (specific — "AI lead-qualification chatbots for real estate agents",
  not "chatbots")
- **Why it's promising** (2–3 evidence points with source URLs)
- **Estimated demand level** (low/med/high + why)
- **Competition level** (low/med/high + how saturated)
- **Suggested starter pricing** (Basic/Standard/Premium)
- **Differentiation angle** (what hook makes the user's gig stand out)
- **Quick-win first gig** (the exact gig title + 1-line description to launch with)
- **Risks / unknowns**

Output the brief to `.tmp/niche_brief_<YYYY-MM-DD>.md`. Once the user has reviewed and
chosen a direction, the next workflow (gig launch) takes over.

## Tools Used
- `WebSearch` — discovery
- `WebFetch` — pull public Fiverr/Reddit/Upwork pages
- No Python tools required for v1. Build tools only if a step becomes repetitive or
  unreliable enough to need determinism (e.g., a Reddit batch fetcher, a competitor
  tracking sheet writer). When that happens, add the tool to `tools/` and update this
  workflow.

## Outputs
- `.tmp/fiverr_landscape_<date>.md` — what's being sold
- `.tmp/demand_signals_<date>.md` — what buyers want
- `.tmp/competitors_<date>.md` — who the top players are
- `.tmp/niche_brief_<date>.md` — final ranked recommendations (the deliverable)

When the brief is ready, offer to copy it into a Google Doc or Sheet so it lives in
the user's cloud, per the project convention.

## Edge Cases & Lessons Learned
*(This section grows over time as the workflow runs and we learn what breaks.)*

- **Fiverr blocks scrapers AND WebFetch**: Confirmed 2026-04-08 — direct WebFetch on
  `fiverr.com/gigs/<keyword>` returns HTTP 403. Don't waste cycles retrying. Workarounds:
  (a) Google search snippets surface gig titles/prices in the index — use
  `site:fiverr.com "<keyword>"` searches; (b) ask the user to paste specific gig URLs
  they want analyzed; (c) accept that gross-level competitor counts and pricing tiers
  must come from secondary sources (Medium roundups, Fiverr's own category landing
  pages which sometimes ARE fetchable, blog comparisons).
- **Reddit search is noisy**: Filter results by score > 5 and recency (last 6 months) to
  cut spam.
- **"AI automation" is too broad**: Always force the recommendations down to a specific
  vertical + specific deliverable. Vague niches don't sell.
