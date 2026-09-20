from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Inches, Pt, RGBColor

from app.errors import AppError
from app.models.document import DocumentSection, DocumentSpecification


def write_docx(spec: DocumentSpecification, output_path: Path) -> Path:
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        document = Document()
        _apply_page_setup(document, spec)
        _set_run_font_defaults(document, spec.font_size)

        for section in spec.sections:
            _render_section(document, section, spec.font_size)

        _add_footer(document, spec.title)
        document.save(str(output_path))
        return output_path
    except AppError:
        raise
    except Exception as exc:
        raise AppError(f"Failed to write DOCX: {exc}", status_code=500) from exc


def _apply_page_setup(document: Document, spec: DocumentSpecification) -> None:
    section = document.sections[0]
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.9)
    section.top_margin = Inches(0.9)
    section.bottom_margin = Inches(0.9)
    if spec.orientation == "landscape":
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width, section.page_height = section.page_height, section.page_width


def _set_run_font_defaults(document: Document, font_size: int) -> None:
    style = document.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(font_size)
    style.font.color.rgb = RGBColor(0x22, 0x22, 0x22)


def _render_section(document: Document, section: DocumentSection, font_size: int) -> None:
    if section.type == "heading":
        paragraph = document.add_heading(section.text or "", level=min(max(section.level, 1), 3))
        for run in paragraph.runs:
            run.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)
        return
    if section.type == "paragraph":
        paragraph = document.add_paragraph(section.text or "")
        paragraph.paragraph_format.space_after = Pt(10)
        return
    if section.type == "summary":
        if not section.items:
            return
        table = document.add_table(rows=1, cols=len(section.items))
        _shade_header(table.rows[0])
        for i, item in enumerate(section.items):
            cell = table.rows[0].cells[i]
            cell.text = f"{item.label}: {item.value}"
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.bold = True
                    run.font.size = Pt(font_size)
        document.add_paragraph("")
        return
    if section.type == "table":
        _add_data_table(document, section, font_size)
        return
    if section.type == "cards":
        for card in section.cards:
            heading = document.add_heading(card.title, level=3)
            for run in heading.runs:
                run.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)
            if card.fields:
                table = document.add_table(rows=len(card.fields), cols=2)
                table.style = "Table Grid"
                for i, field in enumerate(card.fields):
                    table.rows[i].cells[0].text = field.label
                    table.rows[i].cells[1].text = field.value
                    for run in table.rows[i].cells[0].paragraphs[0].runs:
                        run.bold = True
            document.add_paragraph("")


def _add_data_table(document: Document, section: DocumentSection, font_size: int) -> None:
    cols = max(len(section.headers), 1)
    table = document.add_table(rows=1 + len(section.rows), cols=cols)
    table.style = "Table Grid"
    header_row = table.rows[0]
    _shade_header(header_row)
    for i, header in enumerate(section.headers):
        cell = header_row.cells[i]
        cell.text = header
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
                run.font.size = Pt(font_size)
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for r, row in enumerate(section.rows, start=1):
        for c in range(cols):
            value = row[c] if c < len(row) else ""
            table.rows[r].cells[c].text = value
            for paragraph in table.rows[r].cells[c].paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(max(font_size - 1, 8))


def _shade_header(row) -> None:
    for cell in row.cells:
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), "1A365D")
        shading.set(qn("w:val"), "clear")
        cell._tc.get_or_add_tcPr().append(shading)


def _add_footer(document: Document, title: str) -> None:
    footer = document.sections[0].footer
    paragraph = footer.paragraphs[0]
    paragraph.text = title
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = paragraph.add_run("  |  Generated by Excel → Word")
    run.italic = True
