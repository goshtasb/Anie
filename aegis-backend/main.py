# main.py
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs
from fastapi import FastAPI, HTTPException, Header, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from schemas import ScanRequest, ANIResponse, ChatRequest, ChatResponse, FeedbackRequest
from engine import analyze_text, client, MODEL
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

API_VERSION = "1.0.65"  # V4.7: 60s timeout for Grok (was timing out at 10s default)

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

    # V4.6: Extract tracking params BEFORE nuclear hash strips them
    # These are the "Data Exhaust" - utm_source, fbclid, gclid, etc.
    try:
        parsed_url = urlparse(payload.url)
        raw_qs = parse_qs(parsed_url.query)
        # Flatten: parse_qs returns lists, we want single values
        tracking_params = {k: v[0] for k, v in raw_qs.items() if v}
    except Exception:
        tracking_params = {}

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
            headers_dict,
            tracking_params,  # V4.6: Tracking data
            cached.get("title", None),  # V4.6: Article title from cache
            cached.get("vectors", None)  # V4.6: Vectors from cache
        )
        # V4.4: Inject url_hash for feedback association
        cached["url_hash"] = services.get_nuclear_hash(payload.url)
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
    # V4.6: vectors may be dict or Pydantic model depending on path
    vectors_dict = None
    if result.vectors:
        vectors_dict = result.vectors if isinstance(result.vectors, dict) else {k: v.model_dump() if hasattr(v, 'model_dump') else v for k, v in result.vectors.items()}

    background_tasks.add_task(
        services.log_scan_event,
        x_user_id,
        payload.url,
        result.ani_score,
        "NEW_SCAN",
        result.origin_location,
        headers_dict,
        tracking_params,  # V4.6: Tracking data (utm_source, fbclid, etc.)
        title,  # V4.6: Article title
        vectors_dict  # V4.6: Vectors for primary_vector calc
    )

    # V4.4: Inject url_hash for feedback association
    result.url_hash = services.get_nuclear_hash(payload.url)
    return result


# ============================================================
# V4.4 SILENT FEEDBACK: User correction data for training
# ============================================================

