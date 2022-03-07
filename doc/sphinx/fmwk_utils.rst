util subpackage
===============

This section summarizes code in the ``src/util`` subpackage, which contains utility 
functions needed at many places in the code.
It's implemented as a package because putting all the code in a single module
would be difficult to navigate. All modules depend on the python standard
library only.

This section is intended to give an introduction and context for the overall
code organization, which might be difficult to gain from the complete docstring
listing at the :doc:`fmwk_autodoc_toc`. In particular, we don't describe every class
or function in detail here. 

Modules in the package
----------------------

\_\_init\_\_.py
^^^^^^^^^^^^^^^

The util package contains a non-trivial ``__init__.py``, describing the "public"
members of each module that are provided when the ``util`` package is imported
as a whole. New classes or functions added to a module in the package should be
listed here in order to be usable outside the package.

:doc:`src.util.basic`
^^^^^^^^^^^^^^^^^^^^^

This module contains implementations of the simplest data structures and utility
functions needed by the framework. In general, code is placed in this module to
avoid the need for circular imports (which can be done safely in python, but
which we avoid.)

:doc:`src.util.dataclass`
^^^^^^^^^^^^^^^^^^^^^^^^^

This module contains extensions to the python standard library's
:py:mod:`dataclasses` and :py:mod:`re` modules. Recall that python dataclasses
provide an alternative syntax for class definition that's most useful in
defining "passive" classes that mainly serve as a container for typed data
fields (hence the name), for example, records of a database. The code in this
module extends this functionality to the use case of instantiating dataclasses
from the results of a regex match on a string: *our* main use case is assembling
a data catalog on the fly by using a regex to parse paths of model data files in
a set directory hierarchy convention.

For a simple example of how the major functionality of this module is used in
the framework, examine the code for :class:`src.cmip6.CMIP6_VariantLabel`. This
class simply parses a variant label of the type used in the CMIP6 conventions:
given a string of the form ``r1i2f3``, return a CMIP6\_VariantLabel object with
``realization_index`` attribute set to ``1``, etc.

Regexes
+++++++

The :class:`~src.util.dataclass.RegexPattern` class extends the functionality of
the standard library's :py:class:`re.Pattern`: it wraps a regex where all
capture groups are named, and provides a dict-like interface to the values
captured by those groups upon a successful match. 

A :class:`~src.util.dataclass.ChainedRegexPattern` is instantiated from multiple
:class:`~src.util.dataclass.RegexPattern`\s: given an input string, it tries
parsing it with each RegexPattern in order, stopping at the first one that
matches successfully. In other words, this is a convenience wrapper for taking
the logical 'or' of the RegexPatterns, which is cumbersome to do at the level of
the regexes themselves.

Dataclasses
+++++++++++

We implement the :func:`src.util.dataclass.mdtf_dataclass` decorator to smooth
over the following rough edges in the standard library implementation of
dataclasses -- otherwise, usage is unchanged from
:py:func:`dataclasses.dataclass`.

- Re-implement checking for mandatory fields. Standard library dataclasses allow
  for both mandatory and optional fields, but the optional fields must be declared
  after the mandatory ones, which breaks when dataclasses inherit from other
  dataclasses (the parent class's fields are declared first in the auto-generated
  ``__init__`` method). 

  Our workaround is to always declare fields as optional (in the context of the
  standard library's dataclass, that we're wrapping) and denote those that are
  meant to be mandatory with a default sentinel value.

- Perform type coercion on instance creation (after the class's ``__init__`` and
  ``__post_init__``). Python is committed to being a weakly ("duck") typed
  language, which won't do for our use case: the field values returned by the
  regex will all be strings, and we want to coerce these to ints, dates, etc.
  using the pre-existing dataclass type annotation syntax.

  The logic for doing so is in
  :func:`~src.util.dataclass._mdtf_dataclass_typecheck`: implementing full type
  awareness (as done by ``mypy`` or similar projects) is far beyond our scope, so
  this only does coercion on the simplest cases that actually arise in practice
  and throws a :class:`~src.util.exceptions.DataclassParseError` if it encounters
  anything it can't understand.

