"""MetaHIA M7 -- JEV/Kev P8.3b: LABELED `instructions`-wording robustness.

Explicit follow-up requested after P8.3a: P8.3a tested LABELED's
sensitivity to the ORDER of `criteria`'s keys and found it real but
milder than STRICT's. The one remaining LABELED-specific input P8.3a
said nothing about is the exact wording of `instructions` -- always the
same hardcoded string, `DEFAULT_LABELED_GLOSSED_INSTRUCTIONS =
"Which relation applies to this sentence?"`, across every real run so
far (P8.1 baseline, all of P8.3a). Before treating LABELED's P8.1
numbers as settled, this module asks: does a synonymous rewording of
the instruction alone -- same criteria order (the P8.1/original order,
fixed, so this axis is not confounded with P8.3a's) -- move the result?

Required `m7_jev_relation_choice_v0_1.propose_relation_jev()` extension
(same day, in place, not a new module version -- P8's ongoing-work
convention, same as P8.1's 3-tuple change): a new optional
`instructions_override` parameter, `None` by default (preserves every
existing caller exactly). This was the only viable approach -- rebuilding
the LABELED request/response logic standalone here, just to vary one
string, would have duplicated `propose_relation_jev`'s already-tested
validation (self-loop rejection, closed-vocabulary rejection, malformed-
probability handling), the same "never force a parallel implementation"
discipline already applied throughout this project (e.g. Brier/ECE
reimplemented standalone in `m7_jev_benchmark_v0_2.py` only because THAT
case genuinely had an incompatible data model, not by default).

Five designed instruction variants, chosen for genuine variety in
register and structure (formal vs imperative vs indirect question),
not as near-duplicates of each other or of the original:

  formal            -- "Select the relation that best describes the
                        sentence below."
  imperative_short   -- "Classify this sentence."
  alt_phrasing       -- "What relationship does this sentence express?"
  verbose_careful     -- "Read the sentence carefully and choose the
                        single relation, if any, that it expresses."
  procedural         -- "Determine which relation, if any, applies to
                        the following text."

The original wording itself is NOT re-run here -- its LABELED result
already exists, real and saved
(`validation/jev_benchmark_v0_2_results_2026-09-22.json`), same
convention as every prior P8 ablation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence, Tuple

from m7_jev_benchmark_v0_2 import CORPUS_PATH, CaseOutcome, ConditionReport, load_corpus
from m7_jev_relation_choice_v0_1 import (
    DEFAULT_LABELED_GLOSSED_INSTRUCTIONS,
    RELATION_VOCABULARY_MODE_LABELED,
    JevDecideClient,
    propose_relation_jev,
)

INSTRUCTION_VARIANTS: Mapping[str, str] = {
    "formal": "Select the relation that best describes the sentence below.",
    "imperative_short": "Classify this sentence.",
    "alt_phrasing": "What relationship does this sentence express?",
    "verbose_careful": "Read the sentence carefully and choose the single relation, if any, that it expresses.",
    "procedural": "Determine which relation, if any, applies to the following text.",
}

assert DEFAULT_LABELED_GLOSSED_INSTRUCTIONS not in INSTRUCTION_VARIANTS.values(), (
    "every variant must be genuinely different from the original wording -- "
    "re-testing the original under a new name would silently double-count it"
)


def run_instruction_robustness(
    client: JevDecideClient,
    variants: Mapping[str, str] = INSTRUCTION_VARIANTS,
    *,
    corpus_path: Path = CORPUS_PATH,
) -> Tuple[ConditionReport, ...]:
    """Runs the full 39-case evaluation corpus through LABELED for each
    supplied `instructions` wording, criteria order fixed to
    `load_corpus()`'s own vocabulary order (the same order P8.1's
    baseline used) so this axis is never confounded with P8.3a's
    criteria-order axis. Always LABELED -- STRICT's `instructions` is
    tied to its worked-examples framing (P8.2's axis) and GLOSSED's
    wording robustness is explicitly out of scope for P8.3 (LABELED
    only, per the request that started this sub-chapter).
    """
    vocabulary, _demonstration_set, cases = load_corpus(corpus_path)
    reports = []
    for label, instructions_text in variants.items():
        outcomes = []
        for case in cases:
            proposal = propose_relation_jev(
                text=case.text,
                subject=case.subject,
                obj=case.object,
                all_relations=vocabulary,
                semantic_condition=RELATION_VOCABULARY_MODE_LABELED,
                client=client,
                instructions_override=instructions_text,
            )
            outcomes.append(
                CaseOutcome(
                    case_id=case.case_id,
                    category=case.category,
                    expected_relation=case.expected_relation,
                    proposal=proposal,
                )
            )
        reports.append(
            ConditionReport(semantic_condition=f"LABELED_instructions_{label}", vocabulary=vocabulary, outcomes=tuple(outcomes))
        )
    return tuple(reports)


__all__ = ["INSTRUCTION_VARIANTS", "run_instruction_robustness"]
