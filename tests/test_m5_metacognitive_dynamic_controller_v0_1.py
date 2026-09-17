from kernel2 import OBSERVATION, Node, build_structural_graph, discover_paths, node_ref
from e20d_cognitive_control_v0_1 import PathCandidate
from m5_metacognitive_dynamic_controller_v0_1 import (
    DECISION_CHANGE_STRATEGY,
    DECISION_CONTINUE,
    DECISION_DEFER,
    DECISION_REQUEST_EVIDENCE,
    DECISION_STOP,
    ControlContext,
    ExplorationObservation,
    MetacognitiveController,
    dynamic_vs_exhaustive,
    replay_policy,
)


def obs(i, op, a, b):
    return Node(i, OBSERVATION, (op, a, b), provenance=(i,))


def make_path():
    A, B = map(node_ref, ("A", "B"))
    R = node_ref("R")
    graph = build_structural_graph([obs("e1", R, A, B)])
    return discover_paths(graph, start=A, max_depth=1)[0]


def test_baseline_decision_is_structural_and_deterministic():
    controller = MetacognitiveController()
    context = ControlContext(depth=1, novelty=1.0, redundancy=0.0, cost=1.0, expected_gain=1.0)
    d1 = controller.decide(context)
    d2 = controller.decide(context)
    assert d1.decision == DECISION_CONTINUE
    assert d1 == d2
    assert d1.policy_version == 0


def test_observation_updates_version_and_snapshot():
    controller = MetacognitiveController()
    context = ControlContext(depth=2, expected_gain=1.0, cost=2.0)
    observation = ExplorationObservation(
        "o1", context, DECISION_CONTINUE, 0.5, 1.0, 1.0, True
    )
    snap = controller.observe(observation)
    assert snap.version == 1
    assert snap.total_observations == 1
    assert snap.contexts[context.key()].attempts == 1


def test_negative_history_can_change_strategy():
    controller = MetacognitiveController(min_observations_for_adaptation=2, drift_threshold=0.1)
    context = ControlContext(depth=2, expected_gain=2.0, cost=1.0, novelty=1.0)
    for i in range(2):
        controller.observe(
            ExplorationObservation(f"n{i}", context, DECISION_CONTINUE, 2.0, 0.01, 2.0, False)
        )
    decision = controller.decide(context)
    assert decision.strategy == "ADAPTIVE"
    assert "NEGATIVE_DRIFT_CONSERVATIVE_ADJUSTMENT" in decision.reason_codes


def test_low_useful_rate_can_request_strategy_change():
    controller = MetacognitiveController(min_observations_for_adaptation=2, drift_threshold=0.1)
    context = ControlContext(depth=2, expected_gain=2.0, cost=1.0)
    for i in range(2):
        controller.observe(
            ExplorationObservation(f"u{i}", context, DECISION_CONTINUE, 2.0, 0.01, 2.0, False)
        )
    decision = controller.decide(context)
    assert decision.decision == DECISION_CHANGE_STRATEGY


def test_high_uncertainty_with_evidence_available_requests_evidence():
    controller = MetacognitiveController()
    context = ControlContext(depth=1, uncertainty=0.9, expected_gain=2.0, cost=1.0)
    decision = controller.decide(context, evidence_available=True)
    assert decision.decision == DECISION_REQUEST_EVIDENCE


def test_stable_history_does_not_trigger_adaptation():
    controller = MetacognitiveController(min_observations_for_adaptation=3, drift_threshold=0.5)
    context = ControlContext(depth=1, expected_gain=1.0, cost=1.0)
    for i in range(3):
        controller.observe(
            ExplorationObservation(f"s{i}", context, DECISION_CONTINUE, 1.0, 1.0, 1.0, True)
        )
    decision = controller.decide(context)
    assert decision.strategy == "BASELINE"
    assert "STABLE_HISTORY" in decision.reason_codes


def test_candidate_context_is_semantic_free():
    path = make_path()
    candidate = PathCandidate(path, structural_novelty=1.0, expected_gain=2.0, estimated_cost=1.0)
    controller = MetacognitiveController()
    d = controller.decide_for_candidate(candidate)
    assert d.decision == DECISION_CONTINUE


