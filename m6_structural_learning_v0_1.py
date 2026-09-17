"""MetaHIA M6 -- Structural Learning v0.1.

Learns `Rule x Context x Depth x Provenance -> distribution of epistemic
outcomes`. M6 is a calibration/learning layer over records that M4 and M5
already produce -- it introduces no new epistemic vocabulary and no new
"ground truth" source of its own.

Design decisions (fixed 2026-09-17, agreed before implementation):

1. Rule identity is structural, never reference identity and never a
   human-assigned name: `structural_signature(pattern)` (kernel2.py) for a
   Node-kind PATTERN/SHAPE_PATTERN, or `path_pattern_structural_form(pattern)`
   for a `PathPattern` (E20-D.12 generalized path rule) -- widened 2026-09-17
   when a real corpus surfaced that `generalize_path_pattern()` produces
   `PathPattern`, not `Node`, and `PathPattern`'s own default dataclass
   equality includes its per-discovery `pattern_id`/`source_path_ids`, which
   would wrongly split one abstract rule into as many "rules" as discovery
   events. Two different instances of the same abstract pattern, of either
   kind, must be the same rule for learning purposes.

2. Context is deliberately coarse (3 bands x 3 bands on novelty/redundancy =
   9 buckets), because the learning key is `Rule x Context x Depth x
   Provenance` and a context axis as fine as M5's raw floats would starve
   every bucket of support. `Provenance` here is M4's closed 3-valued
   evidence vocabulary (GROUNDED_DIRECT/GROUNDED_ANALOGY/UNGROUNDED_HUMAN),
   never M5's per-fact-chain `path.provenance` tuple, which is unique per
   observation and cannot repeat -- using it as a bucket key would give every
   rule exactly one example per bucket and make calibration meaningless.

3. Learned outcome classes are exactly M4/M2's three SETTLED states --
   SUPPORTED, CONTRADICTED, UNKNOWN. DERIVED is deliberately excluded: it is
   the pre-evaluation state, not an observed outcome, and predicting it would
   blur "not yet evaluated" with "evaluated".

4. A record's `outcome` must come from M4's independent evidence resolution
   (an `AcquisitionTransition` outcome), never from the mere existence of a
   derived pattern. This is M2's own founding invariant ("a derivation cannot
   be its own evidence") applied at the M6 layer: `StructuralOutcomeRecord`
   validates its `outcome`/`provenance` against the closed vocabularies at
   construction time and never accepts DERIVED as an outcome.

5. train/validation/holdout is split by RULE, never by individual record: if
   one rule's records were scattered across splits, holdout would only test
   memorization of stats already seen for that exact rule, not generalization
   to an unseen rule -- the same holdout philosophy E20-D/M3 already use
   ("holdout on renamed operands", never "holdout on an instance of the same
   rule").

6. Calibration reuses the project's existing vocabulary (ECE, Brier) rather
   than inventing a new metric: multi-class Brier score is the primary,
   promotion-blocking metric; top-label ECE is a secondary diagnostic. Both
   are reported sliced by rule, context, depth and provenance separately, per
   the roadmap's explicit requirement -- a single global number is not
   sufficient to decide promotion.

7. Promotion (`evaluate_promotion`) blocks by default in v0.1 (not merely
   reported) whenever: the holdout is empty, the candidate's holdout Brier
   exceeds an absolute threshold, the candidate regresses versus the previous
   promoted version, or any bucket with enough support to be trusted
   (`min_bucket_support`) is catastrophically miscalibrated. A policy is
   versioned and `fit()` always returns a new, immutable policy -- version
   only ever increases through a genuine training update, never through
   `predict()`.

Trajectory (roadmap Sec. 11): this module covers M6 IMPLEMENTATION only.
Third-party validation and the independent holdout gate are separate,
later steps -- exactly as for M3, M4 and M5.
"""
from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Sequence, Tuple

from kernel2 import Node, PathPattern, path_pattern_structural_form, structural_signature
from m4_cold_start_evidence_v0_1 import (
    CONTRADICTED,
    GROUNDED_ANALOGY,
    GROUNDED_DIRECT,
    SUPPORTED,
    UNGROUNDED_HUMAN,
    UNKNOWN,
)

OUTCOME_CLASSES: Tuple[str, ...] = (SUPPORTED, CONTRADICTED, UNKNOWN)
PROVENANCE_CLASSES: Tuple[str, ...] = (GROUNDED_DIRECT, GROUNDED_ANALOGY, UNGROUNDED_HUMAN)
CONTEXT_BANDS: Tuple[str, ...] = ("LOW", "MED", "HIGH")

