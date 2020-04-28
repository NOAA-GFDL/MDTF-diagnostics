# Modes of operation
1. 

# GFDL-specific settings
All [command-line settings]() in the uncustomized framework are available. In addition to those, 

* `--GFDL-PPAN-TEMP, --GFDL_PPAN_TEMP <DIR>`: If running on GFDL PPAN, set the `$MDTF_GFDL_TMPDIR` environment variable to this location and create temp files here. **Note**: must be accessible via gcp. Defaults to `$TMPDIR`.
* `--GFDL-WS-TEMP, --GFDL_WS_TEMP <DIR>`: If running on a GFDL workstation, set the `$MDTF_GFDL_TMPDIR` environment variable to this location and create temp files here. The directory will be created if it doesn't exist. **Note**: must be accessible via gcp. Defaults to `/net2/$USER/tmp`.
* `--frepp`: Set flag to run framework in 'online' mode, processing data as part of the FRE pipeline. Normally this is done by calling the [mdtf_gfdl.csh](../blob/feature//gfdl-data/src/mdtf_gfdl.csh) wrapper script from the XML.
* `--ignore-component, --ignore_component`: Set flag search entire /pp/ directory for model data; default is to restrict to model component passed by FRE. Ignored if --frepp is not set.

### Paths:
Environment variables in paths (eg `$HOME`) are resolved according to the shell context mdtf.py was called from. **Note** that many of the default variables refer to `$MDTF_GFDL_TMPDIR`, which is set according to whether the code is running on PPAN or a workstation to locations defined in setting above. Relative paths are resolved relative to the repo directory.
* `--OBS-DATA-REMOTE, --OBS_DATA_REMOTE <DIR>`: Site-specific installation of observational data used by individual PODs. This will be GCP'ed locally if running on PPAN.

### Model data retrieval settings:
* `--data-manager, --data_manager <DATA_MANAGER>` Method used to fetch model data. (default: GFDL_auto)

### Runtime settings:
* `--environment-manager, --environment_manager <ENVIRONMENT_MANAGER>`: Method to manage POD runtime dependencies. This defaults to using Anaconda as installed in the DET Team's role account.
* `--conda-root, --conda_root <DIR>`: This defaults to the Anaconda installation in the DET Team's role account. All required conda environments are maintained there as part of the site installation. 
* `--conda-env-root, --conda_env_root <DIR>`: This defaults to the Anaconda installation in the DET Team's role account. All required conda environments are maintained there as part of the site installation.









