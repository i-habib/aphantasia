"""P7: fusiform imagery node (FIN)–frontoparietal connectivity in ABIDE I.

Plan: ``projects/P7_fin_connectivity_abide/protocol/preregistration.md``.
``map_nodes`` uses only the atlas image and may run before registration.
``run_p7`` computes group comparisons and is gated by the frozen plan and a
registration URL (``verify_registration``). Outputs are aggregate only.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm, t

from .models import ESTIMATE_COLUMNS, AnalysisStop, _matrix, _ols_cluster_state, _ols_hc3, _rows, _write
from .nifti import read_nifti, voxel_to_world, world_to_voxel
from .p5 import Registration, _json_safe

PLAN_PATH = Path("projects/P7_fin_connectivity_abide/protocol/preregistration.md")
DATA = Path("projects/P7_fin_connectivity_abide/data_raw/abide")

# Spagna et al. (2021), visual imagery > control ALE peaks (MNI); plan §4.2.
NODES = {
    "fin_left": (-42, -54, -18),
    "left_ipl_ips": (-40, -44, 46),
    "left_pmd_mfg": (-26, -2, 60),
    "left_ifj_mfg": (-52, 10, 38),
    "fin_right_homologue": (42, -54, -18),
    "right_ipl": (40, -42, 48),
    "right_pmd_mfg": (30, -4, 54),
}
LEFT_TARGETS = ["left_ipl_ips", "left_pmd_mfg", "left_ifj_mfg"]
RIGHT_TARGETS = ["right_ipl", "right_pmd_mfg"]
NEAREST_LIMIT_MM = 6.0
LOCAL_EXCLUSION_MM = 20.0
FD_MAX = 0.2
MIN_PER_GROUP_PER_SITE = 5
EQUIVALENCE_BOUND_SD = 0.15
FUNCTIONAL_QC = ["qc_rater_1", "qc_func_rater_2", "qc_func_rater_3"]


# ---------------------------------------------------------------- atlas only
def map_nodes(atlas_path: Path, nodes: dict[str, tuple[float, float, float]] = NODES) -> dict[str, Any]:
    """Assign each MNI coordinate to the atlas parcel containing it (nearest within 6 mm otherwise)."""
    volume, affine = read_nifti(atlas_path)
    labels = np.rint(volume).astype(int)
    labelled = np.argwhere(labels > 0)
    labelled_xyz = voxel_to_world(affine, labelled)
    mapping: dict[str, Any] = {}
    for name, xyz in nodes.items():
        ijk = np.rint(world_to_voxel(affine, xyz)[0]).astype(int)
        inside = np.all((ijk >= 0) & (ijk < labels.shape))
        label = int(labels[tuple(ijk)]) if inside else 0
        distance = 0.0
        if label == 0:
            distances = np.linalg.norm(labelled_xyz - np.asarray(xyz, dtype=float), axis=1)
            nearest = int(np.argmin(distances))
            distance = float(distances[nearest])
            if distance > NEAREST_LIMIT_MM:
                raise AnalysisStop("blocked", "node_outside_atlas", f"{name} is {distance:.1f} mm from the nearest parcel (> {NEAREST_LIMIT_MM} mm).")
            label = int(labels[tuple(labelled[nearest])])
        mapping[name] = {"mni": list(xyz), "parcel": label, "distance_mm": round(distance, 2)}
    parcels = [entry["parcel"] for entry in mapping.values()]
    if len(set(parcels)) != len(parcels):
        raise AnalysisStop("blocked", "nodes_share_parcel", "Two prespecified nodes fall in the same parcel.", mapping)
    centroids = {int(label): voxel_to_world(affine, np.argwhere(labels == label)).mean(axis=0).round(2).tolist()
                 for label in np.unique(labels) if label > 0}
    return {"atlas": atlas_path.name, "nodes": mapping, "parcel_centroids_mni": centroids}


# ---------------------------------------------------------------- per-person edges
def read_timeseries(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep="\t")
    frame.columns = [int(str(column).lstrip("#")) for column in frame.columns]
    return frame


def person_edges(series: pd.DataFrame, node_map: dict[str, Any]) -> dict[str, float] | None:
    """Fisher-z edges for one participant; None when a node parcel has no signal (plan §3.2 step 4)."""
    nodes = node_map["nodes"]
    centroids = {int(k): np.asarray(v) for k, v in node_map["parcel_centroids_mni"].items()}
    needed = [entry["parcel"] for entry in nodes.values()]
    if any(label not in series.columns for label in needed):
        return None
    values = series.to_numpy(dtype=float)
    sd = values.std(axis=0)
    column = {label: index for index, label in enumerate(series.columns)}
    if any(not np.isfinite(sd[column[label]]) or sd[column[label]] == 0 for label in needed):
        return None
    valid = np.isfinite(sd) & (sd > 0)
    standardized = np.where(valid, (values - values.mean(axis=0)) / np.where(valid, sd, 1), 0.0)
    correlations = standardized.T @ standardized / len(values)
    z = np.arctanh(np.clip(correlations, -0.999999, 0.999999))

    def edge(a: str, b: str) -> float:
        return float(z[column[nodes[a]["parcel"]], column[nodes[b]["parcel"]]])

    fin = column[nodes["fin_left"]["parcel"]]
    fin_centroid = centroids[nodes["fin_left"]["parcel"]]
    excluded = {nodes[name]["parcel"] for name in ["fin_left", *LEFT_TARGETS]}
    others = [column[label] for label in series.columns
              if label not in excluded and valid[column[label]] and label in centroids
              and np.linalg.norm(centroids[label] - fin_centroid) > LOCAL_EXCLUSION_MM]
    left = {name: edge("fin_left", name) for name in LEFT_TARGETS}
    right = {name: edge("fin_right_homologue", name) for name in RIGHT_TARGETS}
    left_mean = float(np.mean(list(left.values())))
    fin_other = float(np.mean(z[fin, others]))
    return {**{f"edge_{k}": v for k, v in left.items()}, **{f"edge_right_{k}": v for k, v in right.items()},
            "primary_left_mean": left_mean, "fin_other_mean": fin_other,
            "specificity": left_mean - fin_other,
            "lateralisation": left_mean - float(np.mean(list(right.values())))}


# ---------------------------------------------------------------- sample flow
def apply_exclusions(phenotype: pd.DataFrame, has_file: pd.Series, *, fd_max: float | None = FD_MAX) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Plan §3.2 steps 1–3 and 5 (step 4 needs time series; step 6 runs after edges)."""
    frame = phenotype.copy()
    flow = [{"step": "phenotype rows", "n": int(len(frame))}]
    frame = frame.loc[(frame["FILE_ID"] != "no_filename") & has_file.reindex(frame.index, fill_value=False)]
    flow.append({"step": "1 time-series file present", "n": int(len(frame))})
    if fd_max is not None:
        frame = frame.loc[pd.to_numeric(frame["func_mean_fd"], errors="coerce") <= fd_max]
        flow.append({"step": f"2 mean FD <= {fd_max}", "n": int(len(frame))})
    failed = np.zeros(len(frame), dtype=bool)
    for column in FUNCTIONAL_QC:
        if column in frame:
            failed |= frame[column].astype(str).str.strip().str.lower().eq("fail").to_numpy()
    frame = frame.loc[~failed]
    flow.append({"step": "3 no functional QC fail", "n": int(len(frame))})
    return frame, flow


