# main.py
from fastapi import FastAPI, HTTPException, Header, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from schemas import ScanRequest, ANIResponse, Coordinates
from engine import analyze_text
import services
from scraper import scrape_article
import uvicorn

app = FastAPI(title="Acuity Core (Free Alpha)")

# CORS: Allow all origins for the Alpha launch
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_VERSION = "1.0.45"  # V3.10 Lifestyle Exception: Food/Travel/Entertainment Leniency

@app.get("/")
def health_check():
    return {"status": "Acuity Systems Online (Alpha Mode)", "version": API_VERSION}


@app.delete("/v1/cache/clear")
async def clear_cache_endpoint(url: str = None):
    """
    DEBUG ENDPOINT: Force-clear the cache for a specific URL or all entries.
    Use this when testing to ensure Grok is actually called.
    """
    if url:
        # Clear specific URL
        success = services.clear_cache(url)
        return {"cleared": success, "url": url}
    else:
        # Clear ALL cache (nuclear option)
        if services.supabase:
            try:
                # Delete all entries
                services.supabase.table("scan_cache").delete().neq("url_hash", "").execute()
                print("🗑️ NUCLEAR: All cache entries cleared")
                return {"cleared": True, "message": "All cache cleared"}
            except Exception as e:
                return {"cleared": False, "error": str(e)}
        return {"cleared": False, "message": "Supabase not configured"}

@app.post("/v1/scan", response_model=ANIResponse)
async def scan_endpoint(
    payload: ScanRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    x_user_id: str = Header(None, alias="X-User-ID")
):
    # Extract headers for analytics (run once, reuse)
    headers_dict = dict(request.headers)

    # 1. CACHE CHECK (Canonical URL)
    # Frontend sends the stable canonical URL, not the dirty browser URL
    cached = services.check_cache(payload.url)
    if cached:
        # LOG CACHE HIT (Background - doesn't slow response)
        background_tasks.add_task(
            services.log_scan_event,
            x_user_id,
            payload.url,
            cached.get("ani_score", 0),
            "CACHE_HIT",
            cached.get("origin_location", "Global"),
            headers_dict
        )
        return ANIResponse(**cached)

    # 2. PAYMENT GATE (DISABLED FOR ALPHA)
    # We log the user, but we do NOT stop them if they have 0 credits.
    if x_user_id:
        print(f"👤 User Scan: {x_user_id}")
    else:
        print("👤 Anonymous Scan")

    # 3. GET TEXT (from payload or by scraping)
    text_to_analyze = payload.text
    title = payload.title

    # If no text provided (mobile/web users), scrape it from URL
    if not text_to_analyze or len(text_to_analyze) < 100:
        print("📱 URL-only request detected, initiating server-side scrape...")
        scrape_result = await scrape_article(payload.url)

        if not scrape_result["success"]:
            raise HTTPException(
                status_code=422,
                detail=scrape_result.get("error", "Could not extract article content")
            )

        text_to_analyze = scrape_result["text"]
        title = scrape_result.get("title", title)
        print(f"✅ Scraped {len(text_to_analyze)} chars, title: {title[:50]}...")

    # 4. RUN GROK (The Cost)
    result = await analyze_text(text_to_analyze, title=title)

    # 5. GEO-INTEL: Convert origin_location to coordinates
    if result.origin_location and result.origin_location != "Global":
        coords = services.get_coordinates(result.origin_location)
        if coords:
            result.coordinates = Coordinates(**coords)

    # 6. SAVE TO CACHE (Canonical URL)
    # Save using the stable canonical URL as key
    services.save_to_cache(payload.url, result.model_dump(), result.ani_score)

    # 7. LOG NEW SCAN EVENT (Background - the Firehose)
    background_tasks.add_task(
        services.log_scan_event,
        x_user_id,
        payload.url,
        result.ani_score,
        "NEW_SCAN",
        result.origin_location,
        headers_dict
    )

    return result

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8010)
