from cop.training.deep_learning import MLP_ARCHITECTURE, mlp_parameter_count


def test_mlp_parameter_count_matches_declared_architecture() -> None:
    assert MLP_ARCHITECTURE == (128, 64)
    assert mlp_parameter_count(10) == (10 + 1) * 128 + (128 + 1) * 64 + 65
