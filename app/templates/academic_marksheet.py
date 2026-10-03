from app.models.dataset import NormalizedDataset
from app.models.document import DocumentEdits, DocumentSpecification
from app.templates.common import (
    build_summary_items,
    display_subtitle,
    display_title,
    heading,
    paragraph,
    selected_columns,
    summary_section,
    table_rows,
    table_section,
)


def build_academic_marksheet(
    dataset: NormalizedDataset, edits: DocumentEdits
) -> DocumentSpecification:
    columns = selected_columns(dataset, edits)
    title = display_title(
        dataset,
        edits,
        f"{dataset.dataset.name.replace('_', ' ').title()} Academic Marksheet",
    )
    subtitle = display_subtitle(edits, "Academic performance register")
    sections = [heading(title)]
    if subtitle:
        sections.append(paragraph(subtitle))
    if edits.show_summary:
        sections.append(summary_section(build_summary_items(dataset, columns)))
    sections.append(table_section(columns, table_rows(dataset, columns), edits.column_widths))
    return DocumentSpecification(
        template="academic_marksheet",
        title=title,
        subtitle=subtitle,
        font_size=edits.font_size,
        orientation=edits.orientation or "landscape",
        sections=sections,
    )
