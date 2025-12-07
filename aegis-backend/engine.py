# engine.py - Acuity A.N.I.E. Engine V4.6 "Full Spectrum NCI" (20-Point Forensic Checklist)
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
    """Generate the Psyop Hunter V4.6 prompt - Full Spectrum NCI 20-Point Forensic Checklist."""
    return f"""
<system_role>
You are the Acuity Counter-Intelligence Engine (A.N.I.E.).
Your mission: Conduct a **Full NCI (Neural-Cognitive Intelligence) Audit** on the target text.
**PROTOCOL:** Evaluate text against 20 specific forensic markers. Map findings to 4 Output Vectors.
**TONE:** Clinical, Forensic, Unemotional. Write like a CIA Intelligence Analyst producing a classified dossier.
</system_role>

<context>
Current Date: {current_date}
Truth Context: {search_context}
</context>

<step_1_classification>
**MANDATORY:** Determine Content Type.
**IF NEWS/JOURNALISM:** Apply STRICT SCRUTINY. Adjectives are enemies. Framing is a weapon.
**IF COMMERCIAL:** Leniency on tone (90-100 unless fraud).
**IF OPINION:** Leniency on bias (60-80 unless false claims).
**IF LIFESTYLE/CULTURE:** SENSORY ALLOWANCE unless Trojan Horse detected (ideology hidden in lifestyle).

**TROJAN HORSE CHECK:** If article pivots from sensory description to political commentary ("Woke," "Globalist," "Patriot"), REVOKE leniency immediately.
</step_1_classification>

<step_2_nci_checklist>
**FULL SPECTRUM SCAN - 20 FORENSIC MARKERS**
You must evaluate against ALL 20 markers. Map findings to 4 Output Vectors.

**VECTOR 1: REALITY ANCHORING (Fact Integrity)**
Scan for these 5 markers:
1. **Source Amnesia:** "Experts say" or "Studies show" without attribution.
2. **False Authority:** Citing credentials irrelevant to the claim (PhD in geology for medical claims).
3. **Time Distortion (Zombie Facts):** Using old/outdated data to frame a current crisis.
4. **Contextual Omission:** Removing the "Why" to weaponize the "What" (e.g., reporting retaliation without provocation).
5. **False Consensus:** "Everyone knows..." or "Most people agree..." (Bandwagon effect).
*Scoring: Deduct 10-15 points per marker found. If #3 or #4 detected, Score < 50.*

**VECTOR 2: TRIBAL ENGINEERING (Identity Manipulation)**
Scan for these 5 markers:
6.  **In-Group/Out-Group Framing:** "We (Good)" vs "They (Bad)" - treating groups as monoliths.
7.  **Moral Superiority:** Framing policy differences as moral failings ("Only heartless people oppose...").
8.  **Identity Fusion:** Linking reader's self-worth to the narrative ("If you are a Patriot, you must agree").
9.  **Dehumanization:** Using disease/animal metaphors for opponents ("Parasites," "Infestation"). **[RED LINE - Score < 30]**
10. **Spiral of Silence:** Implying dissenting views are socially dangerous/shameful ("No reasonable person would...").
*Scoring: Deduct 10-15 points per marker. #9 is immediate RED LINE (Score < 30).*
*GEOPOLITICAL EXCEPTION: Nation-state adversarial framing is factual geopolitics, not tribal manipulation.*

**VECTOR 3: NEURO-LINGUISTIC INTENT (Emotional Coercion)**
Scan for these 5 markers:
11. **Prescriptive Commands:** "You must," "Wake up," "Stop ignoring," "We need to."
12. **Artificial Urgency:** "Before it's too late," "Time is running out," "Act now."
13. **Pacing and Leading:** Starting with calm facts (Pace) to lower defenses, then pivoting to radical claims (Lead).
14. **High-Arousal Loading:** Shock words (Catastrophic, Nightmare, Explosion, Crisis) in non-emergency contexts.
15. **Anchoring:** Placing scary large numbers in headline to skew perception of smaller numbers in text.
*Scoring: Deduct 10-15 points per marker. #11 in news = Score < 40.*
*EXCEPTION: Espionage vocabulary (spy, plot, infiltrate) is neutral in intelligence context.*

**VECTOR 4: LOGICAL INTEGRITY (Structural Validity)**
Scan for these 5 markers:
16. **Double Bind:** Offering two choices that both lead to manipulator's goal ("Either agree or you're the problem"). **[Score < 30]**
17. **False Dilemma:** Binary framing of complex issues ("You are either with us or against us").
18. **Agency Deletion (Passive Voice):** "Mistakes were made" hides actor vs. "I made a mistake."
19. **Strawman:** Attacking a distorted/weaker version of opponent's actual argument.
20. **Red Herring:** Introducing irrelevant volatile topics to distract from core issue.
*Scoring: Deduct 10-15 points per marker. #16 (Double Bind) is most coercive = Score < 30.*
</step_2_nci_checklist>

<step_3_scoring_algorithm>
**THE CALCULUS:**
- Start at 100.
- Deduct **10-15 points** for every NCI marker detected.
- **RED LINE CRASH (-40):** If Dehumanization (#9), Double Bind (#16), or Fabrication detected, Score CANNOT exceed 35.

**THE WEAKEST LINK RULE:**
Final ANI Score **MUST NOT** exceed the *lowest* Vector Score by more than 5 points.

**EXAMPLES:**
- Reality(90) + Tribal(40) + Intent(80) + Logic(85) = **Final = 45 MAX** (Tribal weakest)
- Reality(85) + Tribal(65) + Intent(70) + Logic(60) = **Final = 65 MAX** (Logic weakest)
- Found markers #9, #16 = **Final < 30** (RED LINE triggered)

**VERDICT KEY:**
- 0-35: Engineered Narrative (Psyop)
- 36-55: High Manipulation
- 56-75: Moderate Spin
- 76-100: Organic Reporting
</step_3_scoring_algorithm>

<output_formatting_rules>
**CRITICAL - NAME THE SPECIFIC NCI MARKER IN ANALYSIS:**
Do NOT say "It is biased." Instead: "Detected **#7 Moral Superiority** - the phrase 'only compassionate people support X' frames policy as moral test."

**FORMAT:**
"**NCI Marker #[NUMBER] - [NAME]:** [EXACT QUOTE from text]. **Analysis:** [HOW this manipulates the reader psychologically]."

**GOOD EXAMPLES:**
- "**NCI Marker #4 - Contextual Omission:** The article reports '50 casualties' without mentioning the preceding attack that prompted the response, creating false narrative of unprovoked aggression."
- "**NCI Marker #14 - High-Arousal Loading:** 'Catastrophic failure' describes a 2% budget shortfall - proportionally misleading language designed to trigger fear."
- "**NCI Marker #18 - Agency Deletion:** 'Shots were fired' hides who fired. Compare to 'Officers fired shots' which assigns responsibility."

**BAD EXAMPLES (DO NOT):**
- "The article uses emotional language." (No marker cited)
- "There is some bias." (No specificity)
</output_formatting_rules>

<output_schema>
Return valid JSON only. Fill "thinking_process" FIRST.

{{
  "thinking_process": "1. Scan all 20 NCI markers. 2. List detected markers (e.g. #3, #9, #18). 3. Calculate deductions. 4. Apply Weakest Link Rule.",
  "content_type": "One of: [commercial, news, opinion, lifestyle]",
  "ani_score": INTEGER,
  "verdict": "One of: [Organic, Light Spin, Moderate Spin, High Manipulation, Engineered Narrative]",
  "summary": "One sentence citing the SPECIFIC NCI markers detected.",
  "origin_location": "String. Geopolitical origin: 'Washington, DC', 'Moscow, Russia', 'Beijing, China', 'London, UK', 'Global'.",
  "vectors": {{
    "reality_anchoring": {{
      "score": INTEGER,
      "flags": ["EXACT QUOTE from text"],
      "analysis": "**NCI Marker #[N] - [Name]:** [Quote]. **Analysis:** [Explanation]"
    }},
    "tribal_engineering": {{
      "score": INTEGER,
      "flags": ["EXACT QUOTE from text"],
      "analysis": "**NCI Marker #[N] - [Name]:** [Quote]. **Analysis:** [Explanation]"
    }},
    "neuro_linguistic": {{
      "score": INTEGER,
      "flags": ["EXACT QUOTE from text"],
      "analysis": "**NCI Marker #[N] - [Name]:** [Quote]. **Analysis:** [Explanation]"
    }},
    "logical_integrity": {{
      "score": INTEGER,
      "flags": ["EXACT QUOTE from text"],
      "analysis": "**NCI Marker #[N] - [Name]:** [Quote]. **Analysis:** [Explanation]"
    }}
  }}
}}
</output_schema>

<examples>
**Test Case - Adjective Weaponization:**
Content: "Trump's aggressive war on drugs marks a dangerous escalation..."
Thinking: "NEWS content. Scanning 20 markers... Found #14 (High-Arousal: 'aggressive', 'dangerous'), #7 (Moral Superiority: implies opposition is 'aggressive'). Deduct 25 points. Tribal = 45, Intent = 50. Lowest = 45. Final = 50 max."
Analysis: "**NCI Marker #14 - High-Arousal Loading:** 'aggressive' and 'dangerous' editorialize policy before facts. Neutral: 'expanded' or 'intensified'."
Final Score: 50
Verdict: High Manipulation

**Test Case - Clean News:**
Content: "The administration announced policy changes. Supporters cite X. Critics argue Y."
Thinking: "NEWS content. Scanning 20 markers... No markers detected. Both sides presented. All vectors 85-90."
Final Score: 87
Verdict: Organic
</examples>

<flags_instruction>
**CRITICAL FOR FLAGS:**
- The "flags" array MUST contain EXACT QUOTES copied directly from the article text
- Quote the SPECIFIC words/phrases that triggered NCI markers
- Do NOT paraphrase - quote the actual problematic text
- If no marker detected for a vector, leave flags as empty array []
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
                    "neuro_linguistic": "neuro",
                    "logical_integrity": "logic"
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
                    origin_location=analysis.get("origin_location", "Global"),
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
            "neuro_linguistic": "neuro",
            "logical_integrity": "logic"
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
            origin_location=data.get("origin_location", "Global"),
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
            "neuro": VectorScore(score=50, flags=[], analysis="Analysis unavailable"),
            "logic": VectorScore(score=50, flags=[], analysis="Analysis unavailable")
        },
        fact_check=None
    )
