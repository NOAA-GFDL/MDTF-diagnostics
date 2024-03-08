Framework configuration and parsing
===================================

This section describes the :doc:`src.cli`, responsible for parsing input configuration.

CLI functionality
-----------------

Overview
++++++++

Flexibility and extensibility are among the MDTF project's design goals, which must be accommodated by the package's configuration logic. Our use case requires the following features:

- Allow for specifying and recording user input in a file, to allow provenance of package runs and to eliminate the need for long strings of CLI flags.
- Record whether the user has explicitly set an option (to a value which may or may not be the default), or whether the option is unset and its default value is being used.
- Enable site-specific customizations, which can add to or modify any of the above properties.
- Define CLIs through configuration files instead of code to streamline the process of defining all of the above.

The MDTF framework uses the `Python Click package <https://click.palletsprojects.com/en/8.1.x/>`__
to create the CLI from the runtime configuration file options,
eliminating the need for custom the CLI modules and plugins in prior versions of the code.

.. _ref-cli-subcommands:

CLI subcommands
+++++++++++++++

Subcommands are used to organize different aspects of a program's functionality: e.g. ``git status`` and ``git log`` are both provided by ``git``, but each git subcommand takes its own options and flags. Subcommand parsing is currently implemented in the :doc:`src.cli` but not used: subcommands are manually dispatched in `mdtf_framework.py <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/mdtf_framework.py>`__. Full use of subcommands was planned for inclusion in a future release, to avoid excessive changes to the UI.

Currently recognized subcommands are:

- **mdtf** (no subcommand; default), or **mdtf run**: Run analyses on model data. 
- **mdtf info**: Implemented in the :doc:`src.mdtf_info`. Displays information on currently installed PODs and the variables needed to run individual diagnostics. 
- **mdtf help**: display help on command-line options and exit, equivalent to the ``-h``\/``--help`` flag.

In addition, the following subcommands were planned:

- **mdtf verify**: User-facing interface to the :doc:`src.verify_links` as a standalone script. This parses the HTML pages from a completed run of the package and determines if all linked plots exist.
- **mdtf install**: This would invoke the :doc:`src.install` to do initial installation of the package, conda environments and supporting POD and model data. This installer script is currently unused, on the grounds that the manual installation process described in the user-facing documentation is less error-prone.
- **mdtf update**: Would invoke a subset of the installer's functions to ensure that all code, supporting data and third-party dependencies are updated to their current versions.

Additional package manager-like commands could be added to allow users to selectively install the subset of PODs of interest to them (and their corresponding supporting data and conda environments.)

.. _ref-cli-plugins:


File-based CLI definition
-------------------------

The CLI for the package is constructed from a runtime configuration file.
The syntax for these files is essentially a direct JSON serialization of the arguments given to :py:class:`~argparse.ArgumentParser`,
with a few extensions described below.

Location of configuration files
+++++++++++++++++++++++++++++++

The top-level configuration files have hard-coded names:

CLI configuration file syntax
+++++++++++++++++++++++++++++

A subcommand ``cli_file`` is a JSONC struct which may contain:

- Arguments taken by the constructor for :py:class:`~argparse.ArgumentParser`;
- An attribute named ``arguments``, containing a list of argument structs not in any argument group;
- An attribute named ``argument_groups``, containing a list of structs each containing arguments taken by the :py:meth:`~argparse.ArgumentParser.add_argument_group` method of :py:class:`~argparse.ArgumentParser`, and an ``arguments`` attribute.

The ``arguments`` attribute referred to above defines a list of CLI options, in the order they're to be listed in online help (following basic unix convention, the order options are given doesn't affect their parsing). This is also the syntax used by the ``cli`` argument for each CLI plugin.

Attributes of a struct in the ``arguments`` list can include:

- Arguments taken by the :py:meth:`~argparse.ArgumentParser.add_argument` method of :py:class:`~argparse.ArgumentParser`, in particular:

  - ``name`` corresponds to the ``name_or_flags`` argument to :py:meth:`~argparse.ArgumentParser.add_argument`. It can be either a string, or list of strings, all of which will be taken to define the same flag. Initial hyphens (GNU syntax) are added, and underscores are converted to hyphens: ``name: "hyphen_opt"`` defines an option that can be set with either ``--hyphen_opt`` or ``--hyphen-opt``. If ``dest`` is not supplied, the first entry will be taken as the destination variable for the setting. 
  - ``action`` is one of the `allowed values <https://docs.python.org/3/library/argparse.html#action>`__ recognized by add_argument, or the fully qualified (module) name of a custom `Action <https://docs.python.org/3/library/argparse.html#action-classes>`__ subclass, which will be imported if it's not present in the current namespace.

- The following extensions to this set of arguments:

  - ``short_name``, optional, is used to define single-letter abbreviated flags for the most commonly used options. These are added to the synonymous flags defined via ``name``. Use of full-word (GNU style) flags is preferred, as it makes the set of arguments more comprehensible.
  - ``is_positional``, default False, is a boolean used to identify positional arguments (as opposed to flag-based arguments, which are identified by their flag rather than their position on the command line.)
  - ``hidden``, default False, is a boolean used to identify options that are recognized by the parser but not displayed to the user in online help.

Use in the code
+++++++++++++++

:doc:`src.cli` defines a hierarchy of classes representing objects in a CLI parser specification, which are instantiated by values from the configuration files. At the root of the hierarchy is :class:`~src.cli.CLIConfigManager`, a Singleton which reads all the files, begins the object creation process, and stores the results. The other classes in the hierarchy are, in descending order:



CLI parsers
-----------

Parser classes
++++++++++++++


