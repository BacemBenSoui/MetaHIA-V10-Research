"""P1-TEXT-STRUCT gateway A: deterministic text -> target structure (STRUCTURE_CONVENTION.md, frozen GEL 1).

Answers only: "which canonical syntactic structure, under the frozen convention, matches this sentence?"
It never answers what the sentence means. It uses closed-class word lists and morphology only (all
declared in RESOURCES), no open-class lexicon, no statistics, no I/O. Whenever the frozen rules and
closed classes do not decide a structure, it abstains (returns None) instead of guessing: a guess could
misplace a role or a negation, which are hard safety gates.

Addendum GEL 1-bis applied: A1 copula + morphological past participle -> R2 (by optional);
A2 subject nobody/nothing -> neg(verb(_, ...)); A3 possessive determiners -> null; A4 deictic
adverbs yesterday/today/now/tonight (sentence-initial or final) -> R8 time adverbs.

Known deliberate abstentions (documented in the development report):
  - sentence-initial or bare post-verbal words not introduced by a closed-class item (bare objects
    such as "eats food", "right now"): without an open-class lexicon they cannot be told apart from
    arguments; deictic adverbs anywhere but the sentence edges;
  - "none"/"no one" and negative pronouns outside the subject position;
  - possessive determiners (A3), "of" phrases, other prepositions (with, for, to, from...), two adjuncts
    whose serialisation order would depend on an ambiguous preposition (in/on/at);
  - questions, coordination, subordination (R15).
"""
from __future__ import annotations

import re
from typing import Optional

RESOURCES = {
    "DETERMINERS": "determiners", "POSSESSIVE_DETERMINERS": "determiners",
    "PRONOUNS": "pronouns", "WH_WORDS": "pronouns",
    "PREPOSITIONS_TIME": "prepositions", "PREPOSITIONS_PLACE": "prepositions",
    "PREPOSITIONS_AMBIGUOUS": "prepositions", "PREPOSITIONS_UNCOVERED": "prepositions",
    "COPULAS": "auxiliaries", "HAVE_FORMS": "auxiliaries", "DO_FORMS": "auxiliaries", "MODALS": "auxiliaries",
    "NEGATIVE_CONTRACTIONS": "auxiliaries",
    "NEGATORS": "negators", "NEGATIVE_PRONOUNS": "negators", "NEGATIVE_SUBJECTS": "negators",
    "DEICTIC_ADVERBS": "deictic_adverbs",
    "CLAUSE_MARKERS": "conjunctions",
    "QUANTIFIERS_ALL": "quantifiers", "QUANTIFIERS_SOME": "quantifiers",
    "NUMBER_WORDS": "number_words",
    "IRREGULAR_VERB_FORMS": "irregular_forms", "IRREGULAR_NOUN_FORMS": "irregular_forms",
    "IRREGULAR_PARTICIPLES": "irregular_forms",
    "E_FINAL_STEM_ENDINGS": "suffix_rules", "SIBILANT_ENDINGS": "suffix_rules", "DOUBLED_CONSONANTS": "suffix_rules",
}

DETERMINERS = {"the", "a", "an", "this", "that", "these", "those"}
POSSESSIVE_DETERMINERS = {"my", "your", "his", "her", "its", "our", "their"}
PRONOUNS = {"i", "you", "he", "she", "it", "we", "they", "me", "him", "us", "them"}
WH_WORDS = {"who", "whom", "whose", "which", "what", "where", "when", "why", "how"}
PREPOSITIONS_TIME = {"during", "before", "after", "since", "until"}
PREPOSITIONS_PLACE = {"inside", "outside", "under", "behind", "near", "beside", "above", "below", "into",
                      "onto", "across", "through", "along", "around", "between", "among", "against",
                      "toward", "towards", "beneath", "over"}
