# voting.py - V5.14 "Majority Vote": first scans ask the model more than once and keep
# each rule's majority answer, so one run's drift can't decide a score.
#
# How it works:
#   1. Two runs are made in parallel. Each is checked by the rulebook on its own
#      (quote verified in the article, Quote Shield, Target Rule), so a run's answer to a
#      rule is "counted" or "not counted" exactly as the score would see it.
#   2. If both runs answered all 24 rules and agree on every one, the first run is used.
#      Otherwise a third run is made.
#   3. Each rule takes the answer a majority of the runs made gave (2 of 2, or 2 of 3).
#      A run that skipped a rule casts no vote; if a rule has no majority, there is no score.
#   4. The voted ledger copies each rule's row from a run that gave the majority answer,
#      so a counted rule always carries a quote that was verified in the article.
#      The rulebook then scores that ledger: code alone computes the score.
import asyncio
import copy

from rulebook import apply_rulebook, MARKERS, HIGH_AROUSAL

FIRST_ROUND = 2   # runs made in parallel on every first scan
MAX_RUNS = 3      # the tie-break run, made only when the first two disagree


def _counted(rb) -> frozenset:
    return frozenset(c["marker"] for c in rb["checklist"] if c["counted"])


def needs_tiebreak(analyses, article_text: str) -> bool:
    """True unless every run answered all 24 rules and they agree on which rules count."""
    rbs = [apply_rulebook(a, article_text) if a else None for a in analyses]
    if any(rb is None for rb in rbs):
        return True
    return len({_counted(rb) for rb in rbs}) > 1


def vote(analyses, article_text: str):
    """Return the voted analysis (a run's dict with a majority nci_ledger), or None when
    fewer than a majority of runs were complete or any rule has no majority."""
    need = len(analyses) // 2 + 1
    complete = [(a, apply_rulebook(a, article_text)) for a in analyses if a]
    complete = [(a, rb) for a, rb in complete if rb]
    if len(complete) < need:
        return None
    sets = [_counted(rb) for _, rb in complete]

    decided = {}
    for n in MARKERS:
        yes = sum(n in s for s in sets)
        if yes >= need:
            decided[n] = True
        elif len(sets) - yes >= need:
            decided[n] = False
        else:
            return None  # no majority on this rule: no score
    voted_set = frozenset(n for n, hit in decided.items() if hit)

    # Summary, vectors' prose and sheet come from the run closest to the vote (earliest on ties).
    base_i = min(range(len(complete)), key=lambda i: len(sets[i] ^ voted_set))
    voted = copy.deepcopy(complete[base_i][0])

    rows = []
    for n in MARKERS:
        src = next(i for i, s in enumerate(sets) if (n in s) == decided[n])
        rows.append(copy.deepcopy(_row(complete[src][0], n)))
        if n == HIGH_AROUSAL:
            # #14's status depends on the run's content_type (Target Rule), so take both together.
            voted["content_type"] = complete[src][0].get("content_type")
    voted["nci_ledger"] = rows
    return voted


def _row(analysis: dict, n: int) -> dict:
    for row in analysis.get("nci_ledger") or []:
        if isinstance(row, dict) and row.get("marker") == n:
            return row
    return {"marker": n, "hit": False}


async def run_with_vote(call, article_text: str):
    """Run the model call FIRST_ROUND times in parallel, a third time only on disagreement.
    Returns (voted_analysis_or_None, runs_made, all_failed)."""
    runs = list(await asyncio.gather(*(call() for _ in range(FIRST_ROUND))))
    if needs_tiebreak(runs, article_text) and len(runs) < MAX_RUNS:
        runs.append(await call())
    all_failed = not any(runs)
    return (None if all_failed else vote(runs, article_text)), len(runs), all_failed