"Regex dataclasses"
+++++++++++++++++++

The regex and dataclass functionalities described above are combined using the
:func:`~src.util.dataclass.regex_dataclass` decorator. Its argument is a
RegexPattern instance, and it decorates a mdtf\_dataclass, and its main function
is to wrap the auto-generated ``__init__`` method to allow the mdtf\_dataclass
to be instantiated from parsing a string using the RegexPattern.

Extra effort is needed to make this work properly under composition (i.e., if
the types of one or more of the fields of the current regex\_dataclass are *also*
regex\_dataclasses.) This is mainly done in
:func:`~src.util.dataclass._regex_dataclass_preprocess_kwargs`: we parse the
constituent regex\_dataclasses in depth-first order, and keep track of their
field assignments in a :class:`~src.util.basic.ConsistentDict` which throws an
exception if we try to alter a previously defined value.

Other functionality
+++++++++++++++++++

Interoperability between standard library dataclasses is cumbersome: e.g. if a
dataclass has a field named ``id``, there's no straightforward way to relate it
to the ``id`` field on a different class, even if one inherits from the other.
We implement two functions for this purpose, which are roughly inverses of each
other.

:func:`~src.util.dataclass.filter_dataclass` returns a dict of the field values
in one dataclass that correspond to fields names that are present in a second
dataclass. :func:`~src.util.dataclass.coerce_to_dataclass` creates an instance
of a given dataclass using field values specified by a second dataclass, or a
dict.


:doc:`src.util.datelabel`
^^^^^^^^^^^^^^^^^^^^^^^^^

This module implements classes for representing the date range of data sets and
the frequency with which they are sampled. As the warnings on the module's
docstring should make clear, this is **not** intended to provide a full
implementation of calendar math. The intended use case is parsing date ranges
given as parts of filenames (hence "datelabel") for the purpose of determining
whether that data falls within the analysis period.

Date ranges and dates
+++++++++++++++++++++

Date ranges are described by the :class:`~src.util.datelabel.DateRange` class.
This stores the two endpoints of the date range as :py:class:`datetime.datetime`
objects, as well as a precision attribute specified by the
:class:`~src.util.datelabel.DatePrecision` enum. DateRanges are always
**closed** intervals; e.g. ``DateRange('1990-1999')`` starts at 0:00 on 1 Jan
1990 and ends at 23:59 on 31 Dec 1999. In all cases, the DateRange is defined to
be the maximal range of dates consistent with the input string (i.e., the
precision with which that string was specified). 

Because we retain precision information, the :class:`~src.util.datelabel.Date`
class is implemented as a DateRange, rather than the other way around; for
example ``DateRange('1990')`` has yearly precision, so it maps to the range of
dates from 0:00 on 1 Jan 1990 to 23:59 on 31 Dec 1990. 

Sampling frequencies
++++++++++++++++++++

The frequency with which data is sampled is represented by the
:class:`~src.util.datelabel.DateFrequency` class, which is essentially a wrapper
for the standard library's :py:class:`datetime.timedelta` that provides string
parsing logic.

Static data
+++++++++++

The module defines :class:`~src.util.datelabel.FXDateRange`,
:class:`~src.util.datelabel.FXDateMin`, :class:`~src.util.datelabel.FXDateMax`
and :class:`~src.util.datelabel.FXDateFrequency` placeholder objects to describe
static data with no time dependence. These are defined at the module level, so
they behave like singletons. Comparisons and logic with normal DateRange, Date
and DateFrequency objects work correctly.

:doc:`src.util.exceptions`
^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to simplify the set of modules imported by other framework modules, all
framework-specific exceptions are defined in this module, regardless of context.
All framework-specific exceptions inherit from
:class:`~src.util.exceptions.MDTFBaseException`.

