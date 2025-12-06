# engine.py - Aegis A.N.I. Engine V3.4 "Context-Aware" (Commercial Immunity)
import os
import json
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from openai import AsyncOpenAI
from schemas import ANIResponse, VectorScore, FactCheckVector
from dotenv import load_dotenv

load_dotenv()

# Initialize xAI Grok Client
xai_key = os.getenv("XAI_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")

if xai_key and not xai_key.startswith("xai-your"):
    client = AsyncOpenAI(
        api_key=xai_key,
        base_url="https://api.x.ai/v1"
    )
    MODEL = "grok-3-mini"
    print("🚀 Engine V3.1: xAI Grok-3 (Parallel Swarm)")
else:
    client = AsyncOpenAI(api_key=openai_key)
    MODEL = "gpt-4o-mini"
    print("🔄 Engine V3.0: OpenAI GPT-4o-mini (Fallback)")

# Initialize Tavily
tavily_client = None
if tavily_key and not tavily_key.startswith("tvly-your"):
    try:
        from tavily import TavilyClient
        tavily_client = TavilyClient(api_key=tavily_key)
        print("✅ Truth Layer V3.1: Parallel Swarm ACTIVE")
    except ImportError:
        print("⚠️ Truth Layer: tavily-python not installed")
else:
    print("⚠️ Truth Layer: DISABLED (No Tavily API key)")


