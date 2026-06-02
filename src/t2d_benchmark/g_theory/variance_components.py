"""Variance-component estimation for G-Theory analyses.

Ported verbatim from the production pipeline (ANOVA expected-mean-squares with
an optional REML cross-check). The only change from the source is that the
component labels are rendered in English for this public release.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

try:
    import statsmodels.api as sm
except ImportError:  # pragma: no cover - optional dependency at runtime
    sm = None


@dataclass(slots=True)
class VarianceComponent:
    source: str
    label: str
    estimate: float
    percent_of_total: float
    se: float | None = None
    ci_lower: float | None = None
    ci_upper: float | None = None
    truncated_from_negative: bool = False


@dataclass(slots=True)
class VarianceComponentResult:
    components: list[VarianceComponent]
    total_variance: float
    estimation_method: str
    n_object: int
    n_prompt: int
    n_occasion: int
    n_observations: int
    convergence_info: dict[str, object] = field(default_factory=dict)
    ms_table: dict[str, float] = field(default_factory=dict)
    ss_table: dict[str, float] = field(default_factory=dict)
    df_table: dict[str, int] = field(default_factory=dict)
    balanced: bool = True

    def component_map(self) -> dict[str, float]:
        return {component.source: component.estimate for component in self.components}

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["components"] = [asdict(component) for component in self.components]
        return payload


# Generic G-theory facet labels. This engine is a generic balanced
# object x facet1 x facet2 ANOVA. In the study it was applied with the patient
# as the object of measurement and prompt ordering and repetition as the two
# random facets; see VARIANCE_COMPONENTS.md for that mapping.
COMPONENT_LABELS = {
    "object": "Object of measurement",
    "prompt": "Facet 1 (prompt)",
    "occasion": "Facet 2 (occasion)",
    "object_prompt": "Object x Facet 1",
    "object_occasion": "Object x Facet 2",
    "prompt_occasion": "Facet 1 x Facet 2",
    "residual": "Residual",
}


def _require_balanced_fully_crossed(data: pd.DataFrame) -> tuple[int, int, int]:
    required = {"object_id", "prompt_id", "occasion_id", "score"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Matrix is missing required columns: {sorted(missing)}")

    matrix = data[["object_id", "prompt_id", "occasion_id", "score"]].copy()
    n_object = matrix["object_id"].nunique()
    n_prompt = matrix["prompt_id"].nunique()
    n_occasion = matrix["occasion_id"].nunique()
    if min(n_object, n_prompt, n_occasion) < 2:
        raise ValueError("Balanced q x t x o ANOVA requires at least 2 levels for object, prompt, and occasion.")

    cell_counts = (
        matrix.groupby(["object_id", "prompt_id", "occasion_id"], dropna=False)["score"].size().reset_index(name="n")
    )
    if len(cell_counts) != n_object * n_prompt * n_occasion:
        raise ValueError("G-Theory ANOVA requires a complete fully crossed lattice.")
    if cell_counts["n"].nunique() != 1 or int(cell_counts["n"].iloc[0]) != 1:
        raise ValueError("G-Theory ANOVA requires exactly one score per object x prompt x occasion cell.")
    return n_object, n_prompt, n_occasion


def estimate_variance_components_anova(
    data: pd.DataFrame,
    *,
    object_col: str = "object_id",
    prompt_col: str = "prompt_id",
    occasion_col: str = "occasion_id",
    score_col: str = "score",
) -> VarianceComponentResult:
    frame = data[[object_col, prompt_col, occasion_col, score_col]].copy()
    frame.rename(
        columns={object_col: "object_id", prompt_col: "prompt_id", occasion_col: "occasion_id", score_col: "score"},
        inplace=True,
    )
    n_object, n_prompt, n_occasion = _require_balanced_fully_crossed(frame)

    grand_mean = float(frame["score"].mean())
    object_means = frame.groupby("object_id")["score"].mean()
    prompt_means = frame.groupby("prompt_id")["score"].mean()
    occasion_means = frame.groupby("occasion_id")["score"].mean()
    object_prompt_means = frame.groupby(["object_id", "prompt_id"])["score"].mean()
    object_occasion_means = frame.groupby(["object_id", "occasion_id"])["score"].mean()
    prompt_occasion_means = frame.groupby(["prompt_id", "occasion_id"])["score"].mean()

    ss_object = n_prompt * n_occasion * float(((object_means - grand_mean) ** 2).sum())
    ss_prompt = n_object * n_occasion * float(((prompt_means - grand_mean) ** 2).sum())
    ss_occasion = n_object * n_prompt * float(((occasion_means - grand_mean) ** 2).sum())

    ss_object_prompt = (
        n_occasion
        * float(
            (
                object_prompt_means.to_numpy()
                - object_means.reindex(object_prompt_means.index.get_level_values(0)).to_numpy()
                - prompt_means.reindex(object_prompt_means.index.get_level_values(1)).to_numpy()
                + grand_mean
            )
            .astype(float)
            .dot(
                (
                    object_prompt_means.to_numpy()
                    - object_means.reindex(object_prompt_means.index.get_level_values(0)).to_numpy()
                    - prompt_means.reindex(object_prompt_means.index.get_level_values(1)).to_numpy()
                    + grand_mean
                ).astype(float)
            )
        )
    )
    ss_object_occasion = (
        n_prompt
        * float(
            (
                object_occasion_means.to_numpy()
                - object_means.reindex(object_occasion_means.index.get_level_values(0)).to_numpy()
                - occasion_means.reindex(object_occasion_means.index.get_level_values(1)).to_numpy()
                + grand_mean
            )
            .astype(float)
            .dot(
                (
                    object_occasion_means.to_numpy()
                    - object_means.reindex(object_occasion_means.index.get_level_values(0)).to_numpy()
                    - occasion_means.reindex(object_occasion_means.index.get_level_values(1)).to_numpy()
                    + grand_mean
                ).astype(float)
            )
        )
    )
    ss_prompt_occasion = (
        n_object
        * float(
            (
                prompt_occasion_means.to_numpy()
                - prompt_means.reindex(prompt_occasion_means.index.get_level_values(0)).to_numpy()
                - occasion_means.reindex(prompt_occasion_means.index.get_level_values(1)).to_numpy()
                + grand_mean
            )
            .astype(float)
            .dot(
                (
                    prompt_occasion_means.to_numpy()
                    - prompt_means.reindex(prompt_occasion_means.index.get_level_values(0)).to_numpy()
                    - occasion_means.reindex(prompt_occasion_means.index.get_level_values(1)).to_numpy()
                    + grand_mean
                ).astype(float)
            )
        )
    )

    merged = frame.merge(
        object_prompt_means.rename("mean_object_prompt"),
        left_on=["object_id", "prompt_id"],
        right_index=True,
    ).merge(
        object_occasion_means.rename("mean_object_occasion"),
        left_on=["object_id", "occasion_id"],
        right_index=True,
    ).merge(
        prompt_occasion_means.rename("mean_prompt_occasion"),
        left_on=["prompt_id", "occasion_id"],
        right_index=True,
    )
    merged["mean_object"] = merged["object_id"].map(object_means)
    merged["mean_prompt"] = merged["prompt_id"].map(prompt_means)
    merged["mean_occasion"] = merged["occasion_id"].map(occasion_means)
    ss_residual = float(
        (
            merged["score"]
            - merged["mean_object_prompt"]
            - merged["mean_object_occasion"]
            - merged["mean_prompt_occasion"]
            + merged["mean_object"]
            + merged["mean_prompt"]
            + merged["mean_occasion"]
            - grand_mean
        )
        .pow(2)
        .sum()
    )

    df_table = {
        "object": n_object - 1,
        "prompt": n_prompt - 1,
        "occasion": n_occasion - 1,
        "object_prompt": (n_object - 1) * (n_prompt - 1),
        "object_occasion": (n_object - 1) * (n_occasion - 1),
        "prompt_occasion": (n_prompt - 1) * (n_occasion - 1),
        "residual": (n_object - 1) * (n_prompt - 1) * (n_occasion - 1),
    }
    ss_table = {
        "object": ss_object,
        "prompt": ss_prompt,
        "occasion": ss_occasion,
        "object_prompt": ss_object_prompt,
        "object_occasion": ss_object_occasion,
        "prompt_occasion": ss_prompt_occasion,
        "residual": ss_residual,
    }
    ms_table = {
        source: (ss_table[source] / df_table[source]) if df_table[source] > 0 else 0.0
        for source in df_table
    }

    raw_estimates = {
        "residual": ms_table["residual"],
        "object_prompt": (ms_table["object_prompt"] - ms_table["residual"]) / n_occasion,
        "object_occasion": (ms_table["object_occasion"] - ms_table["residual"]) / n_prompt,
        "prompt_occasion": (ms_table["prompt_occasion"] - ms_table["residual"]) / n_object,
        "object": (
            ms_table["object"] - ms_table["object_prompt"] - ms_table["object_occasion"] + ms_table["residual"]
        )
        / (n_prompt * n_occasion),
        "prompt": (
            ms_table["prompt"] - ms_table["object_prompt"] - ms_table["prompt_occasion"] + ms_table["residual"]
        )
        / (n_object * n_occasion),
        "occasion": (
            ms_table["occasion"] - ms_table["object_occasion"] - ms_table["prompt_occasion"] + ms_table["residual"]
        )
        / (n_object * n_prompt),
    }

    estimates: dict[str, tuple[float, bool]] = {}
    for source, estimate in raw_estimates.items():
        truncated = estimate < 0
        estimates[source] = (max(0.0, float(estimate)), truncated)

    total_variance = float(sum(value for value, _ in estimates.values()))
    components = []
    for source in ("object", "prompt", "occasion", "object_prompt", "object_occasion", "prompt_occasion", "residual"):
        estimate, truncated = estimates[source]
        pct = (estimate / total_variance * 100.0) if total_variance > 0 else 0.0
        components.append(
            VarianceComponent(
                source=source,
                label=COMPONENT_LABELS[source],
                estimate=estimate,
                percent_of_total=round(pct, 3),
                truncated_from_negative=truncated,
            )
        )

    return VarianceComponentResult(
        components=components,
        total_variance=round(total_variance, 6),
        estimation_method="ANOVA_EMS",
        n_object=n_object,
        n_prompt=n_prompt,
        n_occasion=n_occasion,
        n_observations=len(frame),
        convergence_info={"status": "ok"},
        ms_table={key: round(float(value), 6) for key, value in ms_table.items()},
        ss_table={key: round(float(value), 6) for key, value in ss_table.items()},
        df_table=df_table,
        balanced=True,
    )


def estimate_variance_components_reml(
    data: pd.DataFrame,
    *,
    object_col: str = "object_id",
    prompt_col: str = "prompt_id",
    occasion_col: str = "occasion_id",
    score_col: str = "score",
    prompt_fixed: bool = False,
) -> VarianceComponentResult:
    if sm is None:
        raise RuntimeError("statsmodels is not installed; REML cross-check is unavailable.")

    frame = data[[object_col, prompt_col, occasion_col, score_col]].copy()
    frame.rename(
        columns={object_col: "object_id", prompt_col: "prompt_id", occasion_col: "occasion_id", score_col: "score"},
        inplace=True,
    )
    _require_balanced_fully_crossed(frame)
    frame["group_id"] = "all"
    frame["object_prompt"] = frame["object_id"].astype(str) + "::" + frame["prompt_id"].astype(str)
    frame["object_occasion"] = frame["object_id"].astype(str) + "::" + frame["occasion_id"].astype(str)
    frame["prompt_occasion"] = frame["prompt_id"].astype(str) + "::" + frame["occasion_id"].astype(str)

    vc_formula = {
        "object": "0 + C(object_id)",
        "occasion": "0 + C(occasion_id)",
        "object_prompt": "0 + C(object_prompt)",
        "object_occasion": "0 + C(object_occasion)",
        "prompt_occasion": "0 + C(prompt_occasion)",
    }
    formula = "score ~ C(prompt_id)" if prompt_fixed else "score ~ 1"
    if not prompt_fixed:
        vc_formula = {"prompt": "0 + C(prompt_id)", **vc_formula}

    model = sm.MixedLM.from_formula(
        formula,
        groups="group_id",
        re_formula="0",
        vc_formula=vc_formula,
        data=frame,
    )
    fit = model.fit(reml=True, method="lbfgs", disp=False)

    vcomp_names = list(vc_formula.keys())
    vcomp_values = list(fit.vcomp) if getattr(fit, "vcomp", None) is not None else []
    component_values = {name: 0.0 for name in ("object", "prompt", "occasion", "object_prompt", "object_occasion", "prompt_occasion")}
    for name, value in zip(vcomp_names, vcomp_values):
        component_values[name] = max(0.0, float(value))
    component_values["residual"] = max(0.0, float(fit.scale))

    total_variance = float(sum(component_values.values()))
    components = []
    for source in ("object", "prompt", "occasion", "object_prompt", "object_occasion", "prompt_occasion", "residual"):
        estimate = component_values.get(source, 0.0)
        pct = (estimate / total_variance * 100.0) if total_variance > 0 else 0.0
        components.append(
            VarianceComponent(
                source=source,
                label=COMPONENT_LABELS[source],
                estimate=round(float(estimate), 6),
                percent_of_total=round(float(pct), 3),
            )
        )

    return VarianceComponentResult(
        components=components,
        total_variance=round(total_variance, 6),
        estimation_method="REML",
        n_object=frame["object_id"].nunique(),
        n_prompt=frame["prompt_id"].nunique(),
        n_occasion=frame["occasion_id"].nunique(),
        n_observations=len(frame),
        convergence_info={
            "status": "ok",
            "converged": bool(getattr(fit, "converged", False)),
            "llf": round(float(getattr(fit, "llf", np.nan)), 6) if hasattr(fit, "llf") else None,
            "prompt_fixed": prompt_fixed,
        },
    )
