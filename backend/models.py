"""
backend/models.py — Pydantic request/response schemas for the FastAPI API.
Defines the contract between Streamlit frontend and FastAPI backend.
"""

from pydantic import BaseModel, field_validator
from typing import Optional, List

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    question: str
    history: List[ChatMessage] = []

    @field_validator("question")
    @classmethod
    def question_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question must not be empty.")
        return v


class ChatResponse(BaseModel):
    answer: str
    chart_base64: Optional[str] = None   # Base64 PNG string if a chart was generated
    chart_type: Optional[str] = None     # e.g. "histogram", "bar", "pie"
    error: Optional[str] = None          # Non-null if something went wrong
