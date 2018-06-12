=============================
modpipe: modules as pipelines
=============================


.. image:: https://img.shields.io/pypi/v/modpipe.svg
        :target: https://pypi.python.org/pypi/modpipe

.. image:: https://img.shields.io/travis/jbn/modpipe.svg
        :target: https://travis-ci.org/jbn/modpipe

.. image:: https://readthedocs.org/projects/modpipe/badge/?version=latest
        :target: https://modpipe.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


.. image:: https://pyup.io/repos/github/jbn/modpipe/shield.svg
     :target: https://pyup.io/repos/github/jbn/modpipe/
     :alt: Updates

A package that loads a module as a callable pipeline.


Auxillary Functions
-------------------

By default, underscore-prefixed callable do not enter the pipeline. Semantically, they are **auxiliary functions**.

Assert Your Expectations
------------------------

Use assertions liberally for top level code in each module (i.e. pipeline. Changes to expectations should fail loudly at import time. 

.. code-block:: python
   
   def sqrt(x):
       return type(x)(x ** 0.5)
   
   assert sqrt(1764) == 42, "Uh oh!"


Conventions
-----------

* If your function returns ``None``, the pipeline assumes you modified the function arguments *in place* and the next function in the pipeline receives the same function arguments, rather than none.
* If you want to return ``None``, return the ``Done(None)`` from your function. 
* If you process a value and want to skip processing until another function, return ``SkipTo(f2, arg1, arg2)``.

The pipeline is mostly a sequence of function applications. SkipTo makes trivial DAGs easy to implement and hard ones challenging. This is a feature, not a bug. Complicated DAGs makes reasoning about your data challenging. The best solution is to compose near-decomposable pipelines as modules, with custom processing in the joins.

Simplifying assumptions 
-----------------------

I'm sure this is going to bite me in the ass, but if you return a tuple from a function and that tuple's size matches the arity of the next function in the pipeline, it does ``f(*res)``. Otherwise, it does f(res). Keyword arguments don't work. 

Misc
----

I think this was inspired by PyMC3.
