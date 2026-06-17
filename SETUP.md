# DailyBreadAI — Developer Setup

Bible RAG app: **Next.js** frontend, **FastAPI** backend, **PostgreSQL + pgvector** for storage/search, **Ollama** for local embeddings and chat (no OpenAI API key required).

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Latest | Recommended — runs the full stack |
| Git | Any | Clone the repo |

**Disk space:** plan for **~15–20 GB** (Docker images + Ollama models + database). Minimal learning setup: **~6–8 GB**.

**Optional (local dev without Docker for API/client):**
- Python 3.12+
- Node.js 20+

---

## Project structure

```
DailyBreadAI/
├── api/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── routers/
│   │   │   ├── health.py        # GET /health
│   │   │   └── chat.py          # POST /chat (RAG)
│   │   └── services/
│   │       ├── ollama.py        # Ollama chat + embed
│   │       ├── retrieval.py     # pgvector similarity search
│   │       └── rag.py           # RAG orchestration
│   ├── scripts/
│   │   ├── ingest_bolls_one.py
│   │   ├── ingest_bolls_chapter.py
│   │   ├── generate_ingest_queue.py
│   │   ├── run_ingest_queue.py
│   │   └── embed_verses.py      # Verse text → pgvector
│   └── data/
│       ├── catalog/             # Book lists (e.g. niv.json)
│       └── queues/              # Chapter ingest jobs
├── client/                      # Next.js chat UI
├── docker/                      # DB init scripts (pgvector)
├── docs/                        # Architecture & learning guides
├── docker-compose.yml
├── SETUP.md                     # This file
├── SCRIPTS.md                   # Commands reference
└── RAG.md                       # RAG implementation guide
```

---

## Quick start (Docker — recommended)

### 1. Clone and enter the project

```bash
git clone <repo-url>
cd DailyBreadAI
```

### 2. Environment variables (optional)

Defaults work out of the box. To customize Ollama models:

```bash
cp .env.example .env
```

```env
OLLAMA_CHAT_MODEL=llama3.2
OLLAMA_EMBED_MODEL=nomic-embed-text
```

### 3. Build and start all services

```bash
docker compose up --build
```

Run in the background:

```bash
docker compose up --build -d
```

| Service | URL | Description |
|---------|-----|-------------|
| **Client** | http://localhost:3000 | Chat UI |
| **API** | http://localhost:8000 | FastAPI backend |
| **API docs** | http://localhost:8000/docs | Swagger UI |
| **Health** | http://localhost:8000/health | `{"status":"ok"}` |
| **Postgres** | `localhost:5432` | DB: `dailybread` |
| **Adminer** | http://localhost:8080 | Web UI for Postgres |
| **Ollama** | http://localhost:11434 | Local LLM + embeddings |

### 4. Pull Ollama models (first time only)

Ollama starts empty. Download models before testing chat or embeddings:

```bash
docker exec dailybread-ollama ollama pull llama3.2
docker exec dailybread-ollama ollama pull nomic-embed-text
```

Smaller chat model (saves ~1 GB):

```bash
docker exec dailybread-ollama ollama pull llama3.2:1b
```

Verify models are installed:

```bash
docker exec dailybread-ollama ollama list
```

### 5. Confirm everything works

```bash
# All containers running
docker compose ps

# Ollama is up
curl http://localhost:11434

# API health
curl http://localhost:8000/health

# Ollama chat test
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [{ "role": "user", "content": "Say hello in one sentence." }],
  "stream": false
}'
```

Open http://localhost:3000 in your browser for the chat UI. Ask a Bible question to test RAG (requires ingested + embedded verses — see below).

```bash
# Test RAG chat endpoint
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What does the Bible say about peace?"}' | python3 -m json.tool
```

Response includes `reply` and `sources` (verse text + references).

---

## Docker services

| Container | Image | Port | Role |
|-----------|-------|------|------|
| `dailybread-db` | `pgvector/pgvector:pg16` | 5432 | PostgreSQL + vector extension |
| `dailybread-ollama` | `ollama/ollama` | 11434 | Local embeddings + LLM |
| `dailybread-api` | Built from `./api` | 8000 | FastAPI (hot reload) |
| `dailybread-client` | Built from `./client` | 3000 | Next.js (hot reload) |
| `dailybread-adminer` | `adminer` | 8080 | Database web UI |

On first DB start, `docker/init-db.sql` runs:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## Environment variables

### Root `.env` (optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_CHAT_MODEL` | `llama3.2` | Model for generating answers |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Model for embeddings |

### API (set automatically in Docker)

| Variable | Docker value | Description |
|----------|--------------|-------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@db:5432/dailybread` | Postgres connection |
| `CLIENT_URL` | `http://localhost:3000` | CORS origin for frontend |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama inside Docker network |

For **local API** (not in Docker), copy `api/.env.example` to `api/.env` and use `localhost` URLs.

