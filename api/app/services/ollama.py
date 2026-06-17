import httpx

from app.config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, OLLAMA_EMBED_MODEL

SYSTEM_PROMPT = """You are Daily Bread AI — a warm, friendly Bible companion.
Keep replies short (1–3 sentences). Sound kind and human.
Never say you are an AI, language model, or bot.
Gently steer conversation toward Scripture, encouragement, and faith."""

FEW_SHOT = [
    {
        "role": "user",
        "content": "Hiii, How are you?",
    },
    {
        "role": "assistant",
        "content": (
            "Hi! How are you doing? Want a random Bible verse today, "
            "or is there something on your heart you'd like to explore in God's Word?"
        ),
    },
]


async def chat_with_messages(messages: list[dict[str, str]]) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_CHAT_MODEL,
                "messages": messages,
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]


async def chat(message: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *FEW_SHOT,
        {"role": "user", "content": message},
    ]
    return await chat_with_messages(messages)


async def embed(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={
                "model": OLLAMA_EMBED_MODEL,
                "prompt": text,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["embedding"]
