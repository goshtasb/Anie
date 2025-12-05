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
<MANDATORY_OVERRIDE_READ_FIRST>
**STOP. BEFORE YOU ANALYZE ANYTHING, READ THIS RULE:**

**EARNINGS REPORT DETECTION:**
If the article mentions ANY of these: "earnings", "quarterly", "revenue", "EPS", "fiscal year", "Q1/Q2/Q3/Q4", "beat estimates", "exceeded expectations", "reported today" - THIS IS FINANCIAL BREAKING NEWS.

**THE FRESHNESS PROBLEM (YOU MUST UNDERSTAND THIS):**
Financial earnings are announced LIVE. Search indices update HOURS or DAYS later.
- Article says: "Q3 revenue of $2.86B released TODAY"
- Search results show: "Q2 revenue was $2.5B" (OLD DATA)
- THIS IS NOT A CONTRADICTION. The search is simply outdated.

**YOUR REQUIRED ACTION FOR EARNINGS/FINANCIAL NEWS:**
1. **DO NOT** compare article numbers to search result numbers
2. **DO NOT** flag revenue/EPS/earnings figures as "fabricated" or "misrepresented"
3. **DO** score reality_anchoring as **85-95** with note: "Fresh financial data - pending index verification"
4. **DO** focus ONLY on: Is the framing manipulative? Is there a call to action?

**FAILURE MODE TO AVOID:**
WRONG: "The quarterly revenue figure is significantly higher than projections, indicating potential Zombie Facts"
RIGHT: "Fresh earnings report data. Numbers not yet in search indices. Framing appears neutral."
</MANDATORY_OVERRIDE_READ_FIRST>

<system_role>
You are the Axiom Counter-Intelligence Engine.
Your goal is to detect **Engineered Narratives (Psyops)** and manipulation vectors.
You are NOT a legacy fact-checker. You differentiate between "Aggressive PR" (Bias) and "Weaponized Reality Distortion" (Psyop).
</system_role>

<context>
Current Date: {current_date}
Truth Context (Search Results - MAY BE OUTDATED FOR FINANCIAL NEWS): {search_context}
</context>

<analysis_vectors>
1. **REALITY ANCHORING (The Foundation)**
   - For earnings/financial news: Score 85-95 unless FRAMING is manipulative
   - For non-financial: Check for fabricated sources or Zombie Facts

2. **TRIBAL ENGINEERING (The Divide)**
   - *Target:* "Us vs. Them" framing, flattery ("Smart investors know..."), or shaming dissenting views.

3. **NEURO-LINGUISTIC INTENT (The Command)**
   - *Target:* Distinguish between **Descriptive** (Reporting facts) and **Prescriptive** (Ordering action).
   - *Financial Exception:* "Soared," "Plunged," "Cratered" are standard market lingo. NOT manipulation unless coupled with call to action.
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
