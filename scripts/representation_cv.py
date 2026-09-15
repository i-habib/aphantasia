#!/usr/bin/env python3
"""Cross-validated comparison of visual-only vs multisensory imagery representations.

Point --data-root at output from scripts/fetch_public.py. Participant-level data
remain in memory. Only aggregate CV metrics and bootstrap intervals are written.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import GridSearchCV, RepeatedStratifiedKFold, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from aphantasia.datasets import load_arnold_code

SEED = 20260914
C_GRID = [0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0]
P1_MODALITIES = ["image", "sound", "touch", "motor", "taste", "smell", "emotion", "voice"]
P3_MODALITIES = ["visual", "auditory", "smell", "taste", "touch", "movement"]


@dataclass
class OutcomeSpec:
    project: str
    cohort: str
    outcome: str
    frame: pd.DataFrame
    modality_cols: list[str]
    visual_col: str
    outcome_col: str
    age_col: str = "age"
    sex_col: str = "sex_gender"
    broad_threshold: float = 10.0
    pure_threshold: float = 5.0


class GeneralImageryTransformer(BaseEstimator, TransformerMixin):
    """Train-fold standardize modality columns, then average them to one score."""

    def fit(self, X, y=None):
        X = np.asarray(X, dtype=float)
        self.mean_ = np.nanmean(X, axis=0)
        self.scale_ = np.nanstd(X, axis=0, ddof=0)
        self.scale_[~np.isfinite(self.scale_) | (self.scale_ <= 0)] = 1.0
        return self

    def transform(self, X):
        X = np.asarray(X, dtype=float)
        z = (X - self.mean_) / self.scale_
        return np.nanmean(z, axis=1, keepdims=True)


def find_one(root: Path, name: str) -> Path:
    hits = list(root.rglob(name))
    if len(hits) != 1:
        raise RuntimeError(f"Expected exactly one {name} under {root}, found {len(hits)}: {hits[:5]}")
    return hits[0]


def load_new_from_fetch(data_root: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    members = {1: "Exp1.1003.txt", 2: "Exp3.1020.txt"}
    out = []
    flow = {}
    for study, filename in members.items():
        path = find_one(data_root, filename)
        src = pd.read_csv(path, sep="\t", dtype="string", keep_default_na=False, encoding="cp1252")
        numeric = ["nbact", "age", "diag", *P1_MODALITIES] + (["isneurodev"] if study == 2 else [])
        for col in numeric:
            if col not in src:
                raise RuntimeError(f"Study {study} missing {col}")
            src[col] = pd.to_numeric(src[col], errors="coerce")
        kept = src.loc[src["nbact"].ge(3)].copy()
        expected = 949 if study == 1 else 1003
        if len(kept) != expected:
            raise RuntimeError(f"Study {study} retained {len(kept)} rows; expected {expected}")
        frame = kept[[*P1_MODALITIES, "age", "sex", "diag"] + (["isneurodev"] if study == 2 else [])].copy()
        frame = frame.rename(columns={"sex": "sex_gender", "diag": "treatment", "isneurodev": "ndd"})
        frame["study_id"] = study
        out.append(frame)
        flow[f"study_{study}"] = {
            "n": int(len(frame)),
            "treatment_yes": int(frame["treatment"].eq(1).sum()),
            **({"ndd_yes": int(frame["ndd"].eq(1).sum())} if study == 2 else {}),
        }
    return pd.concat(out, ignore_index=True), flow


def prepare_spec_frame(spec: OutcomeSpec) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    cols = [spec.outcome_col, spec.age_col, spec.sex_col, *spec.modality_cols]
    df = spec.frame[cols].copy()
    for col in [spec.outcome_col, spec.age_col, *spec.modality_cols]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df[spec.sex_col] = df[spec.sex_col].astype("string").replace("", pd.NA)
    # Hold the comparison cohort fixed across representations.
    df = df.dropna(subset=cols).reset_index(drop=True)
    y = df[spec.outcome_col].astype(int)
    if set(y.unique()) != {0, 1}:
        raise RuntimeError(f"{spec.cohort}/{spec.outcome}: outcome is not binary 0/1")
    visual = df[spec.visual_col].astype(float)
    df["visual_aphantasia_broad"] = (visual <= spec.broad_threshold).astype(float)
    df["visual_aphantasia_pure"] = (visual == spec.pure_threshold).astype(float)
    return df, {
        "covariates_only": [],
        "visual_binary_broad": ["visual_aphantasia_broad"],
        "visual_binary_pure": ["visual_aphantasia_pure"],
        "visual_continuous": [spec.visual_col],
        "general_imagery": list(spec.modality_cols),
        "multidimensional": list(spec.modality_cols),
    }


def build_pipeline(spec: OutcomeSpec, representation: str, feature_cols: list[str]) -> Pipeline:
    transformers = [
        ("age", Pipeline([("scale", StandardScaler())]), [spec.age_col]),
        ("sex", OneHotEncoder(handle_unknown="ignore", drop="first", sparse_output=False), [spec.sex_col]),
    ]
    if representation in {"visual_binary_broad", "visual_binary_pure"}:
        transformers.append(("imagery", "passthrough", feature_cols))
    elif representation == "visual_continuous":
        transformers.append(("imagery", Pipeline([("scale", StandardScaler())]), feature_cols))
    elif representation == "general_imagery":
        transformers.append(("imagery", Pipeline([("general", GeneralImageryTransformer()), ("scale", StandardScaler())]), feature_cols))
    elif representation == "multidimensional":
        transformers.append(("imagery", Pipeline([("scale", StandardScaler())]), feature_cols))
    elif representation != "covariates_only":
        raise ValueError(representation)

    preprocess = ColumnTransformer(transformers=transformers, remainder="drop", sparse_threshold=0)
    model = LogisticRegression(penalty="l2", solver="lbfgs", max_iter=5000, class_weight=None)
    return Pipeline([("pre", preprocess), ("model", model)])


def metric_dict(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    return {
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "brier": float(brier_score_loss(y, p)),
        "auc": float(roc_auc_score(y, p)),
    }


def stratified_bootstrap_delta(
    y: np.ndarray, p_new: np.ndarray, p_ref: np.ndarray, *, seed: int, reps: int = 4000
) -> dict[str, Any]:
    """Person-level stratified bootstrap; positive deltas favor the new representation."""
    rng = np.random.default_rng(seed)
    pos = np.flatnonzero(y == 1)
    neg = np.flatnonzero(y == 0)
    observed_new = metric_dict(y, p_new)
    observed_ref = metric_dict(y, p_ref)
    observed = {
        "log_loss_improvement": observed_ref["log_loss"] - observed_new["log_loss"],
        "brier_improvement": observed_ref["brier"] - observed_new["brier"],
        "auc_improvement": observed_new["auc"] - observed_ref["auc"],
    }
    draws = {key: np.empty(reps, dtype=float) for key in observed}
    for b in range(reps):
        idx = np.concatenate([
            rng.choice(pos, size=len(pos), replace=True),
            rng.choice(neg, size=len(neg), replace=True),
        ])
        yy = y[idx]
        mn = metric_dict(yy, p_new[idx])
        mr = metric_dict(yy, p_ref[idx])
        draws["log_loss_improvement"][b] = mr["log_loss"] - mn["log_loss"]
        draws["brier_improvement"][b] = mr["brier"] - mn["brier"]
        draws["auc_improvement"][b] = mn["auc"] - mr["auc"]
    return {
        key: {
            "estimate": float(observed[key]),
            "ci95": [float(np.quantile(draws[key], 0.025)), float(np.quantile(draws[key], 0.975))],
            "bootstrap_prob_gt_0": float(np.mean(draws[key] > 0)),
        }
        for key in observed
    }


def repeated_nested_cv(spec: OutcomeSpec, outer_repeats: int = 20, outer_folds: int = 5) -> dict[str, Any]:
    df, feature_sets = prepare_spec_frame(spec)
    y = df[spec.outcome_col].astype(int).to_numpy()
    n = len(df)
    if y.sum() < outer_folds or (n - y.sum()) < outer_folds:
        raise RuntimeError(f"Too few events/non-events for {outer_folds}-fold CV")

    outer = RepeatedStratifiedKFold(n_splits=outer_folds, n_repeats=outer_repeats, random_state=SEED)
    split_list = list(outer.split(np.zeros(n), y))
    predictions = {name: np.zeros((outer_repeats, n), dtype=float) for name in feature_sets}
    seen = {name: np.zeros((outer_repeats, n), dtype=bool) for name in feature_sets}
    chosen_cs = {name: [] for name in feature_sets}

    for split_idx, (train_idx, test_idx) in enumerate(split_list):
        repeat_idx = split_idx // outer_folds
        y_train = y[train_idx]
        min_class = int(min(y_train.sum(), len(y_train) - y_train.sum()))
        inner_splits = min(4, max(2, min_class))
        inner = StratifiedKFold(n_splits=inner_splits, shuffle=True, random_state=SEED + split_idx + 1)
        for name, feature_cols in feature_sets.items():
            grid = GridSearchCV(
                build_pipeline(spec, name, feature_cols),
                param_grid={"model__C": C_GRID},
                scoring="neg_log_loss",
                cv=inner,
                n_jobs=-1,
                refit=True,
                error_score="raise",
            )
            grid.fit(df.iloc[train_idx], y_train)
            prob = grid.predict_proba(df.iloc[test_idx])[:, 1]
            predictions[name][repeat_idx, test_idx] = prob
            seen[name][repeat_idx, test_idx] = True
            chosen_cs[name].append(float(grid.best_params_["model__C"]))

    for name in feature_sets:
        if not seen[name].all():
            raise RuntimeError(f"Incomplete OOF coverage for {name}")

    avg_pred = {name: arr.mean(axis=0) for name, arr in predictions.items()}
    metrics = {name: metric_dict(y, p) for name, p in avg_pred.items()}
    pairs = [
        ("visual_continuous", "visual_binary_broad"),
        ("general_imagery", "visual_continuous"),
        ("multidimensional", "visual_continuous"),
        ("multidimensional", "general_imagery"),
        ("visual_continuous", "covariates_only"),
        ("general_imagery", "covariates_only"),
        ("multidimensional", "covariates_only"),
    ]
    comparisons = {
        f"{better}_vs_{reference}": stratified_bootstrap_delta(
            y, avg_pred[better], avg_pred[reference], seed=SEED + i * 97
        )
        for i, (better, reference) in enumerate(pairs)
    }
    return {
        "project": spec.project,
        "cohort": spec.cohort,
        "outcome": spec.outcome,
        "n": int(n),
        "events": int(y.sum()),
        "event_rate": float(y.mean()),
        "modalities": spec.modality_cols,
        "outer_cv": {"folds": outer_folds, "repeats": outer_repeats, "seed": SEED},
        "inner_C_grid": C_GRID,
        "metrics": metrics,
        "comparisons": comparisons,
        "chosen_C_summary": {
            name: {"median": float(np.median(vals)), "min": float(np.min(vals)), "max": float(np.max(vals))}
            for name, vals in chosen_cs.items()
        },
        "privacy": "Only aggregate metrics are returned; OOF participant probabilities are not persisted.",
    }


def render_markdown(results: list[dict[str, Any]]) -> str:
    lines = [
        "# Cross-validated imagery-representation comparison",
        "",
        "Exploratory/post-hoc analysis. All models include age and recorded sex/gender. "
        "Primary metric is OOF log loss; AUC and Brier are secondary. Nested CV tunes only L2 strength. "
        "Paired uncertainty uses a person-level stratified bootstrap.",
        "",
    ]
    order = [
        "covariates_only", "visual_binary_broad", "visual_binary_pure", "visual_continuous",
        "general_imagery", "multidimensional",
    ]
    for r in results:
        lines += [
            f"## {r['project']} — {r['cohort']} / {r['outcome']}", "",
            f"N={r['n']}, events={r['events']} ({r['event_rate']:.1%}).", "",
            "| Representation | Log loss ↓ | Brier ↓ | AUC ↑ |",
            "|---|---:|---:|---:|",
        ]
        for name in order:
            m = r["metrics"][name]
            lines.append(f"| {name} | {m['log_loss']:.5f} | {m['brier']:.5f} | {m['auc']:.4f} |")
        lines += [
            "", "### Paired representation gains", "",
            "Positive values favor the first-named representation.", "",
            "| Comparison | Δ log loss | 95% CI | Δ AUC | 95% CI |",
            "|---|---:|---:|---:|---:|",
        ]
        for name, d in r["comparisons"].items():
            ll = d["log_loss_improvement"]
            auc = d["auc_improvement"]
            lines.append(
                f"| {name} | {ll['estimate']:.5f} | [{ll['ci95'][0]:.5f}, {ll['ci95'][1]:.5f}] | "
                f"{auc['estimate']:.4f} | [{auc['ci95'][0]:.4f}, {auc['ci95'][1]:.4f}] |"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("representation_cv_results"))
    ap.add_argument("--outer-repeats", type=int, default=20)
    args = ap.parse_args()

    new_frame, new_flow = load_new_from_fetch(args.data_root)
    arnold_zip = find_one(args.data_root, "Autism_Aphantasia_Analyses_code.zip")
    arnold_group, _, _, arnold_flow = load_arnold_code(arnold_zip)

    specs = []
    for study in (1, 2):
        sf = new_frame.loc[new_frame["study_id"].eq(study)].copy()
        specs.append(OutcomeSpec("P1", f"new_study_{study}", "current_treatment", sf, P1_MODALITIES, "image", "treatment"))
    sf2 = new_frame.loc[new_frame["study_id"].eq(2)].copy()
    specs.append(OutcomeSpec("P1", "new_study_2", "broad_diagnosed_or_suspected_NDD", sf2, P1_MODALITIES, "image", "ndd"))
    specs.append(OutcomeSpec("P3", "arnold_formal_dx_vs_comparison", "autism_group", arnold_group, P3_MODALITIES, "visual", "diagnosis_group"))

    results = []
    for spec in specs:
        print(f"Running {spec.project} {spec.cohort} {spec.outcome}", flush=True)
        results.append(repeated_nested_cv(spec, outer_repeats=args.outer_repeats))

    args.output.mkdir(parents=True, exist_ok=True)
    payload = {
        "analysis": "visual binary vs visual continuous vs general vs multidimensional imagery prediction",
        "status": "exploratory_post_hoc",
        "source_flow": {"new": new_flow, "arnold": arnold_flow},
        "results": results,
    }
    (args.output / "representation_cv.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "representation_cv.md").write_text(render_markdown(results), encoding="utf-8")
    print((args.output / "representation_cv.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
