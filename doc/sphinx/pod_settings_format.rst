POD settings file format
========================

Each POD must contain a text file named ``settings.yml`` in the `YAML <https://en.wikipedia.org/wiki/YAML>`_ format. 

Settings section
------------------

POD description
^^^^^^^^^^^^^^^

- ``driver``: Filename of the top-level driver script for the POD. This is inferred by _check_pod_driver() if missing.
- ``long_name``: POD's name used for display purposes. May contain spaces.
- ``description``: Short description of POD inserted by the link in the top-level index.html file. 
- ``convention`` (optional): Variable naming convention that the POD expects to be used in its input data. Defaults to 'CF' if left blank.

Runtime checks
^^^^^^^^^^^^^^

The following settings are all optional. If given, they are passed to the ``validate_environment.sh`` script which makes sure they're present in the environment that the POD is run in, and skips running the POD if they aren't found.

- ``required_programs``: List of executables required by the POD (typically language interpreters).
- ``required_python_modules``: List of Python modules required by the POD, if any. It's only necessary to list non-standard library modules. 
- ``required_ncl_scripts``: List of NCL scripts required by the POD but not included with it, if any. 
- ``required_r_packages``: List of R packages required by the POD, if any. It's only necessary to list packages that aren't part of the base installation.
- ``pod_env_vars``: Dict of shell environment variables (list of ``<name>``:``<value>`` pairs) needed by the POD (if any), in addition to those provided by the framework. 


Varlist section
-----------------

TBD

Example
-------

::

  settings:
    driver: my_POD_driver.py
    long_name: My Example POD
    description: My example diagnostic, which computes various things and produces interesting plots.
    required_programs: ['python', 'ncl']
    required_python_modules: ['numpy', 'scipy', 'netCDF4']
    required_ncl_scripts: ['contributed', 'gsn_code', 'gsn_csm']

  varlist:
    - var_name: rlut_var
      freq: day
      requirement: required
    - var_name: pr_var
      freq: day
      requirement: required

::