def _covariates(frame: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=frame.index)
    out["autism"] = (pd.to_numeric(frame["DX_GROUP"]) == 1).astype(float)
    out["age"] = pd.to_numeric(frame["AGE_AT_SCAN"], errors="coerce")
    out["age_sq"] = (out["age"] - out["age"].mean()) ** 2
    out["fd"] = pd.to_numeric(frame["func_mean_fd"], errors="coerce")
    out["sex"] = frame["SEX"].astype("string")
    out["eyes"] = frame["EYE_STATUS_AT_SCAN"].astype("string")
    out["site"] = frame["SITE_ID"].astype("string")
    out["fiq"] = pd.to_numeric(frame.get("FIQ"), errors="coerce").where(lambda v: v > 0)
    for column in ("ADOS_TOTAL", "SRS_RAW_TOTAL", "AQ_TOTAL"):
        if column in frame:
            out[column] = pd.to_numeric(frame[column], errors="coerce").where(lambda v: v >= 0)
    return out


def _balanced_sites(frame: pd.DataFrame) -> pd.DataFrame:
    counts = frame.groupby(["site", "autism"]).size().unstack(fill_value=0)
    keep = counts.index[(counts.min(axis=1) >= MIN_PER_GROUP_PER_SITE) & (counts.shape[1] == 2)]
    return frame.loc[frame["site"].isin(keep)]


