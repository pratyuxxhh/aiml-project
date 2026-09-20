from pydantic import BaseModel


class TemplateInfo(BaseModel):
    id: str
    name: str
    description: str
    best_for: str
