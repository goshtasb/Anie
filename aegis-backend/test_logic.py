import os
import asyncio
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

SYSTEM_PROMPT = """
<system_role>
You are the Axiom Counter-Intelligence Engine.
Your goal is to detect **Engineered Narratives (Psyops)** and manipulation vectors.
You are NOT a legacy fact-checker. You differentiate between "Aggressive PR" (Bias) and "Weaponized Reality Distortion" (Psyop).
</system_role>

<context>
Current Date: {current_date}
Truth Context (Search Results): {search_context}
</context>

<critical_protocol_temporal_verification>
**THE "FRESHNESS" RULE (CRITICAL FOR FINANCIAL NEWS):**
Breaking news (especially Earnings Reports) appears in articles HOURS before it appears in search indices.
1. **Compare Dates:** Look at the dates in the `Truth Context`. Are they from *today* or *yesterday*?
2. **The "Absence of Evidence" Clause:** - IF the article claims "Q3 Earnings Released Today" (e.g., $2.86B)...
   - AND the Search Results show older data (Q2, Forecasts, or dates from last month)...
   - **THEN you must IGNORE the Search Context for those specific numbers.**
   - **DO NOT** flag the mismatch as "Fabricated." Assume the article has the latest data.
   - **ACTION:** Score `reality_anchoring` as **85-100** (Fresh Data), noting "New data pending verification" in the analysis.
</critical_protocol_temporal_verification>

<analysis_vectors>
1. **REALITY ANCHORING (The Foundation)**
   - *Target:* Fabricated sources, "Zombie Facts" (using 2022 data to prove a 2025 crisis), or citing reports that do not exist.
   - *Scoring:* - **0-30:** Explicit fabrication or Zombie Facts.
     - **85-100:** Fresh earnings data, verified facts, or plausible breaking news.

2. **TRIBAL ENGINEERING (The Divide)**
   - *Target:* "Us vs. Them" framing, flattery ("Smart investors know..."), or shaming dissenting views.
   - *Scoring:* Deduct points for moral superiority or forced tribal allegiance.

3. **NEURO-LINGUISTIC INTENT (The Command)**
   - *Target:* Distinguish between **Descriptive** (Reporting a crash) and **Prescriptive** (Ordering you to panic/sell).
   - *Financial Exception:* Market terminology like "Plunged," "Soared," or "Cratered" is standard industry lingo. DO NOT flag this as "Emotional Coercion" unless it is coupled with a call to action (e.g., "Sell everything now").
</analysis_vectors>

<output_schema>
Return valid JSON only:
{{
  "ani_score": INTEGER (0-100),
  "verdict": "String",
  "summary": "String",
  "vectors": {{
    "reality_anchoring": {{ "score": INTEGER, "analysis": "String" }},
    "tribal_engineering": {{ "score": INTEGER, "analysis": "String" }},
    "neuro_linguistic": {{ "score": INTEGER, "analysis": "String" }}
  }}
}}
</output_schema>
"""

CURRENT_DATE = "December 5, 2025"
STALE_SEARCH_CONTEXT = """
[August 29, 2025] Ulta Beauty Q2 revenue fell 1% to $2.5 billion.
[August 30, 2025] Analysts cut forecasts for Ulta ahead of Q3.
[October 15, 2025] Ulta CEO warns of slowing cosmetics demand.
"""
FRESH_ARTICLE_TEXT = """
ULTA BEAUTY SMASHES Q3 EARNINGS, SHARES SOAR
Dec 5, 2025 - Ulta Beauty reported Q3 revenue of $2.86 billion today, beating analyst estimates of $2.71 billion.
The stock surged 12% in after-hours trading. CEO Dave Kimbell noted that holiday demand has arrived early.
Despite the broader retail slowdown, Ulta's strategic pivot is working.
"""

async def run_test():
    print("🚀 Running Unit Test: V3.2 Freshness Protocol...")
    formatted_prompt = SYSTEM_PROMPT.format(
        current_date=CURRENT_DATE,
        search_context=STALE_SEARCH_CONTEXT
    )
    try:
        completion = await client.chat.completions.create(
            model="grok-3-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": formatted_prompt},
                {"role": "user", "content": f"ARTICLE TEXT:\n{FRESH_ARTICLE_TEXT}"}
            ],
            temperature=0.0
        )
        content = completion.choices[0].message.content
        data = json.loads(content)
        print("\n--- RESULTS ---")
        print(f"SCORE: {data['ani_score']}/100")
        print(f"VERDICT: {data['verdict']}")
        print(f"REALITY VECTOR: {data['vectors']['reality_anchoring']['score']}")
        print(f"ANALYSIS: {data['vectors']['reality_anchoring']['analysis']}")
        if data['ani_score'] >= 85:
            print("\n✅ TEST PASSED: Freshness Rule Active.")
        else:
            print("\n❌ TEST FAILED: Latency Gap punished as Fabrication.")
            print("Output dump:", content)
    except Exception as e:
        print(f"Test Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
