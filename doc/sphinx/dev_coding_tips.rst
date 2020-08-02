Coding best practices: avoiding common issues
=============================================

In this section we describe issues we've seen in POD code that have caused problems in the form of bugs, inefficiencies, or unintended consequences.

All languages
-------------

- **PS vs. EPS figures**: Save vector plots as .eps (Encapsulated PostScript), not .ps (regular PostScript).

  *Why*: Postscript (.ps) is perhaps the most common vector graphics format, and almost all plotting packages are able to output postscript files. `Encapsulated Postscript <https://en.wikipedia.org/wiki/Encapsulated_PostScript>`__ (.eps) includes bounding box information that describes the physical extent of the plot's contents. This is used by the framework to generate bitmap versions of the plots correctly: the framework calls `ghostscript <https://www.ghostscript.com/>`__ for the conversion, and if not provided with a bounding box ghostscript assumes the graphics use an entire sheet of (letter or A4) paper. This can cause plots to be cut off if they extend outside of this region.

  Note that many plotting libraries will set the format of the output file automatically from the filename extension. The framework will process both `*.ps` and `*.eps` files.

Python: General
----------------

- **Whitespace**: Indent python code with four spaces per indent level.

  *Why*: Python uses indentation to delineate nesting and scope within a program, and intentation that's not done consistently is a syntax error. Using four spaces is not required, but is the generally accepted standard.

  Indentation can be configured in most text editors, or fixed with scripts such as ``reindent.py`` described `here <https://stackoverflow.com/q/1024435>`__. We recommend using a `linter <https://books.agiliq.com/projects/essential-python-tools/en/latest/linters.html>`__ such as ``pylint`` to find common bugs and syntax errors.

  Beyond this, we don't impose requirements on how your code is formatted, but voluntarily following standard best practices (such as descriped in `PEP8 <https://www.python.org/dev/peps/pep-0008/>`__ or the Google `style guide <https://github.com/google/styleguide/blob/gh-pages/pyguide.md>`__\) will make it easier for you and others to understand your code, find bugs, etc.


- **Filesystem commands**: Use commands in the `os <https://docs.python.org/3.7/library/os.html>`__ and `shutil <https://docs.python.org/3.7/library/shutil.html>`__ modules to interact with the filesystem, instead of running unix commands using ``os.system()``, ``commands`` (which is deprecated), or ``subprocess``.

  *Why*: Hard-coding unix commands makes code less portable. Calling out to a subprocess introduces overhead and makes error handling and logging more difficult. The main reason, however, is that Python already provides these tools in a portable way. Please see the documentation for the `os <https://docs.python.org/3.7/library/os.html>`__ and `shutil <https://docs.python.org/3.7/library/shutil.html>`__ modules, summarized in this table:

  .. list-table:: Recommended python functions for filesystem interaction
     :header-rows: 1

     * - Task
       - Recommended function
     * - Construct a path from *dir1*, *dir2*, ..., *filename*
       - `os.path.join <https://docs.python.org/3.7/library/os.path.html?highlight=os%20path#os.path.join>`__\(*dir1*, *dir2*, ..., *filename*)
     * - Split a *path* into directory and filename
       - `os.path.split <https://docs.python.org/3.7/library/os.path.html?highlight=os%20path#os.path.split>`__\(*path*) and related functions in `os.path <https://docs.python.org/3.7/library/os.path.html?highlight=os%20path>`__
     * - List files in directory *dir*
       - `os.scandir <https://docs.python.org/3.7/library/os.html#os.scandir>`__\(*dir*)
     * - Move or rename a file or directory from *old_path* to *new_path*
       - `shutil.move <https://docs.python.org/3.7/library/shutil.html#shutil.move>`__\(*old_path*, *new_path*)
     * - Create a directory or sequence of directories *dir*
       - `os.makedirs <https://docs.python.org/3.7/library/os.html#os.makedirs>`__\(*dir*)
     * - Copy a file from *path* to *new_path*
       - `shutil.copy2 <https://docs.python.org/3.7/library/shutil.html#shutil.copy2>`__\(*path*, *new_path*)
     * - Copy a directory *dir*, and everything inside it, to *new_dir*
       - `shutil.copytree <https://docs.python.org/3.7/library/shutil.html#shutil.copytree>`__\(*dir*, *new_dir*)
     * - Delete a single file at *path*
       - `os.remove <https://docs.python.org/3.7/library/os.html#os.remove>`__\(*path*)
     * - Delete a directory *dir* and everything inside it
       - `shutil.rmtree <https://docs.python.org/3.7/library/shutil.html#shutil.rmtree>`__\(*dir*)

  In particular, using `os.path.join <https://docs.python.org/3.7/library/os.path.html?highlight=os%20path#os.path.join>`__ is more verbose than joining strings but eliminates bugs arising from missing or redundant directory separators.