BASIS_EXACT_BUCKET = "EXACT_BUCKET"
BASIS_RULE_ONLY = "RULE_ONLY"
BASIS_GLOBAL_PRIOR = "GLOBAL_PRIOR"
BASIS_UNIFORM_NO_DATA = "UNIFORM_NO_DATA"


def _band(value: float) -> str:
    """Bands a [0,1]-clipped float into LOW/MED/HIGH (thirds)."""
    v = max(0.0, min(1.0, float(value)))
    if v < 1.0 / 3.0:
        return "LOW"
    if v < 2.0 / 3.0:
        return "MED"
    return "HIGH"


def _rule_signature(rule: object):
    """Structural, reference-free identity for a rule of either supported kind.

    `PathPattern` is a plain frozen dataclass whose default equality includes
    `pattern_id`/`source_path_ids` -- fields that encode WHICH discovery event
    produced it, not what the pattern structurally IS. Two PathPattern
    instances describing the identical operator/direction/binding skeleton
    but discovered from different paths must still be the SAME rule for
    learning purposes, exactly like two Node-kind PATTERN instances already
    are via `structural_signature()`. `path_pattern_structural_form()` is
    kernel2.py's own purpose-built stripped-down form for this (fixed
    2026-09-17, found while wiring in a real E20-D.12-generalized corpus).
    """
    if isinstance(rule, PathPattern):
        return path_pattern_structural_form(rule)
    return structural_signature(rule)


@dataclass(frozen=True)
class StructuralOutcomeRecord:
    """One independently-resolved (rule, context) observation for M6 to learn from.

    `outcome` must be the result of M4's evidence resolution, not the mere
    existence of `rule` as a discovered pattern -- see module docstring, point 4.
    """

    record_id: str
    rule: object
    novelty: float
    redundancy: float
    depth: int
    provenance: str
    outcome: str

    def __post_init__(self) -> None:
        if not self.record_id:
            raise ValueError("record_id is required")
        if not isinstance(self.rule, (Node, PathPattern)):
            raise ValueError(
                "rule must be a kernel Node (PATTERN or SHAPE_PATTERN) or a "
                "PathPattern (E20-D.12 generalized path rule)"
            )
        if self.outcome not in OUTCOME_CLASSES:
            raise ValueError(
                f"outcome must be one of {OUTCOME_CLASSES!r} (a settled, "
                f"independently-resolved state), got {self.outcome!r} -- "
                "DERIVED is never a valid learning outcome"
            )
        if self.provenance not in PROVENANCE_CLASSES:
            raise ValueError(f"provenance must be one of {PROVENANCE_CLASSES!r}, got {self.provenance!r}")
        if self.depth < 0:
            raise ValueError("depth must be >= 0")

    @property
    def rule_signature(self):
        """Structural, reference-free identity of this record's rule."""
        return _rule_signature(self.rule)

    def bucket_key(self) -> Tuple[object, str, str, int, str]:
        return (
            self.rule_signature,
            _band(self.novelty),
            _band(self.redundancy),
            int(self.depth),
            self.provenance,
        )


def split_by_rule(
    records: Sequence[StructuralOutcomeRecord],
    *,
    val_fraction: float = 0.2,
    holdout_fraction: float = 0.2,
    seed: int = 0,
) -> Tuple[Tuple[StructuralOutcomeRecord, ...], Tuple[StructuralOutcomeRecord, ...], Tuple[StructuralOutcomeRecord, ...]]:
    """Splits records into (train, validation, holdout), partitioned by RULE.

    Every record of a given rule lands in exactly one split -- never scattered
    across two -- so holdout measures generalization to an unseen rule, not
    memorization of a rule already partially seen in training.
    """
    if not (0.0 <= val_fraction and 0.0 <= holdout_fraction and val_fraction + holdout_fraction < 1.0):
        raise ValueError("val_fraction and holdout_fraction must be >= 0 and sum to < 1")

    rule_ids = sorted({r.rule_signature for r in records}, key=repr)
    rng = random.Random(seed)
    shuffled = list(rule_ids)
    rng.shuffle(shuffled)

    n = len(shuffled)
    n_holdout = int(round(n * holdout_fraction))
    n_val = int(round(n * val_fraction))
    holdout_ids = set(shuffled[:n_holdout])
    val_ids = set(shuffled[n_holdout:n_holdout + n_val])

    train, val, holdout = [], [], []
    for r in records:
        if r.rule_signature in holdout_ids:
            holdout.append(r)
        elif r.rule_signature in val_ids:
            val.append(r)
        else:
            train.append(r)
    return tuple(train), tuple(val), tuple(holdout)