### Client

| Variable | Value | Description |
|----------|-------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | API base URL (browser) |

---

## Local development (without full Docker)

Useful if you prefer running API/client natively but still want Docker for Postgres + Ollama.

### Start DB + Ollama only

```bash
docker compose up db ollama -d
docker exec dailybread-ollama ollama pull llama3.2
docker exec dailybread-ollama ollama pull nomic-embed-text
```

### API (terminal 1)

```bash
cd api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### Client (terminal 2)

```bash
cd client
npm install
npm run dev
```

---

## Useful Docker commands

```bash
# Follow logs
docker compose logs -f
docker compose logs -f api

# Stop containers
docker compose stop

# Stop and remove containers
docker compose down

# Stop and DELETE all data (DB, models, node_modules volumes)
docker compose down -v

# Rebuild after Dockerfile changes
docker compose up --build

# Remove unused Docker images/volumes globally
docker system prune -a --volumes
```

### Reclaim disk space on Mac

1. `docker compose down -v` — removes project volumes (biggest win for Ollama models + DB)
2. Docker Desktop → **Settings → Resources → Disk usage** → prune
3. `docker system prune -a --volumes` — global cleanup

---

## Troubleshooting

### Port already in use

```bash
lsof -i :8000   # API
lsof -i :3000   # Client
lsof -i :5432   # Postgres
kill <PID>
```

### `model 'llama3.2' not found`

Ollama is running but the model isn't downloaded:

```bash
docker exec dailybread-ollama ollama pull llama3.2
```

### `connection refused` on port 11434

```bash
docker compose up -d ollama
docker compose ps ollama
```

### Client slow on first start

The first `docker compose up` runs `npm ci` inside the container. Wait 1–2 minutes, then refresh http://localhost:3000.

### API can't reach Ollama

Inside Docker, the API uses `http://ollama:11434` (service name). From your Mac terminal, use `http://localhost:11434`.

### Reset everything and start fresh

```bash
docker compose down -v
docker compose up --build
docker exec dailybread-ollama ollama pull llama3.2
docker exec dailybread-ollama ollama pull nomic-embed-text
```

---

## What works today vs. what's next

**Working now:**
- Docker full stack (db, ollama, api, client, adminer)
- Health endpoint (`GET /health`)
- Bible ingestion from Bolls.life → Postgres (`verses` table)
- Verse embeddings → pgvector (`verse_embeddings` table)
- RAG pipeline: embed question → retrieve top verses → Ollama answer
- `POST /chat` returns `reply` + `sources`
- Next.js chat UI connected to API (`client/utils/http.ts` + axios)
- Verse citations shown as `VerseCard` components

**Coming next (optional improvements):**
- Chat conversation history (multi-turn)
- Streaming responses
- pgvector index for faster search at scale
- Score thresholds / better greeting detection tuning
- Additional translations beyond NIV

---

## Next: set up the database and ingest Bible text

### 1. Ensure DB + pgvector are running

```bash
cd /Users/jharold/Projects/DailyBreadAI
docker compose up -d db
```

### 2. Create tables (schema)

If you start from a fresh DB volume, `docker/init-db.sql` runs automatically on first boot.
If you already have a DB volume and want to apply the schema now, run:

```bash
docker exec -i dailybread-db psql -U postgres -d dailybread < docker/schema.sql
```

### 3. Ingest a first verse (NIV, John 3:16)

This hits the structured JSON API on `bolls.life` and inserts the verse text into `verses`.

```bash
docker exec -it dailybread-api python /app/scripts/ingest_bolls_one.py \
  --translation NIV \
  --book John \
  --chapter 3 \
  --verse 16
```

### 4. Ingest a whole chapter (NIV, John 3 — all 36 verses)

One API call fetches the entire chapter:

```bash
docker exec -it dailybread-api python /app/scripts/ingest_bolls_chapter.py \
  --translation NIV \
  --book John \
  --chapter 3
```

### 5. Verify you have data

```bash
docker exec -it dailybread-db psql -U postgres -d dailybread -c \
  "SELECT translation_code, book_num, chapter, verse, left(text, 60) AS text FROM verses WHERE book_num = 43 AND chapter = 3 ORDER BY verse;"
```

You should see **36 rows** for John 3.

### 6. Automate with a chapter queue (per book or whole Bible)

Bolls does not offer one "whole book" endpoint — ingestion is **one chapter per API call**.
We generate a queue from `get-books` (book list + chapter counts), then process chapter by chapter.

**Generate catalog + queue for John only (21 chapters):**

```bash
docker exec -it dailybread-api python /app/scripts/generate_ingest_queue.py \
  --translation NIV \
  --book John
```

**Generate queue for the entire Bible (1,189 chapters for NIV):**

```bash
docker exec -it dailybread-api python /app/scripts/generate_ingest_queue.py \
  --translation NIV
```

