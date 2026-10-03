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


def build_professional_report(dataset: NormalizedDataset, edits: DocumentEdits) -> DocumentSpecification:
    columns = selected_columns(dataset, edits)
    title = display_title(
        dataset,
        edits,
        f"{dataset.dataset.name.replace('_', ' ').title()} Report",
    )
    default_sub = (
        f"Prepared from {dataset.dataset.source_file}"
        + (f" ({dataset.dataset.sheet})" if dataset.dataset.sheet else "")
        + f". {dataset.row_count} records included."
    )
    subtitle = display_subtitle(edits, default_sub)
    sections = [heading(title)]
    if subtitle:
        sections.append(paragraph(subtitle))
    if edits.show_summary:
        sections.append(heading("Summary", level=2))
        sections.append(summary_section(build_summary_items(dataset, columns)))
    sections.append(heading("Details", level=2))
    sections.append(table_section(columns, table_rows(dataset, columns), edits.column_widths))
    return DocumentSpecification(
        template="professional_report",
        title=title,
        subtitle=subtitle,
        font_size=edits.font_size,
        orientation=edits.orientation or "portrait",
        sections=sections,
    )
