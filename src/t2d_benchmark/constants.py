"""Cross-module contract constants for the T2D benchmark package.

A single source of truth for the small set of values that would otherwise risk
drifting between modules -- the cohort size enforced by the release audit and
derived by the factorial-index builder, and the protocol labels shared by the
analysis and synthetic-data modules.

Domain-local constants deliberately stay in their owning modules: the
factor-level tuples and mixed-radix strides live with the factorial
decomposition (:mod:`t2d_benchmark.build_factorial_index`), the release-audit
pattern fragments stay inline in :mod:`t2d_benchmark.audit_release` (so that
audit file remains free of any plaintext forbidden token), and the synthetic
scoring coefficients stay in
:mod:`t2d_benchmark.analysis.generate_synthetic_demo_data`.
"""

from __future__ import annotations

# --- Cohort / design contracts ---------------------------------------------
EXPECTED_VIGNETTE_COUNT = 480
"""Number of synthetic vignettes in the released full-factorial cohort."""

N_RELIABILITY_QUESTIONS = 15
"""Reliability questions: 8 medication selection + 3 follow-up + 4 patient education."""

EXPECTED_COEFFICIENT_ROWS = 12
"""Rows in the released coefficients table: 3 configurations x 4 reasoning parts."""

TRAP_STEP = 10
"""Every TRAP_STEP-th vignette in the canonical order is a designated trap case."""

# --- Protocol labels (on-disk encoding) ------------------------------------
BASELINE = "baseline"
"""The Baseline (no guideline reference) CDSS configuration."""

DRG = "rubric_assisted"
"""Document-Referenced Generation; encoded on disk as ``rubric_assisted``."""

# Defensive invariants: these values are quoted verbatim in the manuscript.
assert EXPECTED_VIGNETTE_COUNT == 480
assert N_RELIABILITY_QUESTIONS == 15
