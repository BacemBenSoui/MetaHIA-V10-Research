"""MetaHIA M5 — Metacognitive Dynamic Controller v0.1.

M5 is an additive policy layer above M4/D19.  It does not modify kernel2.py
and never interprets semantic labels.

Design contract
---------------
- D19 provides a structural candidate and a static ROI signal.
- M5 observes the result of its own prior decisions and updates a policy.
- M2 remains the only authority for epistemic state assignment.
- M5 may *observe* an externally supplied epistemic transition, but does not
  adjudicate truth from it.
- Policy state is keyed only by structural/control context, not semantic labels.
- The same context + same policy history produces the same decision.
- Learning is online but versioned and serializable.
- A policy change requires a minimum observation count and a measurable drift
  signal; otherwise the controller stays with the baseline strategy.

Decision space
--------------
CONTINUE          continue structural exploration
DEFER             keep candidate for later
STOP              stop this candidate/branch
REQUEST_EVIDENCE  request evidence via M4
CHANGE_STRATEGY   switch from the current learned strategy to baseline or a
                  more conservative strategy for the current context
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from math import isfinite
from statistics import fmean
from typing import Dict, Iterable, Mapping, MutableMapping, Optional, Sequence, Tuple

from e20d_cognitive_control_v0_1 import (
    DECISION_DEFER,
    DECISION_EXPLORE,
    DECISION_STOP,
    PathCandidate,
    score_candidate,
    structural_cost,
)
from kernel2 import PathRecord, path_properties


DECISION_CONTINUE = "CONTINUE"
DECISION_REQUEST_EVIDENCE = "REQUEST_EVIDENCE"
DECISION_CHANGE_STRATEGY = "CHANGE_STRATEGY"


@dataclass(frozen=True)
class ControlContext:
    """Non-semantic context observed by M5."""

    depth: int
    uncertainty: float = 0.0
    provenance: Tuple[str, ...] = ()
    conflict: float = 0.0
    novelty: float = 1.0
    redundancy: float = 0.0
    cost: float = 1.0
    expected_gain: float = 0.0

    @classmethod
    def from_path_candidate(cls, candidate: PathCandidate) -> "ControlContext":
        props = path_properties(candidate.path)
        return cls(
            depth=int(props.length),
            uncertainty=0.0,
            provenance=tuple(candidate.path.provenance),
            conflict=0.0,
            novelty=float(candidate.structural_novelty),
            redundancy=float(candidate.redundancy),
            cost=float(candidate.estimated_cost),
            expected_gain=float(candidate.expected_gain),
        )

    def key(self) -> Tuple[object, ...]:
        """Stable context key. Values are bucketed to prevent unbounded policy keys."""
        return (
            int(max(0, self.depth)),
            round(_clip01(self.uncertainty), 1),
            tuple(self.provenance),
            round(_clip01(self.conflict), 1),
            round(_clip01(self.novelty), 1),
            round(_clip01(self.redundancy), 1),
            round(max(0.0, self.cost), 1),
        )


@dataclass(frozen=True)
class ExplorationObservation:
    """Outcome of one M5 decision, supplied by the execution layer."""

    observation_id: str
    context: ControlContext
    decision: str
    expected_roi: float
    realized_gain: float
    actual_cost: float
    useful: bool
    epistemic_transition: Optional[Tuple[str, str]] = None
    candidate_id: Optional[str] = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.observation_id:
            raise ValueError("observation_id is required")
        allowed = {
            DECISION_CONTINUE,
            DECISION_EXPLORE,
            DECISION_DEFER,
            DECISION_STOP,
            DECISION_REQUEST_EVIDENCE,
            DECISION_CHANGE_STRATEGY,
        }
        if self.decision not in allowed:
            raise ValueError("invalid decision")
        if not isfinite(float(self.expected_roi)):
            raise ValueError("expected_roi must be finite")
        if not isfinite(float(self.realized_gain)) or float(self.realized_gain) < 0:
            raise ValueError("realized_gain must be finite and >= 0")
        if not isfinite(float(self.actual_cost)) or float(self.actual_cost) < 0:
            raise ValueError("actual_cost must be finite and >= 0")
        if not isinstance(self.useful, bool):
            raise ValueError("useful must be boolean")
        if self.epistemic_transition is not None:
            if len(self.epistemic_transition) != 2:
                raise ValueError("epistemic_transition must contain (from_state, to_state)")

    @property
    def realized_roi(self) -> float:
        return float(self.realized_gain) / max(float(self.actual_cost), 1e-9)


@dataclass(frozen=True)
class PolicyStats:
    """Versioned empirical state for one structural/control context."""

    attempts: int = 0
    useful_count: int = 0
    gains: Tuple[float, ...] = ()
    costs: Tuple[float, ...] = ()
    realized_rois: Tuple[float, ...] = ()

    @property
    def mean_gain(self) -> float:
        return fmean(self.gains) if self.gains else 0.0

    @property
    def mean_cost(self) -> float:
        return fmean(self.costs) if self.costs else 0.0

    @property
    def mean_roi(self) -> float:
        return fmean(self.realized_rois) if self.realized_rois else 0.0

    @property
    def useful_rate(self) -> float:
        return self.useful_count / self.attempts if self.attempts else 0.0

    def observe(self, observation: ExplorationObservation, *, memory: int = 32) -> "PolicyStats":
        gain_values = (self.gains + (float(observation.realized_gain),))[-memory:]
        cost_values = (self.costs + (float(observation.actual_cost),))[-memory:]
        roi_values = (self.realized_rois + (observation.realized_roi,))[-memory:]
        return PolicyStats(
            attempts=self.attempts + 1,
            useful_count=self.useful_count + int(observation.useful),
            gains=gain_values,
            costs=cost_values,
            realized_rois=roi_values,
        )


@dataclass(frozen=True)
class PolicySnapshot:
    """Immutable export of the learned controller state."""

    version: int
    total_observations: int
    contexts: Mapping[Tuple[object, ...], PolicyStats]


@dataclass(frozen=True)
class MetacognitiveDecision:
    """Auditable decision emitted by M5."""

    context_key: Tuple[object, ...]
    decision: str
    strategy: str
    policy_version: int
    expected_gain: float
    expected_roi: float
    baseline_roi: float
    historical_roi: float
    historical_useful_rate: float
    drift: float
    reason_codes: Tuple[str, ...]


@dataclass(frozen=True)
class DynamicBenchmarkResult:
    """Comparison of a dynamic policy to an exhaustive/static baseline."""

    exhaustive_cost: float
    dynamic_cost: float
    exhaustive_gain: float
    dynamic_gain: float
    exhaustive_useful: int
    dynamic_useful: int
    total_targets: int
    dynamic_decisions: Tuple[str, ...]

    @property
    def cost_reduction(self) -> float:
        if self.exhaustive_cost <= 0:
            return 0.0
        return 1.0 - self.dynamic_cost / self.exhaustive_cost

    @property
    def gain_retention(self) -> float:
        if self.exhaustive_gain <= 0:
            return 1.0
        return self.dynamic_gain / self.exhaustive_gain

    @property
    def useful_coverage(self) -> float:
        if self.total_targets <= 0:
            return 0.0
        return self.dynamic_useful / self.total_targets


def _clip01(value: float) -> float:
    value = float(value)
    return max(0.0, min(1.0, value))


class MetacognitiveController:
    """Online controller that learns exploration utility from observed outcomes."""

    def __init__(
        self,
        *,
        explore_threshold: float = 0.5,
        defer_threshold: float = 0.2,
        min_observations_for_adaptation: int = 3,
        drift_threshold: float = 0.35,
        conservative_factor: float = 0.75,
        memory: int = 32,
    ) -> None:
        if explore_threshold < defer_threshold:
            raise ValueError("explore_threshold must be >= defer_threshold")
        if min_observations_for_adaptation < 1:
            raise ValueError("min_observations_for_adaptation must be >= 1")
        if not 0.0 <= drift_threshold:
            raise ValueError("drift_threshold must be >= 0")
        if not 0.0 < conservative_factor <= 1.0:
            raise ValueError("conservative_factor must be in (0,1]")
        if memory < 1:
            raise ValueError("memory must be >= 1")
        self.explore_threshold = float(explore_threshold)
        self.defer_threshold = float(defer_threshold)
        self.min_observations_for_adaptation = int(min_observations_for_adaptation)
        self.drift_threshold = float(drift_threshold)
        self.conservative_factor = float(conservative_factor)
        self.memory = int(memory)
        self._version = 0
        self._total_observations = 0
        self._contexts: MutableMapping[Tuple[object, ...], PolicyStats] = {}

    @property
    def version(self) -> int:
        return self._version

    @property
    def total_observations(self) -> int:
        return self._total_observations

    def snapshot(self) -> PolicySnapshot:
        return PolicySnapshot(
            version=self._version,
            total_observations=self._total_observations,
            contexts=dict(self._contexts),
        )

    def observe(self, observation: ExplorationObservation) -> PolicySnapshot:
        """Update empirical strategy from the observed result.

        M5 records the result; it does not decide whether the transition was
        semantically correct. The caller owns ``useful`` and the epistemic
        transition label.
        """
        observation.validate()
        key = observation.context.key()
        old = self._contexts.get(key, PolicyStats())
        self._contexts[key] = old.observe(observation, memory=self.memory)
        self._total_observations += 1
        self._version += 1
        return self.snapshot()

    def _stats_for(self, context: ControlContext) -> PolicyStats:
        return self._contexts.get(context.key(), PolicyStats())

    def _baseline(self, context: ControlContext) -> Tuple[str, float, Tuple[str, ...]]:
        roi = max(0.0, float(context.expected_gain)) * _clip01(context.novelty)
        roi *= 1.0 - _clip01(context.redundancy)
        roi /= max(float(context.cost), 1e-9)
        if roi >= self.explore_threshold:
            return DECISION_CONTINUE, roi, ("BASELINE_EXPLORE",)
        if roi >= self.defer_threshold:
            return DECISION_DEFER, roi, ("BASELINE_DEFER",)
        return DECISION_STOP, roi, ("BASELINE_STOP",)

    def decide(
        self,
        context: ControlContext,
        *,
        evidence_available: bool = False,
        force_request_on_high_uncertainty: float = 1.1,
    ) -> MetacognitiveDecision:
        """Choose the next action using baseline + learned outcome history."""
        baseline_decision, baseline_roi, baseline_reasons = self._baseline(context)
        stats = self._stats_for(context)
        historical_roi = stats.mean_roi
        historical_useful = stats.useful_rate

        expected_gain = max(0.0, float(context.expected_gain))
        drift = 0.0
        strategy = "BASELINE"
        reasons = list(baseline_reasons)

        if stats.attempts >= self.min_observations_for_adaptation:
            expected_baseline_roi = max(baseline_roi, 1e-9)
            drift = abs(historical_roi - expected_baseline_roi) / expected_baseline_roi
            if drift >= self.drift_threshold:
                strategy = "ADAPTIVE"
                expected_gain = max(expected_gain, stats.mean_gain)
                if historical_roi < expected_baseline_roi:
                    expected_gain *= self.conservative_factor
                    reasons.append("NEGATIVE_DRIFT_CONSERVATIVE_ADJUSTMENT")
                else:
                    expected_gain = max(expected_gain, stats.mean_gain)
                    reasons.append("POSITIVE_DRIFT_GAIN_UPDATE")
            else:
                reasons.append("STABLE_HISTORY")

        adapted_roi = expected_gain * _clip01(context.novelty)
        adapted_roi *= 1.0 - _clip01(context.redundancy)
        adapted_roi /= max(float(context.cost), 1e-9)

        if evidence_available and _clip01(context.uncertainty) >= force_request_on_high_uncertainty:
            # Unreachable for normalized uncertainty, kept as an explicit API
            # guard for callers that supply a >1 domain-specific scale.
            decision = DECISION_REQUEST_EVIDENCE
            reasons.append("EXPLICIT_EVIDENCE_REQUEST")
        elif _clip01(context.uncertainty) >= 0.8 and evidence_available:
            decision = DECISION_REQUEST_EVIDENCE
            reasons.append("HIGH_UNCERTAINTY_WITH_EVIDENCE_AVAILABLE")
        elif strategy == "ADAPTIVE" and drift >= self.drift_threshold and historical_useful < 0.34:
            decision = DECISION_CHANGE_STRATEGY
            reasons.append("LOW_HISTORICAL_USEFUL_RATE")
        elif adapted_roi >= self.explore_threshold:
            decision = DECISION_CONTINUE
            reasons.append("ADAPTIVE_CONTINUE")
        elif adapted_roi >= self.defer_threshold:
            decision = DECISION_DEFER
            reasons.append("ADAPTIVE_DEFER")
        else:
            decision = DECISION_STOP
            reasons.append("ADAPTIVE_STOP")

        return MetacognitiveDecision(
            context_key=context.key(),
            decision=decision,
            strategy=strategy,
            policy_version=self._version,
            expected_gain=expected_gain,
            expected_roi=adapted_roi,
            baseline_roi=baseline_roi,
            historical_roi=historical_roi,
            historical_useful_rate=historical_useful,
            drift=drift,
            reason_codes=tuple(reasons),
        )

    def decide_for_candidate(
        self,
        candidate: PathCandidate,
        *,
        uncertainty: float = 0.0,
        provenance: Optional[Sequence[str]] = None,
        conflict: float = 0.0,
        evidence_available: bool = False,
    ) -> MetacognitiveDecision:
        context = ControlContext(
            depth=path_properties(candidate.path).length,
            uncertainty=uncertainty,
            provenance=tuple(provenance or candidate.path.provenance),
            conflict=conflict,
            novelty=candidate.structural_novelty,
            redundancy=candidate.redundancy,
            cost=candidate.estimated_cost,
            expected_gain=candidate.expected_gain,
        )
        return self.decide(context, evidence_available=evidence_available)


def replay_policy(
    controller: MetacognitiveController,
    observations: Iterable[ExplorationObservation],
) -> PolicySnapshot:
    """Replay observations deterministically to rebuild policy state."""
    for observation in observations:
        controller.observe(observation)
    return controller.snapshot()


def dynamic_vs_exhaustive(
    *,
    total_targets: int,
    exhaustive_cost: float,
    exhaustive_gain: float,
    exhaustive_useful: int,
    dynamic_observations: Sequence[ExplorationObservation],
) -> DynamicBenchmarkResult:
    """Summarize a dynamic run against an externally defined exhaustive baseline."""
    if total_targets < 0:
        raise ValueError("total_targets must be >= 0")
    if exhaustive_cost < 0 or exhaustive_gain < 0:
        raise ValueError("exhaustive cost/gain must be >= 0")
    if exhaustive_useful < 0 or exhaustive_useful > total_targets:
        raise ValueError("exhaustive_useful must be within target count")
    for item in dynamic_observations:
        item.validate()

    return DynamicBenchmarkResult(
        exhaustive_cost=float(exhaustive_cost),
        dynamic_cost=sum(float(x.actual_cost) for x in dynamic_observations),
        exhaustive_gain=float(exhaustive_gain),
        dynamic_gain=sum(float(x.realized_gain) for x in dynamic_observations),
        exhaustive_useful=int(exhaustive_useful),
        dynamic_useful=sum(int(x.useful) for x in dynamic_observations),
        total_targets=int(total_targets),
        dynamic_decisions=tuple(x.decision for x in dynamic_observations),
    )


__all__ = [
    "DECISION_CONTINUE",
    "DECISION_REQUEST_EVIDENCE",
    "DECISION_CHANGE_STRATEGY",
    "ControlContext",
    "ExplorationObservation",
    "PolicyStats",
    "PolicySnapshot",
    "MetacognitiveDecision",
    "DynamicBenchmarkResult",
    "MetacognitiveController",
    "replay_policy",
    "dynamic_vs_exhaustive",
]
