import argparse
import os
from typing import Optional

import _path  # noqa: F401
import httpx
import psycopg2

from app.db import get_connection


def to_vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{float(v):.8f}" for v in values) + "]"


def embed_text(client: httpx.Client, base_url: str, model: str, text: str) -> list[float]:
    response = client.post(
        f"{base_url.rstrip('/')}/api/embeddings",
        json={"model": model, "prompt": text},
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    embedding = payload.get("embedding")
    if not isinstance(embedding, list):
        raise RuntimeError(f"Unexpected embeddings response: {payload}")
    return embedding


def select_pending_verses(
    cur: psycopg2.extensions.cursor,
    translation: str,
    model: str,
    batch_size: int,
    book: Optional[str],
) -> list[tuple[int, str, str, int, int]]:
    cur.execute(
        """
        SELECT v.id, v.text, b.name, v.chapter, v.verse
        FROM verses v
        JOIN books b ON b.book_num = v.book_num
        LEFT JOIN verse_embeddings e
          ON e.verse_id = v.id AND e.model = %s
        WHERE v.translation_code = %s
          AND (%s IS NULL OR b.name = %s)
          AND e.verse_id IS NULL
        ORDER BY v.id
        LIMIT %s
        """,
        (model, translation, book, book, batch_size),
    )
    return cur.fetchall()


def upsert_embedding(
    cur: psycopg2.extensions.cursor,
    verse_id: int,
    model: str,
    embedding: list[float],
) -> None:
    cur.execute(
        """
        INSERT INTO verse_embeddings (verse_id, model, embedding)
        VALUES (%s, %s, %s::vector)
        ON CONFLICT (verse_id, model) DO UPDATE
        SET embedding = EXCLUDED.embedding
        """,
        (verse_id, model, to_vector_literal(embedding)),
    )


def count_pending(
    cur: psycopg2.extensions.cursor, translation: str, model: str, book: Optional[str]
) -> int:
    cur.execute(
        """
        SELECT COUNT(*)
        FROM verses v
        JOIN books b ON b.book_num = v.book_num
        LEFT JOIN verse_embeddings e
          ON e.verse_id = v.id AND e.model = %s
        WHERE v.translation_code = %s
          AND (%s IS NULL OR b.name = %s)
          AND e.verse_id IS NULL
        """,
        (model, translation, book, book),
    )
    return int(cur.fetchone()[0])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create Ollama embeddings for verses and store them in pgvector."
    )
    parser.add_argument("--translation", default=os.getenv("BOLLS_TRANSLATION", "NIV"))
    parser.add_argument("--book", default=os.getenv("BOLLS_BOOK"), help="Optional, e.g. John")
    parser.add_argument(
        "--model", default=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    )
    parser.add_argument(
        "--ollama-base-url",
        default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    conn = get_connection()
    conn.autocommit = True
    cur = conn.cursor()

    pending_before = count_pending(cur, args.translation, args.model, args.book)
    scope = f"{args.translation} {args.book}" if args.book else args.translation
    print(f"Embedding scope: {scope}")
    print(f"Model: {args.model}")
    print(f"Pending verses before run: {pending_before}")

    processed = 0
    with httpx.Client() as client:
        while True:
            if args.limit is not None and processed >= args.limit:
                break

            current_batch_size = args.batch_size
            if args.limit is not None:
                current_batch_size = min(current_batch_size, args.limit - processed)
                if current_batch_size <= 0:
                    break

            rows = select_pending_verses(
                cur=cur,
                translation=args.translation,
                model=args.model,
                batch_size=current_batch_size,
                book=args.book,
            )
            if not rows:
                break

            for verse_id, text, book_name, chapter, verse in rows:
                embedding = embed_text(
                    client=client,
                    base_url=args.ollama_base_url,
                    model=args.model,
                    text=text,
                )
                upsert_embedding(cur, verse_id, args.model, embedding)
                processed += 1
                print(
                    f"[{processed}] embedded {book_name} {chapter}:{verse} "
                    f"(dim={len(embedding)})"
                )

    pending_after = count_pending(cur, args.translation, args.model, args.book)
    print(f"Done. Embedded this run: {processed}")
    print(f"Pending verses after run: {pending_after}")


if __name__ == "__main__":
    main()
