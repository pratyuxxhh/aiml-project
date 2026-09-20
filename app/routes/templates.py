from fastapi import APIRouter

from app.services.template_service import list_templates

router = APIRouter()


@router.get("/templates")
def get_templates():
    return {"templates": [t.model_dump() for t in list_templates()]}
