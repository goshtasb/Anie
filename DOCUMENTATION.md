# Project Aegis / Acuity - Complete Technical Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Backend API](#backend-api)
4. [Analysis Engine](#analysis-engine)
5. [Frontend Clients](#frontend-clients)
6. [Database Schema](#database-schema)
7. [Synapse Directives History](#synapse-directives-history)
8. [Deployment](#deployment)
9. [API Reference](#api-reference)

---

## Project Overview

### What is Acuity (A.N.I.E.)?

Acuity (Acuity Narrative Integrity Engine, also known as A.N.I.E.) is an AI-powered forensic analysis platform that detects manipulation, bias, and psychological operations ("psyops") in news articles and web content.

**Mission:** Help users distinguish between organic journalism and engineered narratives by providing a 0-100 "Narrative Integrity Score" along with detailed forensic breakdowns.

### Core Concepts

1. **Narrative Integrity Score (0-100)**
   - 0-35: Engineered Narrative (Psyop)
   - 36-55: High Manipulation
   - 56-75: Moderate Spin
   - 76-100: Organic Reporting

2. **Four Analysis Vectors**
   - **Reality Anchoring:** Fact-checking, source verification, trend inversion detection
   - **Tribal Engineering:** In-group/out-group framing, dehumanization, identity manipulation
   - **Neuro-Linguistic Intent:** Hot psyops (fear/rage), cold psyops (inevitability framing)
   - **Logical Integrity:** Double binds, false dilemmas, strawman arguments

3. **Quote Attribution Protocol (V5.3)**
   - Distinguishes between "The Messenger" (journalist) and "The Message" (quoted subject)
   - Does NOT penalize articles for accurately quoting manipulative sources
   - Only penalizes when the journalist ENDORSES toxic framing in their own voice

### Technology Stack

| Component | Technology |
|-----------|------------|
| Backend API | Python FastAPI, deployed on Render |
| AI Engine | xAI Grok-4.1-fast-reasoning (2M context) |
| Truth Layer | Tavily API for real-time fact verification |
| Database | Supabase (PostgreSQL) |
| Web Scraper | Firecrawl (primary), Jina.ai (fallback) |
| Website | Static HTML/CSS/JS on Netlify |
| Mobile | React Native / Expo |
| Extension | Chrome Manifest V3 |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND CLIENTS                               │
├──────────────────┬─────────────────────┬────────────────────────────────┤
│   Chrome         │    iOS/Android      │         Website                │
│   Extension      │    Mobile App       │    (www.goanie.com)        │
│   (popup.html)   │   (React Native)    │      (index.html)              │
└────────┬─────────┴──────────┬──────────┴─────────────┬──────────────────┘
         │                    │                        │
         └────────────────────┼────────────────────────┘
                              │ HTTPS POST
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     BACKEND API (Render.com)                            │
│                  https://aegis-alpha.onrender.com                       │
├─────────────────────────────────────────────────────────────────────────┤
│  main.py                                                                │
│  ├── POST /v1/scan        → Analyze article                            │
│  ├── POST /v1/chat        → Interrogation Mode Q&A                     │
│  ├── POST /v1/feedback    → V4.4 Silent Feedback Loop                  │
│  ├── GET  /v1/stats       → Live ticker stats                          │
│  └── DELETE /v1/cache     → Debug: Clear cache                         │
├─────────────────────────────────────────────────────────────────────────┤
│  services.py              │  engine.py              │  scraper.py       │
│  - Cache management       │  - AI Analysis          │  - URL scraping   │
│  - Event logging          │  - Psyop detection      │  - Firecrawl      │
│  - Nuclear hash           │  - Vector scoring       │  - Jina.ai        │
└─────────┬─────────────────┴──────────┬──────────────┴──────────┬────────┘
          │                            │                         │
          ▼                            ▼                         ▼
┌─────────────────┐    ┌───────────────────────┐    ┌────────────────────┐
│   Supabase      │    │   xAI Grok API        │    │  Tavily API        │
│   PostgreSQL    │    │   (Analysis Engine)   │    │  (Truth Layer)     │
│                 │    │   grok-4-1-fast       │    │  Real-time search  │
│  - scan_cache   │    │   -reasoning          │    │  for fact-checking │
│  - scan_events  │    │                       │    │                    │
│  - guests       │    │   2M context window   │    │                    │
└─────────────────┘    └───────────────────────┘    └────────────────────┘
```

---

## Backend API

### File Structure

```
aegis-backend/
├── main.py           # FastAPI app, endpoints, CORS
├── engine.py         # AI analysis engine (Psyop Hunter)
├── schemas.py        # Pydantic models for request/response
├── services.py       # Supabase cache, event logging
├── scraper.py        # URL content extraction
├── requirements.txt  # Python dependencies
└── .env.example      # Environment variables template
```

### Key Files Explained

#### main.py (API Server)
Current version: `1.0.61`

**Endpoints:**
- `GET /` - Health check
- `POST /v1/scan` - Main analysis endpoint
- `POST /v1/chat` - Interrogation Mode (follow-up Q&A)
- `POST /v1/feedback` - V4.4 Silent Feedback
- `GET /v1/stats` - Live ticker statistics
- `DELETE /v1/cache/clear` - Debug endpoint

**Scan Flow:**
1. Check cache for existing analysis (Nuclear Hash lookup)
2. If cache miss, scrape article text (Firecrawl → Jina → Direct)
3. Run Grok AI analysis
4. Save to cache
5. Log scan event to `scan_events` table (background task)
6. Return `ANIResponse` with score, verdict, vectors

#### engine.py (AI Engine V5.3)

**The Psyop Hunter Protocol:**
- Uses a 400+ line system prompt defining 24 forensic markers
- Implements Quote Attribution Protocol (V5.3)
- Sanitizes output to remove internal codes (NCI Marker references)

**Key Functions:**
- `analyze_text(text, title, url)` - Main entry point
- `extract_sources(text)` - Find citations for verification
- `search_for_truth_context(extracted)` - Parallel Tavily searches
- `psyop_analysis(text, title, search_results)` - Grok AI analysis
- `sanitize_output(text)` - V5.6 Clean Room sanitizer

**AI Model:**
```python
MODEL = "grok-4-1-fast-reasoning"  # V6.0: 2M context window
```

#### services.py (Cache & Analytics)

**Nuclear Hash System:**
```python
def get_nuclear_hash(url: str) -> str:
    """
    Aggressive URL normalization for cache consistency.
    'https://www.CNN.com/story/?id=123&ref=twitter' → 'cnn.com/story'
    """
```

This ensures:
- Website scans (with `?cid=ios_app` params)
- Extension scans (canonical URLs)
- Mobile scans (shared links with tracking)
ALL resolve to the SAME cache key.

**Cache TTL:** 24 hours (stories evolve, search indices update)

**Event Logging (Data Exhaust):**
```python
def log_scan_event(user_id, url, score, action, origin_location, headers):
    """
    Fire-and-forget logger for the 'Firehose' table.
    Captures EVERY interaction for analytics/B2B data.
    """
```

#### scraper.py (Content Extraction)

**Fallback Chain:**
1. Firecrawl (Premium, best anti-bot bypass)
2. Jina.ai (Free, handles JS rendering)
3. Archive.today (for blocked domains)
4. Direct fetch with JSON-LD extraction

**Known Cloud-Blocked Domains:**
```python
CLOUD_BLOCKED_DOMAINS = [
    'cnn.com', 'bbc.com', 'reuters.com', 'apnews.com',
    'nbcnews.com', 'cbsnews.com', 'foxnews.com', ...
]
```

These domains return garbage HTML to cloud IPs, so we try Archive.today first.

---

## Analysis Engine

### The 24 Forensic Markers (NCI Checklist)

**Vector 1: Reality Anchoring (6 markers)**
1. Source Amnesia - "Experts say" without attribution
2. False Authority - Irrelevant credentials for claims
3. Time Distortion (Zombie Facts) - Outdated data as current
4. Contextual Omission - Missing "why" to weaponize "what"
5. False Consensus - "Everyone knows..."
6. **Trend Inversion (RED LINE)** - Claiming UP is DOWN

**Vector 2: Tribal Engineering (5 markers)**
7. In-Group/Out-Group Framing - "We" vs "They"
8. Moral Superiority - Policy as moral failing
9. Identity Fusion - Link self-worth to narrative
10. **Dehumanization (RED LINE)** - Disease/animal metaphors
11. Spiral of Silence - Dissent as shameful

**Vector 3: Neuro-Linguistic Intent (8 markers)**
12. Prescriptive Commands - "You must", "Wake up"
13. Artificial Urgency - "Before it's too late"
14. High-Arousal Loading - Inflammatory adjectives
15. Inevitability Framing (Cold Psyop) - "It will happen anyway"
16. Elite Mimicry - "Smart people already know"
17. Preemptive Neutralization - "No drama, no villains"
18. False Liberation - Loss framed as "freedom"
19. Pacing and Leading - Facts → Prescriptive claims

**Vector 4: Logical Integrity (5 markers)**
20. **Double Bind (RED LINE)** - Both choices favor manipulator
21. False Dilemma - Binary framing of complex issues
22. Agency Deletion - "Mistakes were made"
23. Strawman - Attacking distorted opponent argument
24. Red Herring - Irrelevant distractions

### Scoring Algorithm

```
Start at 100
- Deduct 10-15 points per manipulation tactic in JOURNALIST'S voice
- Deduct 15-20 points per Cold Psyop tactic

RED LINE CRASH (Score < 35):
- Dehumanization in journalist's voice
- Double Bind in journalist's voice
- Trend Inversion (confirmed fabrication)
- Full Consensus Engineering (all 3 cold psyop markers)

QUOTE SHIELD (V5.3):
- Toxic language INSIDE quotes = Score 85-95 (reporting on toxic subject)
- Journalist ENDORSES toxic quote = Score 30-50 (endorsement penalty)

WEAKEST LINK RULE:
- Final score MUST NOT exceed lowest Vector Score by more than 5 points
```

---

## Frontend Clients

### 1. Website (anie-site/)

**URL:** https://www.goanie.com

**Features:**
- URL input scanner
- Real-time loading messages
- Vector breakdown display
- Interrogation Mode (chat with Anie)
- V4.4 Feedback buttons (👍/👎)
- Live stats ticker

**Key Files:**
- `index.html` - Single page app
- `style.css` - Dark theme styling
- `privacy.html`, `terms.html` - Legal pages

### 2. Mobile App (anie-mobile/)

**Platform:** React Native / Expo

**Bundle ID:** `com.axiom.anie`

**Two Entry Points:**
1. **Context A:** User opens app → `MainDashboard.tsx`
2. **Context B:** User shares URL from Safari/Twitter → `ShareModal.tsx`

**Share Extension:**
```json
"plugins": [
  ["expo-share-intent", {
    "ios": {
      "activationRules": {
        "NSExtensionActivationSupportsWebURLWithMaxCount": 1,
        "NSExtensionActivationSupportsText": true
      }
    }
  }]
]
```

**Key Components:**
- `App.tsx` - Root navigator, share intent provider
- `ShareModal.tsx` - Scan modal with results, chat, feedback
- `MainDashboard.tsx` - URL input, history, about section
- `utils/api.ts` - API client functions
- `utils/storage.ts` - AsyncStorage for scan history
- `types/index.ts` - TypeScript interfaces, colors

### 3. Chrome Extension (aegis-extension-mvp/)

**Manifest Version:** 3

**Permissions:** activeTab, scripting, storage

**Files:**
- `manifest.json` - Extension configuration
- `popup.html` - Extension popup UI
- `popup.js` - Scan logic, text extraction
- `background.js` - Service worker

**How it works:**
1. User clicks extension icon on any webpage
2. Extension extracts article text via DOM scraping
3. Sends text + URL to `/v1/scan`
4. Displays forensic dossier in popup

---

## Database Schema

### Supabase Tables

#### 1. scan_cache
Stores analysis results to avoid re-analyzing the same URL.

```sql
CREATE TABLE public.scan_cache (
  id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
  url_hash text UNIQUE NOT NULL,  -- Nuclear hash (MD5)
  url text NOT NULL,              -- Original URL
  ani_score integer,              -- 0-100 score
  scan_data jsonb NOT NULL,       -- Full ANIResponse
  created_at timestamp with time zone DEFAULT now()
);
```

**TTL:** Entries older than 24 hours are deleted on next cache check.

#### 2. scan_events
Event ledger for analytics ("Firehose").

```sql
CREATE TABLE public.scan_events (
  id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id text DEFAULT 'anonymous',
  url text NOT NULL,
  url_hash text,                  -- V4.1: B2B aggregation key
  ani_score integer,
  action_type text,               -- 'NEW_SCAN' or 'CACHE_HIT'
  origin_location text,           -- Geopolitical origin
  geo_country text,               -- User's country (from Cloudflare)
  device_type text,               -- 'mobile', 'extension', 'web'
  meta jsonb,                     -- User agent, etc.
  created_at timestamp with time zone DEFAULT now(),

  -- V4.4 Feedback columns
  user_feedback text,             -- 'UP' or 'DOWN'
  correction_note text,           -- Optional reason
  feedback_timestamp timestamp with time zone
);
```

#### 3. guests (Future Use)
For device-based credits without authentication.

```sql
CREATE TABLE public.guests (
  id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
  device_id text UNIQUE NOT NULL,
  credits integer DEFAULT 5,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);
```

---

## Synapse Directives History

Synapse is the internal product management system that issues feature requests and architectural changes. Below is the chronological history of Synapse directives that shaped the codebase.

### V3.0 - Psyop Hunter Engine
**Directive:** Create a forensic analysis engine that detects psychological manipulation, not just factual errors.

**Implementation:**
- 24-marker NCI (Neural-Cognitive Intelligence) Checklist
- Four analysis vectors
- "Hot Psyops" (fear/rage) vs "Cold Psyops" (calm inevitability)

### V3.1 - Truth Layer (Parallel Swarm)
**Directive:** Cross-reference claims against live search indices.

**Implementation:**
- Tavily API integration
- Parallel search execution via ThreadPoolExecutor
- Source extraction and verification

### V4.0 - Data Exhaust (Event Ledger)
**Directive:** Create a "Firehose" table to capture every interaction for B2B analytics.

**Implementation:**
- `scan_events` table
- `log_scan_event()` background task
- Captures: user_id, url, score, action, geo, device

### V4.1 - Enterprise Data Hygiene
**Directive:** Store `url_hash` in scan_events for instant aggregation.

**Implementation:**
- Nuclear hash calculated and stored with each event
- Enables queries like "velocity by article" without text cleaning

### V4.3 - Interrogation Mode ("The Mentor")
**Directive:** Add conversational follow-up Q&A about scanned articles.

**Implementation:**
- `/v1/chat` endpoint
- Conversation history tracking
- Suggested follow-up questions
- "Senior Forensic Analyst" persona (not a bot)

### V4.4 - Silent Feedback Loop
**Directive:** Add thumbs up/down buttons for passive data collection.

**PRD (Product Requirements Document):**
```
1. After scan result, show two buttons: 👍 (UP) and 👎 (DOWN)
2. On click, POST to /v1/feedback with {url_hash, vote, reason?}
3. Backend finds most recent scan_event by url_hash and updates:
   - user_feedback: 'UP' or 'DOWN'
   - correction_note: optional reason
   - feedback_timestamp: when feedback was given
4. This is PASSIVE DATA COLLECTION for future ML training
5. Does NOT affect current scoring
```

**Implementation:**
- Added `FeedbackRequest` schema
- Added `url_hash` to `ANIResponse`
- Created `/v1/feedback` endpoint
- Added feedback UI to website, mobile, extension
- Added feedback columns to scan_events table

### V5.2 - Complexity vs Fabrication
**Directive:** Distinguish between FABRICATION (lying about direction) and COMPLEXITY (nuanced trends).

**Implementation:**
- "Just the Facts" Protocol for data-dense articles
- Data Density Reward (>80% citations = Score 90-100)
- Nuance Exception: Long-term trends with short-term reversals are NUANCE, not FABRICATION

### V5.3 - Quote Attribution Protocol
**Directive:** Distinguish between "The Messenger" (Journalist) and "The Message" (Subject).

**Implementation:**
- Quote Shield: Toxic language inside quotes = attribute to SPEAKER, not article
- Endorsement Check: Only penalize if journalist ADOPTS toxic framing
- "Reporting on manipulation is NOT manipulation"

### V5.4 - Score Ceiling Rule
**Directive:** Enforce absolute ceilings based on manipulation in journalist's voice.

**Implementation:**
- Score 80+ requires ZERO manipulation tactics in journalist's voice
- One tactic = max 75
- Two tactics = max 65

### V5.5/V5.6 - Clean Room Sanitizer
**Directive:** Strip ALL internal codes (NCI Marker references) from user-facing output.

**Implementation:**
- `sanitize_output()` function with 8 regex pattern groups
- Catches: "NCI Marker #13", "Marker #7", "#13 - Artificial Urgency", etc.

### V6.0 - Grok-4.1 Upgrade
**Directive:** Upgrade to xAI's latest reasoning model.

**Implementation:**
```python
MODEL = "grok-4-1-fast-reasoning"  # 2M context window
```

---

## Deployment

### Backend (Render.com)

**URL:** https://aegis-alpha.onrender.com

**Configuration:** `render.yaml`
```yaml
services:
  - type: web
    name: aegis-alpha
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:**
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase service role key
- `XAI_API_KEY` - xAI Grok API key
- `TAVILY_API_KEY` - Tavily search API key
- `FIRECRAWL_API_KEY` - Firecrawl scraping API key

### Website (Netlify)

**URL:** https://www.goanie.com

Static files deployed directly to Netlify CDN.

### Mobile (Expo)

**Build:**
```bash
cd anie-mobile
npx expo prebuild
npx expo run:ios  # or run:android
```

**Distribution:**
- iOS: TestFlight / App Store
- Android: Google Play (future)

### Chrome Extension

**Build:**
```bash
cd aegis-extension-mvp
zip -r extension.zip .
```

**Publish:** Chrome Web Store Developer Dashboard

---

## API Reference

### POST /v1/scan

Analyze an article for manipulation and bias.

**Request:**
```json
{
  "url": "https://example.com/article",
  "text": "",  // Optional: If empty, backend will scrape
  "title": "Optional Article Title"
}
```

**Response (ANIResponse):**
```json
{
  "ani_score": 72,
  "verdict": "Moderate Spin",
  "summary": "Detected High-Arousal Language targeting policy discussion.",
  "origin_location": "Washington, DC",
  "url_hash": "a1b2c3d4e5f6",
  "vectors": {
    "reality": {
      "score": 85,
      "flags": [],
      "analysis": "No manipulation tactics detected."
    },
    "tribal": {
      "score": 70,
      "flags": ["Democrat-led cities"],
      "analysis": "In-Group/Out-Group Framing detected..."
    },
    "neuro": {
      "score": 65,
      "flags": ["controversial", "outrage"],
      "analysis": "High-Arousal Language..."
    },
    "logic": {
      "score": 90,
      "flags": [],
      "analysis": "No logical fallacies detected."
    }
  },
  "fact_check": {
    "score": 85,
    "claims_checked": ["USDA reported 12% drop"],
    "sources": ["https://usda.gov/..."],
    "analysis": "..."
  }
}
```

### POST /v1/chat

Follow-up Q&A about a scanned article (Interrogation Mode).

**Request:**
```json
{
  "text": "Article text...",
  "analysis_context": "Score: 72/100. Moderate Spin...",
  "question": "Why is the tribal score low?",
  "conversation_history": [
    {"question": "Previous Q", "reply": "Previous A"}
  ]
}
```

**Response:**
```json
{
  "reply": "The tribal score is 70 because...",
  "suggested_followups": [
    "What phrases triggered the flag?",
    "Is this intentional manipulation?"
  ]
}
```

### POST /v1/feedback

Submit user feedback on scan accuracy (V4.4 Silent Feedback).

**Request:**
```json
{
  "url_hash": "a1b2c3d4e5f6",
  "vote": "DOWN",
  "reason": "Article is satire, not manipulation"
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Feedback recorded"
}
```

### GET /v1/stats

Get aggregate system statistics for live ticker.

**Response:**
```json
{
  "scans_24h": 127,
  "scans_total": 4892,
  "status": "OPERATIONAL"
}
```

---

## Environment Variables

Create a `.env` file in `aegis-backend/`:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# AI
XAI_API_KEY=xai-your-key

# Search (Truth Layer)
TAVILY_API_KEY=tvly-your-key

# Scraping
FIRECRAWL_API_KEY=fc-your-key
```

---

## Contact

- **Email:** musickong@gmail.com
- **Website:** https://www.goanie.com

---

*Documentation Version: 1.0 - December 2025*
*Last Updated: After V4.4 Silent Feedback implementation*
