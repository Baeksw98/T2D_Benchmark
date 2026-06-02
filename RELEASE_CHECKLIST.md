# Release Checklist

Run before publishing the repository.

## Content

1. Confirm the repository contains `README.md`, `REPRODUCIBILITY.md`,
   `VALIDATION.md`, `VARIANCE_COMPONENTS.md`, `PUBLIC_DATA_CARD.md`,
   `DATA_LICENSE.md`, `LICENSE`, `CITATION.cff`, `pyproject.toml`, and
   `requirements.txt`.
2. Confirm `data/vignettes/` has 480 `T2D_V###.json` files plus
   `factorial_index.csv`; `data/g_theory/` has `variance_components.csv` and
   `coefficients.csv`; `data/demo/` has both synthetic tables.
3. Confirm the release does **not** include gold-rubric content, production CDSS
   prompts, raw AI rater outputs, study workbooks (`.xlsx`/`.xls`), private
   source manifests, or internal serving/deployment configuration.
4. Confirm `VALIDATION.md` Section 5 (clinician sign-off) is completed before the
   materials are presented as formally validated.

## Verification

5. Create a clean virtual environment and `pip install -r requirements.txt && pip install -e .`.
6. Run `pytest -q`.
7. Run `python -m t2d_benchmark.audit_release --root .` and confirm
   `Release audit passed.`
8. Run the two pipeline commands in `REPRODUCIBILITY.md` and confirm outputs are
   created.
9. Confirm the vignette set is complete: 480 files, ids `T2D_V001`…`T2D_V480`,
   `factorial_index.csv` is a complete six-dimension grid (480 unique cells).
10. Confirm the released variance components reproduce Φ ≈ 0.984, SEM ≈ 2.92,
    SDD ≈ 8.08 (see `VARIANCE_COMPONENTS.md`).

## Git isolation (critical)

This public tree is developed inside a private working tree. It must ship with a
**fresh, isolated git history** — never the private repository's `.git/`,
history, or remote.

11. Build the publication repository from a **fresh `git init`** (or a copy of
    this tree outside the private working tree, then `git init`). Do **not**
    `git clone` the private repository, reuse its `.git/`, or push to its remote.
12. Confirm `git log` shows only the intended public commit history and the
    committer identity is the intended public identity (not an internal OS
    username).
13. Confirm `.git/config` contains no reference to the private repository remote.
14. Run `git status --short --ignored` and confirm the required public data files
    (the vignette JSONs and the `data/` CSVs) are tracked, not ignored.
15. Confirm the public repository URL is set in `README.md`, `CITATION.cff`, and
    `pyproject.toml` (https://github.com/Baeksw98/T2D_Benchmark).
