Framework configuration and parsing
===================================

This section describes the :doc:`src.cli`, responsible for parsing input configuration. Familiarity with the python :py:mod:`argparse` module is recommended.

CLI functionality
-----------------

Overview
++++++++

Flexibility and extensibility are among the MDTF project's design goals, which must be accommodated by the package's configuration logic. Our use case requires the following features:

- Allow for specifying and recording user input in a file, to allow provenance of package runs and to eliminate the need for long strings of CLI flags.
- Record whether the user has explicitly set an option (to a value which may or may not be the default), or whether the option is unset and its default value is being used.
- Define "plug-ins" for specific tasks (such as model data retrieval) which can define their own CLI settings. This is necessary to avoid confusing the user with settings that are irrelevant for their specified analysis; e.g. the ``--version-date`` flag used by the :ref:`ref-data-source-cmip6` data source would be meaningless for a source of data that didn't have a revision history.
- Enable site-specific customizations, which can add to or modify any of the above properties.
- Define CLIs through configuration files instead of code to streamline the process of defining all of the above.

No third-party CLI package implements all of the above features, so the MDTF package provides its own solution, described here.

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

CLI Plugins
+++++++++++

"Plug-ins" provide different ways to implement the same type of task, following a common API. One example is obtaining model data from different sources: different code is needed for reading the sample model data from a local directory vs. accessing remote data via a catalog interface. In the plug-in system, the code for these two cases would be written as distinct data source plug-ins, and the data retrieval method to use would be selected at runtime by the user via the ``--data-manager`` CLI flag. This allows new functionalities to be developed and tested independently of each other, and without requiring changes to the common logic of the framework.

The categories of plug-ins are fixed by the framework. Currently these are ``data_manager``, which retrieves model data, and ``environment_manager``, which sets up each POD's third-party code dependencies. Two other plug-ins are defined but not exposed to the user through the UI, because only one option is currently implemented for them: ``runtime_manager``, which controls how PODs are executed, and ``output_manager``, which controls how the PODs' output files are collected and processed.

Allowed values for each of these plug-in categories are defined in the ``cli_plugins.jsonc`` files: the "base" one in ``/src``, and optionally one in the site-specific directory selected by the user. 

As noted in the overview above, for a manageable interface we need to allow each plug-in to define its own CLI options. These are defined in the ``cli`` attribute for each plug-in definition in the ``cli_plugins.jsonc`` file, following the syntax described below. When the CLI parser is being configured, the user input is first partially parsed to determine what plug-ins the user has selected, and then their specific CLI options are added to the "full" CLI parser. 

File-based CLI definition
-------------------------

The CLI for the package is constructed from a set of JSONC configuration files. The syntax for these files is essentially a direct JSON serialization of the arguments given to :py:class:`~argparse.ArgumentParser`, with a few extensions described below.

Location of configuration files
+++++++++++++++++++++++++++++++

The top-level configuration files have hard-coded names:

- `src/cli_subcommands.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/cli_subcommands.jsonc>`__ to define the :ref:`subcommands <ref-cli-subcommands>`, and
- `src/cli_plugins.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/cli_plugins.jsonc>`__ to define the :ref:`plug-ins <ref-cli-plugins>`.
- Files with these names in a site directory will override the contents of the above files in ``/src`` if that site is selected, e.g. `sites/NOAA_GFDL/cli_subcommands.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/sites/NOAA_GFDL/cli_subcommands.jsonc>`__.

Plugins define their own CLI options in the ``cli`` attribute in their entry in the plugins file, using the syntax described below. On the other hand, each subcommand defines its CLI through a separate file, given in the ``cli_file`` attribute. Chief among these is 

- `src/cli_template.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/cli_template.jsonc>`__, which defines the CLI for running the package in the absence of site-specific modifications.

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

- :class:`~src.cli.CLICommand`\: Dataclass representing a :ref:`subcommand <ref-cli-subcommands>` or a :ref:`plug-in <ref-cli-plugins>`. This wraps a parser (``parser`` attribute) and objects in the classes below, corresponding to configuration for that parser, which are initialized from the configuration files (``cli`` attribute.) It also implements a :meth:`~src.cli.CLICommand.call` method for dispatching parsed values to the initialization method of the class implementing the subcommand or plug-in.
- :class:`~src.cli.CLIParser`\: Dataclass representing arguments passed to the constructor for :py:class:`~argparse.ArgumentParser`. A parser object (next section) is configured with information in objects in the classes below via this class's :class:`~src.cli.CLIParser.configure` method.
- :class:`~src.cli.CLIArgumentGroup`\: Dataclass representing arguments passed to :py:meth:`~argparse.ArgumentParser.add_argument_group`. This only affects the formatting in the online help.
- :class:`~src.cli.CLIArgument`\: Dataclass representing arguments passed to :py:meth:`~argparse.ArgumentParser.add_argument`, as described above.


CLI parsers
-----------

Parser classes
++++++++++++++

As described above, the CLI used on a specific run of the package depends on the values of some of the CLI arguments: the ``--site``, and the values chosen for recognized plug-ins. This introduces a chicken-and-egg level of complexity, in which we need to parse some arguments in order to determine how to proceed with the rest of the parsing. The :doc:`src.cli` does this by defining several parser classes, all of which inherit from :py:class:`~argparse.ArgumentParser`.

- :class:`~src.cli.MDTFArgParser`: The base class for all parsers, which implements custom help formatting (:class:`~src.cli.CustomHelpFormatter`) and recording of user-provided vs. default values for options (via :class:`~src.cli.RecordDefaultsAction`)
- :class:`~src.cli.MDTFArgPreparser`: Child class used for partial parsing ("preparsing"). This is used in :meth:`~src.cli.MDTFTopLevelArgParser.init_user_defaults` to extract paths to file-based user input, in :meth:`~src.cli.MDTFTopLevelArgParser.init_site` to extract the site, and in :meth:`~src.cli.MDTFTopLevelArgParser.setup` to extract values for the subcommand and plug-in options before the full CLI is parsed.
- :class:`~src.cli.MDTFTopLevelArgParser`: Child class for the top-level CLI interface to the package. Has additional methods for formatting help text, and initiating the CLI configuration and parsing process described in detail below.
- :class:`~src.cli.MDTFTopLevelSubcommandArgParser`: Currently unused. Child class which would take care of parsing and dispatch to MDTF package :ref:`subcommands <ref-cli-subcommands>`. This is currently done by manual inspection of ``sys.argv`` in `mdtf_framework.py <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/mdtf_framework.py>`__.

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
- mdtf_framework.py manually determines the subcommand from the currently recognized values, and constructs the CLI appropriate to it. In this example, we're running the package, so the :class:`~src.cli.MDTFTopLevelArgParser` is initialized and its :meth:`~src.cli.MDTFTopLevelArgParser.setup` method is called.

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

Extending the user interface
----------------------------

Currently, the only method for the user to configure a run of the package is the CLI described above, which parses command-line options and :ref:`configuration files <ref-cli-precedence>`. 

In the future it may be desirable to provide additional invocation mechanisms, e.g. from a larger workflow engine or a web-based front end. 

Parsing and validation logic is split between the :doc:`src.cli` and the :class:`~src.core.MDTFFramework` class. In order to avoid duplicating logic and ensure that configuration gets parsed consistently across the different methods, the raw user input should be introduced into the chain of methods in the parsing logic (described above) as early as possible.

