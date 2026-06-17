import argparse
import os

from bolls_common import (
    find_book,
    get_books,
    get_chapter,
    ingest_chapter,
    upsert_translation_and_book,
)
from app.db import get_connection


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest all verses in one chapter from bolls.life into Postgres."
    )
    parser.add_argument("--translation", default=os.getenv("BOLLS_TRANSLATION", "NIV"))
    parser.add_argument("--book", default=os.getenv("BOLLS_BOOK", "John"))
    parser.add_argument("--chapter", type=int, default=int(os.getenv("BOLLS_CHAPTER", "3")))
    parser.add_argument("--base-url", default=os.getenv("BOLLS_BASE_URL", "https://bolls.life"))
    args = parser.parse_args()

    books = get_books(args.base_url, args.translation)
    book_match = find_book(books, args.book)
    if not book_match:
        raise RuntimeError(
            f"Book '{args.book}' not found for translation '{args.translation}'."
        )

    book_num = int(book_match["bookid"])
    chapter_verses = get_chapter(args.base_url, args.translation, book_num, args.chapter)

    conn = get_connection()
    conn.autocommit = True
    cur = conn.cursor()

    upsert_translation_and_book(
        cur,
        args.translation,
        book_num,
        args.book,
        int(book_match["chapters"]),
    )
    inserted = ingest_chapter(
        cur, args.translation, book_num, args.chapter, chapter_verses
    )

    print(
        f"Ingested {inserted} verses: {args.translation} {args.book} {args.chapter}"
    )


if __name__ == "__main__":
    main()
