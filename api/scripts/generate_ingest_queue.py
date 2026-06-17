import argparse
import os
from pathlib import Path

from bolls_common import build_chapter_jobs, get_books, save_catalog, save_queue


def default_output_path(translation: str, book: str | None) -> Path:
    root = Path(__file__).resolve().parents[1] / "data" / "queues"
    root.mkdir(parents=True, exist_ok=True)
    if book:
        slug = book.lower().replace(" ", "-")
        return root / f"{translation.lower()}-{slug}.json"
    return root / f"{translation.lower()}-all.json"


def default_catalog_path(translation: str) -> Path:
    root = Path(__file__).resolve().parents[1] / "data" / "catalog"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{translation.lower()}.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a chapter-by-chapter ingest queue from bolls.life get-books."
    )
    parser.add_argument("--translation", default=os.getenv("BOLLS_TRANSLATION", "NIV"))
    parser.add_argument("--book", default=None, help="Optional single book, e.g. John")
    parser.add_argument("--base-url", default=os.getenv("BOLLS_BASE_URL", "https://bolls.life"))
    parser.add_argument(
        "--output",
        default=None,
        help="Queue JSON output path (default: api/data/queues/<translation>.json)",
    )
    parser.add_argument(
        "--catalog",
        default=None,
        help="Also save book/chapter catalog JSON (default: api/data/catalog/<translation>.json)",
    )
    args = parser.parse_args()

    books = get_books(args.base_url, args.translation)
    jobs = build_chapter_jobs(args.translation, books, book_filter=args.book)

    queue_path = Path(args.output) if args.output else default_output_path(
        args.translation, args.book
    )
    catalog_path = Path(args.catalog) if args.catalog else default_catalog_path(
        args.translation
    )

    save_queue(str(queue_path), args.translation, args.base_url, jobs)
    save_catalog(str(catalog_path), args.translation, args.base_url, books)

    scope = args.book or "all books"
    print(f"Catalog saved: {catalog_path} ({len(books)} books)")
    print(f"Queue saved:   {queue_path} ({len(jobs)} chapter jobs for {scope})")
    print("Next: run the queue with run_ingest_queue.py")


if __name__ == "__main__":
    main()
