.. role:: code-rst(code)
   :language: reStructuredText

Output Reference
===============================
Processed data, ESM-intake catalogs, POD output, and logs from the MDTF-framework run are stored in a directory called 
:code-rst:`MDTF_output` that is appended to the :code-rst:`OUTPUT_DIR` (defaults to :code-rst:`WORK_DIR` if 
:code-rst:`OUTPUT_DIR` is not set) specified in the runtime configuration file. Each new run will generate an output 
directory with _v# appended to the code-rst:`MDTF_output` base name if the :code-rst:`OUTPUT_DIR` contains directories 
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
          ├── example_multicase.data.log
          ├── index.html
          ├── MDTF_CMIP_Synthetic_r1i1p1f1_gr1_19800101-19841231/
          ├── MDTF_CMIP_Synthetic_r1i1p1f1_gr1_19850101-19891231/
          ├── mdtf_diag_banner.png
          ├── MDTF_main.2024-07-29:17.13.28.log
          ├── MDTF_postprocessed_data.csv
          └── MDTF_postprocessed_data.json

To explain the contents within:
   * :code-rst:`index.html` is the html page used to consolidate the MDTF run for the end-user. 
     This serves as the main way to view all related plots and information for all PODs ran in a nice, condensed manner.
   * :code-rst:`MDTF_postprocessed_data.csv` and :code-rst:`MDTF_postprocessed_data.json` are the ESM-intake catalog 
     csv and json header files with information about the processed model data.
   * The catalog points towards data that can be found in the folders :code-rst:`MDTF_CMIP_Synthetic_*`
   * The rest of the files serve as a method of logging information about what the framework did and various issues that
     might have occured. Information inside these files could greatly help both POD developers and the framework 
     development team!

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
          ├── index.html
          ├── model/
          └── obs/

These files and folders being:
   * :code-rst:`example_multicase.html` serves as the landing page for the POD and can be easily reached from :code-rst:`index.html`.
   * :code-rst:`case_info.yml` provides information about the cases ran for the POD.
   * :code-rst:`model/` and :code-rst:`obs/` contain both plots and data for both the model data and observation data respectively.
   * There also exists various log files which function the same as mentioned previously.

If multiple PODs were run, you would find such a directory for each POD in the :code-rst:`MDTF_output` directory.
