import os
import pytest
import pickle

from modpipe import ModPipe


@pytest.fixture
def math_pipeline():
    return ModPipe('tests.examples.math_mod')


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


def test_name(math_pipeline):
    assert math_pipeline.module_name == 'tests.examples.math_mod'


def test_abs_module_path(math_pipeline):
    def stripped_pyc(s):
        return s[:-1] if s.lower().endswith(".pyc") else s
    dir_path = os.path.dirname(os.path.realpath(__file__))
    expected_path = os.path.join(dir_path, "examples", "math_mod.py")
    assert stripped_pyc(math_pipeline.abs_module_path) == expected_path


def test_is_picklable(math_pipeline):
    pickle.dumps(math_pipeline)
