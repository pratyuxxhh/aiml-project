"""Offline, deterministic semantic classification for normalized datasets."""

from __future__ import annotations

import re

from app.models.dataset import AnalysisResult, SemanticType


def classify_columns(columns: list[str]) -> AnalysisResult:
    """Classify column names and recommend templates without network access."""
    mapping = {column: classify_column(column) for column in columns}
    dataset_type = infer_dataset_type(mapping)
    return AnalysisResult(
        dataset_type=dataset_type,
        column_mapping=mapping,
        recommended_templates=recommend_templates(mapping, dataset_type),
        source="deterministic",
    )


def classify_column(name: str) -> SemanticType:
    """Return a semantic type from explicit, stable header-name rules."""
    key = re.sub(r"[^a-z0-9]+", "", name.lower())
    tokens = set(filter(None, re.split(r"[^a-z0-9]+", name.lower())))

    if "usn" in key or "regno" in key or "registration" in key or tokens & {"reg", "roll"}:
        return "student_id"
    if "cgpa" in key or key.endswith("gpa") or "grade" in key:
        return "academic_score"
    if any(token in key for token in ("package", "salary", "ctc", "stipend")):
        return "salary_package"
    if "name" in key and "file" not in key and "sheet" not in key:
        return "person_name"
    return "generic"


def infer_dataset_type(mapping: dict[str, SemanticType]) -> str:
    types = set(mapping.values())
    if "student_id" in types or {"academic_score", "salary_package"} <= types:
        return "student_placement"
    if "person_name" in types:
        return "people_records"
    return "generic_table"


def recommend_templates(mapping: dict[str, SemanticType], dataset_type: str) -> list[str]:
    types = set(mapping.values())
    if dataset_type == "student_placement" or {"academic_score", "salary_package"} & types:
        return ["professional_report", "generic_table", "profile_cards"]
    if "person_name" in types:
        return ["profile_cards", "generic_table", "professional_report"]
    return ["generic_table", "professional_report", "profile_cards"]
