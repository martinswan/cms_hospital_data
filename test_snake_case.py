from download_cms_hospitals_data_sets import to_snake_case

def test_prompt_example():
    assert (
        to_snake_case("Patients’ rating of the facility linear mean score")
        == "patients_rating_of_the_facility_linear_mean_score"
    )


def test_straight_apostrophe_removed():
    assert to_snake_case("Hospital's Rating") == "hospitals_rating"


def test_simple_mixed_case():
    assert to_snake_case("Facility ID") == "facility_id"


def test_extra_spaces_collapse():
    assert to_snake_case("  Hospital   Name  ") == "hospital_name"


def test_percent_replacement():
    assert to_snake_case("Score (%)") == "score_percent"


def test_hash_replacement():
    assert to_snake_case("Score (#)") == "score_num"


def test_hyphens_and_slashes():
    assert to_snake_case("Start-Date/End Date") == "start_date_end_date"


def test_numbers_kept():
    assert to_snake_case("Measure 1 Score") == "measure_1_score"


def test_already_snake_case_unchanged():
    assert to_snake_case("facility_id") == "facility_id"


def test_ampersand_replacement():
    assert to_snake_case("Q & A") == "q_and_a"


def test_custom_replacements_override_default():
    assert to_snake_case("Q&A", replacements={}) == "q_a"
