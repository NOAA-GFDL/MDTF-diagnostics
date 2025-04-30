.. _ref-dev-gfdl:

Maintaining the GFDL MDTF-diagnostics installation
==================================================

Updating the main branch of the oar.gfdl.mdtf MDTF-diagnostics repo
-------------------------------------------------------------------

A copy of the NOAA-GFDL/MDTF-diagnostics package is located in /home/oar.gfdl.mdtf/mdtf
and is maintained by developers with oar.gfdl.mdtf role account access. The
central installation is synced with main branch at this time. To update the main branch,
log into the role account, `cd` to the /home/oar.gfdl.mdtf/mdtf/MDTF-diagnostics, and run `git pull`.

Maintaining miniconda3 environments
-----------------------------------

A central installation of miniconda3 with the MDTF-diagnostics _MDTF_base, _MDTF_python3_base, _MDTF_NCL_base,
_MDTF_R_base, and _MDTF_dev environments located in /home/oar.gfdl.mdtf/miniconda3. To access conda binaries directly,
open a bash shell and run `source ~/.bashrc`. The conda environments need to be updated
when the environment files in MDTF-diagnostics/src/conda are changed on the main branch. After logging into the
oar.gfdl.mdtf role account, `cd` to /home/oar.gfdl.mdtf/mdtf/MDTF-diagnostics,
pull in changes to the MDTF-diagnostics repo, and run `/src/conda/conda_env_setup.sh -e [environment name] --
conda_root /home/oar.gfdl.mdtf/miniconda3 --env_dir /home/oar.gfdl.mdtf/miniconda3/envs`.
`[environment name]` is "base" for the _MDTF_base environment, "dev" for the _MDTF_dev environment,
"python3_base" for the _MDTF_python3_base environment, "NCL_base" for the _MDTF_NCL_base environment, and "R_base",
for the _MDTF_R_base environment.

Exising environments may require complete removal before updating, as continuously overwriting sometimes
fails to update all packages. You can verify package versions in a particular environment match the specs in the
corresponding environment file by running `conda activate _MDTF_[environment name]`, followed by `conda list`.
To delete a conda environment, run `conda remove -n ENV_NAME --all`. Reinstall the environment using
the `conda_env_setup.sh` call in the previous instructions.

If miniconda3 itself requires updating, completely delete it by running `rm -rf /home/oar.gfdl.mdtf/miniconda3`,
then remove the configuration files with `rm -rf ~/.condarc ~/.conda ~/.continuum`.

Download a tarball of the latest miniconda3 version using `wget`, `curl`, etc..., and install it in
the /home/oar.gfdl.mdtf directory using the `links and instructions
<https://www.anaconda.com/docs/getting-started/miniconda/main>`__ on the Conda website. Reinstall the MDTF-diagnostics
environments by running `/src/conda/conda_env_setup.sh --all --conda_root
/home/oar.gfdl.mdtf/miniconda3 --env_dir /home/oar.gfdl.mdtf/miniconda3/envs`. Note that the _MDTF_dev environment
needs to be installed with `-e dev`, as `--all` only installs the base environments.

Adding copies of POD observational data to the oar.gfdl.mdtf/inputdata directory
--------------------------------------------------------------------------------

Copies of POD bservational datasets are located the /home/oar.gfdl.mdtf/mdtf/inputdata directory.
The data are available in the NCAR MDTF obs_data collection on `Globus 
<https://app.globus.org/file-manager?origin_id=87726236-cbdd-4a91-a904-7cc1c47f8912&origin_path=%2F&two_pane=false>`__.
In addition, GFDL developers who are responsible for reviewing POD pull requests can ask POD developers to email
tarballs with observational and test datasets. This may be necessary to debug issues with the framework that POD
developers encounter when integrating their code into the package.
