"""Standalone generalizability-theory (G-theory) variance-component computation.

This is a self-contained port of the study's G-theory analysis. The three
math-only modules (``variance_components``, ``coefficients``, ``d_study``) are
reproduced verbatim from the production pipeline with their internal import
paths rewritten; ``config`` is a slim, dependency-free replacement that keeps
only the fields these modules read.
"""

from t2d_benchmark.g_theory.coefficients import (
    GTheoryCoefficients,
    compute_coefficients,
)
from t2d_benchmark.g_theory.config import GTheoryConfig
from t2d_benchmark.g_theory.d_study import run_d_study
from t2d_benchmark.g_theory.variance_components import (
    VarianceComponent,
    VarianceComponentResult,
    estimate_variance_components_anova,
    estimate_variance_components_reml,
)

__all__ = [
    "GTheoryCoefficients",
    "compute_coefficients",
    "GTheoryConfig",
    "run_d_study",
    "VarianceComponent",
    "VarianceComponentResult",
    "estimate_variance_components_anova",
    "estimate_variance_components_reml",
]
