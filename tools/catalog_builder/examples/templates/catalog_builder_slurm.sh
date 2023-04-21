#!/usr/bin/env bash
# Slurm batch submission script template for the MDTF-diagnostics ESM-Intake catalog builder:
# Usage:
# > cd /nbhome/[USERNAME]/mdtf/MDTF-diagnostics/tools/catalog_builder
# > sbatch examples/templates/catalog_builder_slurm.sh --config examples/templates/example_builder_config.yml
#SBATCH --job-name=esm_cat_builder
#SBATCH --chdir=/nbhome/jml
#SBATCH --output=/nbhome/jml/logs/slurm_%x.%A_%a.out
#SBATCH --error=/nbhome/jml/logs/slurm_%x.%A_%a.err
#SBATCH --time=1:00:00
#SBATCH --ntasks=8
#SBATCH --constraint=bigmem
#
local_repo="/nbhome/jml/catalog_builder"
_mdtf="/home/oar.gfdl.mdtf/mdtf/MDTF-diagnostics"
source "${_mdtf}/src/conda/conda_init.sh" -q "/home/oar.gfdl.mdtf/miniconda3"
conda activate _MDTF_base
python3 "${local_repo}/catalog_builder.py" "$@"
exit $?
