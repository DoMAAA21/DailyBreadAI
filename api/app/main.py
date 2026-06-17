from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import CLIENT_URL
from app.routers import chat, health

app = FastAPI(title="DailyBreadAI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[CLIENT_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router)


@app.get("/")
def root():
    return {"message": "DailyBreadAI API"}
