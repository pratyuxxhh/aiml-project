"""Deterministic Excel/CSV parsing into a normalized JSON-compatible dataset."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

from app.errors import AppError
from app.models.dataset import Column, DatasetMeta, NormalizedDataset, PrimitiveType
from app.services.normalization_service import make_unique, normalize_column_name

ALLOWED_EXTENSIONS = {".xlsx", ".csv"}
HEADER_SCAN_LIMIT = 30


def validate_upload(filename: str, size: int, max_bytes: int) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise AppError("Unsupported file type. Upload .xlsx or .csv.")
    if size <= 0:
        raise AppError("Uploaded file is empty.")
    if size > max_bytes:
        raise AppError(f"File is too large. Maximum size is {max_bytes // (1024 * 1024)} MB.")
    return suffix


class DatasetParser:
    """Testable parsing stages; no network or LLM dependency."""

    def list_sheets(self, path: Path) -> list[str]:
        if path.suffix.lower() == ".csv":
            return ["csv"]
        try:
            sheets = list(pd.ExcelFile(path).sheet_names)
        except Exception as exc:
            raise AppError(f"Could not read workbook: {exc}") from exc
        if not sheets:
            raise AppError("Workbook has no sheets.")
        return sheets

    def parse_csv(self, path: Path) -> pd.DataFrame:
        try:
            return pd.read_csv(path, header=None, dtype=object, keep_default_na=False)
        except Exception as exc:
            raise AppError(f"Could not parse file: {exc}") from exc

    def parse_excel(self, path: Path, sheet: str | None) -> pd.DataFrame:
        try:
            return pd.read_excel(path, sheet_name=sheet if sheet else 0, header=None, dtype=object)
        except ValueError as exc:
            raise AppError(f"Could not read sheet: {exc}") from exc
        except Exception as exc:
            raise AppError(f"Could not parse file: {exc}") from exc

    def read_raw_frame(self, path: Path, sheet: str | None) -> pd.DataFrame:
        return self.parse_csv(path) if path.suffix.lower() == ".csv" else self.parse_excel(path, sheet)

    def detect_header(self, frame: pd.DataFrame) -> int:
        """Choose the strongest early row with unique, mostly textual labels."""
        if frame.empty:
            raise AppError("Sheet is empty.")
        candidates: list[tuple[float, int]] = []
        for index in range(min(len(frame), HEADER_SCAN_LIMIT)):
            cells = [_stringify(value) for value in frame.iloc[index].tolist()]
            populated = [cell for cell in cells if cell]
            if not populated:
                continue
            unique_ratio = len(set(populated)) / len(populated)
            string_ratio = sum(not _looks_numeric(cell) for cell in populated) / len(populated)
            if unique_ratio < 0.6 or string_ratio < 0.5:
                continue
            coverage = len(populated) / len(cells)
            breadth = min(len(populated) / 2, 1)
            candidates.append(((2 * string_ratio + unique_ratio + coverage) * breadth, index))
        if not candidates:
            raise AppError("Could not detect a header row. Select a header row manually.")
        return max(candidates, key=lambda item: (item[0], -item[1]))[1]

    def normalize_columns(self, headers: list[object]) -> tuple[list[str], list[str]]:
        original = _clean_headers(headers)
        return original, make_unique([normalize_column_name(name) for name in original])

    def infer_column_types(self, data: pd.DataFrame, headers: list[str]) -> list[PrimitiveType]:
        return [infer_primitive_type(data[header]) for header in headers]

    def parse_sheet(
        self, path: Path, *, source_file: str, sheet: str | None, header_row: int | None = None
    ) -> tuple[NormalizedDataset, int]:
        frame = self.read_raw_frame(path, sheet)
        if frame.empty:
            raise AppError("Sheet is empty.")
        detected = self.detect_header(frame) if header_row is None else header_row
        if detected < 0 or detected >= len(frame):
            raise AppError("Header row is out of range.")
        original, normalized = self.normalize_columns(frame.iloc[detected].tolist())
        data = frame.iloc[detected + 1 :].copy()
        data.columns = original
        data = data.loc[~data.apply(lambda row: all(_cell_is_empty(value) for value in row), axis=1)]
        if data.empty:
            raise AppError("No data rows found under the header row.")
        primitive_types = self.infer_column_types(data, original)
        columns = [
            Column(original_name=raw, normalized_name=clean, primitive_type=primitive)
            for raw, clean, primitive in zip(original, normalized, primitive_types)
        ]
        rows = [
            {
                column.normalized_name: coerce_value(row[raw], column.primitive_type)
                for raw, column in zip(original, columns)
            }
            for _, row in data.iterrows()
        ]
        name = re.sub(r"[^a-z0-9]+", "_", Path(source_file).stem.lower()).strip("_") or "dataset"
        return NormalizedDataset(
            dataset=DatasetMeta(name=name, source_file=source_file, sheet=sheet, header_row=detected),
            columns=columns,
            rows=rows,
            row_count=len(rows),
            sample_rows=rows[:5],
        ), detected


def _cell_is_empty(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, str) and pd.isna(value):
        return True
    return not str(value).strip()


def _stringify(value: object) -> str:
    if _cell_is_empty(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _looks_numeric(text: str) -> bool:
    try:
        float(text.replace(",", "").replace("%", ""))
        return True
    except ValueError:
        return False


def _clean_headers(headers: list[object]) -> list[str]:
    names = [_stringify(value) or f"column_{index}" for index, value in enumerate(headers, 1)]
    counts: dict[str, int] = {}
    result: list[str] = []
    for name in names:
        counts[name] = counts.get(name, 0) + 1
        result.append(name if counts[name] == 1 else f"{name}_{counts[name]}")
    return result


def infer_primitive_type(series: pd.Series) -> PrimitiveType:
    """Use an exact all-values match; ambiguous or mixed columns stay strings."""
    values = [value for value in series.tolist() if not _cell_is_empty(value)]
    if not values:
        return "null"
    text = [_stringify(value).lower() for value in values]
    if all(value in {"true", "false", "yes", "no", "y", "n"} for value in text):
        return "boolean"
    if all(_is_integer(value) for value in values):
        return "integer"
    if all(_is_float(value) for value in values):
        return "float"
    parsed = [pd.to_datetime(value, errors="coerce") for value in values]
    if all(not pd.isna(value) for value in parsed):
        if all(value.hour == value.minute == value.second == value.microsecond == 0 for value in parsed):
            return "date"
        return "datetime"
    return "string"


def _is_integer(value: object) -> bool:
    if isinstance(value, bool):
        return False
    text = _stringify(value).replace(",", "")
    try:
        return float(text).is_integer() and "." not in text and "e" not in text.lower()
    except ValueError:
        return False


def _is_float(value: object) -> bool:
    if isinstance(value, bool):
        return False
    return _looks_numeric(_stringify(value))


def coerce_value(value: object, primitive: PrimitiveType) -> Any:
    if _cell_is_empty(value):
        return None
    text = _stringify(value)
    try:
        if primitive == "integer":
            return int(float(text.replace(",", "")))
        if primitive == "float":
            return float(text.replace(",", "").replace("%", ""))
        if primitive == "boolean":
            return text.lower() in {"true", "yes", "y"}
        if primitive in {"date", "datetime"}:
            parsed = pd.to_datetime(value, errors="raise")
            return parsed.date().isoformat() if primitive == "date" else parsed.isoformat()
    except (TypeError, ValueError):
        return text
    return text


_PARSER = DatasetParser()


def list_sheets(path: Path) -> list[str]:
    return _PARSER.list_sheets(path)


def read_raw_frame(path: Path, sheet: str | None) -> pd.DataFrame:
    return _PARSER.read_raw_frame(path, sheet)


def detect_header_row(frame: pd.DataFrame) -> int:
    return _PARSER.detect_header(frame)


def extract_dataset(
    path: Path, *, source_file: str, sheet: str | None, header_row: int | None = None
) -> tuple[NormalizedDataset, int]:
    return _PARSER.parse_sheet(path, source_file=source_file, sheet=sheet, header_row=header_row)


