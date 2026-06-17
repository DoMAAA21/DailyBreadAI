from dataclasses import dataclass

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


def _search_verses_sync(
    query_vector: list[float],
    *,
    translation: str,
    model: str,
    limit: int,
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
                ORDER BY e.embedding <=> %s::vector
                LIMIT %s
                """,
                (vector_literal, model, translation, vector_literal, limit),
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
) -> list[RetrievedVerse]:
    cleaned = question.strip()
    if not cleaned:
        return []

    query_vector = await embed(cleaned)

    # Run DB query in a thread to keep async handlers responsive.
    import asyncio

    return await asyncio.to_thread(
        _search_verses_sync,
        query_vector,
        translation=translation,
        model=model,
        limit=limit,
    )
