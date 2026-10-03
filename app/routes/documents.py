from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.errors import AppError
from app.models.document import DocumentEdits
from app.models.formatting_spec import DocumentFormatting
from app.services.docx_service import write_docx
from app.services.preview_service import render_preview_html
from app.services.template_service import build_specification
from app.store import store

router = APIRouter()


class DocumentRequest(BaseModel):
    dataset_id: str
    template: str = "generic_table"
    edits: DocumentEdits = Field(default_factory=DocumentEdits)
    formatting: DocumentFormatting | None = None


@router.post("/documents/preview")
def preview_document(payload: DocumentRequest):
    spec = _spec_from_request(payload)
    return {"html": render_preview_html(spec), "spec": spec.model_dump()}


@router.post("/documents/export")
def export_document(payload: DocumentRequest):
    spec = _spec_from_request(payload)
    file_id = str(uuid4())
    path = settings.output_dir / f"{file_id}.docx"
    write_docx(spec, path, formatting=payload.formatting)
    filename = f"{spec.title.replace(' ', '_')[:60] or 'document'}.docx"
    return {"id": file_id, "filename": filename}


@router.get("/files/{file_id}")
def download_file(file_id: str):
    path = settings.output_dir / f"{file_id}.docx"
    if not path.exists():
        raise AppError("File not found.", status_code=404)
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{file_id}.docx",
    )


def _spec_from_request(payload: DocumentRequest):
    record = store.get(payload.dataset_id)
    if record is None or record.dataset is None:
        raise AppError("Unknown dataset. Upload a file first.", status_code=404)
    edits = payload.edits.model_copy()
    if not edits.template:
        edits.template = payload.template
    return build_specification(record.dataset, payload.template, edits)
