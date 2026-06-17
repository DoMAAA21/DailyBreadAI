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
├── api/                 # FastAPI backend
├── client/              # Next.js frontend
├── docker/              # DB init scripts (pgvector)
├── docs/                # Architecture & learning guides
├── docker-compose.yml   # Full stack orchestration
└── SETUP.md             # This file
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

Open http://localhost:3000 in your browser for the app UI.

---

## Docker services

| Container | Image | Port | Role |
|-----------|-------|------|------|
| `dailybread-db` | `pgvector/pgvector:pg16` | 5432 | PostgreSQL + vector extension |
| `dailybread-ollama` | `ollama/ollama` | 11434 | Local embeddings + LLM |
| `dailybread-api` | Built from `./api` | 8000 | FastAPI (hot reload) |
| `dailybread-client` | Built from `./client` | 3000 | Next.js (hot reload) |

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
- Docker full stack (db, ollama, api, client)
- Health endpoint
- Chat UI (mock responses until RAG is wired)
- Local Ollama for embeddings + chat

**Coming next:**
- Bible data ingestion → Postgres
- Verse embeddings → pgvector
- `/chat` RAG endpoint
- Frontend connected to real API

See also:
- [`docs/local-rag-learning-plan.md`](docs/local-rag-learning-plan.md) — how to build your own RAG chatbot
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
