"""Tests for rulebook.py: the NCI checklist scoring rules enforced in code."""
from rulebook import apply_rulebook, verdict_for, band_cap

ARTICLE = ('TITLE: Test\nThe rising crime wave in Democrat-led cities continues. '
           'Officials said "these parasites must go". Experts say crime is up. '
           'Smart people already know it will happen anyway. No drama, no villains.')
# V5.10: #14 is found by the word list in code, so the 14 tests use narration with a list word.
HOT = ARTICLE + ' The horrific crime wave goes on.'

def ledger(*hits):
    rows = [{"marker": n, "hit": False, "voice": None, "quote": ""} for n in range(1, 25)]
    for n, voice, quote in hits:
        rows[n - 1] = {"marker": n, "hit": True, "voice": voice, "quote": quote}
    return {"nci_ledger": rows}

def test_clean_article_scores_organic():
    r = apply_rulebook(ledger(), ARTICLE)
    assert r["score"] == 100 and r["verdict"] == "Organic Reporting"
    assert len(r["checklist"]) == 24 and not any(c["counted"] for c in r["checklist"])

def test_hit_without_verbatim_quote_is_dropped():
    r = apply_rulebook(ledger((1, "author", "studies prove everything")), ARTICLE)
    assert r["score"] == 100
    item = r["checklist"][0]
    assert item["hit"] is False and item["status"] == "unverified"

def test_quote_shield_quoted_voice_not_counted():
    r = apply_rulebook(ledger((10, "quoted", "these parasites must go")), ARTICLE)
    assert r["score"] == 100 and r["checklist"][9]["status"] == "quoted"

def test_one_tactic_stays_in_moderate_band():
    r = apply_rulebook(ledger((1, "author", "Experts say crime is up")), ARTICLE)
    assert 60 <= r["score"] <= 79

def test_both_ceilings_cap_at_65():
    r = apply_rulebook(ledger((7, "author", "Democrat-led cities"), (14, "author", "horrific crime wave")), HOT)
    assert r["score"] <= 65

def test_dehumanization_in_author_voice_is_red_line():
    art = ARTICLE + " These parasites are ruining the city."
    r = apply_rulebook(ledger((10, "author", "These parasites are ruining the city")), art)
    assert r["score"] < 30 and r["verdict"] == "Engineered Narrative"

def test_full_consensus_engineering():
    r = apply_rulebook(ledger((15, "author", "it will happen anyway"), (16, "author", "Smart people already know"),
                              (17, "author", "No drama, no villains")), ARTICLE)
    assert r["score"] < 30

def test_stacking_bands_are_ceilings():
    hits = [(n, "author", "Experts say crime is up") for n in (1, 2, 5, 8, 9, 11)]
    assert apply_rulebook(ledger(*hits), ARTICLE)["score"] <= 39
    hits += [(n, "author", "Experts say crime is up") for n in (21, 23)]
    assert apply_rulebook(ledger(*hits), ARTICLE)["score"] < 25

def test_weakest_link_and_vector_caps():
    r = apply_rulebook(ledger((4, "author", "Experts say crime is up"), (1, "author", "Experts say crime is up")), ARTICLE)
    assert r["vectors"]["reality_anchoring"] <= 49
    assert r["score"] <= r["vectors"]["reality_anchoring"] + 5

def test_curly_quotes_and_ellipsis_verify():
    art = "He said it was “the worst day” and then left the room quietly."
    r = apply_rulebook(ledger((1, "author", '"the worst day" ... left the room')), art)
    assert r["checklist"][0]["status"] == "counted"

def test_missing_ledger_returns_none():
    assert apply_rulebook({"ani_score": 50}, ARTICLE) is None

def test_verdict_key_and_bands():
    assert [verdict_for(s) for s in (35, 36, 55, 56, 75, 76)] == [
        "Engineered Narrative", "High Manipulation", "High Manipulation",
        "Moderate Spin", "Moderate Spin", "Organic Reporting"]
    assert [band_cap(n) for n in (0, 1, 3, 4, 5, 6, 7, 8)] == [100, 79, 79, 59, 59, 39, 39, 24]

def test_target_rule_high_arousal_about_object_is_allowed():
    art = "The stunning new phone has a gorgeous screen."
    rows = ledger((14, "author", "stunning new phone"))
    rows["content_type"] = "commercial"
    art = "The shocking new phone has a gorgeous screen."
    r = apply_rulebook(rows, art)
    assert r["score"] == 100 and r["checklist"][13]["status"] == "object"

