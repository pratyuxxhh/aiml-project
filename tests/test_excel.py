from pathlib import Path

import pandas as pd
import pytest

from app.errors import AppError
from app.services.excel_service import DatasetParser, extract_dataset, list_sheets, validate_upload

SAMPLE = Path(__file__).resolve().parents[1] / "sample" / "placement.csv"


def test_validate_rejects_bad_extension():
    with pytest.raises(AppError):
        validate_upload("notes.txt", 10, 1000)


def test_parse_sample_csv():
    dataset, header_row = extract_dataset(SAMPLE, source_file="placement.csv", sheet=None)
    assert header_row == 0
    assert dataset.row_count == 3
    assert [column.normalized_name for column in dataset.columns] == [
        "name", "usn", "cgpa", "package", "company"
    ]
    assert dataset.rows[0]["name"] == "Pratyush"
    assert dataset.rows[0]["cgpa"] == 8.47


def test_header_detection_skips_empty_rows_and_title(tmp_path: Path):
    path = tmp_path / "students.csv"
    pd.DataFrame([
        [None, None, None, None],
        ["Student Data", None, None, None],
        ["Name", "USN", "CGPA", "Package"],
        ["Rahul", "1MS24CS101", 8.5, 12],
    ]).to_csv(path, header=False, index=False)
    dataset, header_row = extract_dataset(path, source_file="students.csv", sheet=None)
    assert header_row == 2
    assert dataset.rows[0]["usn"] == "1MS24CS101"


def test_parser_infers_boolean_date_and_null_types(tmp_path: Path):
    path = tmp_path / "types.csv"
    pd.DataFrame([
        ["Placed", "Joining Date", "Notes", "Age", "Mixed"],
        ["true", "2026-07-01", None, 20, "20"],
        ["false", "2026-07-15", None, 21, "unknown"],
    ]).to_csv(path, header=False, index=False)
    dataset, _ = extract_dataset(path, source_file="types.csv", sheet=None)
    assert [column.primitive_type for column in dataset.columns] == [
        "boolean", "date", "null", "integer", "string"
    ]
    assert dataset.rows[0]["placed"] is True
    assert dataset.rows[0]["joining_date"] == "2026-07-01"
    assert dataset.rows[1]["notes"] is None


def test_duplicate_normalized_headers_remain_unique():
    parser = DatasetParser()
    _, normalized = parser.normalize_columns(["Name", "Name", "C.G.P.A", "CGPA"])
    assert normalized == ["name", "name_2", "cgpa", "cgpa_2"]


def test_empty_sheet_errors(tmp_path: Path):
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(AppError):
        extract_dataset(path, source_file="empty.csv", sheet=None)


def test_xlsx_sheet_list(tmp_path: Path):
    path = tmp_path / "book.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame({"A": [1], "B": [2]}).to_excel(writer, sheet_name="Alpha", index=False)
        pd.DataFrame({"X": [3]}).to_excel(writer, sheet_name="Beta", index=False)
    assert list_sheets(path) == ["Alpha", "Beta"]
    dataset, _ = extract_dataset(path, source_file="book.xlsx", sheet="Beta")
    assert dataset.row_count == 1
    assert dataset.columns[0].normalized_name == "x"
