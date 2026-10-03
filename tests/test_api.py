from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

SAMPLE = Path(__file__).resolve().parents[1] / "sample" / "placement.csv"
client = TestClient(app, raise_server_exceptions=False)


def test_upload_preview_export_flow():
    with SAMPLE.open("rb") as handle:
        res = client.post("/upload", files={"file": ("placement.csv", handle, "text/csv")})
    assert res.status_code == 200, res.text
    body = res.json()
    dataset_id = body["id"]
    assert body["dataset"]["row_count"] == 3
    assert body["analysis"]["source"] == "deterministic"

    templates = client.get("/templates")
    assert templates.status_code == 200
    ids = {t["id"] for t in templates.json()["templates"]}
    assert ids == {
        "generic_table",
        "professional_report",
        "profile_cards",
        "placement_summary",
        "academic_marksheet",
        "attendance_register",
    }

    preview = client.post(
        "/documents/preview",
        json={
            "dataset_id": dataset_id,
            "template": "generic_table",
            "edits": {"title": "Demo", "show_summary": True},
        },
    )
    assert preview.status_code == 200
    assert "Demo" in preview.json()["html"]

    exported = client.post(
        "/documents/export",
        json={"dataset_id": dataset_id, "template": "generic_table", "edits": {"title": "Demo"}},
    )
    assert exported.status_code == 200
    file_id = exported.json()["id"]
    download = client.get(f"/files/{file_id}")
    assert download.status_code == 200
    assert download.content[:2] == b"PK"


def test_invalid_file_type():
    res = client.post("/upload", files={"file": ("x.txt", b"hello", "text/plain")})
    assert res.status_code == 400
    assert "Unsupported" in res.json()["error"]
