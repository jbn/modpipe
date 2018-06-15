import pytest
from modpipe import ModPipe


def test_intro_example():
    raw_items = [1, 2, 3]
    expected = [(2, -2), (4, -4), (6, -6)]

    with ModPipe.on('tests.examples.ingest_pipeline') as f:
        clean_items = [f(item) for item in raw_items]
    assert clean_items == expected


def test_auxillary_function_example():
    seeds = [42, 0xbeef]
    expected = ['00000000000000000000000000101010',
                '00000000000000001011111011101111']

    with ModPipe.on('tests.examples.aux_pipeline') as f:
        res = f(seeds)
    assert res == expected


def test_assertions_at_import_time():
    with pytest.raises(AssertionError):
        with ModPipe.on('tests.examples.asserting_pipeline'):
            pass


def test_result_none_returns_none():
    with ModPipe.on('tests.examples.none_pipeline') as f:
        assert f('hello') == 'HELLO'
        assert f('') is None


def test_tuples_are_special():
    with ModPipe.on('tests.examples.tuples_pipeline', unif_sigs=False) as f:
        assert f(10) == -100
