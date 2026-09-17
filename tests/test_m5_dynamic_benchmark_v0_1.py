from m5_metacognitive_dynamic_controller_v0_1 import (
    DECISION_CONTINUE,
    DECISION_DEFER,
    ControlContext,
    ExplorationObservation,
    MetacognitiveController,
    dynamic_vs_exhaustive,
)


def test_dynamic_policy_reduces_cost_while_retaining_useful_coverage():
    context = ControlContext(depth=2, novelty=1.0, redundancy=0.0, cost=1.0, expected_gain=1.0)
    observations = (
        ExplorationObservation("x1", context, DECISION_CONTINUE, 1.0, 1.0, 1.0, True),
        ExplorationObservation("x2", context, DECISION_CONTINUE, 1.0, 1.0, 1.0, True),
        ExplorationObservation("x3", context, DECISION_DEFER, 0.8, 0.2, 0.5, True),
    )
    result = dynamic_vs_exhaustive(
        total_targets=3,
        exhaustive_cost=6.0,
        exhaustive_gain=2.2,
        exhaustive_useful=3,
        dynamic_observations=observations,
    )
    assert result.cost_reduction > 0.4
    assert result.useful_coverage == 1.0
    assert result.gain_retention > 0.8


def test_dynamic_controller_stops_after_persistent_low_utility():
    context = ControlContext(depth=3, novelty=1.0, redundancy=0.0, cost=1.0, expected_gain=1.0)
    controller = MetacognitiveController(min_observations_for_adaptation=2, drift_threshold=0.1)
    for i in range(3):
        controller.observe(
            ExplorationObservation(f"low{i}", context, DECISION_CONTINUE, 1.0, 0.0, 1.0, False)
        )
    decision = controller.decide(context)
    assert decision.decision in {"CHANGE_STRATEGY", "STOP"}
    assert decision.historical_useful_rate == 0.0
