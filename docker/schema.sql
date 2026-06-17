-- DailyBreadAI schema
-- Includes:
-- - translations: which translation we loaded
-- - books: canonical book number + metadata (Bolls bookid)
-- - verses: verse text for each translation
-- - verse_embeddings: pgvector embeddings (created with default dimension 768)
--
-- NOTE: If your embedding dimension differs from 768, alter verse_embeddings.embedding
-- to the correct `vector(<dim>)` before inserting embeddings.

CREATE TABLE IF NOT EXISTS translations (
  code TEXT PRIMARY KEY,
  name TEXT,
  language TEXT
);

CREATE TABLE IF NOT EXISTS books (
  book_num INT PRIMARY KEY,
  name TEXT NOT NULL,
  testament TEXT,
  chapters INT
);

CREATE TABLE IF NOT EXISTS verses (
  id BIGSERIAL PRIMARY KEY,
  translation_code TEXT NOT NULL REFERENCES translations(code) ON DELETE CASCADE,
  book_num INT NOT NULL REFERENCES books(book_num) ON DELETE CASCADE,
  chapter INT NOT NULL,
  verse INT NOT NULL,
  text TEXT NOT NULL,
  raw JSONB,
  UNIQUE (translation_code, book_num, chapter, verse)
);

-- pgvector embeddings
-- Default dimension for Ollama `nomic-embed-text` is typically 768.
CREATE TABLE IF NOT EXISTS verse_embeddings (
  verse_id BIGINT NOT NULL REFERENCES verses(id) ON DELETE CASCADE,
  model TEXT NOT NULL,
  embedding vector(768) NOT NULL,
  PRIMARY KEY (verse_id, model)
);

