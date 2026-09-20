from app.services.normalization_service import make_unique, normalize_column_name


def test_normalize_abbreviation_and_reg_no():
    assert normalize_column_name("C.G.P.A") == "cgpa"
    assert normalize_column_name("Reg No.") == "reg_no"
    assert normalize_column_name("  Package (LPA) ") == "package_lpa"


def test_unique_names():
    assert make_unique(["name", "name", "usn"]) == ["name", "name_2", "usn"]
