.. image:: https://img.shields.io/pypi/v/modpipe.svg
        :target: https://pypi.python.org/pypi/modpipe
.. image:: https://img.shields.io/travis/jbn/modpipe.svg
        :target: https://travis-ci.org/jbn/modpipe
.. image:: https://ci.appveyor.com/api/projects/status/21l6df8evjepq41s?svg=true 
        :target: https://ci.appveyor.com/project/jbn/modpipe/branch/master 
.. image:: https://coveralls.io/repos/github/jbn/modpipe/badge.svg?branch=master
        :target: https://coveralls.io/github/jbn/modpipe?branch=master


=============================
modpipe: modules as pipelines
=============================

--------------
What is this?
--------------

An opinionated package that loads a module as a callable pipeline.

-------------
Why is this?
-------------

Very frequently, I interactively write data transformations in 
`Jupyter <https://jupyter.org/>`_; then, once it works as (initially) expected,
I move it to *some* module. Recognizing that pattern, this package makes using 
modules as pipelines (esp. in the context of ETL) easier. 

------------------------
Can I see an example?
------------------------

Assume you have a set of raw items (probably deserialized objects) that you
want to transform into clean ones. You accumulate your transformation functions
in ``ingest_pipeline.py``. When the following code runs,

.. code-block:: python
   
   import modpipe

   with modpipe.ModPipe.on('ingest_pipeline') as f:
       clean_items = [f(item) for item in raw_items]

it automatically re/loads the ``ingest_pipeline`` module, sythesizing a 
composition ordered by source code line position. That's a mouth full. 
Concretely, say you have the following in ``ingest_pipeline.py``,

.. code-block:: python
   
   def twice(x):
       return x * 2

   def weird_pair(x):
       return x, -x

Calling ``f`` -- an instance of ``ModPipe`` -- works as if it were defined as,

.. code-block:: python
   
   def f(x):
       return weird_pair(twice(x))

----------
So What?
----------

If you do a painful amount of ETL work, this might strike you as useful. 
If you don't, you might be saying, "so what?" Unfortunately, I think this 
doesn't communicate well without a developer-in-motion screencast (XXX: TODO).
But, for now, I'll lean on the concluding line in Tim Peter's wonderful 
`PEP20 <https://www.python.org/dev/peps/pep-0020/PEP20>`_,

    Namespaces are one honking great idea -- let's do more of those!

By moving transformational code into modules, you free up notebook 
(and cognitive space) for subsequent steps. If you spend a little time 
properly naming the module, it's somewhat easy to navigate. If you 
partition your transformation code into different logical units, it's somewhat
robust. And, if you pepper your pipeline module code with assertions, it 
documents your expectations for the data. 

Everyone wants to write ETL code the same way that they would write other code: 
carefully and with a good test suite. But, realistically, we don't do 
that because of various constraints. Plus, it's *really* tedious code. 
This package (and, the one I extracted it from, 
`vaquero <https://github.com/jbn/vaquero>`_) recognizes your competing 
demands and the reality of the task, and works with you.


----------------------
How is it opinionated?
----------------------

~~~~~~~~~~~~~~~~~~~
Auxillary Functions
~~~~~~~~~~~~~~~~~~~

By default, underscore-prefixed callables do not enter in the pipeline. 
By assumption, these callables are **auxillary functions** used by the 
ones you really want in the linearized pipeline.

.. code-block:: python
   
   def _encode_as_binary(x):  # Not in pipeline by default!
       return bin(x)[2:].rjust(32, '0')

   def convert_seeds(seeds):
       return [_encode_as_binary(seed) for seed in seeds]

~~~~~~~~~~~~~~~~~~~~~~~~
Assert Your Expectations
~~~~~~~~~~~~~~~~~~~~~~~~

As mentioned above, unit-testing ETL code is a pain. And, since dirty data 
violate expectations near-continously, it seriously impedes progress. 
Rather than relying upon unit tests for the transformation functions, 
it's easier to write in-line (in the context of the module) assertions 
that document your assumptions and guard against inadvertent regressions 
by failing loudly at re/import time. 

The following (contrived) example ensures that your pipeline's sqrt function
properly computes the square root and returns the result in the same
numeric type as given.

.. code-block:: python
   
   def sqrt(x):
       return type(x)(x ** 0.5)
   
   assert sqrt(1776) == 42, "Uh oh!"  # Fails loudly if bad code!


~~~~~~~~~~~~~~~~~~
DAGS are Confusing
~~~~~~~~~~~~~~~~~~

