Development instructions
========================

We list several important points to be aware of when developing your POD. This may require you to modify existing code.

Scope of the analysis your POD conducts
---------------------------------------

See the `BAMS article <https://doi.org/10.1175/BAMS-D-18-0042.1>`__ describing version 2.0 of the framework for a description of the project’s scientific goals and what we mean by a “process oriented diagnostic” (POD). We encourage PODs to have a specific, focused scope.

PODs should be relatively lightweight in terms of computation and memory requirements (eg, run time measured in minutes, not hours): this is to enable rapid feedback and iteration cycles to assist users in model development. Bear in mind that your POD may be run on model output of potentially any date range and spatial resolution. Your POD should not require strong assumptions about these quantities, or other details of the model’s operation.

Choice of language(s)
---------------------

In order to accomplish our goal of portability, the MDTF **cannot** accept PODs written in closed-source languages (eg `MATLAB <https://www.mathworks.com/products/matlab.html>`__; depending on your use case, it may be feasible to port MATLAB code to `Octave <https://www.gnu.org/software/octave/>`__). 

We also do not accept PODs written in compiled languages (C or Fortran): installation would rapidly become impractical if the user had to check compilation options for each POD. See below for options if your POD requires the performance of a compiled language.

We require that PODs that are funded through the CPO grant be developed in Python, specifically Python >= 3.6 (official support for Python 2 was discontinued as of January 2020). While the framework is able to call PODs written in any scripting language, Python support will be “first among equals” in terms of priority for allocating developer resources, etc. At the same time, if your POD development is *not* being funded, we  recommend against unnecessarily **re** writing existing analysis scripts in Python. Doing so is likely to introduce new bugs into stable code, especially if you’re unfamiliar with Python.

Managing language and library dependencies
------------------------------------------

We recommend developing your POD using miniconda/Anaconda to manage your POD's dependencies during development for the same reasons we recommend it to :ref:`end users <ref-install>`: it allows you to keep your development environment separate from the rest of your system. Note that conda is not python-specific, but allows coexisting versioned environments of most scripting languages (`R <https://anaconda.org/conda-forge/r-base>`__, `NCL <https://anaconda.org/conda-forge/ncl>`__, `pyFerret <https://anaconda.org/conda-forge/pyferret>`__, etc.)

To prevent the proliferation of dependencies, we suggest that new python development use libraries in the `python_base <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/develop/src/conda/env_python_base.yml>`__ conda environment, if possible. 

If your POD requires libraries that aren't available in an existing environment, we ask that you notify us (since this situation may be relevant to other developers) and submit a `YAML file <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-file-manually>`__ that creates the environment needed for your POD. 

- The environment filename should be ``env_<your POD's name>.yml``, and committed in ``src/conda``.
- The name of the environment should be ``_MDTF_<your POD's name>``.
- We recommend listing `conda-forge <https://anaconda.org/conda-forge>`__ as the first channel to search, as it's entirely open source and has the largest range of packages. Note that combining packages from different channels (in particular, conda-forge and anaconda's channel) may create incompatibilities.
- We recommend constructing the list of packages manually, and *not* exporting your development environment with ``conda env export``. The latter command gives platform-specific version information and will not be fully portable in all cases; it also does so for every package in the environment, not just the "top-level" ones you directly requested. It's straightforward to search your POD's code for ``import`` statements referencing third-party libraries.
- We recommend specifying versions as little as possible, out of consideration for the end user: if each POD specifies exact versions of all its dependencies, conda will need to install multiple versions of the same libraries. In general, specifying a version should only be needed in cases where backward compatibility was broken (eg. python 2 vs. 3) or a bug affecting your POD was fixed (eg. postscript font rendering on MacOS with older NCL). Conda installs the latest version of each package that's consistent with all other dependencies. 

After creating the environment file and placing it in ``src/conda``, verify that your POD works:

