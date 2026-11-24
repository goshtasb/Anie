# rulebook.py - V5.10 "Word List" + V5.9 "Itemized Ledger": the NCI checklist scoring rules, enforced in code.
#
# The model's only job is DETECTION: for each of the 24 markers it says hit or not,
# whose voice it is in, and quotes the line. This module then:
#   1. keeps a hit only if its quote appears verbatim in the article (no quote, no hit),
#   2. drops hits in a quoted speaker's voice (Quote Shield),
#   3. computes vector scores, the final score and the verdict from the rules written in
#      the Psyop Hunter prompt (deductions, vector caps, ceilings, red lines, stacking
#      bands, weakest link, verdict key).
# Every number below is copied from the prompt's own rules so the two cannot drift apart.
import re

from arousal import find_arousal

# marker -> (concept name, vector key)
MARKERS = {
    1: ("Source Amnesia", "reality_anchoring"),
    2: ("False Authority", "reality_anchoring"),
    3: ("Time Distortion", "reality_anchoring"),
    4: ("Contextual Omission", "reality_anchoring"),
    5: ("False Consensus", "reality_anchoring"),
    6: ("Trend Inversion", "reality_anchoring"),
    7: ("In-Group/Out-Group Framing", "tribal_engineering"),
    8: ("Moral Superiority", "tribal_engineering"),
    9: ("Identity Fusion", "tribal_engineering"),
    10: ("Dehumanization", "tribal_engineering"),
    11: ("Spiral of Silence", "tribal_engineering"),
    12: ("Prescriptive Commands", "neuro_linguistic"),
    13: ("Artificial Urgency", "neuro_linguistic"),
    14: ("High-Arousal Loading", "neuro_linguistic"),
    15: ("Inevitability Framing", "neuro_linguistic"),
    16: ("Elite Mimicry", "neuro_linguistic"),
    17: ("Preemptive Neutralization", "neuro_linguistic"),
    18: ("False Liberation", "neuro_linguistic"),
    19: ("Pacing and Leading", "neuro_linguistic"),
    20: ("Double Bind", "logical_integrity"),
    21: ("False Dilemma", "logical_integrity"),
    22: ("Agency Deletion", "logical_integrity"),
    23: ("Strawman", "logical_integrity"),
    24: ("Red Herring", "logical_integrity"),
}
VECTORS = ("reality_anchoring", "tribal_engineering", "neuro_linguistic", "logical_integrity")
COLD_MARKERS = {15, 16, 17, 18, 19}
HIGH_AROUSAL = 14  # THE TARGET RULE: banned only when the target is a SUBJECT (person, group, policy)

# "Deduct 10-15 points per tactic" / "15-20 per Cold Psyop tactic": the top of each stated
# range (tuned Nov 2026: midpoints left heavy spin in the 50s on the tuning set).
DEDUCT_STANDARD = 15
DEDUCT_COLD = 20

# Vector-level caps stated in step_2 ("Score < 50" means at most 49, and so on).
VECTOR_CAPS = {3: 49, 4: 49, 14: 59, 16: 49}
# Final-score red lines stated in step_2 / step_3.
RED_LINES = {6: 24, 10: 29, 20: 29}
FULL_CONSENSUS_CAP = 29          # #15 + #16 + #17 all present
INEVITABILITY_COMBO_CAP = 39     # #15 with #16 or #17
CEILING_SINGLE = 75              # In-Group Framing (#7) or High-Arousal (#14)
CEILING_BOTH = 65                # both
WEAKEST_LINK_MARGIN = 5


def band_cap(tactic_count: int) -> int:
    """V5.4 + V5.8 bands, read as ceilings on the final score."""
    if tactic_count == 0:
        return 100
    if tactic_count <= 3:
        return 79
    if tactic_count <= 5:
        return 59
    if tactic_count <= 7:
        return 39
    return 24


def verdict_for(score: int) -> str:
    """The prompt's VERDICT KEY."""
    if score <= 35:
        return "Engineered Narrative"
    if score <= 55:
        return "High Manipulation"
    if score <= 75:
        return "Moderate Spin"
    return "Organic Reporting"


_QUOTE_CHARS = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"',
                              "‑": "-", "–": "-", "—": "-", " ": " "})


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").translate(_QUOTE_CHARS)).strip().lower()


def quote_in_article(quote: str, article_norm: str) -> bool:
    """True if every ellipsis-separated piece of the quote appears verbatim in the article."""
    pieces = [p.strip(" .,;:\"'") for p in re.split(r"\.\.\.|…", _norm(quote))]
    pieces = [p for p in pieces if len(p) >= 4]
    return bool(pieces) and all(p in article_norm for p in pieces)


def _read_ledger(analysis: dict):
    """Return {marker: row} only when every one of the 24 markers has a yes/no answer.
    V5.11 (Rule 1): a ledger that skips any rule is rejected, never read as "clear"."""
    rows = analysis.get("nci_ledger") if isinstance(analysis, dict) else None
    if not isinstance(rows, list) or not rows:
        return None
    by_marker = {}
    for row in rows:
        if (isinstance(row, dict) and isinstance(row.get("marker"), int) and row["marker"] in MARKERS
                and isinstance(row.get("hit"), bool)):
            by_marker.setdefault(row["marker"], row)
    if set(by_marker) != set(MARKERS):
        return None
    return by_marker


