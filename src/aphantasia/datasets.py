"""In-memory loaders and scoring rules for the staged public datasets.

Raw records are read directly from their source archives and are never written
to disk. Callers receive only the analysis columns needed by prespecified
models; identifiers and free text are dropped before modelling.
"""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


NEW_MEMBERS = {
    1: "Analyses/Exp1.1003.txt",
    2: "Analyses/Exp3.1020.txt",
}
NEW_PUBLISHED_N = {1: 949, 2: 1003}
COMMON_NONVISUAL = ["sound", "touch", "motor", "taste", "smell", "emotion", "voice"]
ARNOLD_MODALITIES = ["visual", "auditory", "smell", "taste", "touch", "movement"]


class DatasetError(RuntimeError):
    """Raised when a source file does not satisfy its declared data contract."""


def _numeric(frame: pd.DataFrame, columns: list[str]) -> None:
    for name in columns:
        if name not in frame:
            raise DatasetError(f"Required source field is absent: {name}")
        frame[name] = pd.to_numeric(frame[name], errors="coerce")


def _zscore(values: pd.Series) -> pd.Series:
    mean = float(values.mean())
    sd = float(values.std(ddof=0))
    if not np.isfinite(sd) or sd <= 0:
        raise DatasetError("A required imagery score has zero or invalid variance.")
    return (values - mean) / sd


