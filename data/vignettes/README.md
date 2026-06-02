# Synthetic T2D vignettes

480 fully synthetic outpatient Type 2 diabetes vignettes, `T2D_V001.json` …
`T2D_V480.json`, plus `factorial_index.csv`. The vignettes are released per the
paper's Data Sharing Statement; they contain no rubric content, model outputs,
or internal provenance.

## Vignette record schema

Each `T2D_V###.json` contains exactly these keys:

| Key | Type | Description |
| --- | --- | --- |
| `vignette_id` | string | Public identifier, `T2D_V001` … `T2D_V480` |
| `vignette_index` | int | 1-based index in the canonical factorial order |
| `language` | string | Always `"en"` (English-only release) |
| `factorial_cell` | object | The six factor levels (see below) |
| `complexity_band` | string | `Easy` / `Medium` / `Hard` (see `../../VALIDATION.md`) |
| `trap_tag` | string | `TRAP` / `NON-TRAP` |
| `prompt_text` | string | The clinical narrative (demographics, visit, history, comorbidities, medications, physical exam, longitudinal labs across 12/9/6/3-months-ago and current, and individualized decision factors) |

`factorial_cell` keys: `ckd_stage`, `hf`, `ascvd`, `masld`, `bmi_category`,
`hba1c_band`.

## `factorial_index.csv`

One row per vignette with its factorial coordinates and tags:

```
vignette_id, vignette_index, ckd_stage, hf, ascvd, masld,
bmi_category, hba1c_band, complexity_band, trap_tag
```

## Factorial structure

The 480 vignettes are a complete six-dimension factorial grid:

> CKD stage (5) × HF (2) × ASCVD (2) × MASLD (2) × BMI category (3) ×
> HbA1c band (4) = 480

Vignettes are numbered in the canonical generation order: the row-major product
order over the factor-level lists, with CKD varying slowest and HbA1c fastest.
The factorial cell of any vignette is therefore a deterministic function of its
1-based index, and `factorial_index.csv` can be regenerated from public
information alone:

```bash
python -m t2d_benchmark.build_factorial_index --output data/vignettes/factorial_index.csv
```

See [`../../VALIDATION.md`](../../VALIDATION.md) for the validation procedure,
the complexity rubric, and the cohort distributions.

## Note on rendered values

Within a factorial cell, the generator samples concrete longitudinal values
(e.g. a specific eGFR, BMI, or HbA1c trajectory). The rendered clinical values
in `prompt_text` may therefore sit near a category boundary or drift over the
12-month window; the authoritative factor level for each axis is the one in
`factorial_cell` / `factorial_index.csv`, fixed by the factorial design.
