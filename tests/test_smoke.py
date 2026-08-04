"""Smoke tests for olink package."""


def test_smoke() -> None:
    """Test that the package can be imported."""
    import olink

    assert olink is not None
