# Excel/CSV → Word Document Generator

A local, fully offline app that parses an `.xlsx` or `.csv` table into normalized JSON, builds a document specification, previews it as HTML, and exports a `.docx`.

## Setup

Python 3.11+ recommended.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

On macOS/Linux, activate with `source .venv/bin/activate` and copy the env file with `cp .env.example .env`.

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and try `sample/placement.csv`.

## Offline pipeline

```text
Excel/CSV → DatasetParser → Normalized JSON Dataset → Rule-Based Classification
         → Template → Document Specification → { HTML Preview, DOCX }
```

`DatasetParser` handles CSV/Excel reading, sheet selection, header detection, header normalization, primitive type inference, and JSON-compatible row construction. Templates only consume the normalized dataset; preview and DOCX both consume the same document specification.

## Deterministic behavior

No OpenAI client, API key, external API, or network call is used by the core workflow. It works offline after dependencies are installed.

- Header detection examines the first 30 rows and selects the strongest row with at least two populated cells, mostly unique values, and at least 50% non-numeric values. Users can override the detected row.
- Normalized names are lower snake case. Duplicates receive suffixes: `Name`, `Name`, `Name` become `name`, `name_2`, `name_3`.
- Primitive types are inferred only when all populated values match: `string`, `integer`, `float`, `boolean`, `date`, `datetime`, or `null`. Mixed values remain `string`.
- Semantic classification uses explicit header rules: `name` → `person_name`; `usn`, `reg`, `registration` → `student_id`; `cgpa`, `gpa`, `grade` → `academic_score`; `package`, `salary`, `ctc`, `stipend` → `salary_package`; otherwise `generic`.
- Template recommendation is deterministic: placement-like data uses `professional_report`, person records use `profile_cards`, and generic data uses `generic_table`.

## API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/upload` | Parse file, classify columns, return normalized dataset |
| `POST` | `/upload/{id}/reprocess` | Change sheet or header row |
| `GET` | `/templates` | List the three templates |
| `POST` | `/documents/preview` | HTML preview from a document specification |
| `POST` | `/documents/export` | Write a `.docx` |
| `GET` | `/files/{id}` | Download generated file |

## Tests

```bash
pytest
```