def apply_rulebook(analysis: dict, article_text: str):
    """Score an analysis from its nci_ledger. Returns None unless all 24 markers were answered."""
    by_marker = _read_ledger(analysis)
    if by_marker is None:
        return None
    article_norm = _norm(article_text)

    checklist, counted = [], set()
    for n, (name, vector) in MARKERS.items():
        row = by_marker.get(n, {})
        claimed = bool(row.get("hit"))
        quote = (row.get("quote") or "").strip()
        voice = (row.get("voice") or "").lower()
        if n == HIGH_AROUSAL:
            # V5.10: #14 comes from the fixed word list in code, never the model's call.
            hits = find_arousal(article_text)
            claimed, quote, voice = bool(hits), (hits[0]["sentence"] if hits else ""), "author"
            row = {"target": "object" if (analysis.get("content_type") or "").lower() == "commercial"
                   else "subject"}
        if not claimed:
            status = "clear"
        elif n != HIGH_AROUSAL and not quote_in_article(quote, article_norm):
            status = "unverified"   # no quote, no hit
        elif voice == "quoted":
            status = "quoted"       # Quote Shield
        elif n == HIGH_AROUSAL and (row.get("target") or "").lower() == "object":
            status = "object"       # Target Rule: high arousal about a product/tech/movie is allowed
        else:
            status = "counted"
            counted.add(n)
        checklist.append({"marker": n, "name": name, "vector": vector,
                          "hit": status in ("counted", "quoted", "object"), "status": status,
                          "voice": voice or None, "quote": quote if status != "clear" else "",
                          "counted": status == "counted"})

    def deduction(n):
        return DEDUCT_COLD if n in COLD_MARKERS else DEDUCT_STANDARD

    # V5.10: the V5.9r5 single-tactic rule is withdrawn. It existed so one loaded phrase
    # couldn't drag straight news to 64; with #14 now a fixed word list, straight news
    # no longer trips it, and the rule let a one-tactic state-media story score 79.

    vectors = {}
    for v in VECTORS:
        hits = [n for n in counted if MARKERS[n][1] == v]
        score = 100 - sum(deduction(n) for n in hits)
        for n in hits:
            score = min(score, VECTOR_CAPS.get(n, 100))
        if v == "neuro_linguistic" and 15 in counted and counted & {16, 17}:
            score = min(score, INEVITABILITY_COMBO_CAP)
        vectors[v] = max(0, score)

    final = 100 - sum(deduction(n) for n in counted)
    final = min(final, band_cap(len(counted)))
    if 7 in counted and 14 in counted:
        final = min(final, CEILING_BOTH)
    elif 7 in counted or 14 in counted:
        final = min(final, CEILING_SINGLE)
    for n, cap in RED_LINES.items():
        if n in counted:
            final = min(final, cap)
    if {15, 16, 17} <= counted:
        final = min(final, FULL_CONSENSUS_CAP)
    final = min(final, min(vectors.values()) + WEAKEST_LINK_MARGIN)
    final = max(0, final)

    return {"score": final, "verdict": verdict_for(final), "vectors": vectors,
            "tactic_count": len(counted), "rules_checked": len(checklist), "checklist": checklist,
            "flags": {v: [c["quote"] for c in checklist if c["counted"] and c["vector"] == v] for v in VECTORS}}


# --- V5.9r4: NCI Engineered Reality sheet items not covered by the 24 markers ---
# Evidence only: these rows are verified and reported, and NEVER change a score,
# cap, deduction or verdict. Items marked True can't be judged from one article;
# they need other coverage (the Tavily search results, when present).
SHEET_ITEMS = [
    ("Timing", True),
    ("Uniform Messaging", True),
    ("Overuse of Novelty", False),
    ("Financial/Political Gain", True),
    ("Emotional Repetition", False),
    ("Manufactured Outrage", False),
    ("Rapid Behavior Shifts", True),
    ("Historical Parallels", False),
]


def apply_sheet(analysis: dict, article_text: str, context_text: str = ""):
    """Verify the model's "nci_sheet" rows. Returns 8 rows of {item, status, quote}
    with status present | absent | needs_search | unverified, or None if no sheet."""
    rows = analysis.get("nci_sheet") if isinstance(analysis, dict) else None
    if not isinstance(rows, list):
        return None
    by_item = {}
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("item"), str):
            by_item[row["item"].strip().lower()] = row
    article_norm = _norm(article_text)
    context_norm = _norm(context_text)
    out = []
    for name, needs_search in SHEET_ITEMS:
        row = by_item.get(name.lower(), {})
        claimed = (row.get("status") or "").strip().lower()
        quote = (row.get("quote") or "").strip()
        if claimed == "present":
            found = quote_in_article(quote, article_norm) or (
                needs_search and bool(context_norm) and quote_in_article(quote, context_norm))
            status = "present" if found else "unverified"
        elif needs_search and not context_norm:
            status = "needs_search"
        else:
            status = "absent"
        out.append({"item": name, "status": status, "quote": quote if status == "present" else None})
    return out