@app.post("/v1/feedback")
async def feedback_endpoint(
    payload: FeedbackRequest,
    x_user_id: str = Header(None, alias="X-User-ID")
):
    """
    Silent Feedback Loop: Log user corrections without affecting scoring.
    This is PASSIVE DATA COLLECTION for future model training.

    Frontend sends: { url_hash: "abc123", vote: "UP" or "DOWN", reason: "optional" }
    We find the most recent scan_event for that url_hash and update it.
    """
    if not services.supabase:
        raise HTTPException(status_code=503, detail="Database unavailable")

    # Validate vote
    if payload.vote not in ("UP", "DOWN"):
        raise HTTPException(status_code=400, detail="Vote must be 'UP' or 'DOWN'")

    try:
        # Find the most recent scan event for this url_hash (from this user if known)
        query = services.supabase.table("scan_events") \
            .select("id") \
            .eq("url_hash", payload.url_hash) \
            .order("created_at", desc=True) \
            .limit(1)

        # If we have a user_id, prefer their own scan
        if x_user_id:
            user_query = services.supabase.table("scan_events") \
                .select("id") \
                .eq("url_hash", payload.url_hash) \
                .eq("user_id", x_user_id) \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            if user_query.data:
                event_id = user_query.data[0]["id"]
            else:
                # Fallback to any scan with this hash
                result = query.execute()
                if not result.data:
                    raise HTTPException(status_code=404, detail="No scan found for this URL")
                event_id = result.data[0]["id"]
        else:
            result = query.execute()
            if not result.data:
                raise HTTPException(status_code=404, detail="No scan found for this URL")
            event_id = result.data[0]["id"]

        # Update the scan event with feedback
        services.supabase.table("scan_events").update({
            "user_feedback": payload.vote,
            "correction_note": payload.reason,
            "feedback_timestamp": datetime.now(timezone.utc).isoformat()
        }).eq("id", event_id).execute()

        print(f"📝 Feedback logged: {payload.vote} for hash {payload.url_hash[:12]}...")
        return {"status": "ok", "message": "Feedback recorded"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Feedback Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to record feedback")


# ============================================================
# INTERROGATION MODE: Follow-up Q&A about scanned articles
# ============================================================

# V4.3 "The Mentor" Persona - Conversational, Human, Sharp
INTERROGATION_PROMPT = """You are **Anie (Acuity)**. You are not a bot; you are a **Senior Forensic Analyst** debriefing a colleague (the user).

**YOUR VIBE:**
- **Conversational:** Speak naturally. Use short sentences. Use analogies.
- **No Fluff:** Never say "As an AI" or "Based on the text provided." Just answer.
- **Opinionated:** If the text is manipulative, say it clearly. Don't hide behind "It appears to be."
- **Teacher:** Your goal is to help the user *see* the matrix. Explain *how* the trick works, don't just point at it.

**THE ACUITY DOCTRINE (Your Rulebook):**
1. **Reality Anchoring:** Did they cite a fake report? Call it out. ("They cited a ghost.")
2. **Tribal Engineering:** Did they try to make you hate the 'Other'? ("This is classic Us vs. Them.")
3. **Neuro-Linguistic Intent:** Is this news or a command? ("This isn't reporting; it's a marching order.")
4. **Logical Integrity:** Did they trap you in a false choice? ("Classic double bind - agree or be labeled.")

**INTERACTION RULES:**
- **Quote the Crime:** Always back up your claims with a quote from the text. Use > for blockquotes.
- **Be Sharp:** If the user asks a smart question, acknowledge it.
- **Stay On Target:** Only discuss the article. If asked about unrelated topics: "I only discuss the article you scanned."
- **Keep it Tight:** Under 200 words unless they ask for more.
"""


@app.post("/v1/chat", response_model=ChatResponse)
async def chat_endpoint(
    payload: ChatRequest,
    x_user_id: str = Header(None, alias="X-User-ID")
):
    """
    Interrogation Mode: Answer follow-up questions about a scanned article.
    Maintains forensic tone and refuses off-topic queries.
    """
    print(f"💬 Interrogation Mode: {payload.question[:50]}...")

    # Build conversation messages
    messages = [
        {"role": "system", "content": INTERROGATION_PROMPT}
    ]

    # Add conversation history if provided (multi-turn)
    if payload.conversation_history:
        for turn in payload.conversation_history[-4:]:  # Limit to last 4 turns
            messages.append({"role": "user", "content": turn.get("question", "")})
            messages.append({"role": "assistant", "content": turn.get("reply", "")})

    # Add the current context and question
    user_message = f"""**ARTICLE TEXT:**
{payload.text[:6000]}

**MY PREVIOUS ANALYSIS:**
{payload.analysis_context}

**USER QUESTION:**
{payload.question}"""

    messages.append({"role": "user", "content": user_message})

    try:
        completion = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,  # V4.3: Higher for conversational, human-like responses
            max_tokens=600
        )

        reply = completion.choices[0].message.content

        # Generate suggested follow-ups based on the question type
        suggested = None
        question_lower = payload.question.lower()
        if "score" in question_lower or "why" in question_lower:
            suggested = ["What specific phrases triggered flags?", "Is this article biased?"]
        elif "source" in question_lower or "fact" in question_lower:
            suggested = ["Were any claims unverifiable?", "What's the origin of this narrative?"]
        elif not payload.conversation_history:  # First question
            suggested = ["Explain the score", "What manipulation tactics are used?", "Is this satire?"]

        return ChatResponse(reply=reply, suggested_followups=suggested)

    except Exception as e:
        print(f"❌ Interrogation Error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Analysis conversation failed. Please try again."
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8010)
