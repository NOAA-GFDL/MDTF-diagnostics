Non-conda installation instructions
===================================

If you're unable to use the conda-based :ref:`installation instructions <ref-install>`, the framework can use pre-existing languages and programs on your systems without the use of conda environments for dependency management. If you choose this option, we assume you know what you're doing: because this mode of operation is dependent on the details of each user’s system, we can only support it at a secondary priority. 

Requirements
------------

The following software needs to be available on your ``$PATH`` when the framework is run:

- `Python <https://www.python.org/>`__ version 2.7: the framework will attempt to create virtualenvs for each POD.
- `NCO utilities <http://nco.sourceforge.net/>`__ version 4.7.6.
- `ghostscript <https://www.ghostscript.com/>`__.
- `NCL <https://www.ncl.ucar.edu/>`__, version 6.5.0 or newer.
- `R <https://www.r-project.org/>`__, for the SM_ET_coupling POD only.

Configuration instructions
--------------------------

Configuring this mode of operation requires adding additional settings to the ``src/default_tests.jsonc`` file. This is a template/example of an input file you can use to define configuration options instead of re-typing them on the command line every time you run the framework. In addition to the settings described in :ref:`ref-configure`, you will also need to:

- Change the value for ``environment_manager`` from ``"Conda"`` to ``"Virtualenv"``.
- Any values for ``conda_root`` and ``conda_env_root`` will be ignored.
- The framework will use ``pip`` to install required python modules in new virtualenvs, which will be installed in the default location for your system's python. To put the files in a different location, create a new setting ``"venv_root": <Path to virtualenv directory>``.
- Likewise, to install packages needed by R in a location other than your system default, create a new setting ``"r_lib_root": <path to R package directory>``.

Known issues with standalone NCL installation
---------------------------------------------

Many Linux distributions (Ubuntu, Mint, etc.) have offered a way of installing `NCL <https://www.ncl.ucar.edu/>`__ through their system package manager (apt, yum, etc.) This method of installation is not recommended: users may encounter errors when running the example PODs provided by NCAR, even if the environment variables and search path have been added. 

The recommended method to install standalone NCL is by downloading the pre-compiled binaries from https://www.ncl.ucar.edu/Download/install_from_binary.shtml. Choose a download option according to the Linux distribution and hardware, unzip the file (results in 3 folders: ``bin``, ``include``, ``lib``), create a folder ncl under the directory ``/usr/local`` (requires permission) and move the 3 unzipped folders into ``/usr/local/ncl``. Then add the following lines to the ``.bashrc`` script (under the user’s home directory; may be different if using shells other than bash, e.g., ``.cshrc`` for csh): 

::

   export NCARG_ROOT=/usr/local/ncl 
   export PATH:$NCARG_ROOT/bin:$PATH 
