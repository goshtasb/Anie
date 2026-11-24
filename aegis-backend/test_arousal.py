"""Tests for arousal.py: High-Arousal Loading (#14) checked by a fixed word list in code."""
from arousal import find_arousal, strip_quoted
from rulebook import apply_rulebook


def _ledger(rows=()):
    led = [{"marker": n, "hit": False, "voice": None, "quote": ""} for n in range(1, 25)]
    for row in rows:
        led[row["marker"] - 1] = row
    return {"nci_ledger": led}


def test_narration_word_is_a_hit_with_its_sentence():
    hits = find_arousal("The council met Tuesday. Critics called it a horrific plan by the mayor. Votes follow.")
    assert [h["word"] for h in hits] == ["horrific"]
    assert hits[0]["sentence"] == "Critics called it a horrific plan by the mayor."


def test_quote_shield_ignores_words_inside_quotes():
    assert find_arousal('The senator said the bill was "a horrific betrayal" of voters.') == []
    assert find_arousal("He called it “disgraceful” and left.") == []
    assert find_arousal("NATO calls the strike a 'disgraceful act' of war.") == []


def test_apostrophes_are_not_treated_as_quotes():
    hits = find_arousal("The mayor's plan is absurd, and the city's budget can't cover it.")
    assert [h["word"] for h in hits] == ["absurd"]


def test_whole_words_only_and_case_insensitive():
    assert find_arousal("The vileness test and evilly named file.") == []           # not whole words
    assert [h["word"] for h in find_arousal("SHOCKING scenes.")] == ["shocking"]


def test_plain_wire_language_has_no_hits():
    text = ("Russian attacks batter Ukraine, killing at least 8. Efforts to set firm rules "
            "on AI-powered drones ran aground Saturday. A court approved a $7.25 billion settlement.")
    assert find_arousal(text) == []


def test_strip_quoted_keeps_narration():
    out = strip_quoted('He said "awful" today.')
    assert len(out) == len('He said "awful" today.') and "awful" not in out and out.startswith("He said")


# --- rulebook uses the code check for #14, not the model's judgment ---
ARTICLE = "TITLE: Test\nThe horrific plan passed. Officials said it was \"a shameful day\"."


def test_rulebook_counts_code_hit_even_if_model_said_no():
    r = apply_rulebook(_ledger(), ARTICLE)
    row = r["checklist"][13]
    assert row["counted"] and row["status"] == "counted" and "horrific" in row["quote"]
    assert r["score"] == 64


def test_rulebook_ignores_model_hit_the_list_does_not_find():
    model = _ledger([{"marker": 14, "hit": True, "voice": "author", "quote": "The horrific plan passed",
                      "target": "subject"}])
    plain = "TITLE: Test\nRussian attacks batter Ukraine, killing at least 8."
    model["nci_ledger"][13]["quote"] = "Russian attacks batter Ukraine"
    r = apply_rulebook(model, plain)
    assert r["score"] == 100 and r["checklist"][13]["status"] == "clear"


def test_rulebook_same_text_same_14_result():
    a = apply_rulebook(_ledger(), ARTICLE)
    b = apply_rulebook(_ledger([{"marker": 14, "hit": True, "voice": "author", "quote": "x" * 9}]), ARTICLE)
    assert a["checklist"][13] == b["checklist"][13]


def test_commercial_content_keeps_object_leniency():
    data = dict(_ledger(), content_type="commercial")
    r = apply_rulebook(data, "TITLE: Phone\nThe stunning, shocking new phone is here.")
    assert r["score"] == 100 and r["checklist"][13]["status"] == "object"


def test_weather_idiom_is_not_a_hit():
    # V5.10.1: "wicked" dropped; AP wrote "Wicked weather on both coasts" in a travel story.
    assert find_arousal("Wicked weather on both coasts. Storms will slow flights.") == []
