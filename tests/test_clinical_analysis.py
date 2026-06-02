from __future__ import annotations

from pathlib import Path

from t2d_benchmark.analysis.generate_synthetic_demo_data import build_protocol_frame
from t2d_benchmark.analysis.run_clinical_analysis import (
    ks_tests,
    paired_differences,
    protocol_means,
)

EXPECTED_QUESTIONS = 15


def test_protocol_means_cover_both_configurations() -> None:
    frame = build_protocol_frame()
    means = protocol_means(frame)
    assert set(means["protocol"]) == {"baseline", "rubric_assisted"}
    assert means["question_key"].nunique() == EXPECTED_QUESTIONS


def test_ks_tests_one_row_per_question() -> None:
    frame = build_protocol_frame()
    ks = ks_tests(frame)
    assert len(ks) == EXPECTED_QUESTIONS
    assert (ks["ks_statistic"] >= 0).all() and (ks["ks_statistic"] <= 1).all()
    assert {"baseline_n", "drg_n", "p_value"} <= set(ks.columns)


def test_paired_differences_has_overall_and_drg_advantage() -> None:
    frame = build_protocol_frame()
    paired = paired_differences(frame)
    assert "OVERALL" in set(paired["question_key"])
    overall = paired[paired["question_key"] == "OVERALL"].iloc[0]
    # Synthetic data is shaped so DRG scores above Baseline (qualitatively
    # mirroring the paper's positive paired difference).
    assert overall["mean_paired_diff"] > 0
    assert 0.0 <= overall["pct_drg_higher"] <= 100.0
    assert overall["n_pairs"] == 10 * EXPECTED_QUESTIONS * 6  # cases x questions x rater configs
