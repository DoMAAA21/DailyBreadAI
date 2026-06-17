import re
from dataclasses import dataclass

from app.services.ollama import chat, chat_with_messages
from app.services.retrieval import RetrievedVerse, search_verses

RAG_SYSTEM_PROMPT = """You are Daily Bread AI — a warm, friendly Bible companion.
Answer using ONLY the verses provided below. Do not invent verses or references.
If the verses only partly answer the question, say what they do say and stay humble.
Keep your reply warm and short (2–4 sentences). Cite book/chapter/verse inline when helpful.
Never say you are an AI, language model, or bot."""

MIN_RELEVANCE_SCORE = 0.45

SUBSTANTIVE_PHRASES = (
    "what does",
    "what is",
    "what are",
    "who is",
    "who was",
    "why does",
    "tell me about",
    "explain",
    "bible",
    "scripture",
    "verse",
)

GREETING_SIGNALS = (
    r"\bhow are you\b",
    r"^h+i+\b",
    r"^hello\b",
    r"^hey\b",
    r"\bgood (morning|afternoon|evening)\b",
    r"^what'?s up\b",
    r"^sup\b",
)


@dataclass
class RagResult:
    reply: str
    sources: list[RetrievedVerse]


def is_greeting(message: str) -> bool:
    text = message.strip().lower()
    if len(text) > 100:
        return False
    if any(phrase in text for phrase in SUBSTANTIVE_PHRASES):
        return False
    return any(re.search(pattern, text) for pattern in GREETING_SIGNALS)


def format_verses_for_prompt(verses: list[RetrievedVerse]) -> str:
    return "\n".join(f"- {v.reference}: {v.text}" for v in verses)


async def answer_question(
    question: str,
    *,
    translation: str = "NIV",
    limit: int = 5,
) -> RagResult:
    cleaned = question.strip()
    if not cleaned:
        return RagResult(reply="", sources=[])

    if is_greeting(cleaned):
        reply = await chat(cleaned)
        return RagResult(reply=reply, sources=[])

    verses = await search_verses(cleaned, translation=translation, limit=limit)

    if not verses:
        return RagResult(
            reply=(
                "I don't have any indexed Scripture to search yet. "
                "Try asking again after verses are embedded."
            ),
            sources=[],
        )

    if verses[0].score < MIN_RELEVANCE_SCORE:
        return RagResult(
            reply=(
                "I couldn't find a clear match in the Scripture I have indexed so far. "
                "Try rephrasing your question, or ask about a specific topic like peace, love, or faith."
            ),
            sources=[],
        )

    context = format_verses_for_prompt(verses)
    messages = [
        {"role": "system", "content": RAG_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Verses:\n{context}\n\nQuestion: {cleaned}",
        },
    ]

    reply = await chat_with_messages(messages)
    return RagResult(reply=reply, sources=verses)
