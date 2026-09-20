from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.errors import register_error_handlers
from app.routes import documents, templates, upload

WEB_DIR = Path(__file__).resolve().parent / "web"

app = FastAPI(title="Excel/CSV → Word Document Generator", version="0.1.0")
register_error_handlers(app)

app.include_router(upload.router)
app.include_router(templates.router)
app.include_router(documents.router)

app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "templates" / "index.html")