# ---------------------------------------------------------------- models
def _fit(frame: pd.DataFrame, outcome: str, *, model: str, extra_numeric: list[str] | None = None,
         categorical: list[str] | None = None, cluster: str | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    numeric = ["autism", "age", "age_sq", "fd", *(extra_numeric or [])]
    categorical = ["sex", "eyes", "site"] if categorical is None else categorical
    categorical = [c for c in categorical if frame[c].nunique() > 1]
    use = frame[[outcome, *numeric, *categorical, *([cluster] if cluster else [])]].dropna()
    if cluster:
        use_frame, x, names, beta, cov, diag = _ols_cluster_state(use, cluster=cluster, numeric=numeric,
                                                                 categorical=[c for c in categorical if c != cluster], y_name=outcome)
        df = len(use_frame) - len(names)
    else:
        x, names = _matrix(use, numeric, categorical)
        beta, cov, diag = _ols_hc3(use[outcome].to_numpy(dtype=float), x)
        df = len(use) - x.shape[1]
    rows = _rows(beta, cov, names, project="P7", model=model, cohort="abide_i", outcome=outcome,
                 effect_kind="mean_difference_fisher_z", n=len(use), p_df=df)
    rows = [row for row in rows if row["term"] in {"autism", "autism_x_age"}]
    index = names.index("autism")
    estimate, se = float(beta[index]), math.sqrt(float(cov[index, index]))
    groups = use.groupby("autism")[outcome]
    pooled_sd = math.sqrt(((groups.count() - 1) * groups.var(ddof=1)).sum() / (groups.count().sum() - 2))
    summary = {"estimate": estimate, "se": se, "ci95": [estimate - t.ppf(0.975, df) * se, estimate + t.ppf(0.975, df) * se],
               "p_two_sided": float(2 * t.sf(abs(estimate / se), df)), "df": int(df),
               "standardized": estimate / pooled_sd, "pooled_sd": pooled_sd,
               "n_autism": int((use["autism"] == 1).sum()), "n_control": int((use["autism"] == 0).sum()),
               "sites": int(use["site"].nunique()), **{k: v for k, v in diag.items() if k in {"covariance", "clusters"}}}
    if "autism_x_age" in names:
        i = names.index("autism_x_age")
        summary["autism_x_age"] = {"estimate": float(beta[i]), "se": math.sqrt(float(cov[i, i]))}
    return rows, summary


def _tost(summary: dict[str, Any], bound_sd: float = EQUIVALENCE_BOUND_SD) -> dict[str, Any]:
    bound = bound_sd * summary["pooled_sd"]
    lower = float(t.sf((summary["estimate"] + bound) / summary["se"], summary["df"]))
    upper = float(t.cdf((summary["estimate"] - bound) / summary["se"], summary["df"]))
    return {"bound_sd": bound_sd, "bound_raw": bound, "p_lower": lower, "p_upper": upper,
            "equivalent_at_05": max(lower, upper) < 0.05}


def _holm(pvalues: dict[str, float]) -> dict[str, float]:
    running, adjusted = 0.0, {}
    for rank, key in enumerate(sorted(pvalues, key=pvalues.get)):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[key]))
        adjusted[key] = running
    return adjusted


