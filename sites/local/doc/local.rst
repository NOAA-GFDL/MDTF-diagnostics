Customizing your installation with the 'local' site
===================================================

About the 'local' site
----------------------

The ``--site`` `command-line flag <../sphinx/ref_cli.html>`__ is used to implement plug-in functionality for site-specific code, (eg, enabling data search from a lab's internally-accessible filesystem.) The default value for this flag is ``local``: code and configuration files placed in the sites/local/ directory will be used to customize the general-purpose framework code in src/.

The most important use case for this functionality is allowing you to set default values for command-line flags, as described in the next section. This lets you set configuration options that are the same for each run (e.g., <*OBS_DATA_ROOT*>, the path to your local copy of the observational data used by the diagnostics) once, in a file in this directory, without having to remember to include the corresponding command-line flag every time you run the package. 

This function only sets default values: any value may be overridden for any run of the package by specifying it explicitly on the command line (or in an input file). Regardless of where they originate, the complete list of configuration settings used in a run of the package is saved in the output, so you can always recreate a run of the package even if you change these defaults.

The full API for the ``--site`` functionality, as well as instructions on how to develop your own site-specific data sources and other code plug-ins, will be documented in an upcoming release.

How to set default values
-------------------------

When run, the framework looks for a file named ``defaults.jsonc`` in the directory for the chosen site. An example of the format for this file is provided in `src/default_tests.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/default_tests.jsonc>`__, which we encourage you to make a copy of, rename, and edit.

More specifically, the ``defaults.jsonc`` file should be a JSON file (with ``//``-comments allowed) listing <*key*>:<*value*> pairs. The <*key*> should be the long name of one of the `command-line flags <../sphinx/ref_cli.html>`__, with hyphens replaced by underscores. The <*value*> should be the desired default value. <*key*>s which don't correspond to recognized command-line flags, such as the ``caselist`` in `src/default_tests.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/default_tests.jsonc>`__, are ignored.

You can test the settings in your ``defaults.jsonc`` file by running :console:`% mdtf --help`. The beginning of the help text will list the path to the default settings files being used, and the help text for each command-line flag will note its default value.

Switching between multiple defaults with multiple sites
-------------------------------------------------------

A site is simply a subdirectory of the ``sites/`` directory. You can manage and easily switch between multiple sets of default values by creating additional subdirectories within ``sites/``, along with a ``defaults.jsonc`` file for each, and selecting one at runtime with the ``--site`` flag. 

This can be useful if you frequently need to analyze data from a variety of different `data sources <../sphinx/ref_data_sources.html>`__: you can create one site per data source, and add the settings specifying the desired data set from that source at runtime.
