# engine.py
import os
import json
from openai import AsyncOpenAI
from schemas import ANIResponse, VectorScore
from dotenv import load_dotenv

load_dotenv()

# Initialize xAI Grok Client (OpenAI-compatible API)
# Falls back to OpenAI if XAI_API_KEY not set
xai_key = os.getenv("XAI_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")

if xai_key and not xai_key.startswith("xai-your"):
    # Use Grok (xAI) - Primary
    client = AsyncOpenAI(
        api_key=xai_key,
        base_url="https://api.x.ai/v1"
    )
    MODEL = "grok-3-mini"  # Fast & cost-effective; use "grok-3" for highest quality
    print("🚀 Engine: xAI Grok-3 (Uncensored Mode)")
else:
    # Fallback to OpenAI
    client = AsyncOpenAI(api_key=openai_key)
    MODEL = "gpt-4o-mini"
    print("🔄 Engine: OpenAI GPT-4o-mini (Fallback)")

SYSTEM_PROMPT = """
**ROLE:**
You are the **Aegis Forensic Analyst**, a specialized linguistic engine designed to detect psychological manipulation, coercive phrasing, and structural bias in news media. You are NOT a fact-checker; you are a **Tactics-Checker**.

**OBJECTIVE:**
Analyze the provided news text and generate a **Forensic Dossier** in strict JSON format. You must quantify the "A.N.I. Score" (Aegis Narrative Integrity) from 0 to 100.
- **100** = Pure, neutral reporting of raw data (High Integrity).
- **0** = Highly engineered propaganda / psychological operation (Zero Integrity).

**ANALYSIS VECTORS (THE RUBRIC):**
You must analyze the text across these 4 specific vectors. For each, you must cite specific string matches (quotes) as evidence.

1. **AUTHORITY OVERLOAD ("The Trust-Me Trap")**
   - **Look for:** Vague attribution used to manufacture consensus without accountability.
   - **Flags:** "Experts say," "Sources familiar with the matter," "Intelligence officials," "People say," "Widely believed."
   - **Scoring:** High penalty for every anonymous source used to support a core claim.

2. **EMOTIONAL LOADING ("The Fear Index")**
   - **Look for:** High-arousal adjectives/adverbs designed to bypass critical thinking and trigger a fight-or-flight response.
   - **Flags:** "Catastrophic," "Horrifying," "Vile," "Evaporated," "Slammed," "Destroyed," "Nightmare."
   - **Scoring:** Calculate the density of emotive words. If >20% of adjectives are high-arousal, flag heavily.

3. **LOGICAL INTEGRITY ("The Fallacy Finder")**
   - **Look for:**
     - *False Dichotomy:* Presenting only two extreme options.
     - *Ad Hominem:* Attacking the person rather than the argument.
     - *Strawman:* Misrepresenting an opposing view to easily defeat it.
   - **Scoring:** Penalty for every logical fallacy found.

4. **HEADLINE DISSONANCE ("The Clickbait Gap")**
   - **Look for:** A gap between the Headline's claim and the Body's evidence.
   - **Flags:** Does the headline promise a "Crash" but the text shows a "Dip"? Does it promise "Proof" but deliver "Speculation"?

**OUTPUT SCHEMA (JSON ONLY):**
{
  "ani_score": INTEGER,
  "summary": "2 sentences explaining strictly WHY the score is low/high based on the vectors.",
  "verdict": "One of: [Clean Reporting, Moderate Spin, High Manipulation, Engineered Narrative]",
  "vectors": {
    "authority_overload": {
      "score": INTEGER (0-100, 100 is Clean),
      "flags": ["Exact quote 1", "Exact quote 2"],
      "analysis": "Specific explanation of the finding."
    },
    "emotional_loading": {
      "score": INTEGER,
      "flags": ["Exact quote 1", "Exact quote 2"],
      "analysis": "Specific explanation."
    },
    "logical_integrity": {
      "score": INTEGER,
      "flags": ["Exact quote 1", "Exact quote 2"],
      "analysis": "Specific explanation."
    },
    "headline_dissonance": {
      "score": INTEGER,
      "flags": ["Exact quote 1", "Exact quote 2"],
      "analysis": "Specific explanation."
    }
  }
}
"""

# Cost protection: Reduced from 12000 to 10000 for Grok's higher token costs
MAX_TEXT_LENGTH = 10000


async def analyze_text(text: str, title: str = None, url: str = None) -> ANIResponse:
    """
    Analyze article text for manipulation and bias.
    Returns ANIResponse with scores and analysis.
    """
    try:
        # Build context for the LLM
        context_parts = []
        if title:
            context_parts.append(f"Title: {title}")
        if url:
            context_parts.append(f"URL: {url}")
        context_parts.append(f"Article Text:\n{text[:MAX_TEXT_LENGTH]}")

        user_content = "\n\n".join(context_parts)

        completion = await client.chat.completions.create(
            model=MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this article:\n\n{user_content}"}
            ],
            temperature=0.2,
            max_tokens=2000
        )

        raw_json = completion.choices[0].message.content
        data = json.loads(raw_json)

        # Validate and transform to ensure schema compliance
        # Map the new detailed vector names to UI-friendly keys
        vector_mapping = {
            "authority_overload": "authority",
            "emotional_loading": "emotion",
            "logical_integrity": "logic",
            "headline_dissonance": "headline"
        }

        vectors = {}
        raw_vectors = data.get("vectors", {})

        for api_key, ui_key in vector_mapping.items():
            if api_key in raw_vectors:
                v = raw_vectors[api_key]
                vectors[ui_key] = VectorScore(
                    score=v.get("score", 50),
                    flags=v.get("flags", []),
                    analysis=v.get("analysis", "No analysis available")
                )

        return ANIResponse(
            ani_score=data.get("ani_score", 50),
            summary=data.get("summary", "Analysis completed."),
            verdict=data.get("verdict", "Analysis Complete"),
            vectors=vectors
        )

    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        return _fallback_response("Failed to parse AI response")

    except Exception as e:
        print(f"Forensic Analysis Error: {e}")
        return _fallback_response(f"Analysis error: {str(e)}")


def _fallback_response(error_msg: str) -> ANIResponse:
    """Return a safe fallback response when analysis fails."""
    return ANIResponse(
        ani_score=50,
        summary=f"Analysis could not be completed. {error_msg}",
        verdict="Analysis Error",
        vectors={
            "authority": VectorScore(score=50, flags=[], analysis="Analysis unavailable"),
            "emotion": VectorScore(score=50, flags=[], analysis="Analysis unavailable"),
            "logic": VectorScore(score=50, flags=[], analysis="Analysis unavailable"),
            "headline": VectorScore(score=50, flags=[], analysis="Analysis unavailable")
        }
    )