def load_new_studies(path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read New et al. study tables, reproduce nbact exclusions, and score P1.

    Source field ``diag`` is the binary response to the questionnaire item
    "Are you currently receiving treatment for a neurologic or psychiatric
    condition?" (No/Yes); ``diag2`` is an open response shown only after Yes.
    ``isneurodev`` is the separate diagnosed-or-strongly-suspected NDD
    indicator in Study 2. The wording and branch are recorded in the project
    variable map; ``diag2`` is never loaded into the analysis frame.
    """
    rows: list[pd.DataFrame] = []
    flow: dict[str, Any] = {}
    with zipfile.ZipFile(path) as archive:
        for study, member in NEW_MEMBERS.items():
            with archive.open(member) as stream:
                source = pd.read_csv(stream, sep="\t", dtype="string", keep_default_na=False, encoding="cp1252")
            if "nbact" not in source or "id" not in source:
                raise DatasetError(f"Study {study} is missing its published QC or row key.")
            if source["id"].duplicated().any():
                raise DatasetError(f"Study {study} has duplicate source row keys.")
            raw_n = len(source)
            attention = pd.to_numeric(source["nbact"], errors="coerce")
            retained = source.loc[attention.ge(3)].copy()
            excluded = raw_n - len(retained)
            if len(retained) != NEW_PUBLISHED_N[study]:
                raise DatasetError(
                    f"Study {study} retained N={len(retained)} after nbact >= 3; expected published N={NEW_PUBLISHED_N[study]}."
                )
            modalities = ["image", *COMMON_NONVISUAL]
            _numeric(retained, modalities + ["age", "diag"] + (["isneurodev"] if study == 2 else []))
            for modality in modalities:
                observed = retained[modality].dropna()
                if len(observed) and ((observed < 5).any() or (observed > 35).any()):
                    raise DatasetError(f"Study {study} {modality} score falls outside the declared 5–35 range.")
            treatment_values = set(retained["diag"].dropna().unique())
            if not treatment_values.issubset({0, 1}) or len(treatment_values) != 2:
                raise DatasetError(f"Study {study} diag must contain explicit 0 and 1 values.")

            for modality in modalities:
                retained[f"z_{modality}"] = _zscore(retained[modality])
            nonvisual_component_mean = retained[[f"z_{name}" for name in COMMON_NONVISUAL]].mean(axis=1)
            # Standardize completed composites within study so every reported
            # composite effect is per one composite SD, like visual_z.
            retained["nonvisual_z"] = _zscore(nonvisual_component_mean)
            z_modalities = [f"z_{name}" for name in modalities]
            general_component_mean = retained[z_modalities].mean(axis=1)
            retained["general_z"] = _zscore(general_component_mean)
            # Preserve the source script's visual extreme-phenotype cut points
            # for the exploratory threshold-versus-dose-response comparison.
            image_present = retained["image"].notna()
            retained["visual_aphantasia"] = np.where(image_present, (retained["image"] == 5).astype(float), np.nan)
            retained["visual_hyperphantasia"] = np.where(image_present, (retained["image"] >= 35).astype(float), np.nan)

            # The analyst frame contains no source IDs, open answers, or comments.
            analysis_columns = ["diag", "nonvisual_z", "z_image", "general_z", "visual_aphantasia", "visual_hyperphantasia", "age", "sex"]
            if study == 2:
                analysis_columns.append("isneurodev")
            analysis = retained[analysis_columns].copy()
            analysis = analysis.rename(columns={"diag": "treatment", "z_image": "visual_z", "sex": "sex_gender", "isneurodev": "ndd"})
            analysis.insert(0, "study_id", study)
            rows.append(analysis.reset_index(drop=True))

            ages = pd.to_numeric(retained["age"], errors="coerce")
            flow[f"study_{study}"] = {
                "source_rows": int(raw_n),
                "attention_excluded_nbact_lt_3": int(excluded),
                "published_analysis_n": int(len(retained)),
                "age_missing": int(ages.isna().sum()),
                "age_outside_18_30": int((ages.notna() & ~ages.between(18, 30)).sum()),
                "treatment_yes": int((retained["diag"] == 1).sum()),
                "treatment_no": int((retained["diag"] == 0).sum()),
                "outcome_mapping": {
                    "source_field": "diag",
                    "question": "Are you currently receiving treatment for a neurologic or psychiatric condition?",
                    "response_options": ["No, I am not currently receiving treatment", "Yes, I am currently receiving treatment"],
                    "yes_code_in_export": 1,
                    "no_code_in_export": 0,
                    "follow_up_field": "diag2",
                    "follow_up_branch": "shown only after Yes",
                },
                "nonvisual_composite": list(COMMON_NONVISUAL),
            }
            if study == 2:
                flow[f"study_{study}"]["ndd_yes"] = int((retained["isneurodev"] == 1).sum())
                flow[f"study_{study}"]["ndd_no"] = int((retained["isneurodev"] == 0).sum())
    return pd.concat(rows, ignore_index=True), flow


_MATLAB_BLOCK = re.compile(r"(?ms)^\s*([A-Za-z_]\w*)\s*=\s*\[(.*?)\]\s*;")
_MATLAB_NUMBER = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def _matlab_arrays(text: str) -> dict[str, np.ndarray]:
    arrays: dict[str, np.ndarray] = {}
    for match in _MATLAB_BLOCK.finditer(text):
        lines = []
        for line in match.group(2).splitlines():
            cleaned = line.split("%", 1)[0].replace("...", " ").strip()
            values = _MATLAB_NUMBER.findall(cleaned)
            if values:
                lines.append([float(value) for value in values])
        if lines and len({len(line) for line in lines}) == 1:
            arrays[match.group(1)] = np.asarray(lines, dtype=float)
    return arrays


def load_arnold_code(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Reconstruct aggregate-safe analysis frames from the authors' public code.

    The .m archive embeds response-level imagery and questionnaire scores. They
    are used only in memory; no response-level rows are persisted or printed.
    """
    with zipfile.ZipFile(path) as archive:
        text = archive.read("Autism_Aphantasia_Analyses_code.m").decode("utf-8", errors="replace")
    arrays = _matlab_arrays(text)
    needed = ["Control_PSIQ", "ASD_PSIQ", "AQ_Items", "Subscale_Scores", "ASD_Ages", "ASD_Genders", "CONTROL_AGEs", "CONTROL_Genders"]
    absent = [name for name in needed if name not in arrays]
    if absent:
        raise DatasetError(f"Arnold code archive is missing declared arrays: {', '.join(absent)}")
    control = arrays["Control_PSIQ"]
    diagnosed = arrays["ASD_PSIQ"]
    aq_items = arrays["AQ_Items"]
    subscales = arrays["Subscale_Scores"]
    if control.shape[1] != 6 or diagnosed.shape[1] != 6 or aq_items.shape[1] != 50 or subscales.shape[1] != 11:
        raise DatasetError("Arnold public code arrays do not match the documented column counts.")
    if diagnosed.shape[0] != aq_items.shape[0] or diagnosed.shape[0] != subscales.shape[0]:
        raise DatasetError("Arnold diagnosed-group arrays are not row-aligned.")
    ndd = arrays["ASD_Ages"].size
    ncc = arrays["CONTROL_AGEs"].size
    if ndd != diagnosed.shape[0] or ncc != control.shape[0]:
        raise DatasetError("Arnold age arrays do not align with the imagery arrays.")
    threshold_match = re.search(r"(?m)^\s*Consistent_Threshold\s*=\s*(\d+);", text)
    aq_threshold = int(threshold_match.group(1)) if threshold_match else 26
    aq_total = aq_items.sum(axis=1)
    selected = aq_total >= aq_threshold
    source_idx = np.flatnonzero(selected)
    control_frame = pd.DataFrame(control, columns=ARNOLD_MODALITIES)
    control_frame["age"] = arrays["CONTROL_AGEs"].reshape(-1)
    control_frame["sex_gender"] = arrays["CONTROL_Genders"].reshape(-1).astype(int).astype(str)
    control_frame["diagnosis_group"] = 0
    asd_full = pd.DataFrame(diagnosed, columns=ARNOLD_MODALITIES)
    asd_full["age"] = arrays["ASD_Ages"].reshape(-1)
    asd_full["sex_gender"] = arrays["ASD_Genders"].reshape(-1).astype(int).astype(str)
    asd_full["diagnosis_group"] = 1
    group_frame = pd.concat([control_frame.copy(), asd_full.copy()], ignore_index=True)
    code_control = control_frame.copy()
    code_control["analysis_set"] = "author_code_AQ_threshold"
    code_asd = asd_full.iloc[source_idx].copy()
    code_asd["analysis_set"] = "author_code_AQ_threshold"
    author_code_frame = pd.concat([code_control, code_asd], ignore_index=True)

    trait_frame = pd.DataFrame(diagnosed, columns=ARNOLD_MODALITIES)
    trait_frame["age"] = arrays["ASD_Ages"].reshape(-1)
    trait_frame["sex_gender"] = arrays["ASD_Genders"].reshape(-1).astype(int).astype(str)
    trait_frame["AQ_total"] = aq_total
    # The first AQ summary column is the imagination subscale; this secondary
    # score sums the remaining four AQ domains to reduce item-content overlap.
    trait_frame["AQ_nonimagination"] = subscales[:, 1:5].sum(axis=1)
    trait_frame["CATI_total"] = subscales[:, 5:11].sum(axis=1)
    diagnostics = {
        "control_n": int(len(control_frame)),
        "diagnosed_source_n": int(len(diagnosed)),
        "diagnosed_selected_by_code_AQ_threshold": int(len(source_idx)),
        "AQ_consistent_threshold": int(aq_threshold),
        "modality_order": list(ARNOLD_MODALITIES),
        "source_code_reproduces_6_modality_case_control_and_trait_models": True,
        "controls_have_AQ_or_CATI": False,
    }
    return group_frame, author_code_frame, trait_frame, diagnostics


def audit_mawtus_feasibility(path: Path) -> dict[str, Any]:
    """Aggregate-only P4 linkage audit; never inspect interview documents."""
    member = "Stage2/Quantitative_Results/data/Aug29data_neat_NOemails_noambig.csv"
    with zipfile.ZipFile(path) as archive, archive.open(member) as stream:
        frame = pd.read_csv(stream, dtype="string", keep_default_na=False, encoding="utf-8")
    modality_columns = {
        "visual": ("psiq_visual", "therapy_involved_visual_imagery_yn"),
        "emotion": ("psiq_emotion", "therapy_involved_emotion_imagery_yn"),
        "auditory": ("psiq_auditory", "therapy_involved_auditory_imagery_yn"),
        "touch": ("psiq_touch", "therapy_involved_touch_imagery_yn"),
        "body": ("psiq_body", "therapy_involved_body_imagery_yn"),
        "other": (None, "therapy_involved_other_imagery_yn"),
    }
    outcomes = ["mh_treatment_effective_yn", "treatment_helped_yn"]
    result: dict[str, Any] = {"rows": int(len(frame)), "columns": int(len(frame.columns)), "outcomes": {}, "modalities": {}}
    for outcome in outcomes:
        if outcome in frame:
            clean = frame[outcome].astype(str).str.strip()
            result["outcomes"][outcome] = {"answered": int(clean.ne("").sum()), "levels": int(clean[clean.ne("")].nunique())}
    paired_total = 0
    for modality, (score, therapy) in modality_columns.items():
        variables = [therapy, "mh_treatment_effective_yn"] + ([score] if score else [])
        sub = frame[variables].copy()
        for field in variables:
            sub[field] = sub[field].astype(str).str.strip().replace("", np.nan)
        paired = sub.dropna(subset=[therapy, "mh_treatment_effective_yn"])
        explicit_binary = False
        cell_counts: dict[str, int | str] = {}
        therapy_values = set(paired[therapy].astype(str).str.casefold()) if len(paired) else set()
        if therapy_values and therapy_values.issubset({"yes", "no"}):
            explicit_binary = True
            tab = pd.crosstab(paired[therapy], paired["mh_treatment_effective_yn"])
            cell_counts = {f"therapy_level_{left_index}|outcome_level_{right_index}": (int(value) if int(value) >= 5 else "<5")
                           for left_index, (_, row) in enumerate(tab.iterrows(), start=1)
                           for right_index, value in enumerate(row, start=1)}
        paired_total = max(paired_total, len(paired))
        score_answered = int(sub[score].notna().sum()) if score else None
        selected_outcome_counts = {}
        if len(paired) and not explicit_binary:
            outcome_counts = paired["mh_treatment_effective_yn"].value_counts()
            selected_outcome_counts = {f"outcome_level_{index}": (int(value) if int(value) >= 5 else "<5")
                                       for index, value in enumerate(outcome_counts.tolist(), start=1)}
        result["modalities"][modality] = {
            "score_field": score,
            "therapy_field": therapy,
            "score_answered": score_answered,
            "therapy_field_nonblank": int(sub[therapy].notna().sum()),
            "therapy_and_global_effectiveness_answered": int(len(paired)),
            "therapy_response_levels_among_nonblank": int(paired[therapy].nunique()) if len(paired) else 0,
            "therapy_has_explicit_yes_and_no": explicit_binary,
            "global_effectiveness_levels": int(paired["mh_treatment_effective_yn"].nunique()) if len(paired) else 0,
            "yes_no_by_global_effectiveness_cells": cell_counts,
            "nonblank_selection_outcome_counts": selected_outcome_counts,
        }
    result["outcome_granularity"] = "participant-level overall treatment effectiveness; no per-modality effectiveness variable identified"
    result["already_published_tests"] = ["imagery-based vs non-imagery-based therapy", "visual vs other imagery-based therapy", "CBT comparisons"]
    result["decision"] = "feasibility_only_no_inferential_model"
    result["maximum_nonblank_modality_global_outcome_n"] = int(paired_total)
    return result
