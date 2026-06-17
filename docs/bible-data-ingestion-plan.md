# Bible Data Ingestion Plan — DailyBreadAI

## What we understood

This is **not** web scraping. We are not parsing HTML pages or depending on website layouts.

We are **bulk-loading structured Bible data** from sources that already expose machine-readable formats:

| Source type | Examples | How we get data |
|-------------|----------|-----------------|
| **JSON APIs** | Bolls.life, GetBible | Request `book + chapter + verse + translation` → receive clean JSON |
| **Structured file dumps** | OSHB (Hebrew), OpenGNT (Greek) on GitHub | Download XML/JSON → parse known schema → load into Postgres |
| **Custom import (exception)** | NKRV (Korean) | One-off script (`fetch_nkrv.py`) from a MySQL dump shared by a community site |

The main ingestion script (`data_ingestion.py`) loops through every **book → chapter → verse** for each supported **translation**, calls the API, and writes rows into Postgres.

Original-language texts are a **separate pipeline** — same end goal (rows in DB), different input format (repo files instead of live API calls).

---

## Goal for DailyBreadAI

Populate PostgreSQL so the RAG pipeline can:

1. **Store** verses with metadata (book, chapter, verse, translation, text)
2. **Embed** verse text (or chunks) into pgvector
3. **Retrieve** relevant passages when a user asks a question
4. **Return** answers with citations (e.g. John 14:27 NIV)

---

## Data sources (planned)

### Translations via API (primary path)

Loop all combinations for ~9 translations, e.g.:

- NIV, ESV, KJV, etc. (confirm exact list with Bolls.life / GetBible docs)

**Flow per verse:**

```
GET /api/...?book=John&chapter=3&verse=16&translation=NIV
→ { "book": "John", "chapter": 3, "verse": 16, "text": "..." }
→ INSERT INTO verses
```

**Notes:**

- Respect rate limits (sleep / retry / batch where supported)
- Make ingestion **idempotent** (`UPSERT` on `translation + book + chapter + verse`)
- Log failures and resume from last checkpoint

### Original languages (secondary path)

| Language | Source | Format |
|----------|--------|--------|
| Hebrew | OSHB (Open Scriptures Hebrew Bible) | Structured XML/JSON from GitHub |
| Greek | OpenGNT | Structured files from GitHub |
| Aramaic | TBD (if needed for OT portions) | Same pattern as above |

Download once → parse → map to same `verses` schema (or a linked `original_text` table).

### NKRV — exception

- Not a clean public API
- Use dedicated `fetch_nkrv.py` to transform MySQL dump → Postgres-compatible rows
- Treat as **Phase 2** after the main API pipeline works

---

## Database schema (first draft)

```sql
-- Core verse storage
CREATE TABLE translations (
  id          SERIAL PRIMARY KEY,
  code        TEXT UNIQUE NOT NULL,   -- e.g. 'NIV', 'ESV', 'NKRV'
  name        TEXT NOT NULL,
  language    TEXT NOT NULL           -- e.g. 'en', 'ko'
);

CREATE TABLE books (
  id          SERIAL PRIMARY KEY,
  name        TEXT NOT NULL,          -- e.g. 'John'
  testament   TEXT NOT NULL,          -- 'OT' | 'NT'
  order_index INT NOT NULL
);

CREATE TABLE verses (
  id              BIGSERIAL PRIMARY KEY,
  translation_id  INT REFERENCES translations(id),
  book_id         INT REFERENCES books(id),
  chapter         INT NOT NULL,
  verse           INT NOT NULL,
  text            TEXT NOT NULL,
  UNIQUE (translation_id, book_id, chapter, verse)
);

-- RAG / vector search (pgvector)
CREATE TABLE verse_embeddings (
  id          BIGSERIAL PRIMARY KEY,
  verse_id    BIGINT REFERENCES verses(id) ON DELETE CASCADE,
  embedding   vector(1536),           -- dimension depends on embedding model
  model       TEXT NOT NULL,
  UNIQUE (verse_id, model)
);
```

