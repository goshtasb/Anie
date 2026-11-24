"""Tests for voting.py: each rule takes the majority answer across runs, and code scores it."""
import asyncio

from rulebook import apply_rulebook
from voting import vote, needs_tiebreak, run_with_vote
from test_rulebook import ARTICLE, ledger

SOURCE = (1, "author", "Experts say crime is up")
GROUP = (7, "author", "Democrat-led cities")
FAKE = (1, "author", "studies prove everything")  # not in the article: unverified


def counted(analysis):
    return {c["marker"] for c in apply_rulebook(analysis, ARTICLE)["checklist"] if c["counted"]}


def test_two_runs_that_agree_need_no_third():
    runs = [ledger(SOURCE), ledger(SOURCE)]
    assert not needs_tiebreak(runs, ARTICLE)
    assert counted(vote(runs, ARTICLE)) == {1}


def test_two_runs_that_disagree_need_a_third():
    assert needs_tiebreak([ledger(SOURCE), ledger()], ARTICLE)


def test_majority_of_three_decides_each_rule():
    runs = [ledger(SOURCE, GROUP), ledger(SOURCE), ledger(GROUP)]
    assert counted(vote(runs, ARTICLE)) == {1, 7}
    runs = [ledger(SOURCE), ledger(), ledger()]
    assert counted(vote(runs, ARTICLE)) == set()


def test_voted_score_equals_score_of_the_majority_ledger():
    runs = [ledger(SOURCE), ledger(SOURCE, GROUP), ledger()]
    assert apply_rulebook(vote(runs, ARTICLE), ARTICLE)["score"] == apply_rulebook(ledger(SOURCE), ARTICLE)["score"]


def test_unverified_quote_votes_as_not_counted():
    # Two runs say yes to rule 1, but one quote is not in the article: only one verified yes.
    runs = [ledger(SOURCE), ledger(FAKE), ledger()]
    assert counted(vote(runs, ARTICLE)) == set()


def test_counted_rule_carries_a_verified_quote():
    runs = [ledger(FAKE), ledger(SOURCE), ledger(SOURCE)]
    rule1 = apply_rulebook(vote(runs, ARTICLE), ARTICLE)["checklist"][0]
    assert rule1["counted"] and rule1["quote"] == "Experts say crime is up"


def test_incomplete_run_casts_no_vote():
    broken = {"nci_ledger": ledger(SOURCE)["nci_ledger"][:20]}
    assert needs_tiebreak([ledger(SOURCE), broken], ARTICLE)
    assert counted(vote([ledger(SOURCE), broken, ledger(SOURCE)], ARTICLE)) == {1}


def test_no_majority_means_no_score():
    broken = {"nci_ledger": []}
    assert vote([ledger(SOURCE), ledger(), broken], ARTICLE) is None
    assert vote([ledger(), broken, None], ARTICLE) is None


def test_run_with_vote_stops_at_two_when_runs_agree():
    calls = []

    async def call():
        calls.append(1)
        return ledger(SOURCE)

    voted, runs, failed = asyncio.run(run_with_vote(call, ARTICLE))
    assert runs == 2 and len(calls) == 2 and not failed and counted(voted) == {1}


def test_run_with_vote_adds_third_run_on_disagreement():
    answers = iter([ledger(SOURCE), ledger(), ledger(SOURCE)])

    async def call():
        return next(answers)

    voted, runs, failed = asyncio.run(run_with_vote(call, ARTICLE))
    assert runs == 3 and counted(voted) == {1}


def test_run_with_vote_reports_when_every_run_failed():
    async def call():
        return None

    voted, runs, failed = asyncio.run(run_with_vote(call, ARTICLE))
    assert voted is None and failed and runs == 3
