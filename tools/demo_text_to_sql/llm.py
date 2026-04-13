"""
LLM helpers for the Text-to-SQL demo.
Generates SQL from natural language using Anthropic Claude or OpenAI GPT.
"""

import time

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
    """Send the question + schema to the LLM and return a SQL query string."""
    if not anthropic_key and not openai_key:
        raise ValueError(
            "No API key configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."
        )

    system = SYSTEM_PROMPT.format(schema=schema)

    if anthropic_key:
        call = lambda: _call_anthropic(system, question, anthropic_key)
    else:
        call = lambda: _call_openai(system, question, openai_key)

    raw = _retry(call, max_attempts=3, deadline=45)
    return _strip_fences(raw)


def _is_retryable(exc: Exception) -> bool:
    """Check if an exception is a transient error worth retrying."""
    msg = str(exc).lower()
    if "overloaded" in msg or "529" in msg or "503" in msg:
        return True
    if "rate" in msg and "limit" in msg:
        return True
    if "timeout" in msg or "timed out" in msg:
        return True
    return False


def _retry(call, max_attempts: int = 3, deadline: float = 30):
    """Retry a callable up to max_attempts times within deadline seconds."""
    start = time.monotonic()
    last_exc = None
    delays = [5, 10]  # backoff between retries

    for attempt in range(max_attempts):
        try:
            return call()
        except Exception as e:
            last_exc = e
            if not _is_retryable(e) or attempt == max_attempts - 1:
                raise
            elapsed = time.monotonic() - start
            wait = delays[attempt] if attempt < len(delays) else 5
            if elapsed + wait > deadline:
                raise
            time.sleep(wait)

    raise last_exc


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