def build_analysis_frame(phenotype: pd.DataFrame, series_dir: Path, node_map: dict[str, Any], *,
                         fd_max: float | None = FD_MAX) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    files = {path.name.replace(f"_{series_dir.name}.1D", ""): path for path in series_dir.glob("*.1D")}
    has_file = phenotype["FILE_ID"].isin(files)
    frame, flow = apply_exclusions(phenotype, has_file, fd_max=fd_max)
    edges = {}
    for index, file_id in frame["FILE_ID"].items():
        result = person_edges(read_timeseries(files[file_id]), node_map)
        if result is not None:
            edges[index] = result
    frame = frame.loc[list(edges)]
    flow.append({"step": "4 signal in all node parcels", "n": int(len(frame))})
    analysis = pd.concat([_covariates(frame), pd.DataFrame.from_dict(edges, orient="index")], axis=1)
    analysis = analysis.dropna(subset=["age", "sex", "eyes"])
    flow.append({"step": "5 age, sex, eye status present", "n": int(len(analysis))})
    analysis = _balanced_sites(analysis)
    flow.append({"step": f"6 sites with >= {MIN_PER_GROUP_PER_SITE} per group", "n": int(len(analysis))})
    return analysis, flow


def run_p7(root: Path, output_dir: Path, *, registration: Registration) -> dict[str, Any]:
    """Run every registered P7 analysis once (plan §6)."""
    if not isinstance(registration, Registration):
        raise AnalysisStop("blocked", "awaiting_preregistration", "run_p7 requires a verified Registration.")
    data = root / DATA
    phenotype = pd.read_csv(data / "Phenotypic_V1_0b_preprocessed1.csv")
    maps = {atlas: map_nodes(data / "atlases" / f"{atlas.upper()}.nii.gz") for atlas in ("cc400", "cc200")}
    primary_dir = data / "cpac" / "filt_noglobal" / "rois_cc400"
    frame, flow = build_analysis_frame(phenotype, primary_dir, maps["cc400"])
    return analyse(frame, flow, output_dir, registration=registration, extra_sets=_sensitivity_sets(phenotype, data, maps), node_map=maps["cc400"])


def _sensitivity_sets(phenotype: pd.DataFrame, data: Path, maps: dict[str, Any]) -> dict[str, pd.DataFrame]:
    sets = {}
    specs = [("SENS_gsr", "filt_global", "rois_cc400", FD_MAX), ("SENS_fd_0.1", "filt_noglobal", "rois_cc400", 0.1),
             ("SENS_no_fd_exclusion", "filt_noglobal", "rois_cc400", None), ("SENS_cc200", "filt_noglobal", "rois_cc200", FD_MAX)]
    for label, strategy, derivative, fd in specs:
        folder = data / "cpac" / strategy / derivative
        if folder.exists() and any(folder.glob("*.1D")):
            sets[label], _ = build_analysis_frame(phenotype, folder, maps[derivative.split("_")[1]], fd_max=fd)
    return sets


