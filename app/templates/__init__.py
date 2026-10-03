from app.templates.academic_marksheet import build_academic_marksheet
from app.templates.attendance_register import build_attendance_register
from app.templates.generic_table import build_generic_table
from app.templates.professional_report import build_professional_report
from app.templates.placement_summary import build_placement_summary
from app.templates.profile_cards import build_profile_cards

TEMPLATE_BUILDERS = {
    "academic_marksheet": build_academic_marksheet,
    "attendance_register": build_attendance_register,
    "generic_table": build_generic_table,
    "professional_report": build_professional_report,
    "placement_summary": build_placement_summary,
    "profile_cards": build_profile_cards,
}

__all__ = ["TEMPLATE_BUILDERS"]
