# Clinical Validation of the Benchmark Vignettes

This document records the clinical validation of the 480 synthetic Type 2
diabetes (T2D) vignettes released in [`data/vignettes/`](data/vignettes/). It
describes the validation **procedure** and the complexity-tagging rubric, and
provides sign-off slots for the clinical review record.

> **Status note.** Sections 1–4 document the validation design and the
> reproducible cohort properties. The clinician sign-off record in Section 5 is
> a template to be completed by the clinical team before the materials are
> treated as formally validated; the slots marked
> `<!-- TO BE COMPLETED BY CLINICAL TEAM -->` are intentionally empty.

## 1. Purpose and scope

The vignettes are fully synthetic outpatient T2D records generated to span the
clinically pivotal axes of T2D pharmacotherapy decision-making. "Validation"
here means review by board-certified diabetologists for **clinical
plausibility**, **internal consistency** (labs, medications, history, and
trajectory cohere), and **guideline relevance** — not validation against any real
patient data.

## 2. Validation procedure

The validation procedure followed in the study (paper Methods; Appendix D):

1. **Generation.** Vignettes were produced by a deterministic, seeded generator
   over the six-dimension factorial grid (Section 4), each as a 12-month
   longitudinal record across four 3-month-interval visits plus a current visit.
2. **Reviewer panel.** Three senior diabetologists with national guideline-panel
   experience reviewed the cohort.
   <!-- TO BE COMPLETED BY CLINICAL TEAM: panel members and affiliations -->
3. **Review protocol.** Each reviewer assessed every vignette for clinical
   plausibility, internal consistency of the longitudinal labs/medications/
   history, and guideline relevance of the encoded clinical profile.
4. **Adjudication.** Discrepancies were resolved by consensus among the senior
   reviewers, who were the final arbiters of clinical plausibility.
5. **Disposition.** Vignettes that failed review were revised and re-reviewed
   until the cohort met the acceptance criteria.

## 3. Complexity and trap tagging

Each vignette carries two labels in
[`data/vignettes/factorial_index.csv`](data/vignettes/factorial_index.csv):

- **`complexity_band`** ∈ {`Easy`, `Medium`, `Hard`} — a CKD-stage-driven
  pre-labeling rubric:
  - `Easy` — CKD stage 1–2
  - `Medium` — CKD stage 3 (3a / 3b)
  - `Hard` — CKD stage 4–5
  This band is a reproducible function of the CKD factor level. It is a
  structural pre-label; any per-case clinician override from the review record
  belongs in Section 5.
- **`trap_tag`** ∈ {`TRAP`, `NON-TRAP`} — every 10th vignette in the canonical
  order is a designated trap case (48 of 480), seeded to carry a recognized
  prescribing-pitfall pattern (e.g. heart-failure–thiazolidinedione, CKD–
  metformin, GLP-1/DPP-4 duplication, secretagogue over-treatment).

## 4. Factorial design

The 480 vignettes are a complete factorial grid over six clinically pivotal axes:

| Dimension | Levels | Count |
| --- | --- | --- |
| CKD stage | Stage 1-2 (60+), Stage 3a (45-59), Stage 3b (30-44), Stage 4 (15-29), Stage 5 (0-15) | 5 |
| Heart failure (HF) | No, Yes | 2 |
| ASCVD | No, Yes | 2 |
| MASLD | No, Yes | 2 |
| BMI category | Normal (<23), Overweight (23-27), Obese (>27) | 3 |
| HbA1c band | 5.5-6.5%, 6.5-7.5%, 7.5-9.0%, 9.0-11.0% | 4 |

5 × 2 × 2 × 2 × 3 × 4 = **480**. The grid is complete: every factor-level
combination appears exactly once. The released-cohort distributions
(reproducible from `factorial_index.csv`) are:

- CKD stage: 96 each across the 5 levels.
- HF / ASCVD / MASLD: 240 / 240 across No / Yes.
- BMI category: 160 each across the 3 levels.
- HbA1c band: 120 each across the 4 levels.
- Complexity band: Easy 96, Medium 192, Hard 192.
- Trap: 48 TRAP, 432 NON-TRAP.

## 5. Clinician sign-off record

<!-- TO BE COMPLETED BY CLINICAL TEAM -->

| Field | Value |
| --- | --- |
| Reviewer 1 (name, credential, affiliation) | |
| Reviewer 2 (name, credential, affiliation) | |
| Reviewer 3 (name, credential, affiliation) | |
| Review dates | |
| Vignettes reviewed / accepted / revised | |
| Inter-reviewer agreement (if computed) | |
| Signed off by (corresponding clinical author) | |
| Sign-off artifact reference | |

## 6. Note on cohort size (180 vs 480)

An earlier internal complexity-labeling exercise was conducted on a 180-vignette
cohort. The **released benchmark is the expanded full-factorial cohort of 480**
vignettes, and all distributions in this document and in `factorial_index.csv`
are computed over those 480. The earlier 180-case complexity counts do not
describe the released cohort and are not reproduced here.

<!-- TO BE COMPLETED BY CLINICAL TEAM: authoritative account of the 180 -> 480 expansion, if it is to be referenced in the manuscript -->
