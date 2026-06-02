"""High-level orchestration of the generalizability-theory analysis.

The numerical core lives in :mod:`variance_components`, :mod:`coefficients`, and
:mod:`d_study` as free functions. :class:`GTheoryEngine` composes them in the
canonical order — estimate variance components once, derive the random-facet and
fixed-facet coefficients, then project the decision study — and returns an
inspectable :class:`GTheoryAnalysis` result bundle. The CLI runner
(:mod:`run_g_theory`) is a thin shell over this engine.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from t2d_benchmark.g_theory.coefficients import GTheoryCoefficients, compute_coefficients
from t2d_benchmark.g_theory.config import GTheoryConfig
from t2d_benchmark.g_theory.d_study import run_d_study
from t2d_benchmark.g_theory.variance_components import (
    VarianceComponentResult,
    estimate_variance_components_anova,
)


@dataclass(frozen=True, slots=True)
class GTheoryAnalysis:
    """Immutable bundle of one G-theory analysis over a score matrix.

    Attributes:
        variance_components: The ANOVA variance-component decomposition.
        random_facet_coefficients: Φ/G/SEM/SDD treating the prompt as a random facet.
        fixed_facet_coefficients: Φ/G/SEM/SDD treating the prompt as fixed.
        d_study: The decision-study projection across facet sizes.
    """

    variance_components: VarianceComponentResult
    random_facet_coefficients: GTheoryCoefficients
    fixed_facet_coefficients: GTheoryCoefficients
    d_study: dict[str, object]

    def summary(self) -> dict[str, object]:
        """Return the headline run summary (random-facet model).

        The key order matches the ``summary.json`` written by the CLI runner.
        """
        vc = self.variance_components
        random = self.random_facet_coefficients
        return {
            "estimation_method": vc.estimation_method,
            "n_object": vc.n_object,
            "n_prompt": vc.n_prompt,
            "n_occasion": vc.n_occasion,
            "n_observations": vc.n_observations,
            "total_variance": vc.total_variance,
            "phi_coefficient": random.phi_coefficient,
            "g_coefficient": random.g_coefficient,
            "sem_abs": random.sem_abs,
            "sdd_abs": random.sdd_abs,
            "phi_interpretation": random.phi_interpretation,
        }


class GTheoryEngine:
    """Compose the variance-component, coefficient, and D-study steps."""

    def __init__(self, config: GTheoryConfig | None = None) -> None:
        self.config = config or GTheoryConfig()

    def analyze(self, frame: pd.DataFrame) -> GTheoryAnalysis:
        """Run the full G-theory analysis on a balanced score-matrix frame.

        The steps run in a fixed order — variance components first (computed
        once), then the random- and fixed-facet coefficients, then the decision
        study — mirroring the original procedural runner exactly.
        """
        variance_components = estimate_variance_components_anova(frame)
        random_facet = compute_coefficients(variance_components, prompt_fixed=False, config=self.config)
        fixed_facet = compute_coefficients(variance_components, prompt_fixed=True, config=self.config)
        d_study = run_d_study(variance_components, self.config)
        return GTheoryAnalysis(
            variance_components=variance_components,
            random_facet_coefficients=random_facet,
            fixed_facet_coefficients=fixed_facet,
            d_study=d_study,
        )
