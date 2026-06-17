import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.ollama import chat as ollama_chat

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    try:
        reply = await ollama_chat(body.message.strip())
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama request failed: {exc}",
        ) from exc

    return ChatResponse(reply=reply)
