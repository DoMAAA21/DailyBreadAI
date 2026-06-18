import json
from dataclasses import dataclass

import httpx

from app.config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL
from app.db import get_connection

_book_names_cache: list[str] | None = None


@dataclass
class RetrievalPlan:
    use_rag: bool
    search_query: str
    book: str | None
    verse_limit: int


def _load_book_names() -> list[str]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM books ORDER BY name ASC")
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def get_book_names() -> list[str]:
    global _book_names_cache
    if _book_names_cache is None:
        _book_names_cache = _load_book_names()
    return _book_names_cache


def _normalize_book(name: str | None) -> str | None:
    if not name:
        return None
    catalog = {book.lower(): book for book in get_book_names()}
    return catalog.get(name.strip().lower())


def _build_planner_prompt() -> str:
    books = ", ".join(get_book_names())
    return f"""You plan retrieval for a Bible chat app. Respond with ONLY valid JSON.

Decide how to search Scripture for the user's message.

JSON fields:
- use_rag (boolean): false for greetings or casual chat; true when Scripture search is needed
- search_query (string): short keyword query for semantic verse search when use_rag is true; otherwise ""
- book (string|null): limit search to one book when the question focuses on a specific book; must be from the catalog or null
- verse_limit (number): 5 for topical questions, 8 for book-wide questions

Book catalog: {books}

Examples:
User: Hiii, how are you?
{{"use_rag":false,"search_query":"","book":null,"verse_limit":5}}

User: What does the Bible say about peace?
{{"use_rag":true,"search_query":"peace comfort rest anxiety fear trust God stillness","book":null,"verse_limit":5}}

User: What is Matthew all about?
{{"use_rag":true,"search_query":"gospel Jesus Messiah kingdom of heaven genealogy disciples teachings parables Sermon on the Mount","book":"Matthew","verse_limit":8}}"""


def _parse_plan(raw: str, fallback_question: str) -> RetrievalPlan:
    try:
        data = json.loads(raw)
        use_rag = bool(data.get("use_rag", True))
        search_query = str(data.get("search_query", "")).strip()
        book = _normalize_book(data.get("book"))
        verse_limit = int(data.get("verse_limit", 5))
        verse_limit = max(1, min(verse_limit, 10))

        if use_rag and not search_query:
            search_query = fallback_question

        return RetrievalPlan(
            use_rag=use_rag,
            search_query=search_query,
            book=book,
            verse_limit=verse_limit,
        )
    except (json.JSONDecodeError, TypeError, ValueError):
        return RetrievalPlan(
            use_rag=True,
            search_query=fallback_question,
            book=None,
            verse_limit=5,
        )


async def plan_retrieval(question: str) -> RetrievalPlan:
    messages = [
        {"role": "system", "content": _build_planner_prompt()},
        {"role": "user", "content": question.strip()},
    ]

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_CHAT_MODEL,
                "messages": messages,
                "stream": False,
                "format": "json",
            },
        )
        response.raise_for_status()
        raw = response.json()["message"]["content"]

    return _parse_plan(raw, question.strip())
