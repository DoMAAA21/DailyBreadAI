import argparse
import json
import os
import re
from typing import Any, Optional, Tuple

import _path  # noqa: F401
import httpx
import psycopg2
import psycopg2.extras

from app.db import get_connection


def strip_html(s: str) -> str:
    # Bolls returns HTML inside `text`; for embedding we want plain text.
    s = re.sub(r"<[^>]+>", "", s or "")
    return s.strip()


def find_first_text(payload: Any) -> Optional[dict]:
    """
    Try to locate the first verse-like object containing `text`.
    Bolls responses vary a bit; this heuristic keeps the script resilient.
    """

    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict) and "text" in item:
                return item
        for item in payload:
            found = find_first_text(item)
            if found:
                return found

    if isinstance(payload, dict):
        if "text" in payload:
            return payload
        for v in payload.values():
            found = find_first_text(v)
            if found:
                return found

    return None


def get_books(base_url: str, translation: str) -> list[dict]:
    url = f"{base_url}/get-books/{translation}/"
    r = httpx.get(url, timeout=60)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict):
        # common keys
        for key in ["books", "data", "results"]:
            if key in data and isinstance(data[key], list):
                return data[key]
    if isinstance(data, list):
        return data
    raise RuntimeError(f"Unrecognized get-books response shape: {type(data)}")


def get_verse(
    base_url: str, translation: str, book_num: int, chapter: int, verse: int
) -> Tuple[str, Any]:
    url = f"{base_url}/get-verses/"
    body = [
        {
            "translation": translation,
            "book": book_num,
            "chapter": chapter,
            "verses": [verse],
        }
    ]
    r = httpx.post(url, json=body, timeout=120)
    r.raise_for_status()
    payload = r.json()
    verse_obj = find_first_text(payload)
    if not verse_obj or "text" not in verse_obj:
        raise RuntimeError(f"Could not find verse text in response: {type(payload)}")
    return strip_html(verse_obj["text"]), verse_obj


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--translation", default=os.getenv("BOLLS_TRANSLATION", "NIV"))
    parser.add_argument("--book", default=os.getenv("BOLLS_BOOK", "John"))
    parser.add_argument("--chapter", type=int, default=int(os.getenv("BOLLS_CHAPTER", "3")))
    parser.add_argument("--verse", type=int, default=int(os.getenv("BOLLS_VERSE", "16")))
    parser.add_argument("--base-url", default=os.getenv("BOLLS_BASE_URL", "https://bolls.life"))
    args = parser.parse_args()

    conn = get_connection()
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    translation = args.translation
    book_name = args.book

    books = get_books(args.base_url, translation)
    book_match = None
    for b in books:
        name = (b.get("name") or "").strip()
        if name.lower() == book_name.lower():
            book_match = b
            break

    if not book_match:
        raise RuntimeError(
            f"Book '{book_name}' not found in get-books for translation '{translation}'. "
            f"Try a different --book value that matches Bolls' spelling."
        )

    book_num = int(book_match["bookid"])
    chapters = book_match.get("chapters")

    # Upsert translation + book
    cur.execute(
        """
        INSERT INTO translations (code, name, language)
        VALUES (%s, %s, %s)
        ON CONFLICT (code) DO UPDATE
        SET name = EXCLUDED.name,
            language = EXCLUDED.language
        """,
        (translation, translation, "en"),
    )

    cur.execute(
        """
        INSERT INTO books (book_num, name, testament, chapters)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (book_num) DO UPDATE
        SET name = EXCLUDED.name,
            testament = EXCLUDED.testament,
            chapters = EXCLUDED.chapters
        """,
        (book_num, book_name, None, chapters),
    )

    verse_text, verse_obj = get_verse(
        args.base_url, translation, book_num, args.chapter, args.verse
    )

    cur.execute(
        """
        INSERT INTO verses (translation_code, book_num, chapter, verse, text, raw)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (translation_code, book_num, chapter, verse) DO UPDATE
        SET text = EXCLUDED.text,
            raw = EXCLUDED.raw
        """,
        (
            translation,
            book_num,
            args.chapter,
            args.verse,
            verse_text,
            json.dumps(verse_obj),
        ),
    )

    print(
        f"Inserted: {translation} {book_name} {args.chapter}:{args.verse}\n"
        f"Text (plain): {verse_text}"
    )


if __name__ == "__main__":
    main()

