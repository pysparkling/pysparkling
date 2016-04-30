.. image:: https://raw.githubusercontent.com/svenkreiss/pysparkling/master/logo/logo-w100.png
    :target: https://github.com/svenkreiss/pysparkling

**Pysparkling** provides a faster, more responsive way to develop programs
for PySpark. It enables code intended for Spark applications to execute
entirely in Python, without incurring the overhead of initializing and
passing data through the JVM and Hadoop. The focus is on having a lightweight
and fast implementation for small datasets at the expense of some data
resilience features and some parallel processing features.

**How does it work?** To switch execution of a script from PySpark to pysparkling,
have the code initialize a pysparkling Context instead of a SparkContext, and
use the pysparkling Context to set up your RDDs. The beauty is you don't have
to change a single line of code after the Context initialization, because
pysparkling's API is (almost) exactly the same as PySpark's. Since it's so easy
to switch between PySpark and pysparkling, you can choose the right tool for your
use case.

**When would I use it?** Say you are writing a Spark application because you
need robust computation on huge datasets, but you also want the same application
to provide fast answers on a small dataset. You're finding Spark is not responsive
enough for your needs, but you don't want to rewrite an entire separate application
for the *small-answers-fast* problem. You'd rather reuse your Spark code but somehow
get it to run fast. Pysparkling bypasses the stuff that causes Spark's long startup
times and less responsive feel.

Here are a few areas where pysparkling excels:

- Small to medium-scale exploratory data analysis
- Application prototyping
- Low-latency web deployments
- Unit tests

*Example:* you have a pipeline that processes 100k input documents
and converts them to normalized features. They are used to train a local
scikit-learn classifier. The preprocessing is perfect for a full Spark
task. Now, you want to use this trained classifier in an API
endpoint. Assume you need the same pre-processing pipeline for a single
document per API call. This does not have to be done in parallel, but there
should be only a small overhead in initialization and preferably no
dependency on the JVM. This is what ``pysparkling`` is for.

.. image:: https://badge.fury.io/py/pysparkling.svg
    :target: https://pypi.python.org/pypi/pysparkling/
.. image:: https://img.shields.io/pypi/dm/pysparkling.svg
    :target: https://pypi.python.org/pypi/pysparkling/
.. image:: https://badges.gitter.im/Join%20Chat.svg
   :alt: Join the chat at https://gitter.im/svenkreiss/pysparkling
   :target: https://gitter.im/svenkreiss/pysparkling?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge


Install
=======

.. code-block:: bash

  pip install pysparkling


Features
========

* Supports URI schemes ``s3://``, ``hdfs://``, ``gs://``, ``http://`` and ``file://``
  for Amazon S3, HDFS, Google Storage, web and local file access.
  Specify multiple files separated by comma.
  Resolves ``*`` and ``?`` wildcards.
* Handles ``.gz``, ``.zip``, ``.lzma``, ``.xz``, ``.bz2``, ``.tar``,
  ``.tar.gz`` and ``.tar.bz2`` compressed files.
  Supports reading of ``.7z`` files.
* Parallelization via ``multiprocessing.Pool``,
  ``concurrent.futures.ThreadPoolExecutor`` or any other Pool-like
  objects that have a ``map(func, iterable)`` method.
* Plain pysparkling does not have any dependencies (use ``pip install pysparkling``).
  Some file access methods have optional dependencies:
  ``boto`` for AWS S3, ``requests`` for http, ``hdfs`` for hdfs


Examples
========

Some demos are in the notebooks
`docs/demo.ipynb <https://github.com/svenkreiss/pysparkling/blob/master/docs/demo.ipynb>`_
and
`docs/iris.ipynb <https://github.com/svenkreiss/pysparkling/blob/master/docs/iris.ipynb>`_
.

**Word Count**

.. code-block:: python

    from pysparkling import Context

    counts = Context().textFile(
        'README.rst'
    ).map(
        lambda line: ''.join(ch if ch.isalnum() else ' ' for ch in line)
    ).flatMap(
        lambda line: line.split(' ')
    ).map(
        lambda word: (word, 1)
    ).reduceByKey(
        lambda a, b: a + b
    )
    print(counts.collect())

which prints a long list of pairs of words and their counts.


API
===

A usual ``pysparkling`` session starts with either parallelizing a ``list`` or
by reading data from a file using the methods ``Context.parallelize(my_list)``
or ``Context.textFile("path/to/textfile.txt")``. These two methods return an
``RDD`` which can then be processed with the methods below.


RDD
---

*API doc*: http://pysparkling.trivial.io/v0.3/api.html#pysparkling.RDD


Context
-------

A ``Context`` describes the setup. Instantiating a Context with the default
arguments using ``Context()`` is the most lightweight setup. All data is just
in the local thread and is never serialized or deserialized.

If you want to process the data in parallel, you can use the ``multiprocessing``
module. Given the limitations of the default ``pickle`` serializer, you can
specify to serialize all methods with ``cloudpickle`` instead. For example,
a common instantiation with ``multiprocessing`` looks like this:

.. code-block:: python

  c = Context(
      multiprocessing.Pool(4),
      serializer=cloudpickle.dumps,
      deserializer=pickle.loads,
  )

This assumes that your data is serializable with ``pickle`` which is generally
faster. You can also specify a custom serializer/deserializer for data.

*API doc*: http://pysparkling.trivial.io/v0.3/api.html#pysparkling.Context


fileio
------

The functionality provided by this module is used in ``Context.textFile()``
for reading and in ``RDD.saveAsTextFile()`` for writing. You can use this
submodule for writing files directly with ``File(filename).dump(some_data)``,
``File(filename).load()`` and ``File.exists(path)`` to read, write and check
for existance of a file. All methods transparently handle ``http://``, ``s3://``
and ``file://`` locations and compression/decompression of ``.gz`` and
``.bz2`` files.

Use environment variables ``AWS_SECRET_ACCESS_KEY`` and ``AWS_ACCESS_KEY_ID``
for auth and use file paths of the form ``s3://bucket_name/filename.txt``.

*API doc*: http://pysparkling.trivial.io/v0.3/api.html#pysparkling.fileio.File
