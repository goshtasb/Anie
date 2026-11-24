"""Tests for rule_checks.py: Source Amnesia (#1), In-Group/Out-Group (#7) and Agency Deletion (#22) in code."""
from rule_checks import find_agency_deletion, find_group_labels, find_source_amnesia


def words(hits):
    return [h["word"] for h in hits]


def test_unnamed_experts_and_studies_are_hits():
    assert words(find_source_amnesia("Experts say the plan will fail.")) == ["experts say"]
    assert words(find_source_amnesia("Many analysts believe shares will fall.")) == ["many analysts believe"]
    assert words(find_source_amnesia("Studies show the drug works.")) == ["studies show"]
    assert words(find_source_amnesia("It is widely believed that he lied.")) == ["it is widely believed"]


def test_named_source_is_not_source_amnesia():
    assert find_source_amnesia("Experts at Yale say the plan will fail.") == []
    assert find_source_amnesia("A study published in The Lancet found the drug works.") == []
    assert find_source_amnesia("Studies show the drug works, according to the World Health Organization.") == []


def test_quote_shield_applies_to_all_three():
    assert find_source_amnesia('The senator said "experts say this is a scam" and left.') == []
    assert find_group_labels('He said “the radical left” wants it.') == []
    assert find_agency_deletion('The CEO said "mistakes were made" last year.') == []


def test_pejorative_group_labels_are_hits_and_wire_terms_are_not():
    assert words(find_group_labels("Crime in Democrat-led cities rose.")) == ["democrat-led"]
    assert words(find_group_labels("What is up with the left's obsession with trains?")) == ["the left's"]
    assert find_group_labels("The Republican-led House voted on the far-right party's bill.") == []


def test_hidden_actor_passive_is_a_hit_unless_actor_named():
    assert words(find_agency_deletion("Mistakes were made, the report admits.")) == ["mistakes were made"]
    assert words(find_agency_deletion("Questions have been raised about the deal.")) == ["questions have been raised"]
    assert find_agency_deletion("Concerns were raised by the city auditor.") == []


def test_plain_wire_language_has_no_hits():
    text = ("Police arrested two men Saturday, officials said. The Labor Department said hiring slowed. "
            "The Republican-led Senate passed the bill 52-48. He was taken to a hospital.")
    assert find_source_amnesia(text) == [] and find_group_labels(text) == [] and find_agency_deletion(text) == []
