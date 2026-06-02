# Synthetic demo data

Two deterministic (SHA256-seeded) synthetic tables that drive the analysis
pipeline end-to-end without any private data. **The numbers they produce are not
the paper's results** — they exist only to exercise the code. Regenerate with:

```bash
python -m t2d_benchmark.analysis.generate_synthetic_demo_data --target both --output-dir data/demo
```

## `synthetic_score_matrix.csv` (540 rows)

Input to the G-theory runner (`t2d_benchmark.g_theory.run_g_theory`). A balanced,
fully crossed `object × prompt × occasion` lattice (12 × 9 × 5), one score per cell.

| Column | Type | Description |
| --- | --- | --- |
| `object_id` | string | Object of measurement (generic facet placeholder; in the study, the patient) |
| `prompt_id` | string | Facet 1 (generic placeholder; in the study, prompt ordering) |
| `occasion_id` | string | Facet 2 (generic placeholder; in the study, repetition) |
| `score` | float | Synthetic measurement value |

## `synthetic_protocol_scores.csv` (1,800 rows)

Input to the Baseline-vs-DRG comparison (`t2d_benchmark.analysis.run_clinical_analysis`).

| Column | Type | Description |
| --- | --- | --- |
| `protocol` | string | `baseline` or `rubric_assisted` (the latter encodes **Document-Referenced Generation, DRG**) |
| `case_id` | string | Synthetic case id (`DEMO_CASE_001`…`DEMO_CASE_010`) |
| `question_key` | string | Reliability question (`Q1`…`Q15`) |
| `rater_config` | string | Rater configuration (`cfg_01`…`cfg_06`) |
| `Y_0_100` | float | Score on the inclusive 0–100 scale |