def get_psyop_hunter_prompt(current_date: str, search_context: str) -> str:
    """Generate the Psyop Hunter V3.4 prompt - Context-Aware with Commercial Immunity."""
    return f"""
<system_role>
You are the Axiom Counter-Intelligence Engine.
Your goal is to analyze text for integrity, BUT you must first determine the **Content Type** to apply the correct scoring standard.
</system_role>

<step_1_classification>
**MANDATORY:** Before scoring, determine the Content Type:

1. **NEWS/JOURNALISM:** Factual reporting, breaking news, financial reports.
2. **OPINION/EDITORIAL:** Op-eds, blog posts, analysis with clear perspective.
3. **COMMERCIAL/MARKETING:** Product pages, sales letters, corporate "About Us" pages, landing pages.
4. **SATIRE:** Clearly humorous/fake (The Onion, Babylon Bee).
</step_1_classification>

<step_2_adaptive_scoring_rules>
**IF COMMERCIAL/MARKETING:**
- **Status:** COMMERCIAL IMMUNITY.
- **Tone:** IGNORE high-arousal words ("Revolutionary", "Amazing", "Protect yourself").
- **Base Score:** If normal product page, Score **90-100** (Organic Commercial).
- **The Only Flags:** Score low ONLY if:
  - **Fraud:** Fake testimonials, fabricated certifications
  - **False Scarcity:** "Only 3 left!" when unlimited stock exists
  - **Fabricated Social Proof:** "1 million users!" with no evidence

**IF NEWS/JOURNALISM:**
- Apply FULL psyop analysis (Reality Anchoring, Tribal Engineering, Neuro-Linguistic Intent).
- This is the PRIMARY target for manipulation detection.
- Legitimate factual reporting: Score 70-100.
- Opinion disguised as news: Score 40-70.
- Fabricated sources or manipulative framing: Score 0-40.

**IF OPINION/EDITORIAL:**
- **Expected:** Persuasive language, clear bias.
- **Base Score:** 60-80 (bias is not a crime).
- **Only flag if:** Presenting demonstrable falsehoods as fact.

**IF SATIRE:**
- **Status:** SATIRE IMMUNITY.
- **Score:** 85-100 (it's intentionally fake for humor).
</step_2_adaptive_scoring_rules>

<context>
Current Date: {current_date}
Truth Context (Search Results): {search_context}
</context>

<analysis_vectors>
**Apply these ONLY for NEWS/JOURNALISM content. For COMMERCIAL, skip to verdict.**

**1. REALITY ANCHORING (The Foundation) - Score 0-100**
- **0-30 (FABRICATED):** Made-up sources, non-existent studies
- **31-50 (MISLEADING):** Real facts weaponized with misleading framing
- **51-70 (MIXED):** Some verified, some unverifiable claims
- **71-85 (MOSTLY ACCURATE):** Generally accurate with minor issues
- **86-100 (VERIFIED):** Well-sourced, factually accurate

**2. TRIBAL ENGINEERING (The Divide) - Score 0-100**
- **0-30 (WEAPONIZED):** "They don't want you to know...", shaming dissenters
- **31-50 (STRONG BIAS):** Clear in-group/out-group framing
- **51-70 (MODERATE BIAS):** Some editorial slant
- **71-85 (MILD):** Minor partisan framing
- **86-100 (NEUTRAL):** No tribal manipulation

**3. NEURO-LINGUISTIC INTENT (The Command) - Score 0-100**
- **0-30 (COERCIVE):** Fear + urgent call to action
- **31-50 (MANIPULATIVE):** Emotional pressure with implied commands
- **51-70 (PERSUASIVE):** Clear agenda but no urgent commands
- **71-85 (EDITORIAL):** Some persuasive framing
- **86-100 (DESCRIPTIVE):** Pure reporting
</analysis_vectors>

<verdict_logic>
**FOR NEWS:** Final Score = MINIMUM of all vector scores.
**FOR COMMERCIAL:** Final Score = 90-100 unless fraud detected.
**FOR OPINION:** Final Score = 60-80 unless spreading demonstrable falsehoods.
**FOR SATIRE:** Final Score = 85-100.

**Verdict Labels:**
- **Organic (86-100):** Clean content for its type.
- **Light Spin (71-85):** Minor issues.
- **Moderate Spin (51-70):** Noticeable bias or framing.
- **High Manipulation (31-50):** Weaponized facts.
- **Engineered Narrative (0-30):** Fabricated or heavily manipulative.
</verdict_logic>

<output_schema>
Return valid JSON only:
{{
  "content_type": "One of: [commercial, news, opinion, satire]",
  "ani_score": INTEGER,
  "verdict": "One of: [Organic, Light Spin, Moderate Spin, High Manipulation, Engineered Narrative]",
  "summary": "One sentence explaining the classification and any concerns.",
  "vectors": {{
    "reality_anchoring": {{
      "score": INTEGER,
      "flags": ["EXACT QUOTE from text if problematic, else empty array"],
      "analysis": "Brief explanation"
    }},
    "tribal_engineering": {{
      "score": INTEGER,
      "flags": ["EXACT QUOTE if problematic, else empty array"],
      "analysis": "Brief explanation"
    }},
    "neuro_linguistic": {{
      "score": INTEGER,
      "flags": ["EXACT QUOTE if problematic, else empty array"],
      "analysis": "Brief explanation"
    }}
  }}
}}
</output_schema>

<examples>
**Nike Product Page Test:**
Content: "Just Do It. The Air Max is revolutionary. Engineered for champions."
Classification: COMMERCIAL
Score: 95 (Organic Commercial)
Reason: Normal marketing language. No fraud, no fake scarcity.

**Snake Oil Test:**
Content: "Miracle cure! FDA approved! 10,000 5-star reviews!"
Classification: COMMERCIAL
Score: 15 (Engineered Narrative)
Reason: Fabricated certifications (FDA doesn't "approve" supplements), fake social proof.

**Anie Landing Page Test:**
Content: "The truth has structure. Anie analyzes news for manipulation."
Classification: COMMERCIAL
Score: 92 (Organic Commercial)
Reason: Marketing a product. Persuasive but not fraudulent.
</examples>

<flags_instruction>
**CRITICAL FOR FLAGS:**
- The "flags" array MUST contain EXACT QUOTES copied directly from the article text
- Do NOT paraphrase - quote the actual problematic words
- If no exact problematic phrase exists, leave flags as empty array []
- For COMMERCIAL content, only flag if fraud/scarcity/fake-proof detected
</flags_instruction>
"""