@dataclass(frozen=True)
class StructuralPrediction:
    """An auditable prediction: the distribution AND how confident its basis is.

    `basis` never overstates its own evidence -- a caller can tell an
    exact-bucket estimate from a global-prior fallback with zero data.
    """

    distribution: Mapping[str, float]
    basis: str
    support: int


class StructuralLearningPolicy:
    """Versioned, immutable-update policy mapping (rule, context, depth,
    provenance) to an empirical distribution over OUTCOME_CLASSES.

    `fit()` always returns a NEW policy; nothing mutates an existing one.
    `version` starts at 0 (never trained) and only increases through `fit()`,
    mirroring M5's versioning contract -- never through `predict()`.
    """

    def __init__(self) -> None:
        self._version = 0
        self._bucket_counts: Dict[tuple, Counter] = {}
        self._rule_counts: Dict[object, Counter] = {}
        self._global_counts: Counter = Counter()

    @property
    def version(self) -> int:
        return self._version

    def fit(self, train_records: Sequence[StructuralOutcomeRecord]) -> "StructuralLearningPolicy":
        new = StructuralLearningPolicy()
        bucket_counts: Dict[tuple, Counter] = defaultdict(Counter)
        rule_counts: Dict[object, Counter] = defaultdict(Counter)
        global_counts: Counter = Counter()
        for r in train_records:
            bucket_counts[r.bucket_key()][r.outcome] += 1
            rule_counts[r.rule_signature][r.outcome] += 1
            global_counts[r.outcome] += 1
        new._bucket_counts = dict(bucket_counts)
        new._rule_counts = dict(rule_counts)
        new._global_counts = global_counts
        new._version = self._version + 1
        return new

    def predict(self, rule: object, novelty: float, redundancy: float, depth: int, provenance: str) -> StructuralPrediction:
        sig = _rule_signature(rule)
        key = (sig, _band(novelty), _band(redundancy), int(depth), provenance)

        bucket = self._bucket_counts.get(key)
        if bucket:
            return self._to_prediction(bucket, BASIS_EXACT_BUCKET)

        rule_bucket = self._rule_counts.get(sig)
        if rule_bucket:
            return self._to_prediction(rule_bucket, BASIS_RULE_ONLY)

        if self._global_counts:
            return self._to_prediction(self._global_counts, BASIS_GLOBAL_PRIOR)

        uniform = {c: 1.0 / len(OUTCOME_CLASSES) for c in OUTCOME_CLASSES}
        return StructuralPrediction(distribution=uniform, basis=BASIS_UNIFORM_NO_DATA, support=0)

    @staticmethod
    def _to_prediction(counter: Counter, basis: str) -> StructuralPrediction:
        total = sum(counter.values())
        dist = {c: counter.get(c, 0) / total for c in OUTCOME_CLASSES}
        return StructuralPrediction(distribution=dist, basis=basis, support=total)


def brier_score_multiclass(policy: StructuralLearningPolicy, records: Sequence[StructuralOutcomeRecord]) -> float:
    """Mean squared error between the predicted distribution and the one-hot
    true outcome, averaged over `records`. In [0, 2] for 3 classes; 0 is
    perfect, proper (never rewards overconfidence)."""
    if not records:
        raise ValueError("brier_score_multiclass requires at least one record")
    total = 0.0
    for r in records:
        pred = policy.predict(r.rule, r.novelty, r.redundancy, r.depth, r.provenance)
        total += sum(
            (pred.distribution.get(c, 0.0) - (1.0 if c == r.outcome else 0.0)) ** 2
            for c in OUTCOME_CLASSES
        )
    return total / len(records)


def expected_calibration_error_top_label(
    policy: StructuralLearningPolicy,
    records: Sequence[StructuralOutcomeRecord],
    *,
    n_bins: int = 10,
) -> float:
    """Standard top-label multi-class ECE: bins predictions by the confidence
    of the arg-max class, compares mean confidence to accuracy per bin."""
    if not records:
        raise ValueError("expected_calibration_error_top_label requires at least one record")
    if n_bins < 1:
        raise ValueError("n_bins must be >= 1")

    bins: list = [[] for _ in range(n_bins)]
    for r in records:
        pred = policy.predict(r.rule, r.novelty, r.redundancy, r.depth, r.provenance)
        top_class = max(pred.distribution, key=pred.distribution.get)
        confidence = pred.distribution[top_class]
        correct = top_class == r.outcome
        idx = min(int(confidence * n_bins), n_bins - 1)
        bins[idx].append((confidence, correct))

    n = len(records)
    ece = 0.0
    for bucket in bins:
        if not bucket:
            continue
        bucket_conf = sum(c for c, _ in bucket) / len(bucket)
        bucket_acc = sum(1 for _, ok in bucket if ok) / len(bucket)
        ece += (len(bucket) / n) * abs(bucket_conf - bucket_acc)
    return ece


