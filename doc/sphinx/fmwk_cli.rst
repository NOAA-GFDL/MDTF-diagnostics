Framework configuration and parsing
===================================

This section describes the :doc:`src.cli`, responsible for parsing input configuration.

CLI functionality
-----------------

Overview
++++++++

Flexibility and extensibility are among the MDTF project's design goals, which must be accommodated by the package's
configuration logic. Our use case requires the following features:

- Allow for specifying and recording user input in a file, to allow provenance of package runs and to eliminate the
  need for long strings of CLI flags.
- Record whether the user has explicitly set an option (to a value which may or may not be the default), or whether
  the option is unset and its default value is being used.
- Enable site-specific customizations, which can add to or modify any of the above properties.
- Define CLIs through configuration files instead of code to streamline the process of defining all of the above.

The MDTF framework uses the `Python Click package <https://click.palletsprojects.com/en/8.1.x/>`__
to create the CLI from the runtime configuration file options,
eliminating the need for custom the CLI modules and plugins in prior versions of the code.
Parameters specified in the runtime configuration file (e.g., ``templates/runtime_config.[jsonc | yml]``) are
passed to a click context object (``ctx``) by attaching the ``@click.option`` decorator to the ``-f`` parameter
associated with the path to the runtime config file (``e.g., ./mdtf -f [runtime_config_file]``). The ctx object that
is instantiated in the `mdtf_framework.py` driver contains the path to the runtime config file passed with the `-f`
parameter. `mdtf_framework.py` then calls cli.py utilities to parse the runtime configuration file and pass the
the runtime parameters to a `config` dictionary attribute attached to the `ctx` instance. The `config` information is
then passed to other framework methods and classes.