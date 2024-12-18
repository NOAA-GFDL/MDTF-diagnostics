.. role:: code-rst(code)
   :language: reStructuredText
.. _ref-output:
Output Reference
===============================
Processed data, ESM-intake catalogs, POD output, and logs from the MDTF-framework run are stored in a directory called 
:code-rst:`MDTF_output` that is appended to the :code-rst:`OUTPUT_DIR` (defaults to :code-rst:`WORK_DIR` if 
:code-rst:`OUTPUT_DIR` is not set) specified in the runtime configuration file. Each new run will generate an output 
directory with _v# appended to the :code-rst:`MDTF_output` base name if the :code-rst:`OUTPUT_DIR` contains directories 
from prior framework runs.

Example Directory
-------------------------------
For an example, we will take a look at the output directory of a run of the :code-rst:`'example_multicase'` POD
on some generated synthetic data. To do this, let's move into the :code-rst:`MDTF_output` directory associated 
with the run in our :code-rst:`wkdir`. The resulting tree should look like this:

   .. code-block:: none

      ── MDTF_output/
          ├── CMIP_Synthetic_r1i1p1f1_gr1_19800101-19841231.log
          ├── CMIP_Synthetic_r1i1p1f1_gr1_19850101-19891231.log
          ├── config_save.json
          ├── example_multicase/
          ├── index.html
          ├── MDTF_CMIP_Synthetic_r1i1p1f1_gr1_19800101-19841231/
          ├── MDTF_CMIP_Synthetic_r1i1p1f1_gr1_19850101-19891231/
          ├── mdtf_diag_banner.png
          ├── MDTF_main.2024-07-29:17.13.28.log
          ├── MDTF_postprocessed_data.csv
          └── MDTF_postprocessed_data.json

To explain the contents within:
   * :code-rst:`config_save.json` contains a copy of the runtime configuraton
   * :code-rst:`index.html` is the html page used to consolidate the MDTF run results for the end-user.
     Open this file in a web browser (e.g., :console:`% firefox index.html`) to view the figures and logs for each
     POD.
   * :code-rst:`MDTF_postprocessed_data.csv` and :code-rst:`MDTF_postprocessed_data.json` are the ESM-intake catalog 
     csv and json header files with information about the processed model data.
   * The catalog points towards data that can be found in the folders :code-rst:`MDTF_CMIP_Synthetic_*`.
     To re-run the framework using the same processed dataset, set `DATA_CATALOG`
     to the path to the :code-rst:`MDTF_processed_data.json` header file and set `run_pp` to `false` in the
     runtime configuration file.
   * The `.log` files contain framework and case-specific logging information. Please include information from these
     logs in any issues related to running the framework that you submit to the MDTF-diagnostics team.

POD Output Directory
-------------------------------
As you probably noticed, there is one directory that was not mentioned in the prior list. 
This directory, :code-rst:`example_multicase`, contains all of the output for the POD we ran. If we were to take a look inside, we would see:
   
   .. code-block:: none

      ── example_multicase/
          ├── case_info.yml
          ├── example_multicase.data.log
          ├── example_multicase.html
          ├── example_multicase.log
          ├── model/
          └── obs/

These files and folders are:
   * :code-rst:`example_multicase.html` serves as the landing page for the POD and can be easily reached from
     :code-rst:`index.html`.
   * :code-rst:`case_info.yml` provides environment variables for each case. Multirun PODs can read and set the
     environment variables from this file following the
     `example_multicase.py template <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/example_multicase/example_multicase.py>`__
   * :code-rst:`model/` and :code-rst:`obs/` contain both plots and data for both the model data and observation data
     respectively. The framework appends a temporary :code-rst:`PS` subdirectory to the :code-rst:`model` and
     :code-rst:`obs` directories where PODs can write postscript files instead of png files. The framework will convert
     any .(e)ps files in the :code-rst:`PS`
     subdirectories to .png files and move them to the :code-rst:`model` and/or :code-rst:`obs` subdirectories, then
     delete the :code-rst:`PS` subdirectories during the output generation stage. Users can retain the :code-rst:`PS`
     directories and files by setting `save_ps` to `true` in the runtime configuration file.
   * :code-rst:`example_multicase.log` contains POD-specific logging information in addition to some main logging messages
     that is helpful when diagnosing issues.
   * :code-rst:`example_multicase.data.log` has a list of processed data files that the POD read.

If multiple PODs are run, you will find a directory for each POD in the :code-rst:`MDTF_output` directory.
