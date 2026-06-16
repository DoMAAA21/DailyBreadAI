# DailyBreadAI

A Bible-focused Retrieval-Augmented Generation (RAG) application. Ask questions about Scripture and get answers grounded in retrieved passages — not hallucinated verses.

This is the first project in a series exploring RAG patterns. Future apps will build on the same core ideas with different domains and data.

## Tech Stack

| Layer | Technology |
|-------|------------|
| **API** | [FastAPI](https://fastapi.tiangolo.com/) |
| **Database** | [PostgreSQL](https://www.postgresql.org/) |
| **Vector search** | [pgvector](https://github.com/pgvector/pgvector) |
| **Frontend** | [Next.js](https://nextjs.org/) |

## How It Works

1. **Ingest** — Bible text is chunked and embedded into vector representations.
2. **Store** — Chunks and embeddings live in PostgreSQL with pgvector for similarity search.
3. **Retrieve** — A user query is embedded and matched against the most relevant passages.
4. **Generate** — An LLM answers using only the retrieved context, keeping responses faithful to Scripture.

```
User question
    │
    ▼
Next.js frontend ──► FastAPI backend
                         │
                         ├── Embed query
                         ├── pgvector similarity search (PostgreSQL)
                         └── LLM response with cited passages
```

## Project Structure

```
DailyBreadAI/
├── api/          # FastAPI backend (RAG pipeline, embeddings, search)
├── web/          # Next.js frontend (chat UI, passage display)
└── README.md
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with the [pgvector extension](https://github.com/pgvector/pgvector#installation)

## Getting Started

### 1. PostgreSQL + pgvector

```bash
# macOS (Homebrew)
brew install postgresql@15
brew install pgvector

# Create database
createdb dailybread
psql dailybread -c "CREATE EXTENSION vector;"
```

### 2. API (FastAPI)

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set environment variables (example)
export DATABASE_URL="postgresql://user:password@localhost:5432/dailybread"
export OPENAI_API_KEY="your-key-here"

uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

### 3. Frontend (Next.js)

```bash
cd web
npm install

# Point at the local API
export NEXT_PUBLIC_API_URL="http://localhost:8000"

npm run dev
```

The app will be available at `http://localhost:3000`.

## Environment Variables

| Variable | Where | Description |
|----------|-------|-------------|
| `DATABASE_URL` | API | PostgreSQL connection string |
| `OPENAI_API_KEY` | API | API key for embeddings and generation |
| `NEXT_PUBLIC_API_URL` | Web | Base URL of the FastAPI backend |

## Roadmap

- [ ] Bible text ingestion and chunking pipeline
- [ ] Embedding generation and pgvector storage
- [ ] Semantic search API endpoint
- [ ] RAG chat endpoint with source citations
- [ ] Next.js chat interface
- [ ] Passage reference linking (book, chapter, verse)

## License

MIT
