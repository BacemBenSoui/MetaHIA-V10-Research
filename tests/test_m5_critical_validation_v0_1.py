from pathlib import Path
import json

from m5_metacognitive_dynamic_controller_v0_1 import (
    DECISION_CHANGE_STRATEGY,
    DECISION_CONTINUE,
    DECISION_REQUEST_EVIDENCE,
    ControlContext,
    ExplorationObservation,
    MetacognitiveController,
    dynamic_vs_exhaustive,
    replay_policy,
)

CORPUS = Path(__file__).with_name("m5_critical_corpus_v0_1.json")


def test_corpus_is_declared_and_complete():
    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    assert len(data["cases"]) == 12
    assert [c["id"] for c in data["cases"]] == [f"C{i:02d}" for i in range(1, 13)]


def test_holdout_same_context_history_same_decision():
    c = ControlContext(depth=2, expected_gain=1.0, cost=1.0)
    obs = tuple(ExplorationObservation(f"h{i}", c, DECISION_CONTINUE, 1.0, 1.0, 1.0, True) for i in range(3))
    a, b = MetacognitiveController(), MetacognitiveController()
    replay_policy(a, obs)
    replay_policy(b, obs)
    assert a.decide(c) == b.decide(c)


def test_positive_history_unlocks_useful_continue():
    c = ControlContext(depth=3, expected_gain=0.1, cost=2.0)
    controller = MetacognitiveController(min_observations_for_adaptation=2, drift_threshold=0.1)
    assert controller.decide(c).decision != DECISION_CONTINUE
    for i in range(2):
        controller.observe(ExplorationObservation(f"p{i}", c, DECISION_CONTINUE, 0.1, 2.0, 1.0, True))
    assert controller.decide(c).decision == DECISION_CONTINUE


def test_negative_drift_can_trigger_strategy_change():
    c = ControlContext(depth=2, expected_gain=2.0, cost=1.0)
    controller = MetacognitiveController(min_observations_for_adaptation=2, drift_threshold=0.1)
    for i in range(2):
        controller.observe(ExplorationObservation(f"n{i}", c, DECISION_CONTINUE, 2.0, 0.01, 2.0, False))
    decision = controller.decide(c)
    assert decision.decision == DECISION_CHANGE_STRATEGY


def test_high_uncertainty_requests_evidence_when_available():
    c = ControlContext(depth=1, uncertainty=0.9, expected_gain=2.0, cost=1.0)
    assert MetacognitiveController().decide(c, evidence_available=True).decision == DECISION_REQUEST_EVIDENCE


def test_semantic_free_control_does_not_read_provenance_labels():
    controller = MetacognitiveController()
    c1 = ControlContext(depth=1, provenance=("odd_relation",), expected_gain=1.0, cost=1.0)
    c2 = ControlContext(depth=1, provenance=("family_relation",), expected_gain=1.0, cost=1.0)
    assert controller.decide(c1).decision == controller.decide(c2).decision


def test_replay_policy_matches_direct_observation_run():
    c = ControlContext(depth=2, expected_gain=1.0, cost=1.0)
    observations = tuple(ExplorationObservation(f"r{i}", c, DECISION_CONTINUE, 1.0, 0.7, 1.0, True) for i in range(4))
    a, b = MetacognitiveController(), MetacognitiveController()
    replay_policy(a, observations)
    for item in observations:
        b.observe(item)
    assert a.snapshot() == b.snapshot()


def test_dynamic_cost_reduction_is_observable_against_external_baseline():
    c = ControlContext(depth=1)
    observations = (
        ExplorationObservation("b1", c, DECISION_CONTINUE, 1.0, 1.0, 1.0, True),
        ExplorationObservation("b2", c, "DEFER", 0.4, 0.4, 0.5, True),
    )
    result = dynamic_vs_exhaustive(
        total_targets=3, exhaustive_cost=4.0, exhaustive_gain=2.0, exhaustive_useful=2,
        dynamic_observations=observations,
    )
    assert result.cost_reduction > 0
    assert result.dynamic_cost == 1.5


def test_policy_version_is_deterministic_and_auditable():
    c = ControlContext(depth=1)
    controller = MetacognitiveController()
    assert controller.version == 0
    controller.decide(c)
    assert controller.version == 0
    controller.observe(ExplorationObservation("v", c, "STOP", 0.0, 0.0, 0.0, False))
    assert controller.version == 1
    decision = controller.decide(c)
    assert decision.policy_version == 1


def test_empty_history_is_conservative_baseline():
    c = ControlContext(depth=2, expected_gain=0.05, cost=3.0)
    decision = MetacognitiveController().decide(c)
    assert decision.strategy == "BASELINE"