SOURCE_HUNT_PROMPT = """
You are a Source Hunter for a Counter-Intelligence operation.

**YOUR MISSION:**
Identify claims that can be VERIFIED or DISPROVED. We need to check if the article's "foundation" is real.

**EXTRACT:**
1. Any organization + statistic cited (e.g., "USDA reported 12% drop")
2. Any implied timeframe ("this quarter", "recently", "same period last year")
3. Any quotes attributed to anonymous sources

**GENERATE SEARCH QUERIES:**
Create queries to verify if THESE SPECIFIC CLAIMS are backed by real documents.

**OUTPUT (JSON):**
{
  "citations": [
    {
      "claim": "The exact claim from the article",
      "source_cited": "Organization/Agency",
      "timeframe": "When this allegedly happened",
      "search_query": "Query to find the actual document/report"
    }
  ],
  "anonymous_sources": ["List any anonymous attributions"],
  "urgency_signals": ["Any 'act now' or 'time is running out' language"]
}
"""


MAX_TEXT_LENGTH = 10000


async def extract_sources(text: str, current_date: str) -> dict:
    """Extract sources and signals for psyop analysis."""
    try:
        completion = await client.chat.completions.create(
            model=MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SOURCE_HUNT_PROMPT},
                {"role": "user", "content": f"Current date: {current_date}\n\nExtract from:\n\n{text[:5000]}"}
            ],
            temperature=0.0,
            max_tokens=800
        )

        raw = completion.choices[0].message.content
        return json.loads(raw)

    except Exception as e:
        print(f"Source extraction error: {e}")
        return {"citations": [], "anonymous_sources": [], "urgency_signals": []}


# Thread pool for running sync Tavily calls in parallel
_executor = ThreadPoolExecutor(max_workers=3)


def _single_tavily_search(citation: dict) -> dict:
    """Execute a single Tavily search (runs in thread pool)."""
    query = citation.get("search_query", "")
    if not query or not tavily_client:
        return None

    source = citation.get("source_cited", "Unknown")
    print(f"🔍 Hunting: [{source}] {query[:60]}...")

    try:
        response = tavily_client.search(
            query=query,
            search_depth="basic",  # "basic" is 2x faster than "advanced"
            max_results=3,
            include_domains=["usda.gov", "fao.org", "reuters.com", "apnews.com",
                           "gov", "edu", "un.org", "who.int", "bbc.com"],
            include_answer=True
        )
        return {"citation": citation, "response": response}
    except Exception as e:
        print(f"Search error for [{source}]: {e}")
        return None


async def search_for_truth_context(extracted: dict) -> dict:
    """Search Tavily in PARALLEL to build Truth Context for comparison."""
    if not tavily_client:
        return {"results": [], "sources": []}

    citations = extracted.get("citations", [])
    if not citations:
        return {"results": [], "sources": []}

    try:
        # Run all searches in parallel using thread pool
        loop = asyncio.get_event_loop()
        search_tasks = [
            loop.run_in_executor(_executor, _single_tavily_search, citation)
            for citation in citations[:3]
        ]

        print(f"🚀 Parallel Swarm: Launching {len(search_tasks)} searches simultaneously...")
        search_results = await asyncio.gather(*search_tasks)

        # Process results
        results_text = []
        sources = []

        for result in search_results:
            if not result:
                continue

            citation = result["citation"]
            response = result["response"]

            result_block = f"\n=== VERIFYING: {citation.get('claim', citation.get('search_query', ''))} ===\n"
            result_block += f"Source Cited: {citation.get('source_cited', 'Unknown')}\n"
            result_block += f"Timeframe Claimed: {citation.get('timeframe', 'unspecified')}\n"

            if response.get("answer"):
                result_block += f"TRUTH: {response['answer']}\n"

            for r in response.get("results", [])[:3]:
                result_block += f"\nFound: {r.get('title', 'Unknown')}\n"
                result_block += f"  URL: {r.get('url', '')}\n"
                result_block += f"  Content: {r.get('content', '')[:300]}\n"
                if r.get("url"):
                    sources.append(r["url"])

            if not response.get("results"):
                result_block += "⚠️ NO SUPPORTING DOCUMENTS FOUND - Citation may be fabricated\n"

            results_text.append(result_block)

        # Add context about anonymous sources and urgency signals
        anon = extracted.get("anonymous_sources", [])
        if anon:
            results_text.append(f"\n=== ANONYMOUS SOURCES DETECTED ===\n{chr(10).join(anon)}")

        urgency = extracted.get("urgency_signals", [])
        if urgency:
            results_text.append(f"\n=== URGENCY SIGNALS DETECTED ===\n{chr(10).join(urgency)}")

        print(f"✅ Swarm complete: {len(results_text)} verification blocks")

        return {
            "results": results_text,
            "sources": list(set(sources))
        }

    except Exception as e:
        print(f"Truth search error: {e}")
        return {"results": [], "sources": []}


