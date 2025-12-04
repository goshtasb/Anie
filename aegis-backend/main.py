# main.py
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from schemas import ScanRequest, ANIResponse, ErrorResponse
from engine import analyze_text
from services import check_cache, save_to_cache, check_credits, deduct_credit, get_or_create_guest
from dotenv import load_dotenv
import uvicorn
import os

load_dotenv()

app = FastAPI(
    title="Aegis Core API",
    description="A.N.I. (Aggregate Narrative Integrity) Analysis Engine",
    version="1.0.0"
)

# CORS Policy for Chrome Extensions
# In production, replace "*" with specific extension IDs
origins = [
    "http://localhost:3000",
    "http://localhost:8010",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8010",
    # Add your extension ID after installing:
    # "chrome-extension://YOUR_EXTENSION_ID_HERE"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permissive for MVP - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Aegis Core API",
        "version": "1.0.0"
    }


@app.get("/health")
def detailed_health():
    """Detailed health check."""
    api_key_set = bool(os.getenv("OPENAI_API_KEY"))
    supabase_set = bool(os.getenv("SUPABASE_URL")) and "your-project-id" not in os.getenv("SUPABASE_URL", "")
    return {
        "status": "online",
        "openai_configured": api_key_set,
        "supabase_configured": supabase_set
    }


@app.get("/v1/credits/{device_id}")
def get_credits(device_id: str):
    """Get credit balance for a device."""
    guest = get_or_create_guest(device_id)
    return {
        "device_id": device_id,
        "credits": guest.get("credits", 0)
    }


@app.post("/v1/scan", response_model=ANIResponse, responses={400: {"model": ErrorResponse}, 402: {"model": ErrorResponse}})
async def scan_article(payload: ScanRequest):
    """
    Analyze an article for manipulation and bias.

    Returns an A.N.I. (Aggregate Narrative Integrity) score and detailed analysis
    across multiple manipulation vectors.

    Flow:
    1. Check cache - if URL was analyzed before, return cached result (free)
    2. Check credits - if no device_id or no credits, return 402
    3. Run AI analysis
    4. Deduct credit and cache result
    """
    print(f"📥 Scan request: {payload.url[:50]}...")

    # 1. Validate API key is configured
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="Server configuration error: OpenAI API key not set"
        )

    # 2. Validate text length
    if not payload.text or len(payload.text.strip()) < 500:
        raise HTTPException(
            status_code=400,
            detail="Insufficient data for forensic analysis. Minimum 500 characters required."
        )

    # 3. CHECK CACHE FIRST (Free - doesn't cost credits)
    cached_result = check_cache(payload.url)
    if cached_result:
        # Get current credits for response (don't deduct for cache hits)
        credits_remaining = None
        if payload.device_id:
            credits_remaining = check_credits(payload.device_id)

        return ANIResponse(
            **cached_result,
            cached=True,
            credits_remaining=credits_remaining
        )

    # 4. CHECK CREDITS (Only for fresh scans)
    credits_remaining = None
    if payload.device_id:
        credits_remaining = check_credits(payload.device_id)
        if credits_remaining <= 0:
            raise HTTPException(
                status_code=402,
                detail="No credits remaining. Purchase more to continue scanning."
            )

    # 5. RUN AI ANALYSIS (This costs money)
    dossier = await analyze_text(
        text=payload.text,
        title=payload.title,
        url=payload.url
    )

    # 6. DEDUCT CREDIT (Only after successful analysis)
    if payload.device_id:
        deduct_credit(payload.device_id)
        credits_remaining = check_credits(payload.device_id)

    # 7. CACHE THE RESULT (Save money on future requests)
    result_dict = dossier.model_dump()
    save_to_cache(payload.url, result_dict, dossier.ani_score)

    # 8. Return with metadata
    dossier.cached = False
    dossier.credits_remaining = credits_remaining

    return dossier


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8010,
        reload=True
    )
