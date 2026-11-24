# rule_checks.py - V5.12: NCI markers #1, #7 and #22 checked in code, like #14 in arousal.py.
#
# On Nov 24 these three were the only rules whose model answers changed between runs of
# the same article (4 of 192 answers). Here each is a fixed phrase test, so the same text
# always gives the same answer. Only the journalist's own narration counts: quoted speech
# is removed first (THE QUOTE SHIELD). Each hit returns the sentence it sits in.
# The phrases come from each rule's definition in the prompt, not from any test article:
#   #1 Source Amnesia: "Experts say" or "Studies show" without attribution.
#   #7 In-Group/Out-Group Framing: "We (Good)" vs "They (Bad)", groups treated as monoliths
#      (prompt example: "Democrat-led cities").
#   #22 Agency Deletion: "Mistakes were made" hides the actor.
# Limitation: a phrase test only catches the wording on its list. Change the lists only on
# evidence from articles outside the test sets.
import re

from arousal import find_in_narration

# --- #1 Source Amnesia: an unnamed authority making a claim ---
_EXPERTS = (r"(?:(?:many|some|most|several|leading|top|independent)\s+)?"
            r"(?:experts?|scientists|researchers|analysts|economists|observers|commentators|specialists)")
_EXPERT_VERBS = (r"(?:say|says|said|believe|believes|believed|agree|agreed|warn|warns|warned|argue|argued|"
                 r"suggest|suggests|suggested|fear|feared|think|thinks|predict|predicted|estimate|estimated)")
_STUDIES = r"(?:studies|research|(?:a|one|the)\s+study|the\s+science)"
_STUDY_VERBS = (r"(?:show|shows|showed|shown|prove|proves|proved|proven|suggest|suggests|suggested|"
                r"confirm|confirms|confirmed|indicate|indicates|indicated|find|finds|found)")
_VAGUE = (r"(?:it\s+is\s+(?:widely\s+)?(?:believed|known|accepted|understood)|"
          r"many\s+(?:say|believe|agree)|some\s+(?:say|believe|argue)|everyone\s+knows)")
SOURCE_AMNESIA_RE = re.compile(
    r"(?<![\w-])(" + _EXPERTS + r"\s+(?:have\s+|had\s+|also\s+|now\s+)?" + _EXPERT_VERBS +
    r"|" + _STUDIES + r"\s+(?:have\s+|has\s+|had\s+|also\s+)?" + _STUDY_VERBS +
    r"|" + _VAGUE + r")(?![\w-])", re.IGNORECASE)
# A named source makes it attributed: "experts at Yale say", "a study published in The Lancet
# found", "according to the World Bank", or a named journal, university or institute.
# Checked within the same sentence.
_ATTRIBUTED_RE = re.compile(
    r"\baccording\s+to\b|\b(?:experts?|scientists|researchers|analysts|economists|observers|"
    r"commentators|specialists|stud(?:y|ies)|research)\s+(?:at|from|with|for|by|published|led|"
    r"including|such\s+as)\b|\bpublished\b|\bjournal\b|\buniversity\b|\binstitute\b", re.IGNORECASE)


def find_source_amnesia(text: str) -> list:
    return find_in_narration(SOURCE_AMNESIA_RE, text,
                             accept=lambda sentence, m: not _ATTRIBUTED_RE.search(sentence))


# --- #7 In-Group/Out-Group Framing: pejorative or monolith labels for a whole side ---
# Descriptive wire terms ("far-right party", "Republican-led House") are not on the list;
# the misspelled "Democrat-led" form is the prompt's own example.
GROUP_LABELS = [
    "democrat-led", "democrat-run", "democrat-controlled", "democrat party",
    "radical left", "radical-left", "the left's", "leftists?", "libs", "libtards?",
    "maga cult", "globalists?", "deep state", "corporate media", "legacy media", "fake news",
    "collective west", "warmongers?", "russophob(?:e|es|ia|ic)", "fascists?", "marxists?",
    "biden regime", "trump regime", "kiev regime", "kyiv regime", "zelensky regime",
    "western puppets?",
]
GROUP_LABEL_RE = re.compile(r"(?<![\w-])(" + "|".join(GROUP_LABELS) + r")(?![\w-])", re.IGNORECASE)


def find_group_labels(text: str) -> list:
    return find_in_narration(GROUP_LABEL_RE, text)


# --- #22 Agency Deletion: a passive that hides who acted ---
AGENCY_DELETION_RE = re.compile(
    r"(?<![\w-])((?:mistakes|errors)\s+(?:were|have\s+been|had\s+been)\s+made"
    r"|lives\s+(?:were|have\s+been|had\s+been)\s+lost"
    r"|it\s+(?:was|has\s+been|had\s+been)\s+(?:decided|determined|agreed)"
    r"|it\s+(?:is|was|has\s+been)\s+(?:said|claimed|alleged|rumou?red|reported)"
    r"|(?:concerns|questions)\s+(?:were|have\s+been|had\s+been)\s+raised)(?![\w-])",
    re.IGNORECASE)


def find_agency_deletion(text: str) -> list:
    # Naming the actor ("... were raised by the auditor") restores agency.
    return find_in_narration(AGENCY_DELETION_RE, text,
                             accept=lambda sentence, m: not re.match(r"\s+by\b", sentence[m.end():], re.I))


CODE_CHECKS = {1: find_source_amnesia, 7: find_group_labels, 22: find_agency_deletion}
