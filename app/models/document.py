from typing import Any, Literal

from pydantic import BaseModel, Field

SectionType = Literal["heading", "paragraph", "summary", "table", "cards"]


class SummaryItem(BaseModel):
    label: str
    value: str


class CardField(BaseModel):
    label: str
    value: str


class Card(BaseModel):
    title: str
    fields: list[CardField] = Field(default_factory=list)


class DocumentSection(BaseModel):
    type: SectionType
    text: str | None = None
    level: int = 1
    items: list[SummaryItem] = Field(default_factory=list)
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    cards: list[Card] = Field(default_factory=list)


class DocumentSpecification(BaseModel):
    """Fully resolved document. Preview and DOCX consume this, not raw Excel."""

    template: str
    title: str
    subtitle: str | None = None
    font_size: int = 11
    orientation: Literal["portrait", "landscape"] = "portrait"
    sections: list[DocumentSection] = Field(default_factory=list)


class DocumentEdits(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    selected_columns: list[str] | None = None
    show_summary: bool = True
    font_size: int = 11
    template: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
