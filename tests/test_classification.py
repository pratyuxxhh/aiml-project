from app.services.classification_service import classify_column, classify_columns


def test_deterministic_student_placement_classification():
    result = classify_columns(["Name", "USN", "CGPA", "Package"])
    assert result.source == "deterministic"
    assert result.column_mapping == {
        "Name": "person_name",
        "USN": "student_id",
        "CGPA": "academic_score",
        "Package": "salary_package",
    }
    assert result.dataset_type == "student_placement"
    assert result.recommended_templates[0] == "professional_report"


def test_generic_and_people_records_rules_are_offline_and_stable():
    result = classify_columns(["Customer Name", "Email"])
    assert result.dataset_type == "people_records"
    assert result.column_mapping["Customer Name"] == "person_name"
    assert result.column_mapping["Email"] == "generic"
    assert classify_column("Filename") == "generic"