def test_replay_is_deterministic():
    context = ControlContext(depth=2, expected_gain=1.0, cost=1.0)
    observations = tuple(
        ExplorationObservation(f"r{i}", context, DECISION_CONTINUE, 1.0, 0.8, 1.0, True)
        for i in range(3)
    )
    c1 = MetacognitiveController()
    c2 = MetacognitiveController()
    assert replay_policy(c1, observations) == replay_policy(c2, observations)


def test_policy_versions_increase_only_on_observation():
    controller = MetacognitiveController()
    context = ControlContext(depth=1)
    assert controller.version == 0
    controller.decide(context)
    assert controller.version == 0
    controller.observe(
        ExplorationObservation("v1", context, DECISION_DEFER, 0.0, 0.0, 0.0, False)
    )
    assert controller.version == 1


def test_dynamic_benchmark_measures_cost_and_gain():
    context = ControlContext(depth=1)
    observations = (
        ExplorationObservation("b1", context, DECISION_CONTINUE, 1.0, 1.0, 1.0, True),
        ExplorationObservation("b2", context, DECISION_DEFER, 0.4, 0.4, 0.5, True),
    )
    result = dynamic_vs_exhaustive(
        total_targets=3,
        exhaustive_cost=4.0,
        exhaustive_gain=2.0,
        exhaustive_useful=2,
        dynamic_observations=observations,
    )
    assert result.dynamic_cost == 1.5
    assert result.dynamic_gain == 1.4
    assert result.dynamic_useful == 2
    assert 0 < result.cost_reduction < 1


def test_benchmark_never_claims_more_useful_items_than_targets():
    context = ControlContext(depth=1)
    observations = tuple(
        ExplorationObservation(f"t{i}", context, DECISION_CONTINUE, 1.0, 1.0, 1.0, True)
        for i in range(2)
    )
    result = dynamic_vs_exhaustive(
        total_targets=2,
        exhaustive_cost=2.0,
        exhaustive_gain=2.0,
        exhaustive_useful=2,
        dynamic_observations=observations,
    )
    assert result.useful_coverage == 1.0


def test_decision_can_transition_from_stop_to_continue_after_positive_history():
    controller = MetacognitiveController(min_observations_for_adaptation=2, drift_threshold=0.1)
    context = ControlContext(depth=3, expected_gain=0.1, cost=2.0, novelty=1.0)
    baseline = controller.decide(context)
    assert baseline.decision == DECISION_STOP
    for i in range(2):
        controller.observe(
            ExplorationObservation(f"p{i}", context, DECISION_CONTINUE, 0.1, 2.0, 1.0, True)
        )
    adapted = controller.decide(context)
    assert adapted.decision == DECISION_CONTINUE
    assert adapted.strategy == "ADAPTIVE"


def test_provenance_is_carried_in_context_but_not_interpreted():
    controller = MetacognitiveController()
    c1 = ControlContext(depth=1, provenance=("GROUNDED_DIRECT",), expected_gain=1.0, cost=1.0)
    c2 = ControlContext(depth=1, provenance=("UNGROUNDED_HUMAN",), expected_gain=1.0, cost=1.0)
    d1 = controller.decide(c1)
    d2 = controller.decide(c2)
    assert d1.decision == d2.decision
    assert d1.context_key != d2.context_key


def test_empty_history_is_not_adaptive():
    controller = MetacognitiveController()
    context = ControlContext(depth=1, expected_gain=0.3, cost=1.0)
    decision = controller.decide(context)
    assert decision.strategy == "BASELINE"
    assert decision.historical_roi == 0.0


if __name__ == "__main__":
    tests = [
        test_baseline_decision_is_structural_and_deterministic,
        test_observation_updates_version_and_snapshot,
        test_negative_history_can_change_strategy,
        test_low_useful_rate_can_request_strategy_change,
        test_high_uncertainty_with_evidence_available_requests_evidence,
        test_stable_history_does_not_trigger_adaptation,
        test_candidate_context_is_semantic_free,
        test_replay_is_deterministic,
        test_policy_versions_increase_only_on_observation,
        test_dynamic_benchmark_measures_cost_and_gain,
        test_benchmark_never_claims_more_useful_items_than_targets,
        test_decision_can_transition_from_stop_to_continue_after_positive_history,
        test_provenance_is_carried_in_context_but_not_interpreted,
        test_empty_history_is_not_adaptive,
    ]
    for test in tests:
        test()
    print("M5: 14/14 PASS")