# Financial detection removed - let the AI analyze naturally without overrides


async def psyop_analysis(text: str, title: str, search_results: dict, current_date: str) -> dict:
    """Apply Psyop Hunter analysis - looking for INTENT, not just errors."""
    try:
        search_context = "\n".join(search_results.get("results", ["No search results available"]))

        prompt = f"""
**ARTICLE TITLE:** {title or "Untitled"}

**ARTICLE TEXT:**
{text[:8000]}

Analyze this article using the Psyop Hunter protocol. Focus on INTENT - what behavior is this trying to force?
Remember: A psyop can use TRUE facts to create a FALSE reality.
"""

        completion = await client.chat.completions.create(
            model=MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": get_psyop_hunter_prompt(current_date, search_context)},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=2000
        )

        raw = completion.choices[0].message.content
        return json.loads(raw)

    except Exception as e:
        print(f"Psyop analysis error: {e}")
        return None


async def analyze_text(text: str, title: str = None, url: str = None) -> ANIResponse:
    """
    Aegis V3.0 - Psyop Hunter Pipeline:
    1. Extract sources and manipulation signals
    2. Build Truth Context via search
    3. Analyze for INTENT (not just facts)
    4. Enforce minimum score rule
    """
    current_date = datetime.now().strftime("%B %d, %Y")

    try:
        # ============================================================
        # PHASE 1: Source & Signal Extraction
        # ============================================================
        if tavily_client:
            print(f"🎯 Psyop Hunter V3.1: Extracting sources and signals...")
            extracted = await extract_sources(text, current_date)

            citations = extracted.get("citations", [])
            anon_sources = extracted.get("anonymous_sources", [])
            print(f"🎯 Found {len(citations)} citations, {len(anon_sources)} anonymous sources")

            # ============================================================
            # PHASE 2: Truth Context Search (PARALLEL)
            # ============================================================
            search_results = await search_for_truth_context(extracted)

            # ============================================================
            # PHASE 3: Psyop Analysis (Intent Detection)
            # ============================================================
            print("⚖️ Analyzing for psychological manipulation intent...")
            analysis = await psyop_analysis(text, title, search_results, current_date)

            if analysis:
                # Extract vectors
                raw_vectors = analysis.get("vectors", {})
                vectors = {}

                vector_mapping = {
                    "reality_anchoring": "reality",
                    "tribal_engineering": "tribal",
                    "neuro_linguistic": "neuro"
                }

                vector_scores = []
                for api_key, ui_key in vector_mapping.items():
                    if api_key in raw_vectors:
                        v = raw_vectors[api_key]
                        score = v.get("score", 50)
                        vector_scores.append(score)
                        vectors[ui_key] = VectorScore(
                            score=score,
                            flags=v.get("flags", []),
                            analysis=v.get("analysis", "No analysis")
                        )

                # ENFORCE MINIMUM SCORE RULE (for NEWS content - catches bad articles)
                ai_score = analysis.get("ani_score", 50)
                min_vector = min(vector_scores) if vector_scores else 50
                avg_vector = sum(vector_scores) / len(vector_scores) if vector_scores else 50

                # Start with AI's score constrained by minimum vector
                final_score = min(ai_score, min_vector)

                # CONSISTENCY BOOST (The "Math Fix")
                # If vectors are all high (avg > 85) but AI gave a lower score,
                # boost the final score to match the vectors. This prevents
                # "100+100+100 = 95" confusion that erodes user trust.
                if avg_vector > final_score and min_vector >= 70:
                    final_score = int(avg_vector)
                    print(f"📈 Consistency Boost: Vectors avg {avg_vector:.0f} > AI {ai_score}, boosting to {final_score}")

                print(f"🔥 Psyop Hunter Result: AI={ai_score}, MinVector={min_vector}, AvgVector={avg_vector:.0f}, Final={final_score}")

                # Determine verdict based on final score
                if final_score <= 30:
                    verdict = "Engineered Narrative"
                elif final_score <= 50:
                    verdict = "High Manipulation"
                elif final_score <= 70:
                    verdict = "Moderate Spin"
                elif final_score <= 85:
                    verdict = "Light Spin"
                else:
                    verdict = "Organic Reporting"

                # Build fact_check response (for UI compatibility)
                fact_check = FactCheckVector(
                    score=raw_vectors.get("reality_anchoring", {}).get("score", 50),
                    claims_checked=[c.get("claim", "") for c in citations],
                    flags=raw_vectors.get("reality_anchoring", {}).get("flags", []),
                    sources=search_results.get("sources", []),
                    analysis=raw_vectors.get("reality_anchoring", {}).get("analysis", "")
                )

                return ANIResponse(
                    ani_score=final_score,
                    summary=analysis.get("summary", "Psyop Hunter analysis complete."),
                    verdict=verdict,
                    vectors=vectors,
                    fact_check=fact_check
                )

        # Fallback: No Tavily - style-only analysis
        print("⚠️ No Truth Layer - running style-only psyop analysis")
        return await _style_only_analysis(text, title, current_date)

    except Exception as e:
        print(f"Psyop Hunter Error: {e}")
        return _fallback_response(f"Analysis error: {str(e)}")


