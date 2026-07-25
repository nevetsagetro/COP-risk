"""Smoke tests for the package scaffold."""


def test_cop_can_be_imported() -> None:
    """The source package is discoverable in the development environment."""
    import cop

    assert cop.__name__ == "cop"