**Chunking decision (for RAG):**

- **Option A — verse-level:** one embedding per verse (simplest, best for citation)
- **Option B — passage-level:** group consecutive verses into chunks (better for context-heavy questions)

**Recommendation:** start with **verse-level** embeddings; add passage chunking later if retrieval quality needs it.

---

## Ingestion pipeline architecture

```
api/scripts/
├── data_ingestion.py      # Main loop: APIs → Postgres (9 translations)
├── fetch_original.py      # OSHB + OpenGNT → Postgres
├── fetch_nkrv.py          # Korean exception (later)
├── embed_verses.py        # Read verses → OpenAI embeddings → pgvector
└── utils/
    ├── books.py           # Canonical book list + chapter counts
    ├── api_clients.py     # Bolls.life / GetBible wrappers
    └── db.py              # SQLAlchemy session + upsert helpers
```

### Phase 1 — Foundation

- [ ] Enable `pgvector` extension in Postgres
- [ ] SQLAlchemy models matching schema above
- [ ] Alembic migrations (or manual SQL for v1)
- [ ] `books.py` — canonical 66-book list with chapter/verse counts

### Phase 2 — API ingestion

- [ ] `api_clients.py` — thin wrappers for Bolls.life and/or GetBible
- [ ] `data_ingestion.py` — nested loop with progress logging
- [ ] Idempotent upserts + resume support
- [ ] Dry-run mode (fetch 1 book, verify, then full run)

### Phase 3 — Original languages

- [ ] Download OSHB / OpenGNT repos (or pin release versions)
- [ ] Parsers for each file format
- [ ] Link original text to translation verses where possible

### Phase 4 — Embeddings

- [ ] `embed_verses.py` — batch embed with **Ollama** (`nomic-embed-text`) — local, no API key
- [ ] Store in `verse_embeddings`
- [ ] Index: `CREATE INDEX ON verse_embeddings USING ivfflat (embedding vector_cosine_ops)`

> See `docs/local-rag-learning-plan.md` for the full local RAG path (Ollama + pgvector, no OpenAI).

### Phase 5 — NKRV (optional / later)

- [ ] `fetch_nkrv.py` — custom MySQL dump → Postgres transform
- [ ] Validate against same schema as other translations

---

## How this connects to the RAG app

```
Ingestion (offline, run once / on schedule)
  data_ingestion.py  →  verses table
  embed_verses.py    →  verse_embeddings table

Runtime (FastAPI)
  User question
    → embed query
    → pgvector similarity search
    → top-k verses as context
    → LLM answer + citations
    → Next.js chat UI
```

---

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| API rate limits / downtime | Retries, backoff, checkpoint resume |
| Translation API differences | Abstract behind `api_clients.py`; one client per provider |
| Copyright / licensing | Confirm each translation's terms before shipping publicly |
| NKRV one-off complexity | Isolate in `fetch_nkrv.py`; don't block main pipeline |
| Embedding cost | Use local Ollama embeddings — free, no API billing |

---

## What we are NOT doing

- Scraping Bible websites HTML
- Depending on CSS selectors or page structure
- Building ingestion around undocumented endpoints

---

## Suggested first milestone

**Get NIV only into Postgres with embeddings, then wire chat to real retrieval.**

1. Ingest John (all chapters) in NIV via API
2. Embed those verses
3. FastAPI `/chat` endpoint: query → retrieve → generate
4. Frontend calls real API instead of mock data

Once that works, scale to all 66 books × 9 translations.

---

## Open questions

- [ ] Final list of 9 translations and which API serves each
- [ ] Verse-level vs passage-level chunking for v1
- [ ] Docker Postgres + pgvector for local dev (recommended)
- [ ] Whether NKRV is required for v1 or can wait
