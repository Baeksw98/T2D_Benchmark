"""Public clinical-analysis pipeline: Baseline vs DRG distribution comparison.

Reproduces the descriptive comparison reported in the paper's reliability
section: per-question Kolmogorov-Smirnov two-sample tests and paired
differences between the Document-Referenced Generation (DRG) configuration
(``rubric_assisted``) and the Baseline configuration (``baseline``).

Outputs (under ``--output``):
    protocol_means.csv     -- per question x protocol: n, mean, SD
    ks_tests.csv           -- per question: two-sample KS statistic + p-value
    paired_differences.csv -- per question + overall: mean paired diff (DRG-Baseline),
                              SD, n, paired t-test p, and % of pairs with DRG > Baseline
    protocol_means.png     -- per-question mean bar plot by protocol
    run_summary.json       -- machine-readable summary

This runs on the synthetic demo table under ``data/demo/``. The numbers are NOT
the paper's reported values; the authoritative reliability estimates are the
curated variance components under ``data/g_theory/``.

Usage:
    python -m t2d_benchmark.analysis.run_clinical_analysis \\
        --input data/demo/synthetic_protocol_scores.csv \\
        --output outputs/clinical_analysis
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from t2d_benchmark.constants import BASELINE, DRG

REQUIRED_COLUMNS = ("protocol", "case_id", "question_key", "rater_config", "Y_0_100")
PAIR_KEYS = ["case_id", "question_key", "rater_config"]


def load_table(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = set(REQUIRED_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Input table {path} is missing required columns: {sorted(missing)}")
    return frame


def _question_order(frame: pd.DataFrame) -> list[str]:
    keys = frame["question_key"].unique().tolist()
    return sorted(keys, key=lambda key: int(str(key).lstrip("Q") or 0))


def protocol_means(frame: pd.DataFrame) -> pd.DataFrame:
    rows = (
        frame.groupby(["question_key", "protocol"])["Y_0_100"]
        .agg(n="count", mean="mean", std="std")
        .reset_index()
    )
    rows["mean"] = rows["mean"].round(4)
    rows["std"] = rows["std"].round(4)
    return rows


def ks_tests(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for question_key in _question_order(frame):
        block = frame[frame["question_key"] == question_key]
        baseline = block.loc[block["protocol"] == BASELINE, "Y_0_100"].to_numpy()
        drg = block.loc[block["protocol"] == DRG, "Y_0_100"].to_numpy()
        if len(baseline) == 0 or len(drg) == 0:
            continue
        result = stats.ks_2samp(baseline, drg, alternative="two-sided", method="auto")
        rows.append(
            {
                "question_key": question_key,
                "baseline_n": int(len(baseline)),
                "drg_n": int(len(drg)),
                "ks_statistic": round(float(result.statistic), 6),
                "p_value": float(result.pvalue),
            }
        )
    return pd.DataFrame(rows)


def paired_differences(frame: pd.DataFrame) -> pd.DataFrame:
    base = frame.loc[frame["protocol"] == BASELINE, PAIR_KEYS + ["Y_0_100"]].rename(
        columns={"Y_0_100": "y_baseline"}
    )
    drg = frame.loc[frame["protocol"] == DRG, PAIR_KEYS + ["Y_0_100"]].rename(
        columns={"Y_0_100": "y_drg"}
    )
    merged = base.merge(drg, on=PAIR_KEYS, how="inner")
    merged["diff"] = merged["y_drg"] - merged["y_baseline"]

    rows: list[dict[str, object]] = []
    for question_key in _question_order(merged):
        diffs = merged.loc[merged["question_key"] == question_key, "diff"].to_numpy()
        rows.append(_difference_row(question_key, diffs))
    rows.append(_difference_row("OVERALL", merged["diff"].to_numpy()))
    return pd.DataFrame(rows)


def _difference_row(label: str, diffs) -> dict[str, object]:
    diffs = np.asarray(diffs, dtype=float)
    n = int(diffs.size)
    if n == 0:
        return {"question_key": label, "n_pairs": 0}
    p_value = None
    if n > 1 and float(np.std(diffs)) > 0:
        p_value = float(stats.ttest_1samp(diffs, 0.0).pvalue)
    return {
        "question_key": label,
        "n_pairs": n,
        "mean_paired_diff": round(float(diffs.mean()), 4),
        "sd_paired_diff": round(float(diffs.std(ddof=1)) if n > 1 else 0.0, 4),
        "paired_t_p_value": p_value,
        "pct_drg_higher": round(float((diffs > 0).mean()) * 100.0, 2),
    }


def write_protocol_means_figure(means: pd.DataFrame, path: Path) -> None:
    order = _question_order(means)
    fig, ax = plt.subplots(figsize=(10, 4))
    width = 0.4
    for offset, protocol, label in ((-width / 2, BASELINE, "Baseline"), (width / 2, DRG, "DRG")):
        sub = means[means["protocol"] == protocol].set_index("question_key").reindex(order)
        positions = [i + offset for i in range(len(order))]
        ax.bar(positions, sub["mean"].to_numpy(), width=width, label=label)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(order, rotation=45, ha="right")
    ax.set_ylabel("Mean reliability score (0-100)")
    ax.set_title("Per-question mean score by configuration (synthetic demo)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def run(input_path: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = load_table(input_path)

    means = protocol_means(frame)
    ks = ks_tests(frame)
    paired = paired_differences(frame)

    means.to_csv(output_dir / "protocol_means.csv", index=False)
    ks.to_csv(output_dir / "ks_tests.csv", index=False)
    paired.to_csv(output_dir / "paired_differences.csv", index=False)
    write_protocol_means_figure(means, output_dir / "protocol_means.png")

    overall = paired[paired["question_key"] == "OVERALL"].iloc[0].to_dict()
    summary = {
        "input": str(input_path),
        "output_dir": str(output_dir),
        "n_rows": int(len(frame)),
        "n_questions": int(frame["question_key"].nunique()),
        "overall_mean_paired_diff": overall.get("mean_paired_diff"),
        "overall_pct_drg_higher": overall.get("pct_drg_higher"),
        "n_pairs": overall.get("n_pairs"),
    }
    (output_dir / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Baseline vs DRG KS + paired-difference analysis.")
    parser.add_argument("--input", type=Path, default=Path("data/demo/synthetic_protocol_scores.csv"))
    parser.add_argument("--output", type=Path, default=Path("outputs/clinical_analysis"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run(args.input.resolve(), args.output.resolve())
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
