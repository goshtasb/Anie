# main.py
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from schemas import ScanRequest, ANIResponse
from engine import analyze_text
import services
import uvicorn

app = FastAPI(title="Aegis Core (Free Alpha)")

# CORS: Allow all origins for the Alpha launch
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "Aegis Systems Online (Alpha Mode)"}

@app.post("/v1/scan", response_model=ANIResponse)
async def scan_endpoint(
    payload: ScanRequest,
    x_user_id: str = Header(None, alias="X-User-ID")
):
    # 1. CACHE CHECK (Content-Based)
    # Hash the TEXT, not URL. Same article content = same score.
    cached = services.check_cache(payload.text)
    if cached:
        return ANIResponse(**cached)

    # 2. PAYMENT GATE (DISABLED FOR ALPHA)
    # We log the user, but we do NOT stop them if they have 0 credits.
    if x_user_id:
        print(f"👤 User Scan: {x_user_id}")
    else:
        print("👤 Anonymous Scan")

    # 3. RUN GROK (The Cost)
    result = await analyze_text(payload.text)

    # 4. SAVE TO CACHE (Content-Based)
    # Save with text hash so same content always returns same score
    services.save_to_cache(payload.url, payload.text, result.model_dump(), result.ani_score)

    return result

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8010)
