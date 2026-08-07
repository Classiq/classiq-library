import pytest


def test_qft_simulation_imports():
    """Test that basic imports work."""
    try:
        import numpy
        import scipy
        import classiq

        assert True
    except ImportError:
        pytest.fail("Required packages not installed")
