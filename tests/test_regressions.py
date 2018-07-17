from modpipe import ModPipe


def test_inconsistent_pipeline():
    pipe = ModPipe('tests.examples.inconsistent_pipeline')
    res = pipe(1)

    assert res == {'computation': 2}