- Create the environment using the ``conda_env_setup.sh`` script described in the :ref:`installation <ref-conda-env-install>` instructions:

   ::

   % cd $CODE_ROOT
   % ./src/conda/conda_env_setup.sh --env <your POD's name> --conda_root $CONDA_ROOT --env_dir $CONDA_ENV_DIR 

- Have the framework run your POD on suitable test data, as described in :doc:`start_config`. No additional steps are needed to specify the environment: if your conda environment follows the naming conventions above, the framework will always use it to run your POD, and your POD only.

Scope of your POD’s code
------------------------

As described above, your POD should accept model data as input and express the results of its analysis in a series of figures, which are presented to the user in a web page. Input model data will be in the form of one netCDF file (with accompanying dimension information) per variable, as requested in your POD’s :doc:`settings file <dev_settings_quick>`. Because your POD may be run on the output of any model, you should be careful about the assumptions your code makes about the layout of these files. Supporting data may be in any format and will not be modified by the framework.

The above data sources are your POD’s only input: you may provide options in the settings file for the user to configure when the POD is installed, but these cannot be changed each time the POD is run. Furthermore, your POD should not access the internet or other networked resources.

The output of your POD should be a series of figures in vector format (.eps or .ps), written to a specific working directory (described below). Optionally, we encourage POD developers to also save relevant output data (eg, the output data being plotted) as netcdf files, to give users the ability to take the POD’s output and perform further analysis on it. 

Observational and supporting data; code organization. 
-----------------------------------------------------

.. figure:: ../img/dev_obs_data.jpg
   :align: center
   :width: 100 %

In order to make your code run faster for the users, we request that you separate any calculations that don’t depend on the model data (eg. pre-processing of observational data), and instead save the end result of these calculations in data files for your POD to read when it is run. We refer to this as “digested observational data,” but it refers to any quantities that are independent of the  model being analyzed. For purposes of data provenance, reproducibility, and code maintenance, we request that you include all the pre-processing/data reduction scripts used to create the digested data in your POD’s code base, along with references to the sources of raw data these scripts take as input (yellow box in the figure).

Digested data should be in the form of numerical data, not figures, even if the only thing the POD does with the data is produce an unchanging reference plot. We encourage developers to separate their “number-crunching code” and plotting code in order to give end users the ability to customize output plots if needed. In order to keep the amount of supporting data needed by the framework manageable, we request that you limit the total amount of digested data you supply to no more than a few gigabytes. 

In collaboration with PCMDI, a framework is being advanced that can help systematize the provenance of observational data used for POD development. Some frequently used datasets have been prepared with this framework, known as PCMDIobs. Please check to see if the data you require is available via PCMDIobs. If it is, we encourage you to use it, otherwise proceed as described above. 

Other tips on implementation: 
-----------------------------

#. Structure of the code package: Implementing the constituent PODs in accordance with the structure described in sections 2 and 3 makes it easy to pass the package (or just part of it) to other groups. 

#. Robustness to model file/variable names: Each POD should be robust to modest changes in the file/variable names of the model output; see section 5 regarding the model output filename structure, and section 6 regarding using the environment variables and robustness tests. Also, it would be easier to apply the code package to a broader range of model output. 

#. Save intermediate output: Can be used, e.g. to save time when there is a substantial computation that can be re-used when re-running or re-plotting diagnostics. See section 3.I regarding where to save the output. 

#. Self-documenting: For maintenance and adaptation, to provide references on the scientific underpinnings, and for the code package to work out of the box without support. See step 5 in section 2. 

#. Handle large model data: The spatial resolution and temporal frequency of climate model output have increased in recent years. As such, developers should take into account the size of model data compared with the available memory. For instance, the example POD precip_diurnal_cycle and Wheeler_Kiladis only analyze part of the available model output for a period specified by the environment variables ``FIRSTYR`` and ``LASTYR``, and the convective_transition_diag module reads in data in segments. 

#. Basic vs. advanced diagnostics (within a POD): Separate parts of diagnostics, e.g, those might need adjustment when model performance out of obs range. 

#. Avoid special characters (``!@#$%^&*``) in file/script names.