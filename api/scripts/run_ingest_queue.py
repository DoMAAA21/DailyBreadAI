import argparse
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import psycopg2

from bolls_common import (
    get_books,
    get_chapter,
    ingest_chapter,
    load_queue,
    upsert_translation_and_book,
    write_queue,
)


def chapter_count_for_book(books: list[dict], book_num: int) -> int:
    for book in books:
        if int(book["bookid"]) == book_num:
            return int(book["chapters"])
    raise RuntimeError(f"Book number {book_num} not found in catalog.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Process a chapter ingest queue (resume-friendly)."
    )
    parser.add_argument(
        "--queue",
        required=True,
        help="Path to queue JSON, e.g. api/data/queues/niv-john.json",
    )
    parser.add_argument(
        "--status",
        default="pending",
        help="Only process jobs with this status (default: pending)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process at most N jobs this run",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.25,
        help="Seconds to wait between chapter API calls",
    )
    args = parser.parse_args()

    queue_path = Path(args.queue)
    payload = load_queue(str(queue_path))
    translation = payload["translation"]
    base_url = payload.get("base_url", "https://bolls.life")
    jobs = payload["jobs"]

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/dailybread",
    )

    books = get_books(base_url, translation)
    book_chapter_counts = {int(b["bookid"]): int(b["chapters"]) for b in books}

    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cur = conn.cursor()

    processed = 0
    for job in jobs:
        if job.get("status") != args.status:
            continue
        if args.limit is not None and processed >= args.limit:
            break

        book_num = int(job["book_num"])
        book_name = job["book_name"]
        chapter = int(job["chapter"])
        chapter_count = book_chapter_counts.get(book_num)
        if chapter_count is None:
            chapter_count = chapter_count_for_book(books, book_num)

        job_id = job["id"]
        print(f"Processing {job_id} ({book_name} {chapter})...")

        try:
            upsert_translation_and_book(
                cur, translation, book_num, book_name, chapter_count
            )
            chapter_verses = get_chapter(base_url, translation, book_num, chapter)
            verses_ingested = ingest_chapter(
                cur, translation, book_num, chapter, chapter_verses
            )

            job["status"] = "done"
            job["verses_ingested"] = verses_ingested
            job["error"] = None
            job["updated_at"] = datetime.now(timezone.utc).isoformat()
            print(f"  done ({verses_ingested} verses)")
        except Exception as exc:  # noqa: BLE001 - keep queue runner resilient
            job["status"] = "failed"
            job["error"] = str(exc)
            job["updated_at"] = datetime.now(timezone.utc).isoformat()
            print(f"  failed: {exc}")

        write_queue(str(queue_path), payload)
        processed += 1

        if args.sleep > 0:
            time.sleep(args.sleep)

    remaining = sum(1 for job in jobs if job.get("status") == "pending")
    done = sum(1 for job in jobs if job.get("status") == "done")
    failed = sum(1 for job in jobs if job.get("status") == "failed")

    print(
        f"Run complete. processed={processed} done={done} failed={failed} pending={remaining}"
    )


if __name__ == "__main__":
    main()
