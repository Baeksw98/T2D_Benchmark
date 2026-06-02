"""Standalone G-theory runner: a CSV score matrix -> variance components + coefficients.

This is a generic balanced ``object x facet1 x facet2`` G-theory ANOVA engine.
In the study it was applied with the patient as the object of measurement and
prompt ordering and repetition as the two random facets (see
``VARIANCE_COMPONENTS.md``). Here the column names ``object_id``/``prompt_id``/
``occasion_id`` are generic facet placeholders.

Reads a balanced, fully crossed score matrix and writes (with a ``demo_`` prefix
to keep them distinct from the curated released estimates under ``data/g_theory/``):

- ``demo_variance_components.csv`` -- the seven-source variance decomposition;
- ``demo_coefficients.csv``        -- Phi, G, SEM, and SDD (random- and fixed-facet);
- ``demo_d_study.csv``             -- a decision-study projection across facet sizes;
- ``summary.json``                 -- a machine-readable run summary.

This runner operates on the public synthetic demo matrix shipped under
``data/demo/``. It reproduces the *mechanics* of the reliability analysis; the
authoritative variance-component estimates from the study are the curated CSVs
under ``data/g_theory/`` (a different, study-specific schema) and are NOT
regenerated here.

Usage:
    python -m t2d_benchmark.g_theory.run_g_theory \\
        --input data/demo/synthetic_score_matrix.csv \\
        --output outputs/g_theory
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Sequence

import pandas as pd

from t2d_benchmark.g_theory.coefficients import GTheoryCoefficients, compute_coefficients
from t2d_benchmark.g_theory.config import GTheoryConfig
from t2d_benchmark.g_theory.d_study import run_d_study
from t2d_benchmark.g_theory.variance_components import (
    VarianceComponentResult,
    estimate_variance_components_anova,
)

REQUIRED_COLUMNS = ("object_id", "prompt_id", "occasion_id", "score")

_COEFFICIENT_FIELDS = (
    "prompt_type",
    "n_object",
    "n_prompt",
    "n_occasion",
    "sigma2_q",
    "sigma2_t",
    "sigma2_o",
    "sigma2_qt",
    "sigma2_qo",
    "sigma2_to",
    "sigma2_residual",
    "sigma2_rel",
    "sigma2_abs",
    "g_coefficient",
    "phi_coefficient",
    "sem_rel",
    "sem_abs",
    "sdd_rel",
    "sdd_abs",
    "g_interpretation",
    "phi_interpretation",
)

_D_STUDY_FIELDS = (
    "scenario_type",
    "n_prompt",
    "n_occasion",
    "prompt_type",
    "g_coefficient",
    "phi_coefficient",
    "sem_rel",
    "sem_abs",
    "sdd_rel",
    "sdd_abs",
    "is_current_design",
)


def load_score_matrix(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = set(REQUIRED_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Score matrix {path} is missing required columns: {sorted(missing)}")
    return frame


def write_variance_components_csv(path: Path, vc: VarianceComponentResult) -> None:
    fieldnames = ["source", "label", "estimate", "percent_of_total", "truncated_from_negative"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for component in vc.components:
            writer.writerow(
                {
                    "source": component.source,
                    "label": component.label,
                    "estimate": round(float(component.estimate), 6),
                    "percent_of_total": component.percent_of_total,
                    "truncated_from_negative": component.truncated_from_negative,
                }
            )


def write_coefficients_csv(
    path: Path,
    random_coeffs: GTheoryCoefficients,
    fixed_coeffs: GTheoryCoefficients,
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(_COEFFICIENT_FIELDS))
        writer.writeheader()
        for coeffs in (random_coeffs, fixed_coeffs):
            writer.writerow({name: getattr(coeffs, name) for name in _COEFFICIENT_FIELDS})


def write_d_study_csv(path: Path, dstudy: dict) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(_D_STUDY_FIELDS))
        writer.writeheader()
        for scenario_type, key in (("random_prompt", "random_prompt_scenarios"), ("fixed_prompt", "fixed_prompt_scenarios")):
            for row in dstudy[key]:
                writer.writerow(
                    {"scenario_type": scenario_type, **{name: row.get(name) for name in _D_STUDY_FIELDS if name != "scenario_type"}}
                )


def run(input_path: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = load_score_matrix(input_path)
    config = GTheoryConfig()

    vc = estimate_variance_components_anova(frame)
    random_coeffs = compute_coefficients(vc, prompt_fixed=False, config=config)
    fixed_coeffs = compute_coefficients(vc, prompt_fixed=True, config=config)
    dstudy = run_d_study(vc, config)

    write_variance_components_csv(output_dir / "demo_variance_components.csv", vc)
    write_coefficients_csv(output_dir / "demo_coefficients.csv", random_coeffs, fixed_coeffs)
    write_d_study_csv(output_dir / "demo_d_study.csv", dstudy)

    summary = {
        "input": str(input_path),
        "output_dir": str(output_dir),
        "estimation_method": vc.estimation_method,
        "n_object": vc.n_object,
        "n_prompt": vc.n_prompt,
        "n_occasion": vc.n_occasion,
        "n_observations": vc.n_observations,
        "total_variance": vc.total_variance,
        "phi_coefficient": random_coeffs.phi_coefficient,
        "g_coefficient": random_coeffs.g_coefficient,
        "sem_abs": random_coeffs.sem_abs,
        "sdd_abs": random_coeffs.sdd_abs,
        "phi_interpretation": random_coeffs.phi_interpretation,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Standalone G-theory variance-component runner.")
    parser.add_argument("--input", type=Path, default=Path("data/demo/synthetic_score_matrix.csv"))
    parser.add_argument("--output", type=Path, default=Path("outputs/g_theory"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run(args.input.resolve(), args.output.resolve())
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
