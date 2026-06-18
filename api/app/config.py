import os
from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_ENV_PATH)

CLIENT_URL = os.getenv("CLIENT_URL", "http://localhost:3000")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/dailybread",
)

# Local AI via Ollama 
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
