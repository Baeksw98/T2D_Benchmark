from __future__ import annotations

import csv
import json
from pathlib import Path

from t2d_benchmark.build_factorial_index import factorial_cell, vignette_id

ROOT = Path(__file__).resolve().parents[1]
VDIR = ROOT / "data" / "vignettes"
EXPECTED_KEYS = {
    "vignette_id",
    "vignette_index",
    "language",
    "factorial_cell",
    "complexity_band",
    "trap_tag",
    "prompt_text",
}
# Internal markers assembled from fragments so this test file stays audit-clean.
INTERNAL_MARKERS = (
    "E" + "11_" + "P",
    "source_" + "hash",
    "generated_at_" + "kst",
    "Gold_" + "Rubric",
    "AI_" + "Sources",
)


def test_exactly_480_vignettes_with_contiguous_ids() -> None:
    files = sorted(VDIR.glob("T2D_V*.json"))
    assert len(files) == 480
    ids = {json.loads(p.read_text())["vignette_id"] for p in files}
    assert ids == {vignette_id(i) for i in range(1, 481)}


def test_every_vignette_has_clean_english_schema() -> None:
    for path in VDIR.glob("T2D_V*.json"):
        record = json.loads(path.read_text())
        assert set(record) == EXPECTED_KEYS, path.name
        assert record["language"] == "en"
        assert set(record["factorial_cell"]) == {
            "ckd_stage", "hf", "ascvd", "masld", "bmi_category", "hba1c_band"
        }


def test_no_internal_markers_in_vignettes() -> None:
    for path in VDIR.glob("T2D_V*.json"):
        blob = path.read_text()
        for marker in INTERNAL_MARKERS:
            assert marker not in blob, f"{marker!r} leaked into {path.name}"


def test_factorial_cell_matches_canonical_index() -> None:
    for path in VDIR.glob("T2D_V*.json"):
        record = json.loads(path.read_text())
        assert record["factorial_cell"] == factorial_cell(record["vignette_index"])


def test_factorial_index_is_complete_grid() -> None:
    rows = list(csv.DictReader((VDIR / "factorial_index.csv").open()))
    assert len(rows) == 480
    cells = {
        (r["ckd_stage"], r["hf"], r["ascvd"], r["masld"], r["bmi_category"], r["hba1c_band"])
        for r in rows
    }
    assert len(cells) == 480  # complete six-dimension grid, no duplicates
    assert sum(r["trap_tag"] == "TRAP" for r in rows) == 48
    assert {r["complexity_band"] for r in rows} == {"Easy", "Medium", "Hard"}