.. _ref-cli-precedence:

Defaults and argument parsing precedence
++++++++++++++++++++++++++++++++++++++++

Long strings of command-line arguments are cumbersome for users. At the same time, provenance and reproducibility of package runs are simplified if all configuration is handled by the same code. For this reason, we implement multiple ways for users to provide CLI arguments:

1. Options explicitly given on the command line.
2. Option values defined in a JSONC file and passed with the ``-f``\/``--input-file`` flag.
3. Option values defined in a JSONC file named ``defaults.jsonc`` located in the directory of the currently selected site.
4. Option values defined in a JSONC file named ``defaults.jsonc`` located in the ``/sites`` directory.
5. The default value (if any) specified in each CLI argument's definition.

The value assigned to every option is determined by the lowest-numbered method that explicitly specifies that value: for example, explicit command-line options override values given in a file passed with ``--input-file``, which in turn override the option defaults listed in the online help.

The intended use case for these different methods is to enable the user to focus on the settings that matter for each run. Continuing the example above, the user could specify the analysis period and desired PODs with explicit flags, options for data from the experiment being analyzed in an input file, and options describing the paths to POD supporting data and conda environments in a site-specific ``defaults.jsonc`` file (see user documentation for `site customization <https://mdtf-diagnostics.readthedocs.io/en/latest/sphinx_sites/local.html>`__.)

File-based input (2, 3 and 4) is read in by the :meth:`~src.cli.MDTFTopLevelArgParser.init_user_defaults` method of :class:`~src.cli.MDTFTopLevelArgParser`. The full precedence logic is implemented in the :meth:`~src.cli.MDTFArgParser.parse_known_args` method, inherited by :class:`~src.cli.MDTFTopLevelArgParser` from :class:`~src.cli.MDTFArgParser`.


Walkthough of CLI creation and parsing
--------------------------------------

Building the CLI
++++++++++++++++

- The mdtf wrapper script activates the ``_MDTF_base`` conda environment and calls `mdtf_framework.py <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/mdtf_framework.py>`__.
- mdtf_framework.py

  - This calls :meth:`~src.cli.MDTFTopLevelArgParser.init_user_defaults`, which parses the value of ``--input-file`` and, if set, reads the file and stores its contents in the ``user_defaults`` attribute of :class:`~src.cli.CLIConfigManager`.
  - It then calls :meth:`~src.cli.MDTFTopLevelArgParser.init_site`, which parses the value of the selected site and reads the site-specific defaults files (if any).
  - Now that we know which site we're using, we know the full set of subcommands and plug-in values (built-in and site-specific). :meth:`~src.cli.CLIConfigManager.read_subcommands` and :meth:`~src.cli.CLIConfigManager.read_plugins` read this information and parse it into :class:`~src.cli.CLICommand` objects stored in the :class:`~src.cli.CLIConfigManager`.
  - Another :class:`~src.cli.MDTFArgPreparser` is created to parse the subcommand and plug-in values. The corresponding plugin-specific arguments are added.

- We're now ready to build the "real" CLI parser, with :meth:`~src.cli.MDTFTopLevelArgParser.configure`. 

  - This simply sets some options relevant for the help text, and adds the CLI arguments (parsed as :class:`~src.cli.CLIArgument` objects) to the parser in :meth:`~src.cli.MDTFTopLevelArgParser.add_contents`, which calls the :meth:`~src.cli.MDTFTopLevelArgParser.configure` method on the :class:`~src.cli.CLIParser` object for the chosen subcommand.

- At this point the :class:`~src.cli.MDTFTopLevelArgParser` is fully configured and ready to parse user input.


Parsing CLI arguments
+++++++++++++++++++++

- Parsing of user input is done by the :meth:`~src.cli.MDTFTopLevelArgParser.dispatch` method of the configured :class:`~src.cli.MDTFTopLevelArgParser` object. 

  - This wraps the :meth:`~src.cli.MDTFTopLevelArgParser.parse_args` method, which differs significantly from the method of the same name on the python :py:class:`~argparse.ArgumentParser`: it inherits from the :meth:`~src.cli.MDTFArgParser.parse_known_args` method on :class:`~src.cli.MDTFArgParser`, which implements the :ref:`precedence logic <ref-cli-precedence>` described above. 
  - Values of configuration that were read from files during CLI configuration are now read from their stored values in :class:`~src.cli.CLIConfigManager`.
  - The :meth:`~src.cli.MDTFArgParser.parse_known_args` method returns a :py:class:`~argparse.Namespace` containing the parsed option name-value results, as with :py:class:`~argparse.ArgumentParser`.

- The parsed option values are stored as a dict in the ``config`` attribute of the :class:`~src.cli.MDTFTopLevelArgParser` object. This will be the starting point for further validation of user input done in the :class:`~src.core.MDTFFramework` class.
- The :meth:`~src.cli.MDTFTopLevelArgParser.dispatch` then imports the modules for all selected plug-in objects. We do this import "on demand," rather than simply always importing everything, because a plug-in may make use of third-party modules that the user hasn't installed (e.g. if the plug-in is site-specific and the user is at a different site.)
- Finally, :meth:`~src.cli.MDTFTopLevelArgParser.dispatch` calls the :meth:`~src.cli.CLICommand.call` method on the selected subcommand to hand off execution. As noted above, subcommand functionality is implemented but unused, so currently we always hand off the the first (only) subcommand, **mdtf run**, regardless of input. The corresponding entry point, as specified in `src/cli_plugins.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/cli_plugins.jsonc>`__, is the ``__init__`` method of :class:`~src.core.MDTFFramework`. 

