# main.py
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Header, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from schemas import ScanRequest, ANIResponse
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

API_VERSION = "1.0.47"  # V3.12 War Room Ticker: Live Stats Endpoint

@app.get("/")
def health_check():
    return {"status": "Acuity Systems Online (Alpha Mode)", "version": API_VERSION}


@app.get("/v1/stats")
async def get_stats():
    """
    Public Endpoint: Returns aggregate system activity for the 'Live Ticker'.
    Privacy-first: No PII, just counts.
    """
    try:
        if not services.supabase:
            return {"scans_24h": "---", "scans_total": "---", "status": "OFFLINE"}

        # 1. Count Scans in last 24h (DAU proxy)
        cutoff_24h = (datetime.now() - timedelta(hours=24)).isoformat()
        daily_scans = services.supabase.table("scan_events") \
            .select("*", count="exact", head=True) \
            .gte("created_at", cutoff_24h) \
            .execute()

        # 2. Count Total Scans (All time)
        total_scans = services.supabase.table("scan_events") \
            .select("*", count="exact", head=True) \
            .execute()

        return {
            "scans_24h": daily_scans.count or 0,
            "scans_total": total_scans.count or 0,
            "status": "OPERATIONAL"
        }
    except Exception as e:
        print(f"⚠️ Stats endpoint error: {e}")
        # Graceful fallback if DB is busy
        return {"scans_24h": "---", "scans_total": "---", "status": "OFFLINE"}


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

    # 5. SAVE TO CACHE (Canonical URL)
    # Save using the stable canonical URL as key
    services.save_to_cache(payload.url, result.model_dump(), result.ani_score)

    # 6. LOG NEW SCAN EVENT (Background - the Firehose)
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
