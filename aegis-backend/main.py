# main.py
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Header, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from schemas import ScanRequest, ANIResponse, ChatRequest, ChatResponse
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

API_VERSION = "1.0.60"  # V4.3 Mentor: Conversational chat persona + temp 0.7

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
