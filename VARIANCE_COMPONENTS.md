# Variance Components and the Dependability Coefficient (Φ)

This document explains the released generalizability-theory (G-theory) estimates
and walks the arithmetic from the released variance components to the paper's
headline reliability numbers, so that an independent reader can reproduce them by
hand.

The released estimates are under [`data/g_theory/`](data/g_theory/):

- `variance_components.csv` — the per-question variance decomposition (one row
  per reliability question).
- `coefficients.csv` — the dependability/generalizability coefficients and
  errors of measurement (per configuration × reasoning part).

These are **aggregate** estimates. They contain no per-patient scores, no rater
identities, and no rubric text; they are the variance-component summaries derived
from the (withheld) raw rater scores.

## Measurement design

The reliability assessment is modeled under generalizability theory with the
**patient as the object of measurement** (n = 480) and the **reliability
question** as the measured behavior (15 questions: 8 medication selection,
3 follow-up & monitoring, 4 patient education). The AI rater scored each
output–question pair under a factorial design of rater configurations (3 prompt
character × 3 prompt type × 3 prompt ordering = 27 configurations, each in
2 repetitions). The two crossed measurement facets are therefore the **prompt
ordering** (`order`) and the **repetition** (`run`).

Three measurements are reported in `coefficients.csv`:

| `configuration`        | Meaning                                                        |
| ---------------------- | -------------------------------------------------------------- |
| `Baseline`             | Reliability of the Baseline configuration's scores.            |
| `DRG`                  | Reliability of the Document-Referenced Generation scores.      |
| `DRG_minus_Baseline`   | Reliability of the **paired DRG − Baseline difference** score. |

The paper's headline reliability (Φ = 0.984) is the dependability of the
`DRG_minus_Baseline` difference measurement at the `overall` reasoning part.

## The coefficients, and how to reproduce them

For each row, let σ²_signal be the between-patient (true-score) variance, SEM_abs
the absolute standard error of measurement, and SEM_rel the relative standard
error of measurement (all in `coefficients.csv`). Then:

- **Dependability coefficient** (absolute decisions):
  `Φ = σ²_signal / (σ²_signal + SEM_abs²)`
- **Generalizability coefficient** (relative decisions):
  `G = σ²_signal / (σ²_signal + SEM_rel²)`
- **Smallest detectable difference**: `SDD = 2.77 × SEM`,
  where `2.77 = 1.96 × √2`.

Worked example — the `DRG_minus_Baseline`, `overall` row:

```
σ²_signal = 513.041644
SEM_abs   = 2.915364     ->  SEM_abs² = 8.499346
SEM_rel   = 2.762625     ->  SEM_rel² = 7.632097

Φ   = 513.041644 / (513.041644 + 8.499346) = 513.041644 / 521.540990 = 0.983703  ≈ 0.984
G   = 513.041644 / (513.041644 + 7.632097) = 513.041644 / 520.673741 = 0.985342
SDD = 2.77 × 2.915364 = 8.075558  ≈ 8.08   (absolute)
```

These match the `phi_coefficient` (0.983703), `g_coefficient` (0.985342), and
`sdd_abs` (8.075557) cells exactly.

> Note: the dependability denominator uses the **error** variance
> `σ²_signal + SEM_abs²` (= 521.54). It is *not* the total observed score
> variance — averaging across the 15 questions and the crossed facets is what
> separates the small per-measurement error from the large between-patient
> signal.

## Per-part reliability

Computing Φ for each reasoning part of the `DRG_minus_Baseline` contrast yields:

| Reasoning part         | Φ        |
| ---------------------- | -------- |
| medication_selection   | 0.977353 |
| follow_up_monitoring   | 0.967791 |
| patient_education       | 0.977852 |

i.e. per-part Φ ranges **0.968–0.978**, as reported in the paper.

## Per-question variance decomposition

`variance_components.csv` reports, for each of the 15 reliability questions, the
ANOVA variance components σ²_patient (the between-patient signal), σ²_order,
σ²_run, and σ²_residual, together with their percentages of the total
random-plus-residual variance. Across questions the patient signal is small
relative to the residual on any single measurement; the high dependability of
the reported scores arises from averaging over the 15 questions and the crossed
rater facets, which is exactly what the coefficients above quantify.
