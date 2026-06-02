# Released G-theory variance-component estimates

These two CSVs are the **aggregate** generalizability-theory estimates that
underlie the paper's reliability results. They are derived from the (withheld)
raw AI-rater scores and contain no per-patient scores, rater identities, or
rubric text. For the full arithmetic that reproduces the headline numbers from
these cells, see [`../../VARIANCE_COMPONENTS.md`](../../VARIANCE_COMPONENTS.md).

`coefficients.csv` is the authoritative source for the reported Φ / SEM / SDD;
`variance_components.csv` is the supporting per-question detail (the two are at
different aggregation levels — see `VARIANCE_COMPONENTS.md`). In the study's
G-theory model the patient is the object of measurement and prompt ordering and
repetition are the two random facets.

## `coefficients.csv`

Dependability/generalizability coefficients and errors of measurement, one row
per `configuration` × `reasoning_part` (12 rows).

| Column                                | Meaning |
| ------------------------------------- | ------- |
| `configuration`                       | `Baseline`, `DRG`, or `DRG_minus_Baseline` (the paired difference measurement) |
| `reasoning_part`                      | `overall`, `medication_selection`, `follow_up_monitoring`, or `patient_education` |
| `n_patients`, `n_questions`           | Design dimensions (480 patients; 15 questions overall, 8/3/4 per part) |
| `sigma2_signal`                       | Between-patient (true-score) variance σ²_signal |
| `g_coefficient`, `phi_coefficient`    | Generalizability (G) and dependability (Φ) coefficients |
| `sem_rel`, `sem_abs`                  | Relative and absolute standard error of measurement |
| `sdd_rel`, `sdd_abs`                  | Smallest detectable difference (= 2.77 × SEM) |

The headline result is the `DRG_minus_Baseline` / `overall` row:
Φ = 0.983703 (≈ 0.984), SEM_abs = 2.915364 (≈ 2.92), SDD_abs = 8.075557 (≈ 8.08).

## `variance_components.csv`

Per-question ANOVA variance decomposition for the 15 reliability questions
(8 medication selection, 3 follow-up & monitoring, 4 patient education).

| Column                       | Meaning |
| ---------------------------- | ------- |
| `question_id`                | Reliability-question identifier (`Q3.*` medication, `Q4.*` follow-up, `Q5.*` education) |
| `reasoning_part`             | The reasoning part the question belongs to |
| `sigma2_patient`             | Between-patient variance (the measurement signal) |
| `sigma2_order`               | Prompt-ordering facet variance |
| `sigma2_run`                 | Repetition (run) facet variance |
| `sigma2_residual`            | Residual variance |
| `total_random_plus_residual` | Sum of the random-effect and residual variances |
| `pct_*`                      | Each component as a percent of `total_random_plus_residual` |

These are the variance-component estimates released per the paper's Data Sharing
Statement. The estimation code that produces equivalent decompositions from a
score matrix is in [`../../src/t2d_benchmark/g_theory/`](../../src/t2d_benchmark/g_theory/);
running it on the synthetic demo matrix reproduces the *mechanics*, not these
exact (study-derived) numbers. That runner writes its outputs with a `demo_`
prefix (`demo_coefficients.csv`, `demo_variance_components.csv`) under a generic
single-measurement schema, so they are never confused with the curated files
here.
