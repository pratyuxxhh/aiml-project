from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Color(BaseModel):
    hex: str | None = None


class TextStyle(BaseModel):
    font_family: str | None = None
    size_pt: int | None = None
    color: Color | None = None
    background_color: Color | None = None
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    alignment: str | None = None


class MarginSpec(BaseModel):
    left_mm: float | None = None
    right_mm: float | None = None
    top_mm: float | None = None
    bottom_mm: float | None = None


class ColumnSpec(BaseModel):
    name: str | None = None
    width_mm: float | None = None
    width_percent: float | None = None


class RowStyleCondition(BaseModel):
    column: str
    operator: str
    value: Any = None


class RowStyleAction(BaseModel):
    bold: bool = False
    italic: bool = False
    underline: bool = False
    font_color: Color | None = None
    highlight_bg: Color | None = None


class RowStyleRule(BaseModel):
    condition: RowStyleCondition
    action: RowStyleAction


class TableSpec(BaseModel):
    columns: list[ColumnSpec] = Field(default_factory=list)
    header_style: TextStyle | None = None
    row_style_rules: list[RowStyleRule] = Field(default_factory=list)
    table_alignment: str | None = None


class SectionSpec(BaseModel):
    id: str | None = None
    type: str = 'table'
    content: Any = None


class DocumentFormatting(BaseModel):
    orientation: Literal['portrait', 'landscape'] | None = None
    margins: MarginSpec | None = None
    body: TextStyle | None = None
    headings: TextStyle | None = None
    sections: list[SectionSpec] = Field(default_factory=list)


__all__ = [
    'Color',
    'TextStyle',
    'MarginSpec',
    'ColumnSpec',
    'RowStyleCondition',
    'RowStyleAction',
    'RowStyleRule',
    'TableSpec',
    'SectionSpec',
    'DocumentFormatting',
]
