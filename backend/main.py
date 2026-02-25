"""
backend/main.py — FastAPI entry point.
Thin routing layer only — delegates all logic to services.
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.models import ChatRequest, ChatResponse
from backend.services.agent_service import run_agent
from config import ALLOWED_ORIGINS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Titanic Chat API",
    description="LangChain-powered chatbot for querying the Titanic passenger dataset.",
    version="1.0.0",
)

# CORS — allows Streamlit frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "Titanic Chat API"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint. Accepts a question and returns a text answer
    plus an optional base64-encoded chart image.
    """
    logger.info(f"Received question: {request.question!r}")

    try:
        result = run_agent(request.question, request.history)
        return ChatResponse(
            answer=result["answer"],
            chart_base64=result.get("chart_base64"),
            chart_type=result.get("chart_type"),
        )
    except Exception as e:
        logger.exception(f"Unhandled error in /chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )
