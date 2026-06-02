"""Minimal configuration for the standalone G-theory computation.

This is a slimmed, dependency-free replacement for the production
``GTheoryConfig``. It keeps only the fields the public ``coefficients`` and
``d_study`` modules actually read:

- ``reliability_*`` thresholds used to label a coefficient as
  excellent / good / acceptable / poor;
- the D-study facet ranges projected by ``run_d_study``.

All path-, artifact-, and locale-related fields of the production config are
intentionally dropped — they reference private infrastructure that is not part
of this public release.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class GTheoryConfig:
    # Reliability-interpretation thresholds (read by coefficients.compute_coefficients).
    reliability_excellent: float = 0.90
    reliability_good: float = 0.80
    reliability_acceptable: float = 0.70

    # D-study projection ranges (read by d_study.run_d_study).
    d_study_prompt_range: List[int] = field(default_factory=lambda: [1, 2, 3, 5, 7, 10])
    d_study_occasion_range: List[int] = field(
        default_factory=lambda: [1, 2, 3, 5, 10, 15, 20]
    )
