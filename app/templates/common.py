from __future__ import annotations

from typing import Any

from app.models.dataset import Column, NormalizedDataset, SemanticType
from app.models.document import (
    Card,
    CardField,
    DocumentEdits,
    DocumentSection,
    DocumentSpecification,
    SummaryItem,
)


def selected_columns(dataset: NormalizedDataset, edits: DocumentEdits) -> list[Column]:
    by_name = {c.normalized_name: c for c in dataset.columns}
    if edits.selected_columns:
        cols = [by_name[n] for n in edits.selected_columns if n in by_name]
        if cols:
            return cols
    return list(dataset.columns)


def display_title(dataset: NormalizedDataset, edits: DocumentEdits, default: str) -> str:
    if edits.title and edits.title.strip():
        return edits.title.strip()
    return default


def display_subtitle(edits: DocumentEdits, default: str | None = None) -> str | None:
    if edits.subtitle is not None:
        text = edits.subtitle.strip()
        return text or None
    return default


def cell_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def table_rows(dataset: NormalizedDataset, columns: list[Column]) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in dataset.rows:
        rows.append([cell_text(row.get(col.normalized_name)) for col in columns])
    return rows


def _numeric_values(dataset: NormalizedDataset, column: Column) -> list[float]:
    values: list[float] = []
    for row in dataset.rows:
        value = row.get(column.normalized_name)
        if isinstance(value, bool) or value is None:
            continue
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            continue
    return values


def build_summary_items(dataset: NormalizedDataset, columns: list[Column]) -> list[SummaryItem]:
    items = [SummaryItem(label="Rows", value=str(dataset.row_count))]

    by_type: dict[SemanticType, Column] = {}
    for col in columns:
        by_type.setdefault(col.semantic_type, col)

    score_col = by_type.get("academic_score")
    if score_col:
        nums = _numeric_values(dataset, score_col)
        if nums:
            avg = sum(nums) / len(nums)
            items.append(SummaryItem(label=f"Average {score_col.original_name}", value=f"{avg:.2f}"))

    salary_col = by_type.get("salary_package")
    if salary_col:
        nums = _numeric_values(dataset, salary_col)
        if nums:
            items.append(
                SummaryItem(label=f"Highest {salary_col.original_name}", value=cell_text(max(nums)))
            )

    if len(items) == 1:
        for col in columns:
            if col.primitive_type in {"integer", "float"}:
                nums = _numeric_values(dataset, col)
                if nums:
                    avg = sum(nums) / len(nums)
                    items.append(SummaryItem(label=f"Average {col.original_name}", value=f"{avg:.2f}"))
                    if len(items) >= 4:
                        break
    return items


def heading(text: str, level: int = 1) -> DocumentSection:
    return DocumentSection(type="heading", text=text, level=level)


def paragraph(text: str) -> DocumentSection:
    return DocumentSection(type="paragraph", text=text)


def summary_section(items: list[SummaryItem]) -> DocumentSection:
    return DocumentSection(type="summary", items=items)


def _aligned_column_widths(
    column_count: int, column_widths: list[float] | None
) -> list[float]:
    if not column_widths or column_count <= 0:
        return []
    if len(column_widths) != column_count:
        return []
    cleaned = [float(width) for width in column_widths if isinstance(width, (int, float)) and width > 0]
    if len(cleaned) != column_count:
        return []
    total = sum(cleaned) or 1.0
    return [width / total * 100.0 for width in cleaned]


def table_section(
    columns: list[Column],
    rows: list[list[str]],
    column_widths: list[float] | None = None,
) -> DocumentSection:
    return DocumentSection(
        type="table",
        headers=[c.original_name for c in columns],
        rows=rows,
        column_widths=_aligned_column_widths(len(columns), column_widths),
    )


def cards_section(dataset: NormalizedDataset, columns: list[Column]) -> DocumentSection:
    title_col = next((c for c in columns if c.semantic_type == "person_name"), columns[0])
    cards: list[Card] = []
    for row in dataset.rows:
        fields = [
            CardField(label=col.original_name, value=cell_text(row.get(col.normalized_name)))
            for col in columns
            if col.normalized_name != title_col.normalized_name
        ]
        cards.append(Card(title=cell_text(row.get(title_col.normalized_name)) or "Record", fields=fields))
    return DocumentSection(type="cards", cards=cards)
