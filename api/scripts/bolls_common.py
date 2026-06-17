import json
import re
from datetime import datetime, timezone
from typing import Any, Optional

import _path  # noqa: F401
import httpx
import psycopg2


def strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s or "")
    return re.sub(r"\s+", " ", s).strip()


def get_books(base_url: str, translation: str) -> list[dict]:
    url = f"{base_url.rstrip('/')}/get-books/{translation}/"
    response = httpx.get(url, timeout=60)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ["books", "data", "results"]:
            if key in data and isinstance(data[key], list):
                return data[key]
    raise RuntimeError(f"Unrecognized get-books response shape: {type(data)}")


def get_chapter(
    base_url: str, translation: str, book_num: int, chapter: int
) -> list[dict]:
    url = f"{base_url.rstrip('/')}/get-text/{translation}/{book_num}/{chapter}/"
    response = httpx.get(url, timeout=120)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise RuntimeError(f"Expected a list of verses, got {type(data)}")
    return data


def infer_testament(book_num: int) -> str:
    return "OT" if book_num <= 39 else "NT"


def find_book(books: list[dict], book_name: str) -> Optional[dict]:
    target = book_name.strip().lower()
    return next(
        (b for b in books if (b.get("name") or "").strip().lower() == target),
        None,
    )


def build_chapter_jobs(
    translation: str,
    books: list[dict],
    book_filter: Optional[str] = None,
) -> list[dict]:
    selected = books
    if book_filter:
        match = find_book(books, book_filter)
        if not match:
            raise RuntimeError(f"Book '{book_filter}' not found for {translation}.")
        selected = [match]

    jobs: list[dict] = []
    for book in selected:
        book_num = int(book["bookid"])
        book_name = (book.get("name") or "").strip()
        chapter_count = int(book["chapters"])
        for chapter in range(1, chapter_count + 1):
            jobs.append(
                {
                    "id": f"{translation}-{book_num}-{chapter}",
                    "translation": translation,
                    "book_num": book_num,
                    "book_name": book_name,
                    "chapter": chapter,
                    "status": "pending",
                    "verses_ingested": None,
                    "error": None,
                    "updated_at": None,
                }
            )
    return jobs


def save_catalog(path: str, translation: str, base_url: str, books: list[dict]) -> None:
    payload = {
        "translation": translation,
        "base_url": base_url,
        "book_count": len(books),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "books": [
            {
                "book_num": int(b["bookid"]),
                "name": b.get("name"),
                "chapters": int(b["chapters"]),
                "chronorder": b.get("chronorder"),
                "testament": infer_testament(int(b["bookid"])),
            }
            for b in books
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def save_queue(path: str, translation: str, base_url: str, jobs: list[dict]) -> None:
    payload = {
        "translation": translation,
        "base_url": base_url,
        "job_count": len(jobs),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "jobs": jobs,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def load_queue(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_queue(path: str, payload: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def upsert_translation_and_book(
    cur: psycopg2.extensions.cursor,
    translation: str,
    book_num: int,
    book_name: str,
    chapter_count: int,
) -> None:
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
        (book_num, book_name, infer_testament(book_num), chapter_count),
    )


def ingest_chapter(
    cur: psycopg2.extensions.cursor,
    translation: str,
    book_num: int,
    chapter: int,
    chapter_verses: list[dict],
) -> int:
    inserted = 0
    for verse_obj in chapter_verses:
        verse_num = int(verse_obj["verse"])
        verse_text = strip_html(verse_obj.get("text", ""))
        if not verse_text:
            continue

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
                chapter,
                verse_num,
                verse_text,
                json.dumps(verse_obj),
            ),
        )
        inserted += 1
    return inserted
