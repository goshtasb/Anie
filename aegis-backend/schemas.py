# schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


# --- INPUT MODELS ---
class ScanRequest(BaseModel):
    url: str
    text: str = Field(default="", max_length=15000, description="Truncated article text")
    title: Optional[str] = None
    domain: Optional[str] = None
    device_id: Optional[str] = None  # Guest mode identifier


class ChatRequest(BaseModel):
    """Interrogation Mode: Follow-up questions about a scanned article."""
    text: str = Field(..., max_length=15000, description="The article text being discussed")
    analysis_context: str = Field(..., description="The summary/verdict from the scan")
    question: str = Field(..., max_length=500, description="User's follow-up question")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Previous Q&A pairs for multi-turn conversations"
    )


class ChatResponse(BaseModel):
    """Response from Interrogation Mode."""
    reply: str = Field(..., description="Anie's forensic response")
    suggested_followups: Optional[List[str]] = Field(
        default=None,
        description="Suggested follow-up questions for the user"
    )


# --- OUTPUT MODELS (The Dossier) ---
class VectorScore(BaseModel):
    score: int = Field(..., ge=0, le=100, description="0-100 score for this vector")
    flags: List[str] = Field(default_factory=list, description="Specific issues found")
    analysis: str = Field(..., description="Detailed explanation")


class FactCheckVector(BaseModel):
    """Special vector for fact-checking with source citations."""
    score: int = Field(..., ge=0, le=100, description="0-100 factual accuracy score")
    claims_checked: List[str] = Field(default_factory=list, description="Claims that were verified")
    flags: List[str] = Field(default_factory=list, description="Specific factual issues found")
    sources: List[str] = Field(default_factory=list, description="Source URLs used for verification")
    analysis: str = Field(..., description="Detailed explanation of fact-check findings")


class ANIResponse(BaseModel):
    ani_score: int = Field(..., ge=0, le=100, description="0-100 Narrative Integrity Score")
    summary: str = Field(..., description="2-3 sentence summary of findings")
    verdict: str = Field(..., description="Human-readable verdict")
    origin_location: str = Field(default="Global", description="Geopolitical origin of the narrative")
    vectors: Dict[str, VectorScore] = Field(
        default_factory=dict,
        description="Analysis vectors: authority, emotion, logic, headline"
    )
    fact_check: Optional[FactCheckVector] = Field(default=None, description="Fact-check results from Truth Layer")
    cached: bool = Field(default=False, description="Whether result was served from cache")
    credits_remaining: Optional[int] = Field(default=None, description="User's remaining credits")


# --- ERROR RESPONSE ---
class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
