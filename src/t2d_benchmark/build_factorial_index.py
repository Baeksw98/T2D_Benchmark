"""Build the factorial index for the 480 synthetic vignettes.

The 480 vignettes form a complete six-dimension factorial grid:

    CKD stage (5) x HF (2) x ASCVD (2) x MASLD (2) x BMI (3) x HbA1c (4) = 480

The vignettes are emitted in the canonical generation order (vignette index 1..480),
which is the row-major ``itertools.product`` order over the factor-level lists below
(CKD outermost, HbA1c innermost). Each vignette's factorial cell is therefore a
deterministic function of its 1-based index -- recovered here by a mixed-radix
decomposition, independent of any drift in the rendered clinical narrative.

The level-label lists and product order are inlined (not imported from any private
module) so this index is fully reproducible from public information alone.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Sequence

# --- Factor-level labels (outermost -> innermost in the product order) -------

CKD_LEVELS = (
    "Stage 1-2 (60+)",
    "Stage 3a (45-59)",
    "Stage 3b (30-44)",
    "Stage 4 (15-29)",
    "Stage 5 (0-15)",
)
HF_LEVELS = ("No", "Yes")
ASCVD_LEVELS = ("No", "Yes")
MASLD_LEVELS = ("No", "Yes")
BMI_LEVELS = ("Normal (<23)", "Overweight (23-27)", "Obese (>27)")
HBA1C_LEVELS = ("5.5-6.5%", "6.5-7.5%", "7.5-9.0%", "9.0-11.0%")

TOTAL_VIGNETTES = (
    len(CKD_LEVELS) * len(HF_LEVELS) * len(ASCVD_LEVELS)
    * len(MASLD_LEVELS) * len(BMI_LEVELS) * len(HBA1C_LEVELS)
)  # == 480

# Radix strides for the mixed-radix decomposition (product order: ckd, hf, ascvd,
# masld, bmi, hba1c with hba1c varying fastest).
_STRIDE_CKD = len(HF_LEVELS) * len(ASCVD_LEVELS) * len(MASLD_LEVELS) * len(BMI_LEVELS) * len(HBA1C_LEVELS)  # 96
_STRIDE_HF = len(ASCVD_LEVELS) * len(MASLD_LEVELS) * len(BMI_LEVELS) * len(HBA1C_LEVELS)  # 48
_STRIDE_ASCVD = len(MASLD_LEVELS) * len(BMI_LEVELS) * len(HBA1C_LEVELS)  # 24
_STRIDE_MASLD = len(BMI_LEVELS) * len(HBA1C_LEVELS)  # 12
_STRIDE_BMI = len(HBA1C_LEVELS)  # 4

# Trap cases: every 10th vignette in the canonical order (48 total).
TRAP_STEP = 10

FIELDNAMES = (
    "vignette_id",
    "vignette_index",
    "ckd_stage",
    "hf",
    "ascvd",
    "masld",
    "bmi_category",
    "hba1c_band",
    "complexity_band",
    "trap_tag",
)


def vignette_id(index: int) -> str:
    """Public, order-preserving vignette identifier for a 1-based index."""
    return f"T2D_V{index:03d}"


def factorial_cell(index: int) -> dict:
    """Return the six factor levels for a 1-based vignette index (1..480)."""
    if not 1 <= index <= TOTAL_VIGNETTES:
        raise ValueError(f"vignette index {index} out of range 1..{TOTAL_VIGNETTES}")
    idx = index - 1
    ckd_i = (idx // _STRIDE_CKD) % len(CKD_LEVELS)
    hf_i = (idx // _STRIDE_HF) % len(HF_LEVELS)
    ascvd_i = (idx // _STRIDE_ASCVD) % len(ASCVD_LEVELS)
    masld_i = (idx // _STRIDE_MASLD) % len(MASLD_LEVELS)
    bmi_i = (idx // _STRIDE_BMI) % len(BMI_LEVELS)
    hba1c_i = idx % len(HBA1C_LEVELS)
    return {
        "ckd_stage": CKD_LEVELS[ckd_i],
        "hf": HF_LEVELS[hf_i],
        "ascvd": ASCVD_LEVELS[ascvd_i],
        "masld": MASLD_LEVELS[masld_i],
        "bmi_category": BMI_LEVELS[bmi_i],
        "hba1c_band": HBA1C_LEVELS[hba1c_i],
    }


def complexity_band(index: int) -> str:
    """CKD-stage-driven complexity band (pre-labeling rubric).

    Easy = CKD stage 1-2; Medium = CKD stage 3 (3a/3b); Hard = CKD stage 4-5.
    See VALIDATION.md for the rubric and how per-case clinician review relates to it.
    """
    ckd_i = ((index - 1) // _STRIDE_CKD) % len(CKD_LEVELS)
    if ckd_i == 0:
        return "Easy"
    if ckd_i in (1, 2):
        return "Medium"
    return "Hard"


def trap_tag(index: int) -> str:
    """Trap flag: every 10th vignette in the canonical order is a trap case."""
    return "TRAP" if index % TRAP_STEP == 0 else "NON-TRAP"


def index_row(index: int) -> dict:
    cell = factorial_cell(index)
    return {
        "vignette_id": vignette_id(index),
        "vignette_index": index,
        **cell,
        "complexity_band": complexity_band(index),
        "trap_tag": trap_tag(index),
    }


def build_rows(total: int = TOTAL_VIGNETTES) -> list[dict]:
    return [index_row(i) for i in range(1, total + 1)]


def write_index(path: Path, total: int = TOTAL_VIGNETTES) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = build_rows(total)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(FIELDNAMES))
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/vignettes/factorial_index.csv"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    n = write_index(args.output.resolve())
    print(f"Wrote {n} factorial rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
