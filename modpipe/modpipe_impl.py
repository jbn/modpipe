from importlib import import_module
from inspect import getfile
from importlib import reload
from types import ModuleType

from modpipe.results import Result, Done, SkipTo
from modpipe.helpers import compile_signatures, load_pipeline_seq


class ModPipe:

    @classmethod
    def on(cls, module_dot_path, unif_sigs=False, ignore_names=True):
        """

        :param module: The module to turn into a pipe, as a fully
            qualified name or a module instance.
        :param unif_sigs: if True, then enforce the expectation that
            every callable in the pipeline has the same signature
        :param ignore_names: if True, then enforce the expectation that
            every callable in the pipeline has the same signature,
            including argument names.
        :return: an instantiated ModPipe
        """
        return ModPipe(module_dot_path, unif_sigs, ignore_names)

    def __init__(self, module, unif_sigs=False, ignore_names=True):
        if isinstance(module, ModuleType):
            module = module.__name__

        self._module_dot_path = module
        self._unif_sigs = unif_sigs
        self._ignore_names = ignore_names

        self.reload()

    @property
    def module_name(self):
        return self._module_name

    @property
    def abs_module_path(self):
        return self._module_path

    def reload(self):
        """
        Reloads the module and all pipeline elements.
        """
        # Don't save a ref to module. It's not picklable.
        module = reload(import_module(self._module_dot_path))
        self._module_name = module.__name__
        self._module_path = getfile(module)
        self._pipeline = load_pipeline_seq(module)

        assert len(self._pipeline) > 0, "No elements in pipeline."

        self._signatures = compile_signatures(self._pipeline,
                                              self._unif_sigs,
                                              self._ignore_names)
        self._expected_args = {k: len(sig.parameters)
                               for k, sig in self._signatures.items()}

    def __delitem__(self, k):
        f = self._pipeline[k]
        del self._pipeline[k]
        del self._signatures[f]
        del self._expected_args[f]

    def __getitem__(self, k):
        return self._pipeline[k]

    def _ipython_key_completions_(self):
        return list(self._pipeline.keys())

    def __repr__(self):
        return "ModPipe({})".format(self._module_name)

    def __enter__(self):
        self.reload()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        return False   # Don't swallow.

    def __call__(self, *args):
        res = Result(args)

        for k, f in self._pipeline.items():

            res = res.apply_to(f, self._expected_args[f])

            if isinstance(res, Done):
                break

        if isinstance(res, SkipTo):
            target_name = res.target_f.__name__
            msg = "Pipeline ended before encountering {}".format(target_name)
            raise RuntimeError(msg)

        return res.args
