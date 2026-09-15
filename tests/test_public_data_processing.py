from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aphantasia.datasets import (  # noqa: E402
    audit_mawtus_feasibility,
    load_arnold_code,
    load_new_studies,
)
from aphantasia.models import run_p1, run_p3  # noqa: E402


def test_new_qc_reproduces_published_sample_counts_and_drops_identifiers():
    frame, flow = load_new_studies(ROOT / "2bdn6-osfstorage-archive.zip")
    assert flow["study_1"]["source_rows"] == 953
    assert flow["study_1"]["attention_excluded_nbact_lt_3"] == 4
    assert flow["study_1"]["published_analysis_n"] == 949
    assert flow["study_2"]["source_rows"] == 1020
    assert flow["study_2"]["attention_excluded_nbact_lt_3"] == 17
    assert flow["study_2"]["published_analysis_n"] == 1003
    assert len(flow["study_1"]["nonvisual_composite"]) == 7
    assert flow["study_1"]["outcome_mapping"]["question"] == "Are you currently receiving treatment for a neurologic or psychiatric condition?"
    assert flow["study_2"]["outcome_mapping"]["follow_up_branch"] == "shown only after Yes"
    assert "ProlificID" not in frame.columns
    assert "comment" not in frame.columns
    assert "id" not in frame.columns


def test_arnold_full_and_author_code_selection_are_distinct():
    formal, code_filtered, traits, flow = load_arnold_code(ROOT / "Autism_Aphantasia_Analyses_code.zip")
    assert formal["diagnosis_group"].value_counts().to_dict() == {0: 327, 1: 327}
    assert len(code_filtered) == 327 + flow["diagnosed_selected_by_code_AQ_threshold"]
    assert flow["diagnosed_selected_by_code_AQ_threshold"] == 242
    assert len(traits) == 327
    assert not {"participant_id", "name", "comment"}.intersection(formal.columns)


def test_p1_and_p3_only_write_aggregate_artifacts():
    p1_frame, _ = load_new_studies(ROOT / "2bdn6-osfstorage-archive.zip")
    p3_formal, p3_code_filtered, p3_traits, _ = load_arnold_code(ROOT / "Autism_Aphantasia_Analyses_code.zip")
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory)
        p1_result = run_p1(p1_frame, target / "P1")
        p3_result = run_p3(p3_formal, p3_traits, target / "P3", p3_code_filtered)
        assert p1_result["status"] == "complete"
        assert p3_result["status"] == "complete"
        assert p3_result["sample_sizes"]["all_self_reported_formal_dx"] == {
            "controls": 327,
            "formally_diagnosed": 327,
        }
        diagnostics_path = next(Path(path) for path in p3_result["artifacts"] if path.endswith("p3_diagnostics.json"))
        repeated = json.loads(diagnostics_path.read_text(encoding="utf-8"))["repeated_modality_model"]
        assert repeated["clusters"] == 654
        assert repeated["joint_autism_by_modality_df"] == 5
        for result in (p1_result, p3_result):
            for artifact in result["artifacts"]:
                text = Path(artifact).read_text(encoding="utf-8")
                assert "ProlificID" not in text
                assert "participant_rows" in text or "project" in text


def test_mawtus_gate_detects_global_not_modality_specific_effectiveness():
    result = audit_mawtus_feasibility(ROOT / "v7krh-osfstorage-archive.zip")
    assert result["rows"] == 2815
    assert result["decision"] == "feasibility_only_no_inferential_model"
    assert "no per-modality effectiveness" in result["outcome_granularity"]
    assert result["modalities"]["auditory"]["therapy_has_explicit_yes_and_no"] is False
