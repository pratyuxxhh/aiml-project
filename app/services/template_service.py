from app.errors import AppError
from app.models.dataset import AnalysisResult, NormalizedDataset
from app.models.document import DocumentEdits, DocumentSpecification
from app.models.template import TemplateInfo
from app.templates import TEMPLATE_BUILDERS

AVAILABLE_TEMPLATES = [
    TemplateInfo(
        id="generic_table",
        name="Generic Table",
        description="Title, optional summary, then a data table.",
        best_for="Any tabular data; the safe default.",
    ),
    TemplateInfo(
        id="professional_report",
        name="Professional Report",
        description="Title, description, summary stats, and a main table.",
        best_for="Reports that need a short narrative framing.",
    ),
    TemplateInfo(
        id="profile_cards",
        name="Profile Cards",
        description="One card per row with labeled fields.",
        best_for="Record-like data such as students, customers, or employees.",
    ),
]


def list_templates() -> list[TemplateInfo]:
    return list(AVAILABLE_TEMPLATES)


def apply_analysis(dataset: NormalizedDataset, analysis: AnalysisResult) -> NormalizedDataset:
    updated = dataset.model_copy(deep=True)
    mapping = analysis.column_mapping
    for col in updated.columns:
        semantic = mapping.get(col.original_name) or mapping.get(col.normalized_name)
        if semantic:
            col.semantic_type = semantic  # type: ignore[assignment]
        else:
            col.semantic_type = "generic"
    return updated


def build_specification(
    dataset: NormalizedDataset,
    template_id: str,
    edits: DocumentEdits | None = None,
) -> DocumentSpecification:
    if template_id not in TEMPLATE_BUILDERS:
        raise AppError(f"Unsupported template: {template_id}", status_code=400)
    resolved = edits or DocumentEdits()
    if resolved.template and resolved.template != template_id:
        template_id = resolved.template
        if template_id not in TEMPLATE_BUILDERS:
            raise AppError(f"Unsupported template: {template_id}", status_code=400)
    return TEMPLATE_BUILDERS[template_id](dataset, resolved)


def default_edits(template_id: str, dataset: NormalizedDataset) -> DocumentEdits:
    return DocumentEdits(
        template=template_id,
        selected_columns=[c.normalized_name for c in dataset.columns],
        show_summary=True,
        font_size=11,
    )
