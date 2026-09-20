from app.templates.generic_table import build_generic_table
from app.templates.professional_report import build_professional_report
from app.templates.profile_cards import build_profile_cards

TEMPLATE_BUILDERS = {
    "generic_table": build_generic_table,
    "professional_report": build_professional_report,
    "profile_cards": build_profile_cards,
}

__all__ = ["TEMPLATE_BUILDERS"]
