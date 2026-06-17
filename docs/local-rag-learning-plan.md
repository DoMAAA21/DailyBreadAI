# Build Your Own Bible Chatbot (Local RAG)

Yes — you can build your **own** chatbot without OpenAI. That is exactly how you learn to be an AI developer.

You are not buying a black-box chat widget. You are building **four pieces** yourself:

```
1. Data      → Bible verses in PostgreSQL
2. Embeddings → Turn text into numbers (vectors)
3. Retrieval  → Find verses similar to the user's question (pgvector)
4. Generation → Local LLM reads those verses and writes an answer (Ollama)
```

That full pipeline **is** RAG. OpenAI is just one possible vendor for steps 2 and 4. We skip it and run everything locally.

---

## The mental model

When a user asks: *"What does the Bible say about peace?"*

```
User question
    │
    ▼
[1] Embed the question          ← Ollama (nomic-embed-text)
    │
    ▼
[2] Search pgvector             ← YOUR code + PostgreSQL
    │   "Which stored verses are closest?"
    ▼
[3] Top 5 verses as context     ← John 14:27, Philippians 4:7, ...
    │
    ▼
[4] Prompt the local LLM        ← Ollama (llama3.2)
    │   "Answer ONLY using these verses..."
    ▼
[5] Return answer + citations   ← FastAPI → Next.js chat UI
```

**You own steps 2, 3, and 5 completely.** Steps 1 and 4 use **Ollama on your machine** — free, local, no API key.

---

## Our local stack

| Piece | Tool | Why |
|-------|------|-----|
| Database | PostgreSQL + pgvector | Store verses + vectors |
| Embeddings | Ollama `nomic-embed-text` | Text → vector, runs locally |
| LLM (chat) | Ollama `llama3.2` (or similar) | Generates answers from context |
| API | FastAPI | Retrieval logic + `/chat` endpoint |
| UI | Next.js | Chat interface you already built |

No OpenAI. No paid API keys for learning.

---

## What you will write (learning path)

### Step 1 — Database models
SQLAlchemy tables: `translations`, `books`, `verses`, `verse_embeddings`

### Step 2 — Ingest Bible text
`data_ingestion.py` — bulk download from Bolls.life / GetBible APIs → Postgres  
(see `bible-data-ingestion-plan.md`)

### Step 3 — Embed verses
`embed_verses.py` — for each verse, call Ollama embeddings API, save vector to pgvector

```python
# Concept only — you'll implement this
verse_text = "Peace I leave with you..."
vector = ollama_embed(verse_text)   # list of 768 floats
db.save(verse_id, vector)
```

### Step 4 — Retrieval service
`app/services/retrieval.py` — embed user question, cosine search in pgvector

```python
query_vector = ollama_embed(user_question)
verses = db.similarity_search(query_vector, limit=5)
```

### Step 5 — RAG service
`app/services/rag.py` — build prompt, call Ollama chat, return answer + sources

```python
prompt = f"""
You are a Bible study assistant. Answer ONLY using the verses below.
If the verses don't answer the question, say so.

Verses:
{format_verses(retrieved)}

Question: {user_question}
"""
answer = ollama_chat(prompt)
```

### Step 6 — Chat endpoint
`POST /chat` — wire retrieval + RAG, return JSON to your Next.js UI

### Step 7 — Connect frontend
Replace mock messages in `chat-interface.tsx` with `fetch('/api/chat')`

---

## Docker services

```bash
docker compose up --build
```

| Service | Port | Role |
|---------|------|------|
| `db` | 5432 | Postgres + pgvector |
| `ollama` | 11434 | Local embeddings + LLM |
| `api` | 8000 | Your RAG logic |
| `client` | 3000 | Chat UI |

### Pull models (first time only)

```bash
docker exec dailybread-ollama ollama pull llama3.2
docker exec dailybread-ollama ollama pull nomic-embed-text
```

---

## Suggested learning order (today)

1. **Start Docker** — `docker compose up`, confirm `/health` works
2. **Pull Ollama models** — commands above
3. **Test Ollama manually** — `curl http://localhost:11434/api/chat` with a simple prompt
4. **Create DB schema** — verses table (even 10 hardcoded verses is fine to start)
5. **Embed those verses** — run embed script, verify rows in `verse_embeddings`
6. **Build retrieval** — ask a question, print top matching verses to console
7. **Build `/chat`** — retrieval + Ollama prompt
8. **Wire frontend** — real answers in your UI

Skip full Bible ingestion until steps 4–8 work with one book (John).

---

## Key concepts to learn

| Concept | What it means |
|---------|----------------|
| **Embedding** | Converting text to a list of numbers so "peace" and "calm" end up near each other |
| **Vector search** | Finding stored verses whose numbers are closest to the question's numbers |
| **Context window** | The verses you pass to the LLM — it only "knows" what you give it |
| **RAG** | Retrieval (find verses) + Augmented (add to prompt) + Generation (LLM writes answer) |
| **Hallucination** | LLM making up verses — RAG reduces this by grounding in real retrieved text |

---

## Why this is "your own" chatbot

- **Your data** — Bible text you ingested
- **Your retrieval** — your SQL, your similarity logic, your top-k choice
- **Your prompt** — you control what the LLM is told to do
- **Your API** — FastAPI endpoints you wrote
- **Your UI** — Next.js chat you built

Ollama is just the engine that runs the model files locally — like Postgres runs your data. You're still the developer building the system.

---

## Optional later: swap components

| Component | Local (now) | Could swap to |
|-----------|-------------|---------------|
| Embeddings | Ollama | sentence-transformers, OpenAI |
| LLM | Ollama | OpenAI, Anthropic, etc. |
| Vector DB | pgvector | Pinecone, Weaviate |

The RAG **architecture** stays the same. Only the adapters change.

---

## Next file to create

When ready: `api/app/services/ollama.py` — thin client for embed + chat calls to Ollama.

Then: `api/app/services/retrieval.py` and `api/app/services/rag.py`.

That is your chatbot brain.
