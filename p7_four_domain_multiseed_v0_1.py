"""MetaHIA P7.2 -- four-domain multi-seed statistical stability probe.

Extends P6.2's three-domain multi-seed probe with the fourth Library domain,
to test directly whether the stabilization trend already observed
(P5 Sec.5 combined-two population std=0.107167 -> P6 Sec.4 combined-three
population std=0.056129) continues, stalls, or reverses at four domains.
No M6 tuning. No promotion threshold changed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean, pstdev
from typing import Iterable, Mapping, Sequence

from m6_corpus_from_m4_m5_v0_2 import build_real_corpus_v2
from m6_corpus_from_organization_v0_1 import build_organization_corpus
from m6_corpus_from_supply_chain_v0_1 import build_supply_chain_corpus
from m6_corpus_from_library_v0_1 import build_library_corpus
from m6_structural_learning_v0_1 import (
    StructuralLearningPolicy,
    brier_score_multiclass,
    expected_calibration_error_top_label,
    split_by_rule,
)

DEFAULT_SEEDS = tuple(range(10))


@dataclass(frozen=True)
class SeedSlice:
    seed: int
    train: int
    validation: int
    holdout: int
    holdout_rules: int
    brier: float
    ece: float


@dataclass(frozen=True)
class MultiSeedDomainReport:
    domain_id: str
    seeds: tuple[SeedSlice, ...]
    brier_mean: float
    brier_std_population: float
    brier_min: float
    brier_max: float
    ece_mean: float


def _measure(domain_id: str, records, seeds: Sequence[int]) -> MultiSeedDomainReport:
    slices = []
    for seed in seeds:
        train, validation, holdout = split_by_rule(
            records, val_fraction=0.2, holdout_fraction=0.2, seed=seed
        )
        if not holdout:
            raise AssertionError(f"empty holdout for {domain_id} seed={seed}")
        train_rules = {r.rule_signature for r in train}
        holdout_rules = {r.rule_signature for r in holdout}
        if not train_rules.isdisjoint(holdout_rules):
            raise AssertionError(f"rule leakage for {domain_id} seed={seed}")
        policy = StructuralLearningPolicy().fit(train)
        slices.append(
            SeedSlice(
                seed=seed,
                train=len(train),
                validation=len(validation),
                holdout=len(holdout),
                holdout_rules=len(holdout_rules),
                brier=brier_score_multiclass(policy, holdout),
                ece=expected_calibration_error_top_label(policy, holdout),
            )
        )
    briers = [item.brier for item in slices]
    eces = [item.ece for item in slices]
    return MultiSeedDomainReport(
        domain_id=domain_id,
        seeds=tuple(slices),
        brier_mean=mean(briers),
        brier_std_population=pstdev(briers),
        brier_min=min(briers),
        brier_max=max(briers),
        ece_mean=mean(eces),
    )


def run_multiseed_regression(seeds: Iterable[int] = DEFAULT_SEEDS) -> Mapping[str, MultiSeedDomainReport]:
    seeds = tuple(int(s) for s in seeds)
    family = tuple(build_real_corpus_v2().records)
    organization = tuple(build_organization_corpus().records)
    supply_chain = tuple(build_supply_chain_corpus().records)
    library = tuple(build_library_corpus().records)
    combined_two = family + organization
    combined_three = family + organization + supply_chain
    combined_four = family + organization + supply_chain + library
    return {
        "FAMILY": _measure("FAMILY", family, seeds),
        "ORGANIZATION": _measure("ORGANIZATION", organization, seeds),
        "SUPPLY_CHAIN": _measure("SUPPLY_CHAIN", supply_chain, seeds),
        "LIBRARY": _measure("LIBRARY", library, seeds),
        "COMBINED_TWO": _measure("COMBINED_TWO", combined_two, seeds),
        "COMBINED_THREE": _measure("COMBINED_THREE", combined_three, seeds),
        "COMBINED_FOUR": _measure("COMBINED_FOUR", combined_four, seeds),
    }


def report_as_dict(report: Mapping[str, MultiSeedDomainReport]) -> Mapping[str, object]:
    return {key: asdict(value) for key, value in report.items()}


if __name__ == "__main__":
    import json
    print(json.dumps(report_as_dict(run_multiseed_regression()), ensure_ascii=False, indent=2, sort_keys=True))