PREPOSITIONS_AMBIGUOUS = {"in", "on", "at"}
PREPOSITIONS_UNCOVERED = {"with", "for", "to", "from", "of", "about", "without", "like", "than", "via", "per"}
COPULAS = {"is", "are", "was", "were", "am", "be", "been", "being"}
HAVE_FORMS = {"has", "have", "had"}
DO_FORMS = {"do", "does", "did"}
MODALS = {"will", "would", "can", "could", "may", "might", "must", "shall", "should"}
NEGATIVE_CONTRACTIONS = {"isn't": "is", "aren't": "are", "wasn't": "was", "weren't": "were", "don't": "do",
                         "doesn't": "does", "didn't": "did", "hasn't": "has", "haven't": "have", "hadn't": "had",
                         "won't": "will", "wouldn't": "would", "can't": "can", "cannot": "can", "couldn't": "could",
                         "shouldn't": "should", "mustn't": "must"}
NEGATORS = {"not", "never"}
NEGATIVE_PRONOUNS = {"none", "noone"}  # still not covered
NEGATIVE_SUBJECTS = {"nobody", "nothing"}  # addendum A2: subject only, neg(verb(_, ...))
DEICTIC_ADVERBS = {"yesterday", "today", "now", "tonight"}  # addendum A4: exclusively these four
CLAUSE_MARKERS = {"and", "or", "but", "because", "while", "although", "though", "if", "unless", "whereas",
                  "so", "nor", "whether"}
QUANTIFIERS_ALL = {"all", "every", "each"}
QUANTIFIERS_SOME = {"some", "several", "few"}
NUMBER_WORDS = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7",
                "eight": "8", "nine": "9", "ten": "10", "eleven": "11", "twelve": "12", "twenty": "20"}
IRREGULAR_VERB_FORMS = {
    "ran": "run", "ate": "eat", "eaten": "eat", "rose": "rise", "risen": "rise", "fell": "fall", "fallen": "fall",
    "won": "win", "lost": "lose", "began": "begin", "begun": "begin", "caught": "catch", "sold": "sell",
    "held": "hold", "left": "leave", "fed": "feed", "made": "make", "took": "take", "taken": "take",
    "gave": "give", "given": "give", "wrote": "write", "written": "write", "drove": "drive", "driven": "drive",
    "rode": "ride", "ridden": "ride", "sang": "sing", "sung": "sing", "swam": "swim", "swum": "swim",
    "sat": "sit", "stood": "stand", "went": "go", "gone": "go", "came": "come", "saw": "see", "seen": "see",
    "told": "tell", "brought": "bring", "bought": "buy", "found": "find", "got": "get", "kept": "keep",
    "met": "meet", "paid": "pay", "said": "say", "sent": "send", "taught": "teach", "wore": "wear",
    "worn": "wear", "broke": "break", "broken": "break", "chose": "choose", "chosen": "choose", "drew": "draw",
    "drawn": "draw", "drank": "drink", "drunk": "drink", "flew": "fly", "flown": "fly", "froze": "freeze",
    "frozen": "freeze", "hid": "hide", "hidden": "hide", "knew": "know", "known": "know", "led": "lead",
    "shook": "shake", "shaken": "shake", "slept": "sleep", "spoke": "speak", "spoken": "speak",
    "stole": "steal", "stolen": "steal", "threw": "throw", "thrown": "throw", "woke": "wake", "woken": "wake",
    "bit": "bite", "bitten": "bite", "fought": "fight", "thought": "think", "built": "build", "felt": "feel",
    "heard": "hear", "lent": "lend", "spent": "spend", "understood": "understand", "dug": "dig",
    "hung": "hang", "rang": "ring", "rung": "ring", "sank": "sink", "sunk": "sink", "spun": "spin",
    "struck": "strike", "swept": "sweep", "wept": "weep", "done": "do",
}
IRREGULAR_NOUN_FORMS = {"children": "child", "men": "man", "women": "woman", "feet": "foot", "teeth": "tooth",
                        "mice": "mouse", "geese": "goose", "oxen": "ox", "people": "people"}
