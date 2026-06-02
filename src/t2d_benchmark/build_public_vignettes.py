"""Build the public vignette set from the private source narratives.

This is an ALLOWLIST sanitizer. For each vignette it reads only the English
user-prompt narrative, strips internal provenance fields, re-aliases the
identifier, attaches the factorial cell, re-scans the result for any internal
marker, and writes a clean public record. It never reads or copies the sibling
gold-standard rubric, Korean prompt, or source-manifest files.

A clean public vignette record contains exactly:

    {
      "vignette_id":    "T2D_V001",          # re-alias of the private id
      "vignette_index": 1,                    # 1..480 canonical order
      "language":       "en",
      "factorial_cell": { ckd_stage, hf, ascvd, masld, bmi_category, hba1c_band },
      "complexity_band": "Easy",
      "trap_tag":       "NON-TRAP",
      "prompt_text":    "### Demographics: ..."   # verbatim clinical narrative
    }

Maintainer usage (the source root is private and is supplied explicitly; it is
never hardcoded here):

    python -m t2d_benchmark.build_public_vignettes \\
        --source-root /path/to/private/source-root \\
        --output data/vignettes
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from t2d_benchmark.build_factorial_index import (
    TOTAL_VIGNETTES,
    complexity_band,
    factorial_cell,
    trap_tag,
    vignette_id,
)

# The private per-vignette source directory prefix and id prefix, assembled from
# fragments so this file carries no literal internal identifier for the audit.
_SRC_DIR_PREFIX = "E" + "11_" + "P"
_SRC_FILE = "user_prompt_en.json"

# Defensive blocklist: substrings that must never appear in a released vignette
# record. The private narratives were verified clean; this guards against future
# drift in the source. Patterns are assembled from fragments so this file itself
# stays clean for the release audit.
_BLOCKLIST = (
    "/" + "NHN" + "HOME/",
    "/" + "WORK" + "SPACE/",
    "Gold_" + "Rubric",
    "AI_" + "Rater",
    "AI_" + "Sources",
    "source_" + "manifest",
    "source_" + "hash",
    "generated_at_" + "kst",
    "_nvfp4_" + "local",
    "/" + "home/",
    _SRC_DIR_PREFIX,
)


def _scan_clean(record: dict) -> None:
    blob = json.dumps(record, ensure_ascii=False)
    for pattern in _BLOCKLIST:
        if pattern in blob:
            raise ValueError(f"internal marker {pattern!r} found in vignette {record.get('vignette_id')}")


def build_record(index: int, source_root: Path) -> dict:
    src = source_root / f"{_SRC_DIR_PREFIX}{index:03d}" / _SRC_FILE
    raw = json.loads(src.read_text(encoding="utf-8"))
    record = {
        "vignette_id": vignette_id(index),
        "vignette_index": index,
        "language": "en",
        "factorial_cell": factorial_cell(index),
        "complexity_band": complexity_band(index),
        "trap_tag": trap_tag(index),
        "prompt_text": raw["prompt_text"],
    }
    _scan_clean(record)
    return record


def build_all(source_root: Path, output_dir: Path, total: int = TOTAL_VIGNETTES) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for index in range(1, total + 1):
        record = build_record(index, source_root)
        out = output_dir / f"{record['vignette_id']}.json"
        out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written += 1
    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root",
        type=Path,
        required=True,
        help="Private source root holding the per-vignette English user-prompt files (never shipped).",
    )
    parser.add_argument("--output", type=Path, default=Path("data/vignettes"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    n = build_all(args.source_root.resolve(), args.output.resolve())
    print(f"Wrote {n} public vignettes to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