Python: Arrays
--------------

To obtain acceptable performance for numerical computation, people use Python interfaces to optimized, compiled code. `NumPy <https://numpy.org/doc/stable/index.html>`__ is the standard module for manipulating numerical arrays in Python. `xarray <http://xarray.pydata.org/en/stable/index.html>`__ sits on top of NumPy and provides a higher-level interface to its functionality; any advice about NumPy applies to it as well.

NumPy and xarray both have extensive documentation and many tutorials, such as:

  + NumPy's own `basic <https://numpy.org/doc/stable/user/absolute_beginners.html>`__ and `intermediate <https://numpy.org/doc/stable/user/quickstart.html>`__ tutorials; xarray's `overview <http://xarray.pydata.org/en/stable/quick-overview.html>`__ and climate and weather `examples <http://xarray.pydata.org/en/stable/examples.html>`__;
  + A `demonstration <https://rabernat.github.io/research_computing/xarray.html>`__ of the features of xarray using earth science data;
  + The 2020 SciPy conference has open-source, interactive `tutorials <https://www.scipy2020.scipy.org/tutorial-information>`__ you can work through on your own machine or fully online using `Binder <https://mybinder.org/>`__. In particular, there are tutorials for `NumPy <https://github.com/enthought/Numpy-Tutorial-SciPyConf-2020>`__ and `xarray <https://xarray-contrib.github.io/xarray-tutorial/index.html>`__.

- **Eliminate explicit for loops**: Use NumPy/xarray functions instead of writing for loops in Python that loop over the indices of your data array. In particular, nested for loops on multidimensional data should never need to be used.

  *Why*: For loops in Python are very slow compared to C or Fortran, because Python is an interpreted language. You can think of the NumPy functions as someone writing those for-loops for you in C, and giving you a way to call it as a Python function.

  It's beyond the scope of this document to cover all possible situations, since this is the main use case for NumPy. We refer to the tutorials above for instructions, and to the following blog posts that discuss this specific issue:

  + "`Look Ma, no for-loops <https://realpython.com/numpy-array-programming/>`__," by Brad Solomon;
  + "`Turn your conditional loops to Numpy vectors <https://towardsdatascience.com/data-science-with-python-turn-your-conditional-loops-to-numpy-vectors-9484ff9c622e>`__," by Tirthajyoti Sarkar;
  + "`'Vectorized' Operations: Optimized Computations on NumPy Arrays <https://www.pythonlikeyoumeanit.com/Module3_IntroducingNumpy/VectorizedOperations.html>`__", part of "`Python like you mean it <https://www.pythonlikeyoumeanit.com/>`__," a free resource by Ryan Soklaski.

- **Use xarray with netCDF data**:

  *Why*: This is xarray's use case. You can think of NumPy as implementing multidimensional matrices in the fully general, mathematical sense, and xarray providing the specialization to the case where the matrix contains data on a lat-lon-time-(etc.) grid.

  xarray lets you refer to your data with human-readable labels such as 'latitude,' rather than having to remember that that's the second dimension of your array. This bookkeeping is essential when writing code for the MDTF framework, when your POD will be run on data from models you haven't been able to test on.

  In particular, xarray provides seamless support for `time axes <http://xarray.pydata.org/en/stable/time-series.html>`__, with `support <http://xarray.pydata.org/en/stable/weather-climate.html>`__ for all CF convention calendars through the ``cftime`` library. You can, eg, subset a range of data between two dates without having to manually convert those dates to array indices.

  Again, please see the xarray tutorials linked above.