:doc:`src.util.filesystem`
^^^^^^^^^^^^^^^^^^^^^^^^^^

Functionality that touches the filesystem: path operations, searching for and
loading files (note that the parsing of files is done elsewhere), and (simple)
HTML templating for the :doc:`src.output_manager`. 

:doc:`src.util.logs`
^^^^^^^^^^^^^^^^^^^^

Functionality involving logging configuration and output. Code in this module
extends the functionality of the python standard library :py:mod:`logging`
module, which we use for all user communication during framework operation
(instead of ``print()`` statements). Python's built-in logging facilities are
powerful, going most of the way towards implementing an event-driven programming
paradigm within the language, and not very clearly documented. The `tutorial
<https://docs.python.org/3.7/howto/logging.html#logging-basic-tutorial>`__ is a
must-read.

Configuration
+++++++++++++

In keeping with the framework's philosophy of extensibility, we want to allow
the user to configure logging themselves (e.g., they may want errors raised by
the MDTF package to be reported to a larger workflow engine.) We do this by
simply exposing the logging module's `configuration interface
<https://docs.python.org/3.7/library/logging.config.html>`__ to the user:
specifically, the :py:func:`~logging.config.dictConfig` `schema
<https://docs.python.org/3.7/library/logging.config.html#logging-config-dictschema>`__,
with the contents of the dict serialized as a .jsonc file. We do this rather
than using the :py:func:`~logging.config.fileConfig` interface, because the
latter uses files in .ini format, and we currently use .jsonc for all other
configuration files in the package.

Specifically, the framework looks for logging configuration in a file named
``logging.jsonc``, as part of the :class:`~src.core.MDTFFramework`\'s
``__init__`` method. It first looks in the ``site`` directory specified by the
user; if no file with that name is found, it falls back to the default
configuration in `src/logging.jsonc
<https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/logging.jsonc>`__.
The contents of this file are stored in the :class:`~src.core.ConfigManager` and
actually used to configure the logger by :func:`~src.util.logs.case_log_config`,
which gets called by the ``__init__`` method of
:class:`~src.data_manager.DataSourceBase`.

Caching
+++++++

The configuration strategy described above creates a chicken-and-egg problem, as
we need to be able to log issues that arise before the logger itself has been
configured. We do this with the :class:`~src.util.logs.MultiFlushMemoryHandler`
log handler, which acts as a temporary cache: all logging events prior to
configuration are captured by this handler. Once the "real" handlers have been
configured by :func:`~src.util.logs.case_log_config`, the contents of this
handler are copied ("flushed") to each of them in turn. This handler is set up
in the top-level script, which also calls
:func:`~src.util.logs.configure_console_loggers` to set up conventional
stdout/stderr logging destinations.

Most of the rest of the code in this module deals with formatting and
presentation of logs, e.g. :class:`~src.util.logs.MDTFHeaderFileHandler` which
writes a header with useful debugging information (such as the git commit hash)
to the log file.

:doc:`src.util.processes`
^^^^^^^^^^^^^^^^^^^^^^^^^

Functionality that involves external subprocesses spawned by the framework. This
is the mechanism by which the framework calls all external executables, e.g.
``tar``. We implement two main functions which take the same arguments:
:func:`~src.util.processes.run_shell_command`, for running commands in a shell
environment (e.g. permitting the use of environment variables), and
:func:`~src.util.processes.run_command`, for spawning a subprocess with the
executable directly, without the overhead of starting up a shell. Both of these
are effectively convenience wrappers around the python standard library's
:py:class:`subprocess.Popen`. 

Note that, due to implementation reasons,
:class:`~src.environment_manager.SubprocessRuntimeManager` doesn't call
:func:`~src.util.processes.run_shell_command` but instead implements its own
wrapper.
