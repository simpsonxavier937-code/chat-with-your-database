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
    """Send the question + schema to the LLM and return a SQL query string."""
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
