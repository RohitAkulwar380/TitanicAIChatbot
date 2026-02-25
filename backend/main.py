"""
backend/main.py — FastAPI entry point.
CORS is enabled so Streamlit Cloud (and any origin) can call this API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.models import ChatRequest, ChatResponse
from backend.services.agent_service import run_agent

app = FastAPI(title="Titanic Chat API")

# ── CORS — required so Streamlit Cloud's iframe JS can call this API ──────────
# allow_origins=["*"] is safe here because this is a read-only public chatbot.
# If you add auth later, restrict this to your Streamlit Cloud URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    result = run_agent(
        question=request.question,
        history=request.history or [],
    )
    return ChatResponse(
        answer=result["answer"],
        chart_base64=result.get("chart_base64"),
        chart_type=result.get("chart_type"),
    )