Outputs:
- `api/data/catalog/niv.json` — all 66 books + chapter counts
- `api/data/queues/niv-john.json` — chapter jobs with `pending` / `done` / `failed` status

**Run the queue (resume-friendly — skips `done` chapters):**

```bash
docker exec -it dailybread-api python /app/scripts/run_ingest_queue.py \
  --queue /app/data/queues/niv-john.json
```

Process only the next 3 chapters (good for testing):

```bash
docker exec -it dailybread-api python /app/scripts/run_ingest_queue.py \
  --queue /app/data/queues/niv-john.json \
  --limit 3
```

The queue file is updated after each chapter, so you can stop and resume later.

### 7. Embed verses (required for RAG search)

**Ingested** and **embedded** are two different steps:

| Step | What it does | Table |
|------|----------------|-------|
| **Ingest** | Saves verse text from Bolls | `verses` |
| **Embed** | Converts verse text to vectors for semantic search | `verse_embeddings` |

RAG only searches verses that are **both** ingested and embedded.

**Embed one book (e.g. John):**

```bash
docker exec -it dailybread-api python /app/scripts/embed_verses.py \
  --translation NIV \
  --book John \
  --batch-size 32
```

**Embed all ingested verses not yet embedded (full Bible):**

```bash
docker exec -it dailybread-api python /app/scripts/embed_verses.py \
  --translation NIV \
  --batch-size 32
```

The script skips verses that already have embeddings — safe to stop and resume.

**Check progress:**

```bash
# Total ingested
docker exec dailybread-db psql -U postgres -d dailybread -c \
  "SELECT COUNT(*) FROM verses WHERE translation_code = 'NIV';"

# Total embedded
docker exec dailybread-db psql -U postgres -d dailybread -c \
  "SELECT COUNT(*) FROM verse_embeddings WHERE model = 'nomic-embed-text';"

# Still pending
docker exec dailybread-db psql -U postgres -d dailybread -c \
  "SELECT COUNT(*) FROM verses v
   LEFT JOIN verse_embeddings e ON e.verse_id = v.id AND e.model = 'nomic-embed-text'
   WHERE v.translation_code = 'NIV' AND e.verse_id IS NULL;"
```

When pending is `0`, all ingested verses are embedded and RAG searches the full corpus.

---

## RAG chat flow

When a user asks a Bible question in the UI:

1. Frontend sends `POST /chat` with `{ "message": "..." }`
2. API embeds the question via Ollama (`nomic-embed-text`)
3. pgvector finds the top 5 most similar verses
4. Ollama (`llama3.2`) generates an answer using only those verses
5. API returns `{ "reply": "...", "sources": [{ "text", "reference" }] }`
6. Frontend shows the reply + `VerseCard` for each source

Casual greetings (e.g. "Hi, how are you?") skip retrieval and use the friendly persona only.

**Key API files:**
- `api/app/services/ollama.py` — `chat()`, `embed()`
- `api/app/services/retrieval.py` — `search_verses()`
- `api/app/services/rag.py` — `answer_question()`
- `api/app/routers/chat.py` — `POST /chat`

**Key client files:**
- `client/utils/http.ts` — axios instance (`NEXT_PUBLIC_API_URL`)
- `client/app/(home)/_components/chat-interface.tsx` — chat UI

See also:
- [`RAG.md`](RAG.md) — full RAG architecture and phases
- [`SCRIPTS.md`](SCRIPTS.md) — all commands and scripts reference
- [`docs/local-rag-learning-plan.md`](docs/local-rag-learning-plan.md) — conceptual learning path
- [`docs/bible-data-ingestion-plan.md`](docs/bible-data-ingestion-plan.md) — Bible data pipeline

---

## Database credentials (local dev)

| Field | Value |
|-------|-------|
| Host | `localhost` |
| Port | `5432` |
| Database | `dailybread` |
| User | `postgres` |
| Password | `postgres` |

Connect with any Postgres client:

```bash
docker exec -it dailybread-db psql -U postgres -d dailybread
```

Check pgvector:

```sql
\dx
```

You should see `vector` in the list.

---

## Adminer (database web UI)

Start Adminer (or bring up the full stack):

```bash
docker compose up -d adminer
```

Open http://localhost:8080 and log in with:

| Field | Value |
|-------|-------|
| System | PostgreSQL |
| Server | `db` |
| Username | `postgres` |
| Password | `postgres` |
| Database | `dailybread` |

Browse the `verses` and `verse_embeddings` tables to confirm your data.

**Useful queries:**

```sql
-- Verses per book
SELECT b.name, COUNT(*) FROM verses v
JOIN books b ON b.book_num = v.book_num
WHERE v.translation_code = 'NIV'
GROUP BY b.name ORDER BY b.name;

-- Embedding count
SELECT COUNT(*) FROM verse_embeddings;
```
