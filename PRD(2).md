# PRD — Excel/CSV → Word Document Generator (MVP)

## 1. Summary

A local web app that takes a tabular Excel/CSV file, understands its columns, turns it into a document using one of a few templates, shows an editable preview, and exports a `.docx`.

**Priority for v1: a thin, fully-working pipeline over any UI polish or feature breadth.**

```text
Excel/CSV → Parse → Normalize → Classify columns (AI, with fallback)
   → Pick template → Document spec → HTML preview (editable) → DOCX
```

One rule governs the whole design: **data, template, and rendering are separate layers**, and the *same* document specification drives both the preview and the DOCX. This is the one piece of architecture worth being disciplined about — everything else should stay as simple as possible.

---

## 2. Goal

Ship an MVP where a user can, end-to-end and locally:

1. Upload a `.xlsx` or `.csv` file.
2. See it parsed into columns + rows with inferred types.
3. Get columns semantically classified (AI-assisted, with a deterministic fallback).
4. Pick from 3 templates (one is auto-recommended).
5. See an HTML preview of the resulting document.
6. Make a small set of edits (title, columns shown, summary on/off).
7. Export a valid `.docx` that opens cleanly in Word/LibreOffice.

---

## 3. Explicit Non-Goals (v1)

Do not spend time on: auth, deployment, multi-user support, real-time collaboration, pixel-perfect Word fidelity, drag-and-drop layout, pagination, typography controls, payments, general enterprise security, or exhaustive Excel edge-case handling.

A functional, ugly UI is a success. A beautiful UI that doesn't produce a working `.docx` is not.

---

## 4. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Backend | Python + FastAPI | fast to build, easy typed I/O via Pydantic |
| Parsing | pandas + openpyxl | reading, type inference, row→dict conversion |
| AI | Any OpenAI-compatible API, isolated in `ai_service.py` | swappable provider, **must have a working non-AI fallback** |
| Document generation | python-docx | headings, paragraphs, tables, basic styling |
| Preview | Jinja2 + plain HTML/CSS/JS | represents the doc spec, not a Word clone |
| Persistence | None required for v1 (in-memory / filesystem) | add SQLite only if you need documents to survive a restart |
| Config | `.env` | `LLM_API_KEY`, `LLM_MODEL`, `UPLOAD_DIR`, `OUTPUT_DIR` |

**Simplification vs. a "full" build:** skip the database entirely for v1. Keep uploaded/generated files on disk under `storage/`, keyed by a generated id, and keep the current session's dataset + spec in memory. This removes a whole subsystem without weakening the architecture — SQLite can be added later purely as persistence, without touching the pipeline.

---

## 5. Project Structure

