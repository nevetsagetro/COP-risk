from cop.evaluation.home_credit import HOME_CREDIT_SEARCH_SPACE


def test_home_credit_search_space_has_reproducible_trials() -> None:
    assert set(HOME_CREDIT_SEARCH_SPACE) == {"logistic_regression", "lightgbm"}
    assert len(HOME_CREDIT_SEARCH_SPACE["logistic_regression"]) == 3
    assert len(HOME_CREDIT_SEARCH_SPACE["lightgbm"]) == 3
