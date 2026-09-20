from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, UploadFile

from app.config import settings
from app.errors import AppError
from app.models.dataset import AnalysisResult
from app.services import classification_service, excel_service
from app.services.template_service import apply_analysis
from app.store import SessionRecord, store

router = APIRouter()


def _parse_header_row(value: str | None) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise AppError("header_row must be an integer.") from exc


def _analyze_file(
    path: Path,
    filename: str,
    sheet: str | None,
    header_row: int | None,
) -> tuple[list[str], object, AnalysisResult, int]:
    sheets = excel_service.list_sheets(path)
    selected = sheet or sheets[0]
    if selected not in sheets:
        raise AppError(f"Unknown sheet '{selected}'. Available: {', '.join(sheets)}")
    dataset, detected = excel_service.extract_dataset(
        path,
        source_file=filename,
        sheet=None if path.suffix.lower() == ".csv" else selected,
        header_row=header_row,
    )
    analysis = classification_service.classify_columns(
        [column.original_name for column in dataset.columns]
    )
    dataset = apply_analysis(dataset, analysis)
    return sheets, dataset, analysis, detected


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    sheet: str | None = Form(default=None),
    header_row: str | None = Form(default=None),
):
    filename = file.filename or "upload"
    body = await file.read()
    excel_service.validate_upload(filename, len(body), settings.max_upload_bytes)

    session_id = str(uuid4())
    dest = settings.upload_dir / f"{session_id}{Path(filename).suffix.lower()}"
    dest.write_bytes(body)

    sheets, dataset, analysis, detected = _analyze_file(
        dest, filename, sheet, _parse_header_row(header_row)
    )
    record = SessionRecord(
        id=session_id,
        path=dest,
        filename=filename,
        dataset=dataset,
        analysis=analysis,
        sheets=sheets,
    )
    store.put(record)
    return {
        "id": session_id,
        "filename": filename,
        "sheets": sheets,
        "selected_sheet": dataset.dataset.sheet or sheets[0],
        "header_row": detected,
        "dataset": dataset.model_dump(),
        "analysis": analysis.model_dump(),
    }


@router.post("/upload/{session_id}/reprocess")
async def reprocess(
    session_id: str,
    sheet: str | None = Form(default=None),
    header_row: str | None = Form(default=None),
):
    record = store.get(session_id)
    if record is None:
        raise AppError("Unknown upload id. Upload the file again.", status_code=404)
    sheets, dataset, analysis, detected = _analyze_file(
        record.path, record.filename, sheet, _parse_header_row(header_row)
    )
    record.dataset = dataset
    record.analysis = analysis
    record.sheets = sheets
    store.update(record)
    return {
        "id": session_id,
        "filename": record.filename,
        "sheets": sheets,
        "selected_sheet": dataset.dataset.sheet or sheets[0],
        "header_row": detected,
        "dataset": dataset.model_dump(),
        "analysis": analysis.model_dump(),
    }
