# DailyBreadAI — Scripts & Commands Reference

Quick reference for all project scripts, Docker commands, and database utilities.

Run commands from the project root unless noted:

```bash
cd /Users/jharold/Projects/DailyBreadAI
```

---

## Docker — stack & services

| Command | What it does |
|---------|----------------|
| `docker compose up --build` | Build and start all services (foreground) |
| `docker compose up --build -d` | Build and start all services (background) |
| `docker compose up -d db` | Start Postgres only |
| `docker compose up -d db api` | Start Postgres + API |
| `docker compose up -d adminer` | Start Adminer database UI |
| `docker compose ps` | List running containers |
| `docker compose logs -f` | Follow logs for all services |
| `docker compose logs -f api` | Follow API logs only |
| `docker compose stop` | Stop containers |
| `docker compose down` | Stop and remove containers |
| `docker compose down -v` | Stop and **delete all data** (DB, Ollama models, volumes) |

### Service URLs

| Service | URL |
|---------|-----|
| Client | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |
| Adminer | http://localhost:8080 |
| Ollama | http://localhost:11434 |
| Postgres | `localhost:5432` |

---

## Ollama — models & testing

| Command | What it does |
|---------|----------------|
| `docker exec dailybread-ollama ollama pull llama3.2` | Download chat model (~2 GB) |
| `docker exec dailybread-ollama ollama pull nomic-embed-text` | Download embedding model (~275 MB) |
| `docker exec dailybread-ollama ollama pull llama3.2:1b` | Smaller chat model (~1 GB) |
| `docker exec dailybread-ollama ollama list` | List installed models |
| `curl http://localhost:11434` | Check Ollama is running |
| `docker exec -it dailybread-ollama ollama run llama3.2 "Hello"` | Interactive chat test |

### Test chat via API

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [{ "role": "user", "content": "Say hello in one sentence." }],
  "stream": false
}'
```

### Test embeddings via API

```bash
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "What does the Bible say about peace?"
}'
```

---

## Database — setup & inspection

| Command | What it does |
|---------|----------------|
| `docker exec -i dailybread-db psql -U postgres -d dailybread < docker/schema.sql` | Apply DB schema (tables + pgvector) |
| `docker exec -it dailybread-db psql -U postgres -d dailybread` | Open Postgres shell |
| `docker exec -it dailybread-db psql -U postgres -d dailybread -c "SELECT count(*) FROM verses;"` | Count ingested verses |
| `docker exec -it dailybread-db psql -U postgres -d dailybread -c "\dx"` | List extensions (check `vector`) |

### Adminer login

Open http://localhost:8080

| Field | Value |
|-------|-------|
| System | PostgreSQL |
| Server | `db` |
| Username | `postgres` |
| Password | `postgres` |
| Database | `dailybread` |

### SQL files

| File | Function |
|------|----------|
| `docker/init-db.sql` | Runs automatically on first DB boot — enables pgvector + creates tables |
| `docker/schema.sql` | Same tables as init — run manually on existing DB volumes |

---

## API scripts — Bible ingestion

All scripts live in `api/scripts/`. Run from Docker:

```bash
docker exec -it dailybread-api python /app/scripts/<script>.py [options]
```

Or from inside the API container (`docker exec -it dailybread-api bash`):

```bash
python /app/scripts/<script>.py [options]
```

### Script overview

| Script | Function |
|--------|----------|
| `bolls_common.py` | **Shared library** — Bolls API helpers, HTML stripping, DB upsert logic (not run directly) |
| `ingest_bolls_one.py` | Ingest **one verse** (good for first test) |
| `ingest_bolls_chapter.py` | Ingest **one full chapter** (all verses in that chapter) |
| `generate_ingest_queue.py` | Build **catalog + chapter queue** from Bolls `get-books` API |
| `run_ingest_queue.py` | **Process the queue** chapter-by-chapter (resume-friendly) |

---

### `ingest_bolls_one.py`

Ingest a single verse into Postgres.

```bash
docker exec -it dailybread-api python /app/scripts/ingest_bolls_one.py \
  --translation NIV \
  --book John \
  --chapter 3 \
  --verse 16
```

| Flag | Default | Description |
|------|---------|-------------|
| `--translation` | `NIV` | Translation code (Bolls slug) |
| `--book` | `John` | Book name (must match Bolls spelling) |
| `--chapter` | `3` | Chapter number |
| `--verse` | `16` | Verse number |
| `--base-url` | `https://bolls.life` | Bolls API base URL |

---

### `ingest_bolls_chapter.py`

Ingest all verses in one chapter (e.g. John 3 = 36 verses).

