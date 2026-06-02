"""Decision-study (D-study) simulations for G-Theory.

Ported verbatim from the production pipeline; only the internal import paths
have been rewritten for the standalone public package.
"""

from __future__ import annotations

from typing import Any, Dict, List

from t2d_benchmark.g_theory.coefficients import compute_coefficients
from t2d_benchmark.g_theory.config import GTheoryConfig
from t2d_benchmark.g_theory.variance_components import (
    VarianceComponentResult,
)


def _scenario_rows(
    *,
    vc: VarianceComponentResult,
    prompt_counts: List[int],
    occasion_counts: List[int],
    prompt_fixed: bool,
    current_prompt: int,
    current_occasion: int,
    config: GTheoryConfig,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for n_prompt in prompt_counts:
        for n_occasion in occasion_counts:
            coeffs = compute_coefficients(
                vc,
                prompt_fixed=prompt_fixed,
                n_prompt=n_prompt,
                n_occasion=n_occasion,
                config=config,
            )
            rows.append(
                {
                    "n_prompt": n_prompt,
                    "n_occasion": n_occasion,
                    "prompt_type": coeffs.prompt_type,
                    "g_coefficient": coeffs.g_coefficient,
                    "phi_coefficient": coeffs.phi_coefficient,
                    "sem_rel": coeffs.sem_rel,
                    "sem_abs": coeffs.sem_abs,
                    "sdd_rel": coeffs.sdd_rel,
                    "sdd_abs": coeffs.sdd_abs,
                    "is_current_design": n_prompt == current_prompt and n_occasion == current_occasion,
                }
            )
    rows.sort(key=lambda item: (item["n_prompt"], item["n_occasion"]))
    return rows


def _pick_optimal_design(
    scenarios: List[Dict[str, Any]],
    *,
    target_phi: float,
) -> Dict[str, Any]:
    meeting = [
        row
        for row in scenarios
        if row.get("phi_coefficient") is not None and float(row["phi_coefficient"]) >= target_phi
    ]
    if not meeting:
        return {"target_phi": target_phi, "minimum_design": None, "cost_efficient_design": None}

    minimum_design = min(meeting, key=lambda item: (item["n_prompt"] * item["n_occasion"], item["n_occasion"], item["n_prompt"]))
    cost_efficient_design = max(
        meeting,
        key=lambda item: (float(item["phi_coefficient"]), -(item["n_prompt"] * item["n_occasion"])),
    )
    return {
        "target_phi": target_phi,
        "minimum_design": minimum_design,
        "cost_efficient_design": cost_efficient_design,
    }


def run_d_study(
    variance_components: VarianceComponentResult,
    config: GTheoryConfig,
) -> Dict[str, Any]:
    current_prompt = variance_components.n_prompt
    current_occasion = variance_components.n_occasion
    prompt_counts = sorted({*config.d_study_prompt_range, current_prompt})
    occasion_counts = sorted({*config.d_study_occasion_range, current_occasion})

    random_rows = _scenario_rows(
        vc=variance_components,
        prompt_counts=prompt_counts,
        occasion_counts=occasion_counts,
        prompt_fixed=False,
        current_prompt=current_prompt,
        current_occasion=current_occasion,
        config=config,
    )
    fixed_prompt_counts = sorted({current_prompt})
    fixed_rows = _scenario_rows(
        vc=variance_components,
        prompt_counts=fixed_prompt_counts,
        occasion_counts=occasion_counts,
        prompt_fixed=True,
        current_prompt=current_prompt,
        current_occasion=current_occasion,
        config=config,
    )

    current_random = next(row for row in random_rows if row["is_current_design"])
    plus_prompt = next(
        (row for row in random_rows if row["n_prompt"] == current_prompt + 1 and row["n_occasion"] == current_occasion),
        None,
    )
    plus_occasion = next(
        (row for row in random_rows if row["n_prompt"] == current_prompt and row["n_occasion"] == current_occasion + 1),
        None,
    )

    def _delta(reference: Dict[str, Any], candidate: Dict[str, Any] | None) -> float | None:
        if candidate is None:
            return None
        if reference.get("phi_coefficient") is None or candidate.get("phi_coefficient") is None:
            return None
        return round(float(candidate["phi_coefficient"]) - float(reference["phi_coefficient"]), 6)

    delta_prompt = _delta(current_random, plus_prompt)
    delta_occasion = _delta(current_random, plus_occasion)

    return {
        "current_design": {"n_prompt": current_prompt, "n_occasion": current_occasion},
        "random_prompt_scenarios": random_rows,
        "fixed_prompt_scenarios": fixed_rows,
        "optimal_design": _pick_optimal_design(random_rows, target_phi=config.reliability_good),
        "marginal_analysis": {
            "effect_of_adding_1_prompt": delta_prompt,
            "effect_of_adding_1_occasion": delta_occasion,
            "more_effective_facet": (
                "occasion"
                if delta_prompt is None or (delta_occasion is not None and delta_occasion > delta_prompt)
                else "prompt"
            ),
        },
    }