```text
excel-to-word/
├── app/
│   ├── main.py
│   ├── routes/          # upload, templates, documents
│   ├── services/
│   │   ├── excel_service.py         # read + extract
│   │   ├── normalization_service.py # column/name normalization
│   │   ├── ai_service.py            # AI + deterministic fallback
│   │   ├── template_service.py      # template → document spec
│   │   ├── preview_service.py       # spec → HTML
│   │   └── docx_service.py          # spec → .docx
│   ├── models/           # dataset.py, document.py, template.py (Pydantic)
│   ├── templates/        # generic_table.py, professional_report.py, profile_cards.py
│   └── web/               # templates/ + static/ for the preview page
├── storage/{uploads,output}/
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

Keep each service independently testable and don't add abstractions you don't need yet.

---

## 6. Core Data Model

```json
{
  "dataset": { "name": "placement_data", "source_file": "students.xlsx", "sheet": "Sheet1" },
  "columns": [
    { "original_name": "Name", "normalized_name": "name", "semantic_type": "person_name" },
    { "original_name": "USN", "normalized_name": "usn", "semantic_type": "student_id" },
    { "original_name": "CGPA", "normalized_name": "cgpa", "semantic_type": "academic_score" },
    { "original_name": "Package", "normalized_name": "package", "semantic_type": "salary" }
  ],
  "rows": [ { "name": "pratyush", "usn": "1ms24cs131", "cgpa": 8.47, "package": 19.5 } ]
}
```

Principle: **templates operate on this normalized structure, never on raw Excel cells.**

---

## 7. Input Handling

- Support `.xlsx` and `.csv` (`.xls` only if trivial to add).
- For Excel: list sheets, let the user pick one, default to the first.
- Detect the header row with a simple deterministic heuristic (first non-empty row with mostly-unique, mostly-string cells); let the user override it.
- Assume reasonably clean tabular input — don't build defensive handling for pathological files in v1.

---

## 8. Processing Pipeline

1. Validate extension + size.
2. Read workbook/sheet.
3. Detect header row.
4. Extract columns, row count, sample rows, inferred primitive types.
5. Normalize column names (`"C.G.P.A" → "cgpa"`, `"Reg No." → "reg_no"`).
6. Send only column names + a small row sample (not the full dataset) to the AI service when AI is enabled.

---

## 9. AI Layer

**Input** (small, not the full dataset):
```json
{ "columns": ["Name", "USN", "CGPA", "Package"],
  "sample_rows": [["Pratyush", "1ms24cs131", 8.47, 19.5]] }
```

**Required output** (validate before use):
```json
{ "dataset_type": "student_placement",
  "column_mapping": { "Name": "person_name", "USN": "student_id" },
  "recommended_templates": ["placement_report", "tabular_report"] }
```

**Fallback is mandatory, not optional.** If the API key is missing, the call fails, or the response doesn't validate, fall back to keyword heuristics (`name → person_name`, `usn/reg*/registration → student_id`, `cgpa/gpa → academic_score`, `package/salary/ctc → salary_package`, anything else → `generic`) and default to the generic table template. The app must never break because the AI is unavailable — this is the one behavior worth writing a test for early.

---

## 10. Templates (ship exactly 3)

| Template | Structure | Best for |
|---|---|---|
| `generic_table` | Title → optional summary → data table | Any tabular data; the safe default |
| `professional_report` | Title → description → summary stats → main table | Reports with a narrative framing |
| `profile_cards` | One card/block per row | Record-like data (students, customers, employees) |

Templates produce a **document specification**, not a `.docx` directly:

```json
{ "template": "placement_report", "title": "Student Placement Report",
  "sections": [ { "type": "summary" }, { "type": "table", "columns": ["name","usn","cgpa","package"] } ] }
```

---

## 11. Document Specification (the central abstraction)

```text
Normalized Data + Template → Document Specification → { HTML Preview, DOCX Renderer }
```

Both renderers consume the *same* spec. This is what prevents preview and export from silently drifting apart — don't let either renderer read the raw dataset directly.

---

## 12. Editing (config-based, not a canvas editor)

Editable fields for v1: title, subtitle, selected columns, column order, template choice, show/hide summary, basic font size. Saving edits re-renders the preview from the updated spec. A drag-and-drop or WYSIWYG editor is explicitly out of scope.

---

## 13. Preview

Plain HTML rendering of the spec — good enough to confirm structure, not a Word facsimile:

```text
2026 PLACEMENT REPORT
Total Students: 3   Average CGPA: 8.62   Highest Package: 19.5
Name       USN          CGPA   Package
Pratyush   1ms24cs131   8.47   19.5
```

---

## 14. DOCX Generation

`docx_service.py` takes `(DocumentSpecification, NormalizedDataset)` → writes `storage/output/<id>.docx`.

Support: title, paragraphs, tables, basic formatting, margins, page orientation, optional header/footer. Nothing beyond that in v1 — the bar is "opens correctly in Word and LibreOffice," not visual fidelity.

---

## 15. API (minimal)

To keep the round-trips simple, **fold parsing + AI analysis into one upload step**: the client shouldn't need to orchestrate two calls just to see the parsed data.

```text
POST /upload              → parses file, runs AI analysis (with fallback), returns dataset + recommended templates
GET  /templates            → list available templates
POST /documents/preview    → dataset + template + edits → HTML preview
POST /documents/export     → dataset + template + edits → .docx
GET  /files/{id}           → download generated file
```

---

## 16. End-to-End Example

```text
Upload sheet → parse → normalize columns → AI classifies
  (student_name, student_id, academic_score, salary_package)
  → recommends "placement_report" → user confirms template
  → spec generated → preview shown → user edits title/columns
  → preview updates → user exports → .docx written