def analyse(frame: pd.DataFrame, flow: list[dict[str, Any]], output_dir: Path, *, registration: Registration,
            extra_sets: dict[str, pd.DataFrame] | None = None, node_map: dict[str, Any] | None = None) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    details: dict[str, Any] = {"flow": flow}

    primary_rows, primary = _fit(frame, "primary_left_mean", model="H1_fin_left_frontoparietal")
    rows += primary_rows
    primary["equivalence"] = _tost(primary)
    details["H1"] = primary

    secondary = {}
    for label, outcome in [("H2_specificity", "specificity"), *[(f"edge_{n}", f"edge_{n}") for n in LEFT_TARGETS],
                           ("lateralisation", "lateralisation")]:
        fitted_rows, secondary[label] = _fit(frame, outcome, model=label)
        rows += fitted_rows
    details["secondary"] = secondary
    details["secondary_holm"] = _holm({k: v["p_two_sided"] for k, v in secondary.items()})

    adults = frame.loc[frame["age"] >= 18]
    reported = {}
    if adults["autism"].nunique() == 2 and len(adults) > 30:
        adult_rows, reported["adults_only"] = _fit(_balanced_sites(adults), "primary_left_mean", model="adults_only")
        rows += adult_rows
    interaction = frame.assign(autism_x_age=frame["autism"] * (frame["age"] - frame["age"].mean()))
    age_rows, reported["age_interaction"] = _fit(interaction, "primary_left_mean", model="age_interaction", extra_numeric=["autism_x_age"])
    rows += age_rows
    details["reported_not_in_holm"] = reported

    sensitivity = {}
    for label, subset in (extra_sets or {}).items():
        fitted_rows, sensitivity[label] = _fit(subset, "primary_left_mean", model=label)
        rows += fitted_rows
    fitted_rows, sensitivity["SENS_iq_adjusted"] = _fit(frame, "primary_left_mean", model="SENS_iq_adjusted", extra_numeric=["fiq"])
    rows += fitted_rows
    males = frame.loc[frame["sex"].astype(str) == "1"]
    fitted_rows, sensitivity["SENS_males_only"] = _fit(_balanced_sites(males), "primary_left_mean", model="SENS_males_only")
    rows += fitted_rows
    fitted_rows, sensitivity["SENS_site_clustered"] = _fit(frame, "primary_left_mean", model="SENS_site_clustered",
                                                            categorical=["sex", "eyes"], cluster="site")
    rows += fitted_rows
    loso = [_fit(frame.loc[frame["site"] != site], "primary_left_mean", model="loso")[1]["estimate"] for site in sorted(frame["site"].unique())]
    sensitivity["SENS_leave_one_site_out"] = {"min": float(min(loso)), "max": float(max(loso)), "n_refits": len(loso)}
    details["sensitivity"] = sensitivity

    exploratory = {}
    autistic = frame.loc[frame["autism"] == 1]
    for column in ("ADOS_TOTAL", "SRS_RAW_TOTAL", "AQ_TOTAL"):
        subset = autistic.dropna(subset=[column]) if column in autistic else autistic.iloc[0:0]
        if len(subset) >= 30:
            x, names = _matrix(subset, [column, "age", "fd"], [c for c in ["sex", "site"] if subset[c].nunique() > 1])
            beta, cov, _ = _ols_hc3(subset["primary_left_mean"].to_numpy(dtype=float), x)
            i = names.index(column)
            exploratory[column] = {"slope": float(beta[i]), "se": math.sqrt(float(cov[i, i])), "n": int(len(subset))}
    details["exploratory_symptom_slopes_autistic_only"] = exploratory

    h1, h2 = details["H1"], secondary["H2_specificity"]
    excludes_zero = lambda s: s["ci95"][1] < 0 or s["ci95"][0] > 0  # noqa: E731
    if h1["ci95"][1] < 0 and h2["ci95"][1] < 0:
        verdict = "reduced_and_specific"
    elif h1["ci95"][1] < 0:
        verdict = "reduced_not_specific"
    elif h1["ci95"][0] > 0:
        verdict = "increased"
    else:
        verdict = "equivalent_to_null" if h1["equivalence"]["equivalent_at_05"] else "inconclusive"
    details["interpretation"] = verdict
    details["any_secondary_ci_excludes_zero"] = {k: excludes_zero(v) for k, v in secondary.items()}
    if node_map is not None:
        details["node_map"] = node_map["nodes"]

    estimates = pd.DataFrame(rows, columns=ESTIMATE_COLUMNS)
    diagnostics = {"project": "P7", "status": "complete", "contains_participant_rows": False,
                   "registration": {"url": registration.url, "plan_sha256": registration.plan_sha256},
                   "sample_sizes": {"autism": primary["n_autism"], "control": primary["n_control"], "sites": primary["sites"]},
                   "details": details, "estimate_rows": int(len(estimates))}
    return _write("P7", estimates, _json_safe(diagnostics), output_dir)


def write_node_map(root: Path) -> Path:
    """Pre-registration step (plan §4.1): atlas-only coordinate→parcel mapping."""
    out = root / "projects/P7_fin_connectivity_abide/results"
    out.mkdir(parents=True, exist_ok=True)
    maps = {atlas: map_nodes(root / DATA / "atlases" / f"{atlas.upper()}.nii.gz") for atlas in ("cc400", "cc200")}
    path = out / "parcel_map.json"
    path.write_text(json.dumps({k: {"atlas": v["atlas"], "nodes": v["nodes"]} for k, v in maps.items()}, indent=2) + "\n", encoding="utf-8")
    return path
