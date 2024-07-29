.. role:: code-rst(code)
   :language: reStructuredText

Output Reference
===============================
After a run of the MDTF framework is completed, the output can be found in the 
output/work directory that is indicated in the :code-rst:`runtime_config.jsonc` file that is
passed as a command-line argument. The default setting is normally :code-rst:`"../wkdir".` 
In this section, we will take a look into such an output directory and explain 
the structure as well as the files within.

Example Directory
-------------------------------
For an example, we will take a look at the output directory of a run of the :code-rst:`'example_multicase'` POD
on some generated synthetic data. To do this, let's move into the :code-rst:`MDTF_output` directory associated 
with the run in our :code-rst:`wkdir`. The resulting tree should look like this:

   .. code-block:: none

      ── MDTF_output/
          ├── CMIP_Synthetic_r1i1p1f1_gr1_19800101-19841231.log
          ├── CMIP_Synthetic_r1i1p1f1_gr1_19850101-19891231.log
          ├── example_multicase/
          ├── MDTF_CMIP_Synthetic_r1i1p1f1_gr1_19800101-19841231/
          ├── MDTF_CMIP_Synthetic_r1i1p1f1_gr1_19850101-19891231/
          ├── MDTF_main.2024-07-26:16.28.21.log
          ├── MDTF_postprocessed_data.csv
          └── MDTF_postprocessed_data.json

To explain the contents within:
   * :code-rst:`MDTF_postprocessed_data.csv` and :code-rst:`MDTF_postprocessed_data.json` are two of the most
     important files in this folder as far as the POD is concerned as these file correspond to the intake-ESM catalog 
     generated for the data processed by the framework.
   * The catalog points towards data that can be found in the folders :code-rst:`MDTF_CMIP_Synthetic_*`
   * The rest of the files serve as a method of logging information about what the framework did and various issues that
     might have arised. Information inside these files could greatly help both POD developers and the framework 
     development team!

POD Output Directory
-------------------------------
As you probably noticed, there is one directory that was not mentioned in the prior list. 
This directory, :code-rst:`example_multicase`, contains all of the output for the POD we ran. If we were to take a look inside, we would see:
   
   .. code-block:: none

      ── example_multicase/
          ├── case_info.yml
          ├── config_save.json
          ├── example_multicase.data.log
          ├── example_multicase.html
          ├── example_multicase.log
          ├── index.html
          ├── mdtf_diag_banner.png
          ├── model/
          └── obs/

These files and folders being:
   * :code-rst:`case_info.yml` and :code-rst:`config_save.json` provide information about the cases ran for the POD.
   * :code-rst:`model/` and :code-rst:`obs/` contain both plots and data for both the model data and observation data respectively.
   * :code-rst:`index.html` is the compiled html page for the POD run. This serves as the main way to view all related plots for this POD in
     nice, condensed manner.
   * There can also be found various log files which function the same as mentioned previously.

If multiple PODs were to be ran, you would find such a directory for each POD in the :code-rst:`MDTF_output` directory.
