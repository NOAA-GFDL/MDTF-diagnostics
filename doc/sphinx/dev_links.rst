Links to external resources
===========================

The following third-party pages contain information that may be helpful for POD development.

Git tutorials/references
------------------------

- The official git `tutorial <https://git-scm.com/docs/gittutorial>`__.
- A more verbose `introduction <https://www.atlassian.com/git/tutorials/what-is-version-control>`__ to the ideas behind git and version control.
- A still more detailed `walkthrough <http://swcarpentry.github.io/git-novice/>`__ which assumes no prior knowledge.

Python coding style
-------------------

- `PEP8 <https://www.python.org/dev/peps/pep-0008/>`__, the officially recognized Python style guide.
- Google's `Python style guide <https://github.com/google/styleguide/blob/gh-pages/pyguide.md>`__.

Python libraries
----------------

As described in :ref:`ref-conda-dev-envs`, we recommend that development of new PODs be done in Python 3 using the libraries provided in the `python3_base <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/conda/env_python3_base.yml>`__ conda environment. 

- Documentation sites for `NumPy <https://numpy.org/doc/stable/index.html>`__, `SciPy <https://docs.scipy.org/doc/scipy/reference/index.html>`__, `xarray <http://xarray.pydata.org/en/stable/>`__, `matplotlib <https://matplotlib.org/>`__ and `cartopy <https://scitools.org.uk/cartopy/docs/latest/>`__.
- NumPy's own `basic <https://numpy.org/doc/stable/user/absolute_beginners.html>`__ and `intermediate <https://numpy.org/doc/stable/user/quickstart.html>`__ tutorials; xarray's `overview <http://xarray.pydata.org/en/stable/quick-overview.html>`__ and climate and weather `examples <http://xarray.pydata.org/en/stable/examples.html>`__;
- A `demonstration <https://rabernat.github.io/research_computing/xarray.html>`__ of the features of xarray using earth science data;
- The 2020 SciPy conference has open-source, interactive `tutorials <https://www.scipy2020.scipy.org/tutorial-information>`__ you can work through on your own machine or fully online using `Binder <https://mybinder.org/>`__. In particular, there are tutorials for `NumPy <https://github.com/enthought/Numpy-Tutorial-SciPyConf-2020>`__ and `xarray <https://xarray-contrib.github.io/xarray-tutorial/index.html>`__.

Code documentation
------------------

Documentation for the framework's code is managed using `sphinx <https://www.sphinx-doc.org/en/master/index.html>`__, which works with files in `reStructured text <https://docutils.sourceforge.io/rst.html>`__ (reST, ``.rst``) format. The framework uses Google style conventions for python docstrings.

- The most convenient way to write and debug reST documentation is with an online editor. We recommend `https://livesphinx.herokuapp.com/ <https://livesphinx.herokuapp.com/>`__ because it recognizes sphinx-specific commands as well.
- reStructured text `introduction <http://docutils.sourceforge.net/docs/user/rst/quickstart.html>`__, `quick reference <http://docutils.sourceforge.net/docs/user/rst/quickref.html>`__ and `in-depth guide <http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html>`__.
- reST `syntax comparison <http://hyperpolyglot.org/lightweight-markup>`__ to other text formats you may be familiar with.
- Sphinx `quickstart <http://www.sphinx-doc.org/en/master/usage/quickstart.html>`__. 
- Style guide for google-style python `docstrings <https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings>`__ and quick  `examples <https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html>`__.
