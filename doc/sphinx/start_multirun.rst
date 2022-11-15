.. role:: console(code)
   :language: console
   :class: highlight
Running the MDTF-diagnostics package in "multirun" mode
================================

Version 3 and later of the MDTF-diagnostics package provides support for "multirun" diagnostics that analyze output from
multiple model and/or observational datasets. At this time, the multirun implementation is experimental, and may only be
run on appropriately-formatted PODs. "Single-run" PODs that analyze one model dataset and/or one observational dataset
must be run separately because the configuration for single-run and multi-run analyses is different. Users and developers
should open issues when they encounter bugs or require additional features to support their PODs, or run existing PODs
on new datasets.

The example_multicase POD and configuration
--------------------------------------------
A multirun test POD called *example_multicase* is available in diagnostics/example_multicase that demonstrates
how to configure "multirun" diagnostics that analyze output from multiple datasets.
The `multirun_config_template.jsonc file
<https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/example_multicase/multirun_config_template.jsonc>`__
contains separate ``pod_list`` and ``case_list`` blocks. As with the single-run configuration, the ``pod_list`` may contain
multiple PODs separated by commas. The ``case_list`` contains multiple blocks of information for each case that the
POD(s) in the ``pod_list`` will analyze. The ``CASENAME``, ``convention``, ``FIRSTYR``, and ``LASTYR`` attributes must be
defined for each case. The ``convention`` must be the same for each case, but ``FIRSTYR`` and ``LASTYR``
may differ among cases.
Directions for generating the synthetic data in the configuration file are provided in the file comments, and in the
quickstart section of the `README file
<https://github.com/NOAA-GFDL/MDTF-diagnostics#5-run-the-framework-in-multi_run-mode-under-development>`__

The multirun implementation is triggered by setting ``data_type`` to "multi_run" in the environment settings section
of the configuration file, or via the command line. The default ``data_type`` value "single_run" if no value is defined
for ``data_type`` in the configuration file.

As with `single_run` mode, the ``OBS_DATA_ROOT``, ``MODEL_DATA_ROOT``, and ``WORKING_DIR`` must be defined.
However, the ``OBS_DATA_ROOT`` does not require a subdirectory for the POD unless the POD analyzes an observational
dataset. The assumption for now is that multirun PODs will only analyze model datasets; settings for observational
data are retained for backwards compatibility, and needs of multirun POD developers will inform the modification
of the data management options moving forward.

All other settings are identical to those described in the :doc:`configuration section <./start_config>`.

POD output
--------------------------------------------
The framework defines a root directory ``$WORKING_DIR/[POD name]`` for each
POD in the pod_list. ``$WORKING_DIR/[POD name]`` contains the the main framework log files, and subdirectories for each
case. Temporary copies of processed data for each case are placed in
``$WORKING_DIR/[pod_name]/[CASENAME]/[data output frequency]``.
The pod html file is written to ``$OUTPUT_DIR/[POD name]/[POD_name].html`` (``$OUTPUT_DIR`` defaults to ``$WORKING_DIR``
if it is not defined), and the output figures are placed in
``$OUTPUT_DIR/[POD name]/model``  depending on how the paths are defined in the
POD's html template.

Note that an obs directory is created by default, but will be empty unless the POD developer
opts to use an observational dataset and write observational data figures to this directory.
Figures that are generated as .eps files before conversion to .png files are written to
``$WORKING_DIR/[POD name]/model/PS``.

Multirun environment variables
--------------------------------------------
Multirun PODs obtain information for environment variables for the case and variable attributes
described in the :doc:`configuration section <./start_config>`
from a yaml file named *case_info.yaml* that the framework generates at runtime. The *case_info.yaml* file is written
to ``$WORKING_DIR/[POD name]``, and has a corresponding environment variable *case_env_file* that the POD uses to
parse the file. The *example_multicase.py* script demonstrates to how to read the environment variables from
*case_info.yaml* using the *case_env_file* environment variable into a dictionary,
then loop through the dictionary to obtain the post-processed data for analysis. An example *case_info.yaml* file
with environment variables defined for the synthetic test data is located in the *example_multicase* directory.