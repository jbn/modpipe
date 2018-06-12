import pytest

from modpipe import ModPipe


@pytest.fixture
def math_pipeline():
    return ModPipe('tests.math_mod')


def test_visit_all_elements(math_pipeline):
    assert math_pipeline(0, 1) == (10, 0)


def test_done_on_zero_vector(math_pipeline):
    assert math_pipeline(0, 0) == (0, 0)


def test_skip_to_on_42(math_pipeline):
    assert math_pipeline(42, 42) == (420, 420)


def test_abort_on_complex(math_pipeline):
    assert math_pipeline(1j, 1j) is None


def test_del(math_pipeline):
    del math_pipeline['normed']
    assert math_pipeline(1, 1) == (10, -10)