- **Memory use and views vs. copies**: Use scalar indexing and `slices <https://numpy.org/doc/stable/reference/arrays.indexing.html#basic-slicing-and-indexing>`__ (index specifications of the form `start_index`:`stop_index`:`stride`) to get subsets of arrays whenever possible, and only use `advanced indexing <https://numpy.org/doc/stable/reference/arrays.indexing.html#advanced-indexing>`__ features (indexing arrays with other arrays) when necessary.

  *Why*: When advanced indexing is used, NumPy will need to create a new copy of the array in memory, which can hurt performance if the array contains a large amount of data. By contrast, slicing or basic indexing is done in-place, without allocating a new array: the NumPy documentation calls this a "view."

  Note that array slices are native `Python objects <https://docs.python.org/3.7/library/functions.html?highlight=slice#slice>`__, so you can define a slice in a different place from the array you intend to use it on. Both NumPy and xarray arrays recognize slice objects.

  This is easier to understand if you think about NumPy as a wrapper around C-like functions: array indexing in C is implemented with pointer arithmetic, since the array is implemented as a contiguous block of memory. An array slice is just a pointer to the same block of memory, but with different offsets. More complex indexing isn't guaranteed to follow a regular pattern, so NumPy needs to copy the requested data in that case.

  See the following references for more information:

  + The numpy `documentation <https://numpy.org/doc/stable/reference/arrays.indexing.html>`__ on indexing;
  + "`Numpy Views vs Copies: Avoiding Costly Mistakes <https://www.jessicayung.com/numpy-views-vs-copies-avoiding-costly-mistakes/>`__," by Jessica Yung;
  + "`How can I tell if NumPy creates a view or a copy? <https://stackoverflow.com/questions/11524664/how-can-i-tell-if-numpy-creates-a-view-or-a-copy>`__" on stackoverflow.


- **MaskedArrays instead of NaNs or sentinel values**: Use NumPy's `MaskedArrays <https://numpy.org/doc/stable/reference/maskedarray.generic.html>`__ for data that may contain missing or invalid values, instead of setting those entries to NaN or a sentinel value.

  *Why*: One sometimes encounters code which sets array entries to fixed "sentinel values" (such as 1.0e+20 or `NaN <https://en.wikipedia.org/wiki/NaN>`__\) to indicate missing or invalid data. This is a dangerous and error-prone practice, since it's frequently not possible to detect if the invalid entries are being used by mistake. For example, computing the variance of a timeseries with missing elements set to 1e+20 will either result in a floating-point overflow, or return zero.

  NumPy provides a better solution in the form of `MaskedArrays <https://numpy.org/doc/stable/reference/maskedarray.html>`__, which behave identically to regular arrays but carry an extra boolean mask to indicate valid/invalid status. All the NumPy mathematical functions will automatically use this mask for error propagation. For `example <https://numpy.org/doc/stable/reference/maskedarray.generic.html#numerical-operations>`__, trying to divide an array element by zero or taking the square root of a negative element will mask it off, indicating that the value is invalid: you don't need to remember to do these sorts of checks explicitly.


Python: Plotting
----------------

- **Use the 'Agg' backend when testing your POD**: For reproducibility, set the shell environment variable ``MPLBACKEND`` to ``Agg`` when testing your POD outside of the framework.

  *Why*: Matplotlib can use a variety of `backends <https://matplotlib.org/tutorials/introductory/usage.html#backends>`__\: interfaces to low-level graphics libraries. Some of these are platform-dependent, or require additional libraries that the MDTF framework doesn't install. In order to achieve cross-platform portability and reproducibility, the framework specifies the ``'Agg'`` non-interactive (ie, writing files only) backend for all PODs, by setting the ``MPLBACKEND`` environment variable.

  When developing your POD, you'll want an interactive backend -- for example, this is automatically set up for you in a Jupyter notebook. When it comes to testing your POD outside of the framework, however, you should be aware of this backend difference.


NCL
---

- **Deprecated calendar functions**: Check the `function reference <https://www.ncl.ucar.edu/Document/Functions/index.shtml>`__ to verify that the functions you use are not deprecated in the current version of `NCL <https://www.ncl.ucar.edu/>`__. This is especially necessary for `date/calendar functions <https://www.ncl.ucar.edu/Document/Functions/date.shtml>`__.

  *Why*: The framework uses a current version of `NCL <https://www.ncl.ucar.edu/>`__ (6.6.x), to avoid plotting bugs that were present in earlier versions. This is especially relevant for calendar functions: the ``ut_*`` set of functions have been deprecated in favor of counterparts beginning with ``cd_`` that take identical arguments (so code can be updated using find/replace). For example, use `cd_calendar <https://www.ncl.ucar.edu/Document/Functions/Built-in/cd_calendar.shtml>`__ instead of the deprecated `ut_calendar <https://www.ncl.ucar.edu/Document/Functions/Built-in/ut_calendar.shtml>`__.

  This change is necessary because only the ``cd_*`` functions support all calendars defined in the CF conventions, which is needed to process data from some models (eg, weather or seasonal models are typically run with a Julian calendar.)