def test_target_rule_subject_still_counts():
    rows = ledger((14, "author", "horrific crime wave"))
    rows["nci_ledger"][13]["target"] = "subject"
    r = apply_rulebook(rows, HOT)
    assert r["checklist"][13]["status"] == "counted" and r["score"] <= 79


# --- V5.10: one tactic keeps its vector cap (V5.9r5 single-tactic rule withdrawn) ---
def test_single_high_arousal_word_caps_at_64():
    r = apply_rulebook(ledger(), HOT)
    assert r["score"] == 64 and r["tactic_count"] == 1

def test_single_vector_capped_marker_keeps_cap():
    for n in (3, 4, 16):
        r = apply_rulebook(ledger((n, "author", "Experts say crime is up")), ARTICLE)
        assert r["score"] <= 54, n

def test_single_red_line_still_crashes():
    art = ARTICLE + " These parasites are ruining the city."
    assert apply_rulebook(ledger((10, "author", "These parasites are ruining the city")), art)["score"] <= 29
    assert apply_rulebook(ledger((6, "author", "Experts say crime is up")), ARTICLE)["score"] <= 24
    assert apply_rulebook(ledger((20, "author", "Experts say crime is up")), ARTICLE)["score"] <= 29


# --- V5.9r4: NCI sheet items (evidence only, never scored) ---
from rulebook import SHEET_ITEMS, apply_sheet

SHEET_ARTICLE = "Officials called the flood an unprecedented, once-in-a-lifetime disaster. Shocking scenes again."


def _sheet(rows):
    return {"nci_sheet": rows}


def test_sheet_has_the_eight_missing_items():
    assert [n for n, _ in SHEET_ITEMS] == [
        "Timing", "Uniform Messaging", "Overuse of Novelty", "Financial/Political Gain",
        "Emotional Repetition", "Manufactured Outrage", "Rapid Behavior Shifts", "Historical Parallels"]


def test_sheet_present_needs_verbatim_quote():
    out = apply_sheet(_sheet([
        {"item": "Overuse of Novelty", "status": "present", "quote": "unprecedented, once-in-a-lifetime disaster"},
        {"item": "Emotional Repetition", "status": "present", "quote": "made up words"},
    ]), SHEET_ARTICLE)
    by = {r["item"]: r for r in out}
    assert by["Overuse of Novelty"]["status"] == "present"
    assert by["Emotional Repetition"]["status"] == "unverified"
    assert by["Manufactured Outrage"]["status"] == "absent"
    assert len(out) == 8


def test_sheet_search_items_default_to_needs_search():
    out = apply_sheet(_sheet([]), SHEET_ARTICLE)
    by = {r["item"]: r["status"] for r in out}
    for n in ("Timing", "Uniform Messaging", "Financial/Political Gain", "Rapid Behavior Shifts"):
        assert by[n] == "needs_search"
    assert by["Historical Parallels"] == "absent"


def test_sheet_search_item_can_quote_search_results():
    out = apply_sheet(_sheet([
        {"item": "Uniform Messaging", "status": "present", "quote": "avoidable tragedy"}]),
        SHEET_ARTICLE, context_text="Outlet B: an avoidable tragedy, officials say")
    assert {r["item"]: r["status"] for r in out}["Uniform Messaging"] == "present"


def test_sheet_in_article_item_cannot_claim_needs_search():
    out = apply_sheet(_sheet([{"item": "Manufactured Outrage", "status": "needs_search", "quote": ""}]), SHEET_ARTICLE)
    assert {r["item"]: r["status"] for r in out}["Manufactured Outrage"] == "absent"


def test_sheet_never_changes_the_score():
    base = {"nci_ledger": [{"marker": n, "hit": False, "voice": None, "quote": ""} for n in range(1, 25)]}
    with_sheet = dict(base, nci_sheet=[{"item": "Overuse of Novelty", "status": "present",
                                        "quote": "unprecedented, once-in-a-lifetime disaster"}])
    assert apply_rulebook(base, SHEET_ARTICLE) == apply_rulebook(with_sheet, SHEET_ARTICLE)


def test_sheet_missing_returns_none():
    assert apply_sheet({}, SHEET_ARTICLE) is None
