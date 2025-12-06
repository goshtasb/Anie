# schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


# --- INPUT MODEL ---
class ScanRequest(BaseModel):
    url: str
    text: str = Field(default="", max_length=15000, description="Truncated article text")
    title: Optional[str] = None
    domain: Optional[str] = None
    device_id: Optional[str] = None  # Guest mode identifier


# --- GEO-INTEL MODELS ---
class Coordinates(BaseModel):
    lat: float
    lon: float


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
    coordinates: Optional[Coordinates] = Field(default=None, description="GPS coordinates of origin location")
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
