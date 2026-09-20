from app.models.dataset import NormalizedDataset
from app.models.document import DocumentEdits, DocumentSpecification
from app.templates.common import (
    build_summary_items,
    cards_section,
    display_subtitle,
    display_title,
    heading,
    paragraph,
    selected_columns,
    summary_section,
)


def build_profile_cards(dataset: NormalizedDataset, edits: DocumentEdits) -> DocumentSpecification:
    columns = selected_columns(dataset, edits)
    title = display_title(dataset, edits, f"{dataset.dataset.name.replace('_', ' ').title()} Profiles")
    subtitle = display_subtitle(edits, f"{dataset.row_count} records")
    sections = [heading(title)]
    if subtitle:
        sections.append(paragraph(subtitle))
    if edits.show_summary:
        sections.append(summary_section(build_summary_items(dataset, columns)))
    sections.append(cards_section(dataset, columns))
    return DocumentSpecification(
        template="profile_cards",
        title=title,
        subtitle=subtitle,
        font_size=edits.font_size,
        orientation="portrait",
        sections=sections,
    )