E_FINAL_STEM_ENDINGS = ("v", "z", "c")
SIBILANT_ENDINGS = ("s", "x", "z", "ch", "sh")
DOUBLED_CONSONANTS = ("bb", "dd", "gg", "mm", "nn", "pp", "rr", "tt")

_VOWELS = "aeiou"
IRREGULAR_PARTICIPLES = {"eaten", "risen", "fallen", "won", "lost", "begun", "caught", "sold", "held", "left", "fed",
                     "made", "taken", "given", "written", "driven", "ridden", "sung", "swum", "seen", "told",
                     "brought", "bought", "found", "got", "kept", "met", "paid", "said", "sent", "taught", "worn",
                     "broken", "chosen", "drawn", "drunk", "flown", "frozen", "hidden", "known", "led", "shaken",
                     "slept", "spoken", "stolen", "thrown", "woken", "bitten", "fought", "thought", "built",
                     "felt", "heard", "lent", "spent", "understood", "dug", "hung", "rung", "sunk", "spun",
                     "struck", "swept", "wept", "done", "gone", "sat", "stood", "run", "come"}


# ------------------------------------------------------------------ 1. tokenisation

def tokenize(text: str) -> Optional[list]:
    raw = text.strip()
    if not raw.endswith("."):
        return None  # questions, exclamations, fragments: out of convention (R15)
    body = raw[:-1].strip().lower()
    if not body or re.search(r"[^a-z0-9' \-]", body):
        return None  # commas, semicolons, quotes...: not covered by the frozen rules
    out = []
    for token in body.split():
        if token in NEGATIVE_CONTRACTIONS:
            out.extend([NEGATIVE_CONTRACTIONS[token], "not"])
        elif "'" in token:
            return None  # other clitics (possessive 's, 're...) are not covered
        else:
            out.append(token)
    return out


# ------------------------------------------------------------------ 2. morphology

def _restore_e(stem: str) -> str:
    groups = re.findall(r"[aeiou]+", stem)
    if stem.endswith(E_FINAL_STEM_ENDINGS):
        return stem + "e"
    if (len(groups) == 1 and len(stem) >= 3 and stem[-2] in _VOWELS and stem[-1] not in _VOWELS + "wxy"
            and stem[-3] not in _VOWELS):
        return stem + "e"
    return stem


def verb_lemma(word: str) -> str:
    if word in IRREGULAR_VERB_FORMS:
        return IRREGULAR_VERB_FORMS[word]
    for suffix in ("ing", "ed"):
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            stem = word[: -len(suffix)]
            if suffix == "ed" and word.endswith("ied"):
                return word[:-3] + "y"
            if stem.endswith(DOUBLED_CONSONANTS):
                return stem[:-1]
            return _restore_e(stem)
    return present_lemma(word)


def present_lemma(word: str) -> str:
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("es") and word[:-2].endswith(SIBILANT_ENDINGS):
        # -sses/-xes/-ches/-shes/-zzes lose "es"; -ses/-ces/-ges/-zes (exercise, close) lose only "s"
        return word[:-2] if word[:-2].endswith(("ss", "x", "ch", "sh", "zz")) else word[:-1]
    if word.endswith("oes"):
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss") and len(word) > 2:
        return word[:-1]
    return word


def noun_lemma(word: str) -> str:
    if word in IRREGULAR_NOUN_FORMS:
        return IRREGULAR_NOUN_FORMS[word]
    if word.endswith(("us", "is", "ss")):
        return word
    return present_lemma(word)


