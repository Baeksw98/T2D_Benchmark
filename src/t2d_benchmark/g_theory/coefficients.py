"""Reliability coefficients derived from G-Theory variance components.

Ported verbatim from the production pipeline; only the internal import paths
have been rewritten for the standalone public package. ``compute_coefficients``
returns the dependability coefficient (Phi), the generalizability coefficient
(G), the standard error of measurement (SEM), and the smallest detectable
difference (SDD = 2.77 x SEM, i.e. 1.96 x sqrt(2) x SEM).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from typing import Any, Dict

from t2d_benchmark.g_theory.config import GTheoryConfig
from t2d_benchmark.g_theory.variance_components import (
    VarianceComponentResult,
)


@dataclass(slots=True)
class GTheoryCoefficients:
    n_object: int
    n_prompt: int
    n_occasion: int
    prompt_type: str
    sigma2_q: float
    sigma2_t: float
    sigma2_o: float
    sigma2_qt: float
    sigma2_qo: float
    sigma2_to: float
    sigma2_residual: float
    sigma2_rel: float
    sigma2_abs: float
    g_coefficient: float | None
    phi_coefficient: float | None
    sem_rel: float
    sem_abs: float
    sdd_rel: float
    sdd_abs: float
    g_interpretation: str
    phi_interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _interpret_reliability(value: float | None, config: GTheoryConfig) -> str:
    if value is None:
        return "not_estimable"
    if value >= config.reliability_excellent:
        return "excellent"
    if value >= config.reliability_good:
        return "good"
    if value >= config.reliability_acceptable:
        return "acceptable"
    return "poor"


def compute_coefficients(
    vc: VarianceComponentResult,
    *,
    prompt_fixed: bool = False,
    n_prompt: int | None = None,
    n_occasion: int | None = None,
    config: GTheoryConfig | None = None,
) -> GTheoryCoefficients:
    config = config or GTheoryConfig()
    components = vc.component_map()
    sigma2_q = float(components.get("object", 0.0))
    sigma2_t = float(components.get("prompt", 0.0))
    sigma2_o = float(components.get("occasion", 0.0))
    sigma2_qt = float(components.get("object_prompt", 0.0))
    sigma2_qo = float(components.get("object_occasion", 0.0))
    sigma2_to = float(components.get("prompt_occasion", 0.0))
    sigma2_residual = float(components.get("residual", 0.0))

    n_prompt = int(n_prompt or vc.n_prompt)
    n_occasion = int(n_occasion or vc.n_occasion)

    sigma2_rel = sigma2_qt / n_occasion + sigma2_qo / n_prompt + sigma2_residual / (n_prompt * n_occasion)
    if prompt_fixed:
        sigma2_abs = sigma2_o / n_occasion + sigma2_qt / n_occasion + sigma2_qo / n_prompt + sigma2_residual / (
            n_prompt * n_occasion
        )
    else:
        sigma2_abs = (
            sigma2_t / n_prompt
            + sigma2_o / n_occasion
            + sigma2_qt / n_occasion
            + sigma2_qo / n_prompt
            + sigma2_to / (n_prompt * n_occasion)
            + sigma2_residual / (n_prompt * n_occasion)
        )

    g_denominator = sigma2_q + sigma2_rel
    phi_denominator = sigma2_q + sigma2_abs
    g_value = sigma2_q / g_denominator if g_denominator > 0 else None
    phi_value = sigma2_q / phi_denominator if phi_denominator > 0 else None
    sem_rel = sqrt(max(0.0, sigma2_rel))
    sem_abs = sqrt(max(0.0, sigma2_abs))
    return GTheoryCoefficients(
        n_object=vc.n_object,
        n_prompt=n_prompt,
        n_occasion=n_occasion,
        prompt_type="fixed" if prompt_fixed else "random",
        sigma2_q=sigma2_q,
        sigma2_t=sigma2_t,
        sigma2_o=sigma2_o,
        sigma2_qt=sigma2_qt,
        sigma2_qo=sigma2_qo,
        sigma2_to=sigma2_to,
        sigma2_residual=sigma2_residual,
        sigma2_rel=round(float(sigma2_rel), 6),
        sigma2_abs=round(float(sigma2_abs), 6),
        g_coefficient=round(float(g_value), 6) if g_value is not None else None,
        phi_coefficient=round(float(phi_value), 6) if phi_value is not None else None,
        sem_rel=round(float(sem_rel), 6),
        sem_abs=round(float(sem_abs), 6),
        sdd_rel=round(float(2.77 * sem_rel), 6),
        sdd_abs=round(float(2.77 * sem_abs), 6),
        g_interpretation=_interpret_reliability(g_value, config),
        phi_interpretation=_interpret_reliability(phi_value, config),
    )
