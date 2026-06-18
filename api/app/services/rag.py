from dataclasses import dataclass

from app.services.ollama import chat, chat_with_messages
from app.services.retrieval import RetrievedVerse, search_verses
from app.services.retrieval_planner import plan_retrieval

RAG_SYSTEM_PROMPT = """You are Daily Bread AI — a warm, friendly Bible companion.
Answer using ONLY the verses provided below. Do not invent verses or references.
If the verses only partly answer the question, say what they do say and stay humble.
Keep your reply warm and short (2–4 sentences). Cite book/chapter/verse inline when helpful.
Never say you are an AI, language model, or bot."""

MIN_RELEVANCE_SCORE = 0.45


@dataclass
class RagResult:
    reply: str
    sources: list[RetrievedVerse]
    search_query: str | None = None


def format_verses_for_prompt(verses: list[RetrievedVerse]) -> str:
    return "\n".join(f"- {v.reference}: {v.text}" for v in verses)


async def answer_question(
    question: str,
    *,
    translation: str = "NIV",
) -> RagResult:
    cleaned = question.strip()
    if not cleaned:
        return RagResult(reply="", sources=[])

    plan = await plan_retrieval(cleaned)

    if not plan.use_rag:
        reply = await chat(cleaned)
        return RagResult(reply=reply, sources=[])

    verses = await search_verses(
        plan.search_query,
        translation=translation,
        limit=plan.verse_limit,
        book_name=plan.book,
    )

    if not verses:
        return RagResult(
            reply=(
                "I don't have any indexed Scripture to search yet. "
                "Try asking again after verses are embedded."
            ),
            sources=[],
            search_query=plan.search_query,
        )

    if verses[0].score < MIN_RELEVANCE_SCORE:
        return RagResult(
            reply=(
                "I couldn't find a clear match in the Scripture I have indexed so far. "
                "Try rephrasing your question, or ask about a specific topic like peace, love, or faith."
            ),
            sources=[],
            search_query=plan.search_query,
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
    return RagResult(reply=reply, sources=verses, search_query=plan.search_query)
