# DailyBreadAI

A Bible-focused **Retrieval-Augmented Generation (RAG)** app. Ask questions about Scripture and get answers grounded in retrieved verses — not hallucinated text.

Runs **fully local** with Docker, PostgreSQL + pgvector, and **Ollama** (no OpenAI API key required).

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | [Next.js](https://nextjs.org/) |
| **API** | [FastAPI](https://fastapi.tiangolo.com/) |
| **Database** | [PostgreSQL](https://www.postgresql.org/) + [pgvector](https://github.com/pgvector/pgvector) |
| **Embeddings** | Ollama `nomic-embed-text` |
| **Chat LLM** | Ollama `llama3.2` |

## How It Works

```
User question
    │
    ▼
Next.js chat UI ──► POST /chat
                        │
                        ├── LLM plans retrieval (search query, book filter, intent)
                        ├── Embed search query (Ollama)
                        ├── pgvector similarity search (PostgreSQL)
                        ├── LLM answer using retrieved verses only
                        └── Reply + verse citations (VerseCard)
```

1. **Ingest** — Bible text from [Bolls.life](https://bolls.life) → `verses` table
2. **Embed** — Each verse → vector in `verse_embeddings` (pgvector)
3. **Retrieve** — LLM plans the search; pgvector finds the closest verses
4. **Generate** — LLM answers using only retrieved context + citations

## Quick Start (Docker)

```bash
git clone <repo-url>
cd DailyBreadAI
docker compose up --build -d

# Pull models (first time only)
docker exec dailybread-ollama ollama pull llama3.2
docker exec dailybread-ollama ollama pull nomic-embed-text
```

| Service | URL |
|---------|-----|
| Chat UI | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Adminer (DB) | http://localhost:8080 |

Test the chat API:

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What does the Bible say about peace?"}'
```

Full setup, ingestion, and embedding instructions: **[SETUP.md](SETUP.md)**

## Project Structure

```
DailyBreadAI/
├── api/
│   ├── app/
│   │   ├── routers/          # /health, /chat
│   │   └── services/
│   │       ├── ollama.py           # Chat + embeddings
│   │       ├── retrieval_planner.py # LLM plans search (JSON)
│   │       ├── retrieval.py        # pgvector search
│   │       └── rag.py              # RAG orchestration
│   └── scripts/
│       ├── ingest_bolls_*.py       # Bible text ingestion
│       ├── generate_ingest_queue.py
│       ├── run_ingest_queue.py
│       └── embed_verses.py         # Verse → vector
├── client/                   # Next.js chat UI
├── docker/                   # DB schema + pgvector init
├── docker-compose.yml
├── SETUP.md                  # Developer setup guide
├── SCRIPTS.md                # Commands reference
└── RAG.md                    # RAG architecture & improvements
```

## Data Pipeline

| Step | Command | Result |
|------|---------|--------|
| Ingest | `run_ingest_queue.py` | Verse text in `verses` |
| Embed | `embed_verses.py` | Vectors in `verse_embeddings` |
| Chat | `POST /chat` | RAG answers with sources |

```bash
# Ingest full NIV Bible (inside API container)
python /app/scripts/generate_ingest_queue.py --translation NIV
python /app/scripts/run_ingest_queue.py --queue /app/data/queues/niv-all.json

# Embed all ingested verses (skips already embedded)
python /app/scripts/embed_verses.py --translation NIV --batch-size 32
```

See **[SCRIPTS.md](SCRIPTS.md)** for all commands.

## Environment Variables

| Variable | Where | Default | Description |
|----------|-------|---------|-------------|
| `DATABASE_URL` | API | `postgresql://...@db:5432/dailybread` | Postgres connection |
| `OLLAMA_BASE_URL` | API | `http://ollama:11434` | Ollama URL |
| `OLLAMA_CHAT_MODEL` | API | `llama3.2` | Chat model |
| `OLLAMA_EMBED_MODEL` | API | `nomic-embed-text` | Embedding model |
| `NEXT_PUBLIC_API_URL` | Client | `http://localhost:8000` | API URL for browser |

Copy `api/.env.example` → `api/.env` for local (non-Docker) development.

## API

### `POST /chat`

```json
{ "message": "What is Matthew all about?" }
```

Response:

```json
{
  "reply": "...",
  "sources": [
    { "text": "...", "reference": "Matthew 5:1 (NIV)" }
  ]
}
```

### `GET /health`

```json
{ "status": "ok" }
```

## Documentation

| Doc | Contents |
|-----|----------|
| [SETUP.md](SETUP.md) | Full dev setup, Docker, ingestion, embedding |
| [SCRIPTS.md](SCRIPTS.md) | All scripts and commands |
| [RAG.md](RAG.md) | RAG phases, architecture, accuracy improvements |
| [docs/local-rag-learning-plan.md](docs/local-rag-learning-plan.md) | Learning path |
| [docs/bible-data-ingestion-plan.md](docs/bible-data-ingestion-plan.md) | Ingestion design |

## Status

- [x] Docker full stack (db, ollama, api, client, adminer)
- [x] NIV Bible ingestion (Bolls.life → Postgres)
- [x] Verse embeddings (Ollama → pgvector)
- [x] LLM retrieval planner (intelligent search)
- [x] RAG chat endpoint with source citations
- [x] Next.js chat UI with VerseCard
- [ ] Streaming responses
- [ ] Chat conversation history
- [ ] Richer embed text (book + reference prefix)
- [ ] Direct verse reference lookup (`John 3:16`)

## License

MIT
