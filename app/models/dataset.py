from typing import Any, Literal

from pydantic import BaseModel, Field

PrimitiveType = Literal[
    "string", "integer", "float", "boolean", "date", "datetime", "null"
]

SemanticType = Literal[
    "person_name",
    "student_id",
    "academic_score",
    "salary_package",
    "generic",
]


class Column(BaseModel):
    original_name: str
    normalized_name: str
    primitive_type: PrimitiveType = "string"
    semantic_type: SemanticType = "generic"


class DatasetMeta(BaseModel):
    name: str
    source_file: str
    sheet: str | None = None
    header_row: int = 0


class NormalizedDataset(BaseModel):
    dataset: DatasetMeta
    columns: list[Column]
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    sample_rows: list[dict[str, Any]] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    dataset_type: str = "generic_table"
    column_mapping: dict[str, SemanticType] = Field(default_factory=dict)
    recommended_templates: list[str] = Field(default_factory=lambda: ["generic_table"])
    source: Literal["deterministic"] = "deterministic"