```bash
docker exec -it dailybread-api python /app/scripts/ingest_bolls_chapter.py \
  --translation NIV \
  --book John \
  --chapter 3
```

| Flag | Default | Description |
|------|---------|-------------|
| `--translation` | `NIV` | Translation code |
| `--book` | `John` | Book name |
| `--chapter` | `3` | Chapter number |
| `--base-url` | `https://bolls.life` | Bolls API base URL |

---

### `generate_ingest_queue.py`

Fetch the book list from Bolls and create a chapter-by-chapter job queue.

**One book (John = 21 chapter jobs):**

```bash
docker exec -it dailybread-api python /app/scripts/generate_ingest_queue.py \
  --translation NIV \
  --book John
```

**Entire Bible (NIV = 1,189 chapter jobs):**

```bash
docker exec -it dailybread-api python /app/scripts/generate_ingest_queue.py \
  --translation NIV
```

| Flag | Default | Description |
|------|---------|-------------|
| `--translation` | `NIV` | Translation code |
| `--book` | *(none)* | Optional — limit queue to one book |
| `--base-url` | `https://bolls.life` | Bolls API base URL |
| `--output` | auto | Queue JSON path |
| `--catalog` | auto | Catalog JSON path |

**Output files:**

| File | Contents |
|------|----------|
| `api/data/catalog/niv.json` | All 66 books + chapter counts |
| `api/data/queues/niv-john.json` | Chapter jobs for John (`pending` / `done` / `failed`) |
| `api/data/queues/niv-all.json` | Chapter jobs for full Bible |

---

### `run_ingest_queue.py`

Process a queue file — fetches and ingests each pending chapter. Updates the queue after every chapter so you can stop and resume.

**Run full queue:**

```bash
docker exec -it dailybread-api python /app/scripts/run_ingest_queue.py \
  --queue /app/data/queues/niv-john.json
```

**Process only next 3 chapters (testing):**

```bash
docker exec -it dailybread-api python /app/scripts/run_ingest_queue.py \
  --queue /app/data/queues/niv-john.json \
  --limit 3
```

| Flag | Default | Description |
|------|---------|-------------|
| `--queue` | *(required)* | Path to queue JSON |
| `--status` | `pending` | Only process jobs with this status |
| `--limit` | *(none)* | Max jobs to process this run |
| `--sleep` | `0.25` | Seconds between API calls (be nice to Bolls server) |

---

## Recommended ingestion flow

```
1. ingest_bolls_one.py      → test one verse (John 3:16)
2. ingest_bolls_chapter.py  → test one chapter (John 3)
3. generate_ingest_queue.py → build queue for a book or full Bible
4. run_ingest_queue.py      → automate chapter-by-chapter ingestion
5. (next) embed verses      → Ollama → pgvector
6. (next) /chat endpoint    → RAG retrieval + answer
```

---

## Local dev (without Docker for API)

```bash
cd api
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

```bash
cd client
npm install
npm run dev
```

DB + Ollama still via Docker:

```bash
docker compose up -d db ollama adminer
```

---

## Environment variables

| Variable | Where | Description |
|----------|-------|-------------|
| `DATABASE_URL` | API | Postgres connection string |
| `CLIENT_URL` | API | CORS origin (`http://localhost:3000`) |
| `OLLAMA_BASE_URL` | API | Ollama URL (`http://ollama:11434` in Docker) |
| `OLLAMA_CHAT_MODEL` | API | Chat model name (`llama3.2`) |
| `OLLAMA_EMBED_MODEL` | API | Embedding model (`nomic-embed-text`) |
| `NEXT_PUBLIC_API_URL` | Client | API URL for browser (`http://localhost:8000`) |
| `BOLLS_TRANSLATION` | Scripts | Default translation for ingest scripts |
| `BOLLS_BOOK` | Scripts | Default book name |
| `BOLLS_CHAPTER` | Scripts | Default chapter number |
| `BOLLS_BASE_URL` | Scripts | Bolls API base URL |

---

## Troubleshooting

| Problem | Command / fix |
|---------|----------------|
| Port in use | `lsof -i :8000` then `kill <PID>` |
| Container name wrong | `docker ps` to see actual names |
| Model not found | `docker exec dailybread-ollama ollama pull llama3.2` |
| Reset everything | `docker compose down -v` then `docker compose up --build` |
| Exit container shell | `exit` or **Ctrl+D** |
| Stop running command | **Ctrl+C** |

---

## Related docs

- [`SETUP.md`](SETUP.md) — full developer setup guide
- [`docs/local-rag-learning-plan.md`](docs/local-rag-learning-plan.md) — build your own RAG chatbot
- [`docs/bible-data-ingestion-plan.md`](docs/bible-data-ingestion-plan.md) — ingestion architecture
