from dataclasses import dataclass
import random

import psycopg2

from app.config import OLLAMA_EMBED_MODEL
from app.db import get_connection
from app.services.ollama import embed


@dataclass
class RetrievedVerse:
    verse_id: int
    text: str
    book_name: str
    chapter: int
    verse: int
    translation_code: str
    score: float

    @property
    def reference(self) -> str:
        return f"{self.book_name} {self.chapter}:{self.verse} ({self.translation_code})"


def _to_vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{float(v):.8f}" for v in values) + "]"


def diversify_verses(candidates: list[RetrievedVerse], limit: int) -> list[RetrievedVerse]:
    """Pick relevant verses from different chapters, with light randomness among top matches."""
    if not candidates:
        return []

    best_per_chapter: dict[tuple[str, int], RetrievedVerse] = {}
    for verse in candidates:
        key = (verse.book_name, verse.chapter)
        current = best_per_chapter.get(key)
        if current is None or verse.score > current.score:
            best_per_chapter[key] = verse

    pool = sorted(best_per_chapter.values(), key=lambda v: v.score, reverse=True)
    top_score = pool[0].score
    close_matches = [v for v in pool if v.score >= top_score - 0.08]
    remaining = [v for v in pool if v.score < top_score - 0.08]

    random.shuffle(close_matches)
    ordered = close_matches + remaining
    return ordered[:limit]


def _search_verses_sync(
    query_vector: list[float],
    *,
    translation: str,
    model: str,
    limit: int,
    book_name: str | None = None,
) -> list[RetrievedVerse]:
    vector_literal = _to_vector_literal(query_vector)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    v.id,
                    v.text,
                    b.name,
                    v.chapter,
                    v.verse,
                    v.translation_code,
                    1 - (e.embedding <=> %s::vector) AS score
                FROM verse_embeddings e
                JOIN verses v ON v.id = e.verse_id
                JOIN books b ON b.book_num = v.book_num
                WHERE e.model = %s
                  AND v.translation_code = %s
                  AND (%s IS NULL OR b.name = %s)
                ORDER BY e.embedding <=> %s::vector
                LIMIT %s
                """,
                (
                    vector_literal,
                    model,
                    translation,
                    book_name,
                    book_name,
                    vector_literal,
                    limit,
                ),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [
        RetrievedVerse(
            verse_id=row[0],
            text=row[1],
            book_name=row[2],
            chapter=row[3],
            verse=row[4],
            translation_code=row[5],
            score=float(row[6]),
        )
        for row in rows
    ]


async def search_verses(
    question: str,
    *,
    translation: str = "NIV",
    model: str = OLLAMA_EMBED_MODEL,
    limit: int = 5,
    book_name: str | None = None,
    diversify: bool = True,
) -> list[RetrievedVerse]:
    cleaned = question.strip()
    if not cleaned:
        return []

    query_vector = await embed(cleaned)
    candidate_limit = max(limit * 5, 25) if diversify else limit

    # Run DB query in a thread to keep async handlers responsive.
    import asyncio

    candidates = await asyncio.to_thread(
        _search_verses_sync,
        query_vector,
        translation=translation,
        model=model,
        limit=candidate_limit,
        book_name=book_name,
    )

    if diversify:
        return diversify_verses(candidates, limit)
    return candidates[:limit]
