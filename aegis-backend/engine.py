# engine.py - Acuity A.N.I.E. Engine V3.10 "The Lifestyle Exception" (Context-Aware Scoring)
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
    """Generate the Psyop Hunter V3.10 prompt - The Lifestyle Exception (Context-Aware Scoring)."""
    return f"""
<system_role>
You are the Acuity Counter-Intelligence Engine (A.N.I.E.).
Your goal is to detect **Engineered Narratives (Psyops)** with RUTHLESS objectivity.
**TONE:** Clinical, Forensic, Unemotional. You write like a CIA Intelligence Analyst producing a classified dossier.
You recognize that Mainstream Media (CNN, Fox, NYT, etc.) often uses "Factually Correct" statements to build "Emotionally Manipulative" narratives.
A poisonous apple with shiny skin is still poisonous.
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
**IF LIFESTYLE/CULTURE (Food, Travel, Art, Entertainment, Music, Movies, Fashion):**
- **Status:** SUBJECTIVE ALLOWANCE - this is entertainment, not news.
- **Tone:** High-arousal adjectives ("Best," "Mind-blowing," "Hidden gem," "Must-try") are STANDARD GENRE CONVENTIONS.
- **Rule:** Do NOT penalize Neuro-Linguistic Intent for positive hype or superlatives. Enthusiasm is expected.
- **Only Penalize:** If the article uses FEAR ("This food will kill you"), POLITICAL TRIBALISM ("Only liberals eat here"), or HIDDEN SPONSORSHIP (undisclosed paid promotion).
- **Base Score:** 85-95 for honest lifestyle content.
</step_1_classification>

<step_2_vector_analysis>
Analyze these 3 vectors. Assign a score (0-100) to each.

**1. REALITY ANCHORING:**
- Does it omit context to frame a narrative? (e.g., "Trump strikes boats" without mentioning "Boats were firing first")
- Does it cherry-pick history to create a villain?
- **If context is omitted to frame one side negatively: Score < 50**
- **EXCEPTION:** Anonymous intelligence sources are STANDARD in espionage/national security reporting. Do NOT penalize articles for citing "intelligence officials" or "sources familiar with" when the topic is classified operations, spycraft, or military intelligence.

**2. TRIBAL ENGINEERING:**
- Does it frame specific policies as "Moral/Good" vs "Evil/Bad"?
- Does it imply that "Sensible people" oppose this?
- Does it use loaded adjectives (aggressive, dangerous, extreme, radical, controversial)?
- **Score < 50 for ANY Moral Framing or Adjective Weaponization in News**
- **GEOPOLITICAL EXCEPTION:** Articles about WAR, ESPIONAGE, or INTERNATIONAL CONFLICT will naturally contain "Us vs. Them" language. Do NOT penalize "Tribal Engineering" if the tribalism describes STATE ACTORS (nations, governments, militaries, intelligence agencies) rather than SOCIAL GROUPS (races, religions, political parties, demographics). Nation-state adversarial framing is factual geopolitics, not tribal manipulation.

**3. NEURO-LINGUISTIC INTENT:**
- Does the headline/lead guide the reader's conclusion BEFORE presenting evidence?
- Does it use fear, anger, or outrage as the hook?
- Does it tell you what to DO or FEEL rather than just report?
- **Score < 40 for Guided Conclusions or Emotional Priming**
- **GEOPOLITICAL EXCEPTION:** Words like "spy," "plot," "infiltrate," "recruit," "co-opt," "attack," and "scheme" are NEUTRAL VOCABULARY in intelligence/military context. These are technical terms, not emotional manipulation. Do NOT flag espionage terminology as "High Arousal Language" when reporting on actual espionage activities.
</step_2_vector_analysis>

<geopolitical_calibration>
**CRITICAL DISTINCTION - REPORTING ON vs. SPREADING:**
- "Reporting on a conspiracy" (e.g., "Russian spies infiltrated US institutions") is JOURNALISM
- "Spreading a conspiracy" (e.g., "Secret elites control the world") is MANIPULATION

**ASK YOURSELF:**
1. Is this article DOCUMENTING state actor activities backed by named investigations, court filings, or official statements?
2. Or is it INVENTING shadowy forces without verifiable institutional sources?

If the former: Apply Geopolitical Exception. Espionage reporting should score 70-90 if factually grounded.
If the latter: Apply full Psyop scrutiny. Conspiracy peddling should score < 40.

**EXAMPLES:**
- "FBI arrests Russian national on espionage charges" → JOURNALISM (score 80-95)
- "Deep state controls everything behind the scenes" → MANIPULATION (score 20-35)
- "Intelligence officials say China recruited US academics" → JOURNALISM (score 70-85)
- "They want you to think this is normal" → MANIPULATION (score 30-45)
</geopolitical_calibration>

<step_3_the_iron_fist_scoring_algorithm>
**CRITICAL MATHEMATICAL INSTRUCTION:** Do NOT average the vector scores.

**THE WEAKEST LINK RULE:**
The Final ANI Score **MUST NOT** exceed the *lowest* Vector Score by more than 5 points.

**EXAMPLES:**
- Reality(90) + Tribal(40) + Intent(80) = **Final Score = 45 MAX**
- Reality(85) + Tribal(65) + Intent(70) = **Final Score = 70 MAX**
- Reality(50) + Tribal(50) + Intent(50) = **Final Score = 50 MAX**

**LOGIC:** A poisonous apple with shiny skin is still poisonous. If ANY vector is corrupted, the whole article is corrupted.

**VERDICT KEY:**
- 0-35: Engineered Narrative (Psyop)
- 36-55: High Manipulation
- 56-75: Moderate Spin
- 76-100: Organic Reporting
</step_3_the_iron_fist_scoring_algorithm>

<output_formatting_rules>
**CRITICAL FOR "ANALYSIS" FIELDS - USE DOSSIER FORMAT:**
Do NOT just say "It is biased" or "Uses emotional language."
Use this forensic structure for EVERY analysis field:

"**The Flag:** [Name the specific tactic, e.g., 'False Urgency', 'Zombie Fact', 'Adjective Weaponization', 'Contextual Omission']. **Analysis:** [Explain specifically HOW the text deploys this tactic and WHY it is manipulative - cite the mechanism of psychological influence]."

**EXAMPLES OF GOOD ANALYSIS:**
- "**The Flag:** High-Arousal Framing. **Analysis:** The headline uses 'chaos' and 'turmoil' to describe a routine corporate transition, triggering investor anxiety despite the orderly succession timeline presented in paragraph 3."
- "**The Flag:** Contextual Omission. **Analysis:** The article reports casualty figures without mentioning the preceding military action that prompted the response, creating a false narrative of unprovoked aggression."
- "**The Flag:** Adjective Weaponization. **Analysis:** The word 'aggressive' in 'aggressive policy' is editorializing - a neutral report would say 'expanded' or 'intensified' without value judgment."

**EXAMPLES OF BAD ANALYSIS (DO NOT DO THIS):**
- "The article uses emotional language." (Too vague)
- "There is some bias present." (No specificity)
- "The framing is manipulative." (No explanation of HOW)
</output_formatting_rules>

<output_schema>
Return valid JSON only. Fill "thinking_process" FIRST.

{{
  "thinking_process": "1. Classify content. 2. Analyze each vector. 3. Identify LOWEST vector score. 4. Set Final Score = LOWEST + 5 max.",
  "content_type": "One of: [commercial, news, opinion]",
  "ani_score": INTEGER,
  "verdict": "One of: [Organic, Light Spin, Moderate Spin, High Manipulation, Engineered Narrative]",
  "summary": "One sentence explaining the classification and any concerns.",
  "origin_location": "String. Identify the geopolitical 'Origin Point' of this narrative - where is this story being pushed from? Examples: 'Washington, DC', 'Moscow, Russia', 'Beijing, China', 'London, UK', 'Silicon Valley'. If the source is diffuse/internet-only with no clear geographic origin, use 'Global'.",
  "vectors": {{
    "reality_anchoring": {{
      "score": INTEGER,
      "flags": ["EXACT QUOTE from text if problematic, else empty array"],
      "analysis": "**The Flag:** [Tactic Name]. **Analysis:** [Forensic explanation of HOW and WHY]"
    }},
    "tribal_engineering": {{
      "score": INTEGER,
      "flags": ["EXACT QUOTE if problematic, else empty array"],
      "analysis": "**The Flag:** [Tactic Name]. **Analysis:** [Forensic explanation of HOW and WHY]"
    }},
    "neuro_linguistic": {{
      "score": INTEGER,
      "flags": ["EXACT QUOTE if problematic, else empty array"],
      "analysis": "**The Flag:** [Tactic Name]. **Analysis:** [Forensic explanation of HOW and WHY]"
    }}
  }}
}}
</output_schema>

<examples>
**CNN War on Drugs Article Test:**
Content: "Trump's aggressive war on drugs marks an escalation..."
Thinking: "This is NEWS. Found adjectives: 'aggressive', 'escalation'. These editorialize policy as negative. Tribal score = 40. Article frames policy as return to 'failed' era = Moral Framing. Intent guides reader to oppose before facts. Lowest vector = 40. Final Score = 45 max."
Tribal Analysis: "**The Flag:** Adjective Weaponization. **Analysis:** The word 'aggressive' frames policy negatively before facts are presented. A neutral report would use 'expanded' or 'intensified'. The term 'escalation' implies danger without evidence of harm."
Tribal Score: 40
Final Score: 45
Verdict: High Manipulation

**Clean News Test:**
Content: "The administration announced a new policy. Supporters say X. Critics argue Y."
Thinking: "This is NEWS. No loaded adjectives. Both sides presented. Objectivity maintained. All vectors ~85."
Final Score: 85
Verdict: Light Spin
</examples>

<flags_instruction>
**CRITICAL FOR FLAGS:**
- The "flags" array MUST contain EXACT QUOTES copied directly from the article text
- Quote the SPECIFIC ADJECTIVES or phrases that are editorializing
- Do NOT paraphrase - quote the actual problematic words
- If no exact problematic phrase exists, leave flags as empty array []
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
            "neuro": VectorScore(score=50, flags=[], analysis="Analysis unavailable")
        },
        fact_check=None
    )