Directed Acyclic Graphs (DAGs) are greate when computers construct 
them for you. But, in lots of contexts, they make it hard to reason 
about what your code is doing when it fails. For the most part, the 
pipeline is a linearized composition of the functions in your module. 
Thus, if the function on line 85 raises an exception when used, you 
know that only the functions above have already executed. This is a 
surprisingly useful cognitive device, especially when you step way 
from your code for six months and visit it again only when it 
becomes a problem.

But, there are two exception to this simple linearization. Sometimes, 
it is necessary to either: 1) abort the pipeline early or 2) skip 
over some of the functions. This package provides a sentinel return 
value for both cases.


.. code-block:: python
    
   from lxml.html import fromstring
   from modpipe import SkipTo, Done

   def extract_doc(raw_html):
       if raw_html.strip():
           return {'doc': fromstring(raw_html)}
       else:
           return Done(None)  # Nothing can be done! Abort!

   def extract_title(d):
       for title in d['doc'].xpath("//title/text()"):
           d['title'] = title

       if 'error' in d['title'].lower():
           return SkipTo(cleanup, d)  # Skip to cleanup!
       else:
           return d

   def extract_headers(d):
        d['headers'] = d['doc'].xpath('//h1/text()')

   def cleanup(d):
        del d['doc']


~~~~~~~~~~~~~~
Returning None
~~~~~~~~~~~~~~

In the prior code listing, ``extract_headers`` and ``cleanup`` did in-place 
transformations on the passed dict. To cut down on LoC while communicating 
mutation, neither returned a value. There are pros on cons to this style. 
But, in any case, ``modpipe`` handles it by assuming the given arguments to a 
function that returns ``None`` should be passed to the next function in the 
pipe. Thus, cleanup receives ``d``.

This begs the question: if you want to return None, how do you do so? In 
this case, you need to return a ``Result``. For example,

.. code-block:: python
   
   from modpipe import Result
    
   def f(s):
       tok = s.upper().strip()
       return tok if tok else Result(None)  # or Done(None)


~~~~~~~~~~~~~~~~~~
Tuples are special
~~~~~~~~~~~~~~~~~~

If you return a tuple from a function and that tuple's length matches 
the arity of the next function in the pipeline, modpipe star-expands
it when calling the next function, otherwise, it does f(res). 

.. code-block:: python
   
   def f(x):
       return x, -x  # i.e. add(x, -x)

   def g(x, y):
       return x + y, x * y  # i.e. h(x + y, x * y)

   def h(items):
       return sum(items)

This works for tuples and tuples alone. (That is, if you returned a list, it 
always passes the whole list as an argument.) You'll note that the call 
structure doesn't allow for keyword arguments. I've tried working around this 
but I didn't find anything that wasn't intrusive. 

~~~~~~~~~~~~~~~~~~~~~~~
Is there anything else?
~~~~~~~~~~~~~~~~~~~~~~~

Yes. Pipelines in ``modpipe`` are very 
`pyspark <https://spark.apache.org/docs/2.2.0/api/python/pyspark.html>`_ 
friendly. Although the Spark team doesn't recommend using RDDs anymore, 
Spark is useful for writing ETL pipelines. But, python object serialization 
and deserialization adds a lot of expense to chains of transformations in 
pyspark proper (i.e. ``map`` on RDDs). If you collect your 
transformations into logical units serialized as modules, it amortizes the 
pickling-related expenses. It won't be scala speed, but at least you can 
take advantage of already existing infrastructure in a somewhat more 
performant manner.


~~~~
Misc
~~~~

I think I got this idea from `PyMC3 <https://docs.pymc.io/>`_. For the major 
version bump, lots of examples started using modules and I thought it was 
annoying at first. Then I realized how nice it can be. Since modeling and 
ETL tend to go hand-to-hand (albeit in a 1:99 ratio), I started writing my 
ETL code in the same way. I'm sure I'm not the first to do so, but I hadn't 
seen it before. (It's probably just one of those things that lots of people 
do naturally without writing up.)

I also wanted to point out `bonobo <https://github.com/python-bonobo/bonobo>`_. 
It's a lot more mature and flexible. According to the docs,

    Bonobo is a young rewrite of an old python2.7 tool that ran millions of 
    transformations per day for years on production. Although it may not 
    yet be complete or fully stable (please, allow us to reach 1.0), 
    the basics are there.

Still, for 90% of projects, vaquero (which uses modpipe) suits me better.
