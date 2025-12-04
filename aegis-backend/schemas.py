# schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


# --- INPUT MODEL ---
class ScanRequest(BaseModel):
    url: str
    text: str = Field(..., max_length=15000, description="Truncated article text")
    title: Optional[str] = None
    domain: Optional[str] = None
    device_id: Optional[str] = None  # Guest mode identifier


# --- OUTPUT MODELS (The Dossier) ---
class VectorScore(BaseModel):
    score: int = Field(..., ge=0, le=100, description="0-100 score for this vector")
    flags: List[str] = Field(default_factory=list, description="Specific issues found")
    analysis: str = Field(..., description="Detailed explanation")


class ANIResponse(BaseModel):
    ani_score: int = Field(..., ge=0, le=100, description="0-100 Narrative Integrity Score")
    summary: str = Field(..., description="2-3 sentence summary of findings")
    verdict: str = Field(..., description="Human-readable verdict")
    vectors: Dict[str, VectorScore] = Field(
        default_factory=dict,
        description="Analysis vectors: authority, emotion, logic, headline"
    )
    cached: bool = Field(default=False, description="Whether result was served from cache")
    credits_remaining: Optional[int] = Field(default=None, description="User's remaining credits")


# --- ERROR RESPONSE ---
class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
