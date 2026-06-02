from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from t2d_benchmark.analysis.generate_synthetic_demo_data import build_gtheory_frame
from t2d_benchmark.g_theory import compute_coefficients, estimate_variance_components_anova
from t2d_benchmark.g_theory.run_g_theory import run as run_gtheory

ROOT = Path(__file__).resolve().parents[1]
COEFFS = ROOT / "data" / "g_theory" / "coefficients.csv"
VARCOMP = ROOT / "data" / "g_theory" / "variance_components.csv"


def test_anova_and_coefficients_on_demo_matrix() -> None:
    frame = build_gtheory_frame()
    vc = estimate_variance_components_anova(frame)
    assert vc.estimation_method == "ANOVA_EMS"
    # Components sum to the reported total variance.
    assert abs(sum(c.estimate for c in vc.components) - vc.total_variance) < 1e-6
    coeffs = compute_coefficients(vc, prompt_fixed=False)
    assert 0.0 <= coeffs.phi_coefficient <= 1.0
    # The demo matrix is shaped for the "excellent" band.
    assert coeffs.phi_coefficient >= 0.90
    assert coeffs.phi_interpretation == "excellent"


def test_sdd_is_277_times_sem() -> None:
    frame = build_gtheory_frame()
    vc = estimate_variance_components_anova(frame)
    coeffs = compute_coefficients(vc, prompt_fixed=False)
    assert abs(coeffs.sdd_abs - 2.77 * coeffs.sem_abs) < 1e-4
    assert abs(coeffs.sdd_rel - 2.77 * coeffs.sem_rel) < 1e-4


def test_released_coefficients_reproduce_phi_g_sdd() -> None:
    rows = list(csv.DictReader(COEFFS.open()))
    assert len(rows) == 12
    for r in rows:
        sig = float(r["sigma2_signal"])
        sem_abs = float(r["sem_abs"])
        sem_rel = float(r["sem_rel"])
        phi = sig / (sig + sem_abs ** 2)
        g = sig / (sig + sem_rel ** 2)
        assert abs(phi - float(r["phi_coefficient"])) < 2e-3
        assert abs(g - float(r["g_coefficient"])) < 2e-3
        assert abs(2.77 * sem_abs - float(r["sdd_abs"])) < 2e-3


def test_released_headline_phi_is_0984() -> None:
    rows = list(csv.DictReader(COEFFS.open()))
    headline = next(
        r for r in rows
        if r["configuration"] == "DRG_minus_Baseline" and r["reasoning_part"] == "overall"
    )
    assert round(float(headline["phi_coefficient"]), 3) == 0.984
    assert round(float(headline["sem_abs"]), 2) == 2.92
    assert round(float(headline["sdd_abs"]), 2) == 8.08


def test_released_per_part_phi_range() -> None:
    rows = list(csv.DictReader(COEFFS.open()))
    parts = [
        float(r["phi_coefficient"])
        for r in rows
        if r["configuration"] == "DRG_minus_Baseline" and r["reasoning_part"] != "overall"
    ]
    assert len(parts) == 3
    assert round(min(parts), 3) == 0.968
    assert round(max(parts), 3) == 0.978


def test_run_g_theory_smoke(tmp_path: Path) -> None:
    frame = build_gtheory_frame()
    inp = tmp_path / "matrix.csv"
    frame.to_csv(inp, index=False)
    out = tmp_path / "out"
    summary = run_gtheory(inp, out)
    for name in ("demo_coefficients.csv", "demo_variance_components.csv", "demo_d_study.csv", "summary.json"):
        assert (out / name).exists(), name
    assert summary["phi_coefficient"] is not None
    assert 0.0 <= summary["phi_coefficient"] <= 1.0


def test_released_variance_components_are_aggregate() -> None:
    df = pd.read_csv(VARCOMP)
    assert len(df) == 15  # 8 medication + 3 follow-up + 4 education
    assert set(df["reasoning_part"]) == {
        "medication_selection", "follow_up_monitoring", "patient_education"
    }
    assert {"sigma2_patient", "sigma2_order", "sigma2_run", "sigma2_residual"} <= set(df.columns)
    assert "patient_id" not in df.columns and "score" not in df.columns
