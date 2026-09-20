from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models.document import DocumentSpecification

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "web" / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_preview_html(spec: DocumentSpecification) -> str:
    template = _env.get_template("preview.html")
    return template.render(spec=spec)