def _closed(word: str) -> bool:
    return (word in DETERMINERS or word in POSSESSIVE_DETERMINERS or word in PRONOUNS or word in WH_WORDS
            or word in PREPOSITIONS_TIME or word in PREPOSITIONS_PLACE or word in PREPOSITIONS_AMBIGUOUS
            or word in PREPOSITIONS_UNCOVERED or word in COPULAS or word in HAVE_FORMS or word in DO_FORMS
            or word in MODALS or word in NEGATORS or word in NEGATIVE_PRONOUNS or word in CLAUSE_MARKERS
            or word in NEGATIVE_SUBJECTS or word in DEICTIC_ADVERBS
            or word in QUANTIFIERS_ALL or word in QUANTIFIERS_SOME or word in NUMBER_WORDS or word == "by"
            or word == "no")


def _is_preposition(word: str) -> bool:
    return word in PREPOSITIONS_TIME or word in PREPOSITIONS_PLACE or word in PREPOSITIONS_AMBIGUOUS


def _is_participle(word: str) -> bool:
    return word in IRREGULAR_PARTICIPLES or (word.endswith("ed") and len(word) > 4)


def _verbal_morphology(word: str) -> bool:
    return (word in IRREGULAR_VERB_FORMS or (word.endswith("ed") and len(word) > 4)
            or (word.endswith("s") and not word.endswith("ss") and len(word) > 3))


# ------------------------------------------------------------------ noun phrases (R5, R11, R12)

def noun_phrase(tokens: list, allow_bare: bool, subject: bool = False) -> Optional[tuple]:
    """(structure, negated_by_no) for a complete token span, or None when not covered."""
    if not tokens:
        return None
    i, card, quant, negated = 0, None, None, False
    first = tokens[0]
    if first in NEGATIVE_SUBJECTS:  # addendum A2: only as the whole subject
        return ("_", True) if subject and len(tokens) == 1 else None
    if first in POSSESSIVE_DETERMINERS:
        return None
    if first in PRONOUNS:
        return (first, False) if len(tokens) == 1 else None
    if first == "no":
        negated, i = True, 1
    elif first == "a" and len(tokens) > 1 and tokens[1] == "few":
        quant, i = "q_some", 2
    elif first in DETERMINERS:
        i = 1
    elif first in QUANTIFIERS_ALL:
        quant, i = "q_all", 1
        if len(tokens) > 1 and tokens[1] == "the":
            i = 2
    elif first in QUANTIFIERS_SOME:
        quant, i = "q_some", 1
    elif first in NUMBER_WORDS or first.isdigit():
        card, i = NUMBER_WORDS.get(first, first), 1
    elif not allow_bare:
        return None
    words = tokens[i:]
    if not words or any(_closed(w) for w in words) or any(w.endswith("ly") and len(w) > 4 for w in words):
        return None
    struct: object = noun_lemma(words[-1])
    for adjective in reversed(words[:-1]):  # closest to the noun first (R5, R13)
        struct = ["attr", struct, adjective]
    if card is not None:
        struct = ["card", struct, card]
    if quant is not None:
        struct = [quant, struct]
    return struct, negated


def _np_start(word: str) -> bool:
    return (word in DETERMINERS or word in QUANTIFIERS_ALL or word in QUANTIFIERS_SOME or word in NUMBER_WORDS
            or word.isdigit() or word == "no" or word in PRONOUNS)


# ------------------------------------------------------------------ clause parsing (R1-R12)

def _manner_adverbs(tokens: list) -> Optional[tuple]:
    """Remove -ly manner adverbs (R8) where their position is unambiguous; None if one sits inside a noun phrase."""
    kept, adverbs = [], []
    for k, word in enumerate(tokens):
        if word.endswith("ly") and len(word) > 4 and not _closed(word):
            prev = tokens[k - 1] if k else ""
            nxt = tokens[k + 1] if k + 1 < len(tokens) else ""
            if prev in DETERMINERS or prev in NUMBER_WORDS or prev in QUANTIFIERS_ALL or prev in QUANTIFIERS_SOME:
                return None  # inside a noun phrase: an adjective, not a manner adverb
            if nxt in NUMBER_WORDS or nxt.isdigit():
                return None  # modifies a number ("exactly ten"), not covered by the convention
            if prev not in COPULAS and nxt and not (_closed(nxt) or _verbal_morphology(nxt)):
                return None  # position between two open-class words: undecidable
            adverbs.append(word)
        else:
            kept.append(word)
    return kept, adverbs


