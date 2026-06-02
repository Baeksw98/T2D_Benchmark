from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "data" / "demo"
GTHEORY = ROOT / "data" / "g_theory"


def test_score_matrix_contract() -> None:
    df = pd.read_csv(DEMO / "synthetic_score_matrix.csv")
    assert list(df.columns) == ["object_id", "prompt_id", "occasion_id", "score"]
    # Balanced, fully crossed lattice.
    n = df["object_id"].nunique() * df["prompt_id"].nunique() * df["occasion_id"].nunique()
    assert len(df) == n
    assert df.groupby(["object_id", "prompt_id", "occasion_id"]).size().max() == 1


def test_protocol_scores_contract() -> None:
    df = pd.read_csv(DEMO / "synthetic_protocol_scores.csv")
    assert list(df.columns) == ["protocol", "case_id", "question_key", "rater_config", "Y_0_100"]
    assert set(df["protocol"]) == {"baseline", "rubric_assisted"}
    assert df["question_key"].nunique() == 15
    assert df["Y_0_100"].between(0, 100).all()


def test_released_gtheory_files_exist_and_are_small() -> None:
    coeffs = pd.read_csv(GTHEORY / "coefficients.csv")
    varcomp = pd.read_csv(GTHEORY / "variance_components.csv")
    assert len(coeffs) == 12
    assert len(varcomp) == 15
    # Aggregate-only: no per-patient / per-rater / raw-score columns.
    forbidden = {"patient_id", "rater_id", "rater_model", "score", "rationale", "rubric"}
    assert forbidden.isdisjoint(set(coeffs.columns))
    assert forbidden.isdisjoint(set(varcomp.columns))


def test_vignette_count() -> None:
    assert len(list((ROOT / "data" / "vignettes").glob("T2D_V*.json"))) == 480
