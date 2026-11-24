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

### V5.7 - Position vs Technique (Opinion Leniency Fix)
**Directive:** Opinion pieces may argue a side, but spin techniques inside them are not excused.

**Why:** The old rule ("IF OPINION: Leniency on bias (60-80 unless false claims)") acted as a score floor. Partisan and state-media pieces got classified as opinion and landed in the 35-55 range instead of being scored on the markers they triggered.

**Implementation:**
- Advocacy, a stated thesis and first-person voice carry no deduction
- All 24 markers in the author's voice are deducted at full rate; Score Ceilings, Red Lines and the Weakest Link Rule apply as for news
- No 60-80 floor: clean opinion can score 80+, spin-loaded opinion can score below 40
- Opinion must be earned: text formatted as news is classified as NEWS

### V5.8 - Stacking Rule
**Directive:** Score bands are ceilings, never floors.

**Why:** "4+ tactics = 40-59" meant an article with 7 tactics in the author's voice still scored about 40 unless a Red Line fired.

**Implementation:**
- 4-5 tactics = 40-59; 6-7 tactics = 25-39; 8+ tactics = below 25
- Quote Shield still applies; each distinct tactic counts once

### V5.9 - Itemized Ledger (Rules Applied in Code)
**Directive:** The model judges each of the 24 markers; the code applies the scoring rules.

**Why:** In testing, the model's own scores broke the prompt's rules on 8 of 10 articles (band caps, Weakest Link, verdict key). The code's verdict mapping (<=30/<=50/<=70/<=85) also differed from the prompt's VERDICT KEY, and the style-only path skipped the Weakest Link Rule.

**Implementation:**
- Model returns `nci_ledger`: one row per marker 1-24 with `hit`, `voice` (author/quoted), an exact `quote` (25 words max), and `target` (subject/object) for High-Arousal Loading
- `rulebook.py` keeps a hit only if its quote appears verbatim in the article, drops quoted-voice hits (Quote Shield) and object-target arousal hits (Target Rule)
- Code computes vectors, final score and verdict: deductions 15 standard / 20 cold (top of stated ranges), vector caps, Score Ceilings (75 / 65), Red Lines, full consensus cap, stacking bands as ceilings, Weakest Link (+5), prompt VERDICT KEY
- Same rules on the Tavily path and the style-only path; response gains an optional `checklist` (marker names only, no NCI numbers)
- Falls back to the old scoring if the ledger is missing; `max_tokens` raised 2000 -> 4000
- Tests: `aegis-backend/test_rulebook.py`

### V5.9r4 - NCI Sheet Evidence
**Directive:** Run every article through the full NCI Engineered Reality sheet (20 items), not only the 24 markers.

**Why:** The 24 markers cover about 12 of the sheet's 20 items. Eight were never checked: Timing, Uniform Messaging, Overuse of Novelty, Financial/Political Gain, Emotional Repetition, Manufactured Outrage, Rapid Behavior Shifts, Historical Parallels.

**Implementation:**
- Model returns `nci_sheet`: 8 rows of {item, status, quote}; `rulebook.apply_sheet` verifies each quote verbatim
- Status: present (quote verified) / absent / needs_search / unverified (claimed without a verbatim quote)
- Timing, Uniform Messaging, Financial/Political Gain and Rapid Behavior Shifts can't be judged from one article: they stay `needs_search` on the style-only path; on the Tavily path the model may quote the search results, and the quote is verified against them
- **Evidence only:** the sheet never changes `ani_score`, caps, deductions or verdict. Returned as `sheet_evidence` on the response

### V5.9r5 - Single-Tactic Rule + Same Article, Same Score
**Directive:** One loaded phrase must not drag a straight story to 64, and the same article must get the same score on every scan.

**Why:** On the Nov 2026 held-out set, one counted High-Arousal phrase in an AP story capped its vector at 59, so Weakest Link made the final 64 (a false alarm). Reruns of the same article also moved by up to 9 points, and the URL cache expires after 12 hours.