async def _style_only_analysis(text: str, title: str, current_date: str) -> ANIResponse:
    """Fallback analysis when Tavily unavailable - still checks for psyop patterns."""
    try:
        completion = await client.chat.completions.create(
            model=MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": get_psyop_hunter_prompt(current_date, "No search results available - analyze text patterns only")},
                {"role": "user", "content": f"Analyze for psyop patterns (no external verification available):\n\nTitle: {title}\n\n{text[:MAX_TEXT_LENGTH]}"}
            ],
            temperature=0.2,
            max_tokens=2000
        )

        data = json.loads(completion.choices[0].message.content)

        vectors = {}
        vector_mapping = {
            "reality_anchoring": "reality",
            "tribal_engineering": "tribal",
            "neuro_linguistic": "neuro"
        }

        for api_key, ui_key in vector_mapping.items():
            if api_key in data.get("vectors", {}):
                v = data["vectors"][api_key]
                vectors[ui_key] = VectorScore(
                    score=v.get("score", 50),
                    flags=v.get("flags", []),
                    analysis=v.get("analysis", "")
                )

        return ANIResponse(
            ani_score=data.get("ani_score", 50),
            summary=data.get("summary", "Style-only psyop analysis (no external verification)."),
            verdict=data.get("verdict", "Analysis Complete"),
            vectors=vectors,
            fact_check=None
        )

    except Exception as e:
        return _fallback_response(f"Style analysis error: {str(e)}")


def _fallback_response(error_msg: str) -> ANIResponse:
    """Return a safe fallback response when analysis fails."""
    return ANIResponse(
        ani_score=50,
        summary=f"Analysis could not be completed. {error_msg}",
        verdict="Analysis Error",
        vectors={
            "reality": VectorScore(score=50, flags=[], analysis="Analysis unavailable"),
            "tribal": VectorScore(score=50, flags=[], analysis="Analysis unavailable"),
            "neuro": VectorScore(score=50, flags=[], analysis="Analysis unavailable")
        },
        fact_check=None
    )