```

---

## 17. One Engineering Rule That Matters Most

Never implement `Excel → DOCX` as one function. Keep the layers real:

```text
Excel → Dataset → Document Specification → { Preview, DOCX }
```

This separation is cheap now and is the only thing that makes future features (custom templates, natural-language edits, charts) additive instead of rewrites.

---

## 18. Deliberately Deferred (don't design for these yet, just don't block them)

Drag-and-drop editor, custom/user-created/AI-generated templates, natural-language editing (e.g. *"make the title bigger, drop USN, sort by package"* → validated spec update), logo/image insertion, charts, multi-file input, Google Sheets, PDF export, saved history, cloud storage, auth, collaboration.

---

## 19. MVP Acceptance Criteria

- [ ] Upload `.xlsx`/`.csv`, pick a sheet, see parsed columns + sample rows.
- [ ] Data is normalized into the JSON structure in §6.
- [ ] AI classifies common columns; deterministic fallback works when AI is disabled/unavailable.
- [ ] All 3 templates work; user can select one.
- [ ] User can edit title/columns/summary toggle and see the preview update.
- [ ] Export produces a `.docx` that opens correctly in Word/LibreOffice.
- [ ] Preview and DOCX are driven by the same document specification.

---

## 20. Build Order

1. **Data**: FastAPI skeleton → upload → Excel/CSV parser → sheet selection → normalization → display parsed data.
2. **Documents**: document spec model → `generic_table` template → DOCX renderer → first working `.docx`.
3. **Templates**: add `professional_report` + `profile_cards` → template selection/config.
4. **Preview**: HTML preview → basic editing → re-render on save.
5. **AI**: `ai_service.py` → column mapping → dataset classification → template recommendation → fallback path.
6. **Integration**: wire the full upload → analyze → template → preview → edit → export flow, add error handling, tests, README.

Keep the app runnable after every phase — don't let it go dark for more than one phase at a time.

---

## 21. Prompt for a Coding Agent

> Build the MVP described in this PRD, in the order given in §20. Stack: Python 3.11+, FastAPI, Uvicorn, pandas, openpyxl, python-docx, Jinja2, vanilla HTML/CSS/JS, Pydantic, python-dotenv — no React/Next.js/Tailwind/Docker/Redis/Celery/microservices, no database unless you hit a real need for persistence beyond the current session. Keep `excel_service`, `ai_service`, `template_service`, `preview_service`, and `docx_service` as separate, independently testable modules; never let the DOCX or preview renderer touch raw Excel data or the AI provider directly. The AI service must degrade to the deterministic heuristics in §9 when the API key is missing or the call fails or the response fails validation — treat this as a required path, not a nice-to-have, and test it. Implement the endpoints in §15. Handle: invalid file, empty sheet, missing/duplicate headers, malformed AI output, AI unavailable, unsupported template, DOCX write failure — return clear errors, not stack traces. Deliverables: source code, `tests/` covering parsing/normalization/template generation/DOCX creation, `requirements.txt`, `.env.example`, a README covering setup and how the AI fallback works, and a small sample dataset. Definition of done: `pip install -r requirements.txt && uvicorn app.main:app --reload`, then upload → select sheet → template → preview → edit → export a `.docx` that opens correctly. Don't mark anything done that isn't actually implemented and runnable.