**Implementation:**
- `rulebook.py`: when only ONE tactic counts, the vector caps (#3, #4, #14, #16) and the 75 ceiling don't apply; the 1-3 tactic band (max 79) and Red Lines still do. Two or more tactics: rules unchanged. Prompt text updated to match
- `services.py` content cache: key = sha256 of normalized title + text plus `ENGINE_VERSION`, stored in the existing `scan_cache` table as `url_hash = "text:<version>:<hash>"` (no schema change), no TTL; error results never cached. `main.py` checks it before calling Grok
- Style-only path temperature 0.2 -> 0.0 (main path was already 0.0)
- Bump `ENGINE_VERSION` in `engine.py` on any prompt or rulebook change, so old cached scores aren't served for a new version
- Note: `DELETE /v1/cache/clear` with no URL wipes the whole table, content entries included
- Tests: `aegis-backend/test_rulebook.py`, `aegis-backend/test_content_cache.py`

### V5.10 - High-Arousal Word List
**Directive:** The same article must get the same High-Arousal (#14) result every time, judged only on the journalist's own words.

**Why:** In the V5.9r5 test, 4 of 4 reruns scored differently, and #14 caused 3 of those flips (an AP story went 79 -> 100 between runs on "ran aground"). The model's #14 call was the biggest source of drift.

**Implementation:**
- `aegis-backend/arousal.py`: a fixed list of emotive words that straight wire copy avoids (horror/disgust, contempt, hype, headline attack verbs, pejorative labels). Whole-word, case-insensitive match
- Quote Shield in code: text inside double quotes, curly quotes or single-quoted phrases is blanked before matching; apostrophes are left alone
- Each hit returns the sentence it sits in as the evidence quote
- `rulebook.py` uses the code result for #14 and ignores the model's #14 row. Commercial content keeps Target Rule object leniency (hits shown as `object`, not counted)
- **V5.9r5 single-tactic rule withdrawn.** It existed so one loaded phrase couldn't drag straight news to 64; with the word list no straight article in the test sets trips #14, and the rule let a one-tactic Sputnik story score 79. Prompt text reverted to match
- `ENGINE_VERSION` = "5.10", so content-cache entries from 5.9r5 aren't reused
- Tested with zero model calls by rescoring 67 saved ledgers on 28 articles: no #14 hit on any of the 9 straight articles; same-article rerun pairs that differ went from 8 of 9 to 5 of 9 (the rest come from other markers)
- Tests: `aegis-backend/test_arousal.py` plus updated `test_rulebook.py`
- Limitation: the list only catches the words on it. The model's analysis prose may still mention High-Arousal language the list doesn't score

### V5.10.1 - Word List Fix (Nov 24, 2026)
**Why:** On a new held-out set of 8 articles (Nov 21-23: 4 AP/Reuters wire stories; RT, Gateway Pundit, Global Times, Common Dreams), an AP travel story hit the list on "Wicked weather on both coasts" and dropped to 64.

**Change:** "wicked" removed from the list (it is a common weather/slang idiom, not loaded language in wire copy). `ENGINE_VERSION` = "5.10.1".

**Held-out result (20 calls, Claude Sonnet standing in for Grok):**
- Straight news: 4 of 4 wire stories 100 after the fix (plain Claude 88-93)
- Spin: RT 54, Global Times 54, Gateway Pundit 70, Common Dreams 75 (plain Claude 30, 30, 58, 28)
- Gap (straight minus spin): 32 vs plain Claude 53, so plain Claude still ranks spin better
- Reruns: 3 of 4 identical; Gateway Pundit went 70 -> 100 (the model found 2 markers once, none the second time)
- Cause of the misses: the list doesn't hold the loaded phrases these stories used ("scandal-plagued", "dangerously deteriorating"); the model flagged them, but V5.10 ignores the model's #14. Counting the model's #14 again brings back false alarms on older sets, so it was not adopted

### V5.11 - Every Rule Answered, Score From Code Only (Nov 24, 2026)
**Why (owner's rules):** Rule 1, every article must run through all the rules. Rule 2, Anie cannot guess; the score must follow from the rules.

**Change:**
- `rulebook._read_ledger` returns nothing unless all 24 markers have a yes/no answer. A missing or malformed row is no longer read as "clear"
- `engine.analyze_text` scores only from `apply_rulebook`. The model's own `ani_score`, vector scores, min-vector check and consistency boost are no longer used on either path
- An incomplete ledger returns verdict "Analysis Incomplete" with no score, instead of falling back to the model's number
- The result reports `rules_checked` (always 24) and the full 24-row checklist with each answer and quote
- `ENGINE_VERSION` = "5.11"; prompt text unchanged
- Tests: 3 new in `test_rulebook.py` (23 rows gives no score, a non yes/no answer gives no score, the model's number is ignored)

**Determinism test (8 held-out articles x 3 runs, Claude Sonnet standing in for Grok, which can't be set to temperature 0):**
- Rule coverage: 24 of 24 answered on all 24 runs
- Same answers give the same score every time (code only)
- 6 of 8 articles scored identically on all 3 runs
- 4 of 192 rule answers changed between runs: #1 Source Amnesia twice, #22 Agency Deletion once, #7 In-Group/Out-Group once
- Gateway Pundit went 70 / 100 / 79 and Common Dreams 75 / 100 / 100 because of those flips
- Production Grok runs at temperature 0 and caches by text hash, so a repeat scan of the same text returns the same result

### V5.12 - Rules 1, 7 and 22 Checked in Code (Nov 24, 2026) [WITHDRAWN in V5.13]
**Why:** In the V5.11 test these were the only rules whose model answers changed between runs (4 of 192). The owner asked for them to become code checks.

**Change:**
- New `aegis-backend/rule_checks.py`: fixed phrase tests written from each rule's definition, with the Quote Shield. The model's rows for #1, #7 and #22 are ignored, as with #14
  - #1 Source Amnesia: unnamed experts, analysts or studies making a claim ("experts say", "studies show", "it is widely believed"), unless the same sentence names the source ("experts at", "according to", a named journal, university or institute)
  - #7 In-Group/Out-Group: pejorative or monolith group labels ("Democrat-led", "radical left", "the left's", "globalists", "Trump regime", "Kyiv regime"). Descriptive wire terms such as "far-right" and "Republican-led" are not on the list
  - #22 Agency Deletion: passives that hide the actor ("mistakes were made", "questions have been raised", "it was decided"), unless "by" names the actor
- `arousal.find_in_narration` is the shared quote-shielded finder for #14 and the three new checks
- `ENGINE_VERSION` = "5.12"
- Tests: `aegis-backend/test_rule_checks.py` (6) plus 2 in `test_rulebook.py`; fixtures no longer rely on model hits for #1 or #7

**Rescore of every saved run (no model calls, `v512-rescore.txt` in the test folder):**
- Nov 21-23 set, 3 runs each: 8 of 8 articles now score the same on all 3 runs (was 6 of 8)
- Wire stories: no #1, #7 or #22 hit on any of the 13 wire articles in the saved sets
- Gateway Pundit and Common Dreams now score 100 on every run: their flagged phrasing ("federal officials are warning", "was reportedly canceled") is not on the lists
- Limitation: a phrase test only catches the wording on its list, so stable is not the same as complete

### V5.13 - Same Article, Same Answer, Through the Cache (Nov 24, 2026)
**Why:** The owner rejected word lists for judging news (V5.12), and asked for the best architectural option for Rule 2 (no guessing, same result every time).

**Decision:** determinism comes from the system, not from turning judgment rules into phrase tests.
- Code alone computes the score from the 24 answers, and a missing answer means no score (V5.11, kept)
- The content cache keys each result on the normalized title and text plus `ENGINE_VERSION`, with no expiry, so the same article text always returns the same stored result
- #1, #7 and #22 go back to the model's yes/no with a verbatim quote that code verifies (V5.12 lists withdrawn)
- #14 keeps the V5.10 word list for now (see below)

**Cache fixes:**
- "Analysis Incomplete" results (a skipped rule) are no longer stored in either cache; before, they were stored forever in the content cache
- The URL cache now stores the engine version with each result and treats an entry from another version as a miss, so a rule change takes effect at once instead of up to 12 hours later
- Tests: 2 new in `test_content_cache.py`

**Grammar parser tested and not adopted:** a pinned spaCy parser (spaCy 3.8.7, en_core_web_sm 3.8.0) found unnamed speakers for #1 ("officials said", "experts say") and passives with no actor for #22. On 10 new articles from outside the test sets, and then on the saved test sets, it flagged AP wire stories as often as partisan ones: AP routinely writes "officials said" or "attorneys contend" after naming those people earlier in the story, and the parser can't see that. It also can't tell a reporting verb ("say") from other verbs that take a clause ("agree to"). The experiment code is kept outside the repo with the test files.

**#14 lexicon check:** the NRC VAD arousal lexicon forbids redistribution and commercial use without a license. A CC BY 4.0 copy of the Warriner et al. (2013) arousal norms exists, but the original terms weren't confirmed. Neither was adopted.

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
