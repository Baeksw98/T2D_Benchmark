# Reproducibility Guide

Command-by-command guide to verify the package and run the analysis pipeline.
All commands are run from the repository root.

## 1. Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Python 3.10+ (the study used 3.12). Dependencies: pandas, numpy, scipy,
statsmodels, matplotlib, pytest. No GPU and no model downloads are required.

## 2. Integrity checks

```bash
pytest -q
python -m t2d_benchmark.audit_release --root .
```

`pytest` runs the unit, data-contract, and release-audit tests. The audit prints
`Release audit passed.` when the released tree is clean.

## 3. Generalizability-theory pipeline

```bash
python -m t2d_benchmark.g_theory.run_g_theory \
  --input data/demo/synthetic_score_matrix.csv \
  --output outputs/g_theory
```

Produces, under `outputs/g_theory/` (the `demo_` prefix and a generic
single-measurement schema keep these distinct from the curated released
estimates under `data/g_theory/`):

| File | Contents |
| --- | --- |
| `demo_variance_components.csv` | Seven-source ANOVA variance decomposition |
| `demo_coefficients.csv` | Φ, G, SEM, SDD (random- and fixed-facet) |
| `demo_d_study.csv` | Decision-study projection across facet sizes |
| `summary.json` | Run summary (Φ lands in the "excellent" band on the demo matrix) |

## 4. Baseline vs DRG distribution comparison

```bash
python -m t2d_benchmark.analysis.run_clinical_analysis \
  --input data/demo/synthetic_protocol_scores.csv \
  --output outputs/clinical_analysis
```

Produces, under `outputs/clinical_analysis/`:

| File | Contents |
| --- | --- |
| `protocol_means.csv` | Per-question mean ± SD by configuration |
| `ks_tests.csv` | Per-question two-sample Kolmogorov–Smirnov statistic + p-value |
| `paired_differences.csv` | Per-question + overall mean paired difference (DRG − Baseline) |
| `protocol_means.png` | Per-question mean bar plot |
| `run_summary.json` | Run summary |

## 5. Regenerating the synthetic demo tables

```bash
python -m t2d_benchmark.analysis.generate_synthetic_demo_data \
  --target both --output-dir data/demo
```

The generators are deterministic (SHA256-seeded), so the tables are byte-stable.

## 6. Regenerating the factorial index

```bash
python -m t2d_benchmark.build_factorial_index \
  --output data/vignettes/factorial_index.csv
```

The factorial index is a deterministic function of the canonical vignette order
and can be rebuilt from public information alone.

## 7. Provenance of the vignettes (not reader-runnable)

`src/t2d_benchmark/build_public_vignettes.py` is a **provenance record** of how
the public vignettes were derived from the study's source narratives: it is an
allowlist sanitizer that reads only the English user-prompt text, strips internal
provenance fields, re-aliases identifiers, and re-scans each record for internal
markers. It requires the withheld private source as input (`--source-root`) and
therefore **cannot be run by readers**; it is included only to document the
derivation. The released vignettes and factorial index are the runnable,
public-data-derivable artifacts.

## What is and is not reproduced

Running the pipeline on the bundled synthetic data verifies the **analysis
mechanics** end-to-end: variance-component estimation, coefficient computation,
KS testing, and paired-difference analysis. It does **not** reproduce the paper's
exact numerical tables, which depend on the withheld raw rater scores. The
authoritative reliability estimates are the curated files under `data/g_theory/`;
[`VARIANCE_COMPONENTS.md`](VARIANCE_COMPONENTS.md) shows the arithmetic that
reproduces Φ = 0.984, SEM = 2.92, and SDD = 8.08 from those released cells.