@dataclass(frozen=True)
class CalibrationSlice:
    key: object
    dimension: str
    brier: float
    support: int
    sufficient_data: bool


def calibration_report(
    policy: StructuralLearningPolicy,
    records: Sequence[StructuralOutcomeRecord],
    dimension: str,
    *,
    min_support: int = 5,
) -> Tuple[CalibrationSlice, ...]:
    """Brier score decomposed by one of 'rule', 'context', 'depth', 'provenance'
    -- the roadmap requires per-axis metrics, not a single global number."""
    groups: Dict[object, list] = defaultdict(list)
    for r in records:
        if dimension == "rule":
            k = r.rule_signature
        elif dimension == "context":
            k = (_band(r.novelty), _band(r.redundancy))
        elif dimension == "depth":
            k = r.depth
        elif dimension == "provenance":
            k = r.provenance
        else:
            raise ValueError(f"unknown calibration dimension: {dimension!r}")
        groups[k].append(r)

    slices = []
    for k, group in groups.items():
        brier = brier_score_multiclass(policy, group)
        slices.append(
            CalibrationSlice(key=k, dimension=dimension, brier=brier, support=len(group), sufficient_data=len(group) >= min_support)
        )
    return tuple(slices)


@dataclass(frozen=True)
class PromotionDecision:
    promote: bool
    reasons: Tuple[str, ...]
    holdout_brier: Optional[float]
    previous_holdout_brier: Optional[float]


def evaluate_promotion(
    candidate: StructuralLearningPolicy,
    previous: Optional[StructuralLearningPolicy],
    holdout_records: Sequence[StructuralOutcomeRecord],
    *,
    brier_threshold: float,
    per_bucket_brier_threshold: Optional[float] = None,
    min_bucket_support: int = 5,
) -> PromotionDecision:
    """Fail-closed promotion gate (Brier blocks promotion in v0.1, per design
    decision 2026-09-17): promotion requires ALL of holdout non-empty,
    candidate holdout Brier at or below `brier_threshold`, no regression
    versus `previous`'s holdout Brier, and no sufficiently-supported bucket
    catastrophically miscalibrated. Buckets without `min_bucket_support`
    examples are reported but never used to block or clear promotion -- there
    is not enough evidence to trust them either way."""
    if not holdout_records:
        return PromotionDecision(promote=False, reasons=("EMPTY_HOLDOUT",), holdout_brier=None, previous_holdout_brier=None)

    reasons = []
    candidate_brier = brier_score_multiclass(candidate, holdout_records)
    previous_brier = brier_score_multiclass(previous, holdout_records) if previous is not None else None

    if candidate_brier > brier_threshold:
        reasons.append("HOLDOUT_BRIER_ABOVE_THRESHOLD")
    if previous_brier is not None and candidate_brier > previous_brier:
        reasons.append("REGRESSION_VS_PREVIOUS_VERSION")

    if per_bucket_brier_threshold is not None:
        per_rule = calibration_report(candidate, holdout_records, "rule", min_support=min_bucket_support)
        for sl in per_rule:
            if sl.sufficient_data and sl.brier > per_bucket_brier_threshold:
                reasons.append(f"CATASTROPHIC_BUCKET:{sl.key!r}")

    return PromotionDecision(
        promote=not reasons,
        reasons=tuple(reasons),
        holdout_brier=candidate_brier,
        previous_holdout_brier=previous_brier,
    )


__all__ = [
    "OUTCOME_CLASSES",
    "PROVENANCE_CLASSES",
    "CONTEXT_BANDS",
    "BASIS_EXACT_BUCKET",
    "BASIS_RULE_ONLY",
    "BASIS_GLOBAL_PRIOR",
    "BASIS_UNIFORM_NO_DATA",
    "StructuralOutcomeRecord",
    "split_by_rule",
    "StructuralPrediction",
    "StructuralLearningPolicy",
    "brier_score_multiclass",
    "expected_calibration_error_top_label",
    "CalibrationSlice",
    "calibration_report",
    "PromotionDecision",
    "evaluate_promotion",
]
