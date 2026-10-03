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


def build_placement_summary(
    dataset: NormalizedDataset, edits: DocumentEdits
) -> DocumentSpecification:
    columns = selected_columns(dataset, edits)
    title = display_title(
        dataset,
        edits,
        f"{dataset.dataset.name.replace('_', ' ').title()} Placement Summary",
    )
    subtitle = display_subtitle(edits, f"{dataset.row_count} placement records")
    sections = [heading(title)]
    if subtitle:
        sections.append(paragraph(subtitle))
    if edits.show_summary:
        sections.append(summary_section(build_summary_items(dataset, columns)))
    sections.append(heading("Placement details", level=2))
    sections.append(table_section(columns, table_rows(dataset, columns), edits.column_widths))
    return DocumentSpecification(
        template="placement_summary",
        title=title,
        subtitle=subtitle,
        font_size=edits.font_size,
        orientation=edits.orientation or "landscape",
        sections=sections,
    )
