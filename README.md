# Physician-Anchored Type 2 Diabetes Clinical-LLM Benchmark — Public Materials

Public materials accompanying the paper **"Clinical LLMs Require Physician-Anchored
Evaluation: A Type 2 Diabetes Benchmark for the Coming Wave of AI in Medicine."**

This repository fulfils the paper's Data Sharing Statement. It provides the
synthetic benchmark cohort, the generalizability-theory variance-component
estimates underlying the reported reliability, and the statistical analysis
pipeline — enough for independent inspection and methodological replication of
the benchmark's measurement properties.

Repository: https://github.com/Baeksw98/T2D_Benchmark

## What this repository releases

1. **The 480 synthetic patient vignettes** with their factorial structure and
   clinical validation documentation — [`data/vignettes/`](data/vignettes/),
   [`VALIDATION.md`](VALIDATION.md).
2. **The variance component estimates underlying the Φ coefficient** under
   generalizability theory — [`data/g_theory/`](data/g_theory/),
   [`VARIANCE_COMPONENTS.md`](VARIANCE_COMPONENTS.md).
3. **The statistical analysis pipeline in Python** — [`src/t2d_benchmark/`](src/t2d_benchmark/),
   runnable end-to-end on the bundled synthetic demo data.

## Release boundary

| Included | Withheld by design |
| --- | --- |
| 480 English synthetic vignettes + factorial index | Patient-specific gold-standard rubric content |
| G-theory variance components + Φ / SEM / SDD estimates | Production CDSS prompt templates (with safety-guard instructions) |
| Statistical analysis pipeline (Python) + synthetic demo data | Raw AI rater outputs |
| Clinical validation procedure (`VALIDATION.md`) | Internal deployment configuration and serving infrastructure |

The withheld materials incorporate safety-guard instructions whose disclosure
could enable circumvention by adversarial inputs and form proprietary components
under continued commercial development. The released variance components are
aggregate estimates that contain no per-patient scores, rater identities, or
rubric text. Reasonable requests for the withheld materials, for academic,
non-commercial research, are reviewed by the corresponding authors under a data
use agreement.

## The benchmark cohort

The 480 vignettes form a complete six-dimension factorial grid of clinically
pivotal axes:

> CKD stage (5) × heart failure (2) × ASCVD (2) × MASLD (2) × BMI category (3) ×
> HbA1c band (4) = **480**

Each vignette is a longitudinal outpatient record. The per-vignette factorial
coordinates are in [`data/vignettes/factorial_index.csv`](data/vignettes/factorial_index.csv);
the schema and validation procedure are in
[`data/vignettes/README.md`](data/vignettes/README.md) and [`VALIDATION.md`](VALIDATION.md).

## Reliability (generalizability theory)

The reliability of the AI-rater scores was quantified under generalizability
theory with the patient as the object of measurement (480 patients × 15
questions). The headline dependability coefficient is **Φ = 0.984** (SEM = 2.92;
SDD = 8.08), with per-part Φ in the range **0.968–0.978**. The released variance
components reproduce these numbers exactly; see
[`VARIANCE_COMPONENTS.md`](VARIANCE_COMPONENTS.md).

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

pytest -q
python -m t2d_benchmark.audit_release --root .
```

## Reproducing the analysis pipeline

The pipeline runs on the bundled **synthetic demo data** under `data/demo/`. It
exercises the full mechanics of the analysis; the numbers it produces are *not*
the paper's reported values (those are the curated estimates under
`data/g_theory/`, derived from the withheld raw scores).

```bash
# Generalizability-theory variance components + coefficients
python -m t2d_benchmark.g_theory.run_g_theory \
  --input data/demo/synthetic_score_matrix.csv \
  --output outputs/g_theory

# Baseline vs DRG distribution comparison (KS tests + paired differences)
python -m t2d_benchmark.analysis.run_clinical_analysis \
  --input data/demo/synthetic_protocol_scores.csv \
  --output outputs/clinical_analysis
```

To regenerate the synthetic demo tables:

```bash
python -m t2d_benchmark.analysis.generate_synthetic_demo_data --target both --output-dir data/demo
```

See [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) for the command-by-command guide
and expected outputs.

## Repository layout

```text
t2d_benchmark_public/
├── README.md                  # this file
├── REPRODUCIBILITY.md         # command-by-command reproduction guide
├── VALIDATION.md              # clinical validation procedure + complexity tagging
├── VARIANCE_COMPONENTS.md     # Φ / SEM / SDD arithmetic from the released estimates
├── PUBLIC_DATA_CARD.md        # description of the released data assets
├── DATA_LICENSE.md            # data-use terms
├── LICENSE                    # MIT (code)
├── CITATION.cff               # how to cite
├── data/
│   ├── vignettes/             # 480 vignettes + factorial_index.csv
│   ├── g_theory/              # released variance components + coefficients
│   └── demo/                  # synthetic inputs for the pipeline
├── src/t2d_benchmark/         # statistical analysis pipeline + build scripts
└── tests/                     # unit, data-contract, and release-audit tests
```

## Models evaluated

As described in the paper, candidate recommendations were generated with **GLM-5**
as the backbone, and the AI rater used **QWEN3.5-397B**. This repository releases
the analysis and aggregate estimates only; it does not release model outputs,
prompts, or serving configuration.

## Citation

If you use these materials, please cite the paper (see [`CITATION.cff`](CITATION.cff)):

> Baek S, Kim JH, Jin S-M, Kim G, Lee Y-B, Kim JY, Cho SH, Oh R, Kim B, Jang M,
> Ko S-H, Moon MK, Kim K, Hur KY. *Clinical LLMs Require Physician-Anchored
> Evaluation: A Type 2 Diabetes Benchmark for the Coming Wave of AI in Medicine.*
> 2026. (Manuscript under review; DOI and persistent repository identifier to be
> added upon publication.)

Corresponding authors: Kyu Yeon Hur (ky.hur@skku.edu), Kyunga Kim
(kyunga.j.kim@gmail.com).

## License

Code is released under the MIT License ([`LICENSE`](LICENSE)). The released data
(vignettes and variance-component estimates) are governed by
[`DATA_LICENSE.md`](DATA_LICENSE.md).