def _split_prepositional(tokens: list) -> Optional[list]:
    """Split a tail into [(preposition, np_tokens)], None if a token is not covered."""
    out, k = [], 0
    while k < len(tokens):
        prep = tokens[k]
        if prep in PREPOSITIONS_UNCOVERED or not (_is_preposition(prep) or prep == "by"):
            return None
        k += 1
        start = k
        while k < len(tokens) and not (_is_preposition(tokens[k]) or tokens[k] == "by"
                                       or tokens[k] in PREPOSITIONS_UNCOVERED):
            k += 1
        out.append((prep, tokens[start:k]))
    return out


def _verb_group_start(tokens: list) -> Optional[int]:
    for k, word in enumerate(tokens):
        if word in COPULAS or word in HAVE_FORMS or word in DO_FORMS or word in MODALS:
            return k if k > 0 else None
    for k, word in enumerate(tokens):
        if k == 0:
            continue
        subject_words = [w for w in tokens[:k] if not _np_start(w) and w not in NEGATORS]
        if subject_words and _verbal_morphology(word) and not _closed(word):
            return k - 1 if tokens[k - 1] in NEGATORS else k  # pre-verbal "never"/"not" opens the verb group
    return None


def parse(text: str) -> Optional[object]:
    tokens = tokenize(text)
    if tokens is None:
        return None
    if any(t in CLAUSE_MARKERS or t in WH_WORDS or t in NEGATIVE_PRONOUNS or t in PREPOSITIONS_UNCOVERED
           or t == "no-one" for t in tokens):
        return None  # coordination, subordination, questions, uncovered negative subjects/prepositions
    deictic, deictic_initial = None, False  # addendum A4: sentence edges only
    if tokens and tokens[0] in DEICTIC_ADVERBS:
        deictic, deictic_initial, tokens = tokens[0], True, tokens[1:]
    elif tokens and tokens[-1] in DEICTIC_ADVERBS:
        deictic, tokens = tokens[-1], tokens[:-1]
    if any(t in DEICTIC_ADVERBS for t in tokens):
        return None  # a second deictic adverb, or one inside the sentence: position undecidable
    removed = _manner_adverbs(tokens)
    if removed is None:
        return None
    tokens, manner = removed
    if len(manner) > 1:
        return None  # relative order of several manner adverbs is not decidable from closed classes
    negations = sum(t in NEGATORS for t in tokens)
    if negations > 1:
        return None
    k = _verb_group_start(tokens)
    if k is None:
        return None
    subject = noun_phrase(tokens[:k], allow_bare=True, subject=True)
    if subject is None:
        return None
    subj, subject_neg = subject
    rest = tokens[k:]
    negated = subject_neg

    def take_negator(i: int) -> int:
        nonlocal negated
        if i < len(rest) and rest[i] in NEGATORS:
            negated = True
            return i + 1
        return i

    core, i, passive, attribute, place = None, 0, False, None, None
    word = rest[0]
    if word in COPULAS:
        i = take_negator(1)
        if i < len(rest) and rest[i] == "being":
            i += 1
        if i >= len(rest):
            return None
        nxt = rest[i]
        if nxt.endswith("ing") and not _closed(nxt):
            verb, i = verb_lemma(nxt), i + 1
        elif _is_participle(nxt) and not _closed(nxt):
            verb, i, passive = verb_lemma(nxt), i + 1, True
        elif nxt in PREPOSITIONS_PLACE or nxt in PREPOSITIONS_AMBIGUOUS:
            place, verb = nxt, None
        elif not _closed(nxt) and not nxt.endswith("s"):
            attribute, verb, i = nxt, None, i + 1
        else:
            return None
    elif word in HAVE_FORMS:
        i = take_negator(1)
        if i < len(rest) and rest[i] == "been":
            i += 1
            if i >= len(rest) or not _is_participle(rest[i]):
                return None
            verb, i, passive = verb_lemma(rest[i]), i + 1, True
        elif i < len(rest) and _is_participle(rest[i]):
            verb, i = verb_lemma(rest[i]), i + 1
        else:
            return None
    elif word in MODALS or word in DO_FORMS:
        i = take_negator(1)
        if word in DO_FORMS and not negated:
            return None  # emphatic do is not covered
        if i < len(rest) and rest[i] == "be":
            i += 1
            if i < len(rest) and _is_participle(rest[i]):
                verb, i, passive = verb_lemma(rest[i]), i + 1, True
            elif i < len(rest) and rest[i].endswith("ing"):
                verb, i = verb_lemma(rest[i]), i + 1
            else:
                return None
        elif i < len(rest) and not _closed(rest[i]):
            verb, i = rest[i], i + 1  # bare infinitive: already the lemma
        else:
            return None
    else:
        i = take_negator(0)  # pre-verbal negator ("never enters")
        if i >= len(rest) or _closed(rest[i]):
            return None
        verb, i = verb_lemma(rest[i]), i + 1

    if place is not None:  # R6: copula + preposition + noun phrase
        tail = _split_prepositional(rest[i:])
        if not tail or tail[0][0] != place:
            return None
        located = noun_phrase(tail[0][1], allow_bare=True)
        if located is None or located[1]:
            return None
        core, adjuncts = [place, subj, located[0]], tail[1:]
    else:
        obj = None
        if i < len(rest) and not (_is_preposition(rest[i]) or rest[i] == "by"):
            j = i
            while j < len(rest) and not (_is_preposition(rest[j]) or rest[j] == "by"):
                j += 1
            if not _np_start(rest[i]):
                return None  # bare post-verbal word: argument or deictic adverb, undecidable here
            parsed = noun_phrase(rest[i:j], allow_bare=False)
            if parsed is None or parsed[1]:
                return None
            obj, i = parsed[0], j
        tail = _split_prepositional(rest[i:])
        if tail is None:
            return None
        agent = "_"
        by_phrases = [t for t in tail if t[0] == "by"]
        if by_phrases:
            if not passive or len(by_phrases) > 1:
                return None
            parsed = noun_phrase(by_phrases[0][1], allow_bare=False)
            if parsed is None or parsed[1]:
                return None
            agent = parsed[0]
        adjuncts = [t for t in tail if t[0] != "by"]
        if attribute is not None:
            core = ["attr", subj, attribute]
        elif passive:
            if obj is not None:
                return None
            core = [verb, agent, subj]
        else:
            core = [verb, subj] + ([obj] if obj is not None else [])

    # R7-R9: wrap adjuncts in canonical serialisation order (manner, place, time; text order within a class)
    places, times, ambiguous = [], [], []
    for prep, np_tokens in adjuncts:
        parsed = noun_phrase(np_tokens, allow_bare=True)
        if parsed is None or parsed[1]:
            return None
        (times if prep in PREPOSITIONS_TIME else places if prep in PREPOSITIONS_PLACE else ambiguous).append(
            (prep, parsed[0]))
    if ambiguous and len(places) + len(times) + len(ambiguous) + (deictic is not None) > 1:
        return None  # serialisation order would depend on an in/on/at phrase whose class is undecidable
    if deictic is not None and deictic_initial and times:
        return None  # closeness to the verb of an initial deictic vs a time phrase is undecidable
    struct: object = core
    for adverb in manner:
        struct = [adverb, struct]
    for prep, np_struct in places + ambiguous + times:
        struct = [prep, struct, np_struct]
    if deictic is not None:
        struct = [deictic, struct]  # R8 time adverb, outermost of the time class (R9)
    if negated:
        struct = ["neg", struct]  # R10: outermost canonical layer
    return struct
