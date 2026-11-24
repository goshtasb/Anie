# arousal.py - V5.10 "Word List": High-Arousal Loading (NCI marker #14) checked in code.
#
# The model used to decide #14, and it flipped between runs on the same article
# (a straight AP story scored 79 on one run and 100 on the next). This module replaces
# that judgment with a fixed list: the same text always gives the same result.
#   - Only the journalist's own narration counts. Text inside quotation marks is
#     removed first (THE QUOTE SHIELD), so a quoted speaker's words never count.
#   - Each hit returns the sentence it sits in, as evidence.
#   - THE TARGET RULE's object leniency is kept by the caller: commercial content
#     (product, tech, movie) is not checked.
# The list holds emotive words that straight wire copy avoids. It was written from the
# prompt's #14 definition, not fitted to any test article; change it only on evidence
# from articles outside the test sets.
import re

AROUSAL_WORDS = sorted({
    # horror and disgust
    "horrific", "horrifying", "horrendous", "appalling", "atrocious", "monstrous",
    "despicable", "sickening", "disgusting", "vile", "evil", "heinous",
    "abhorrent", "deplorable", "shameful", "shameless", "disgraceful", "outrageous",
    "scandalous", "nightmarish", "terrifying", "chilling",
    # mockery and contempt
    "insane", "unhinged", "deranged", "crazed", "lunatic", "idiotic", "moronic",
    "pathetic", "absurd", "absurdly", "ludicrous", "ridiculous", "preposterous",
    "laughable", "clueless", "pathetically",
    # hype and shock
    "shocking", "shockingly", "bombshell", "jaw-dropping", "mind-blowing", "staggering",
    "apocalyptic", "catastrophically",
    # headline attack verbs
    "slams", "slammed", "blasts", "blasted", "rips", "eviscerates", "eviscerated",
    "obliterates", "obliterated", "torches", "torched", "shreds", "shredded",
    "annihilates", "annihilated", "humiliates", "humiliated", "lambasts", "lambasted",
    "skewers", "skewered", "destroys",
    # pejorative labels
    "thug", "thugs", "traitor", "traitors", "treasonous", "puppet", "puppets",
    "stooge", "stooges", "lackey", "lackeys",
})

_WORD_RE = re.compile(r"(?<![\w-])(" + "|".join(re.escape(w) for w in AROUSAL_WORDS) + r")(?![\w-])",
                      re.IGNORECASE)
# Double quotes (straight or curly), and single-quoted phrases that open after a
# non-letter and close before one, so apostrophes ("mayor's", "can't") are left alone.
_QUOTED_RE = re.compile(r"\"[^\"]*\"|“[^”]*”|(?<!\w)['‘][^'’\n]+['’](?!\w)")
_SENTENCE_RE = re.compile(r"[^.!?\n]*[.!?]?")


def strip_quoted(text: str) -> str:
    """Blank out quoted speech, keeping the text length the same."""
    return _QUOTED_RE.sub(lambda m: " " * len(m.group(0)), text or "")


def find_in_narration(pattern, text: str, accept=None) -> list:
    """Return [{"word", "sentence"}] for each match of a compiled pattern in the narration.
    Quoted speech is blanked first (THE QUOTE SHIELD). accept(narration_sentence, match),
    when given, can reject a match (used for attribution exemptions in rule_checks.py)."""
    narration = strip_quoted(text)
    hits = []
    for m in _SENTENCE_RE.finditer(text or ""):
        sentence = m.group(0)
        if not sentence.strip():
            continue
        nar_sentence = narration[m.start():m.end()]
        for w in pattern.finditer(nar_sentence):
            if accept is None or accept(nar_sentence, w):
                hits.append({"word": w.group(1).lower(), "sentence": sentence.strip()})
    return hits


def find_arousal(text: str) -> list:
    """Return [{"word", "sentence"}] for each list word in the narration, in order."""
    return find_in_narration(_WORD_RE, text)
