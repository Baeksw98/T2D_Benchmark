"""Generate fully synthetic demo tables for the public analysis pipeline.

Two deterministic (SHA256-seeded) synthetic tables are produced:

- ``protocol`` -> ``synthetic_protocol_scores.csv``: a Baseline vs
  Document-Referenced Generation (DRG) score table for the Kolmogorov-Smirnov
  and paired-difference analysis.
- ``gtheory``  -> ``synthetic_score_matrix.csv``: a balanced, fully crossed
  ``object x prompt x occasion`` score matrix for the generalizability-theory
  variance-component analysis.

The rows are artificial examples for reproducibility testing only. They are not
sampled from, transformed from, or calibrated to any private study outputs, and
the numbers they yield are NOT the paper's reported values. The protocol table
is shaped only to make the descriptive contrast visible (DRG scores above
Baseline, with the follow-up/education questions hitting Baseline hardest); the
G-theory matrix is shaped to land the demo dependability coefficient in the
"excellent" band, qualitatively mirroring the paper without reproducing it.
"""

from __future__ import annotations

import argparse
import hashlib
from itertools import product
from pathlib import Path
from typing import Sequence

import pandas as pd

from t2d_benchmark.constants import BASELINE, DRG

# --- Protocol (KS / paired-difference) table -------------------------------

PROTOCOLS = (BASELINE, DRG)
CASE_IDS = tuple(f"DEMO_CASE_{idx:03d}" for idx in range(1, 11))
QUESTION_KEYS = tuple(f"Q{idx}" for idx in range(1, 16))  # 15 reliability questions
RATER_CONFIGS = tuple(f"cfg_{idx:02d}" for idx in range(1, 7))
PROTOCOL_COLUMNS = ("protocol", "case_id", "question_key", "rater_config", "Y_0_100")

# Question parts mirror the paper's reasoning sequence (8 + 3 + 4 = 15):
#   Q1-Q8   medication selection,  Q9-Q11 follow-up/monitoring,  Q12-Q15 education.
_FOLLOWUP_EDUCATION = set(range(9, 16))

# --- G-theory score matrix --------------------------------------------------

OBJECTS = tuple(f"P{idx:02d}" for idx in range(1, 13))   # 12 objects of measurement
PROMPTS = tuple(f"T{idx}" for idx in range(1, 10))       # 9 prompts (facet)
OCCASIONS = tuple(f"O{idx}" for idx in range(1, 6))      # 5 occasions (facet)
GTHEORY_COLUMNS = ("object_id", "prompt_id", "occasion_id", "score")


def stable_unit(*parts: object) -> float:
    """Deterministic pseudo-uniform value in [0, 1) from a SHA256 digest."""
    text = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0x100000000


def _centered(*parts: object) -> float:
    """Deterministic pseudo value in [-0.5, 0.5)."""
    return stable_unit(*parts) - 0.5


def protocol_score(protocol: str, case_id: str, question_key: str, rater_config: str) -> float:
    q = int(question_key[1:])
    if protocol == DRG:
        base = 62.0 + (q - 8) * 0.4
        spread = 25.0
    else:  # baseline: competent on medication selection, near-zero on later parts
        base = 2.0 if q in _FOLLOWUP_EDUCATION else 18.0
        spread = 16.0
    base += (int(case_id.rsplit("_", 1)[1]) - 5.5) * 0.6
    base += _centered(protocol, case_id, question_key, rater_config) * 2.0 * spread
    return round(min(100.0, max(0.0, base)), 2)


def gtheory_score(object_id: str, prompt_id: str, occasion_id: str) -> float:
    object_effect = _centered("object", object_id) * 60.0       # large between-object signal
    prompt_effect = _centered("prompt", prompt_id) * 4.0        # small facet variance
    occasion_effect = _centered("occasion", occasion_id) * 3.0  # small facet variance
    residual = _centered(object_id, prompt_id, occasion_id) * 4.0
    return round(50.0 + object_effect + prompt_effect + occasion_effect + residual, 4)


def build_protocol_frame() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for protocol, case_id, question_key, rater_config in product(
        PROTOCOLS, CASE_IDS, QUESTION_KEYS, RATER_CONFIGS
    ):
        rows.append(
            {
                "protocol": protocol,
                "case_id": case_id,
                "question_key": question_key,
                "rater_config": rater_config,
                "Y_0_100": protocol_score(protocol, case_id, question_key, rater_config),
            }
        )
    return pd.DataFrame(rows, columns=PROTOCOL_COLUMNS)


def build_gtheory_frame() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for object_id, prompt_id, occasion_id in product(OBJECTS, PROMPTS, OCCASIONS):
        rows.append(
            {
                "object_id": object_id,
                "prompt_id": prompt_id,
                "occasion_id": occasion_id,
                "score": gtheory_score(object_id, prompt_id, occasion_id),
            }
        )
    return pd.DataFrame(rows, columns=GTHEORY_COLUMNS)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("protocol", "gtheory", "both"), default="both")
    parser.add_argument("--output-dir", type=Path, default=Path("data/demo"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.target in ("protocol", "both"):
        frame = build_protocol_frame()
        path = args.output_dir / "synthetic_protocol_scores.csv"
        frame.to_csv(path, index=False)
        print(f"Wrote {len(frame)} rows to {path}")
    if args.target in ("gtheory", "both"):
        frame = build_gtheory_frame()
        path = args.output_dir / "synthetic_score_matrix.csv"
        frame.to_csv(path, index=False)
        print(f"Wrote {len(frame)} rows to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
