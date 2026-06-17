import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.rag import answer_question

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class VerseSource(BaseModel):
    text: str
    reference: str


class ChatResponse(BaseModel):
    reply: str
    sources: list[VerseSource] = []


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    try:
        result = await answer_question(body.message.strip())
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama request failed: {exc}",
        ) from exc

    return ChatResponse(
        reply=result.reply,
        sources=[
            VerseSource(text=v.text, reference=v.reference) for v in result.sources
        ],
    )
