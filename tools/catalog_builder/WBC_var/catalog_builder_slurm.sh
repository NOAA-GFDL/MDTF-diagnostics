#!/usr/bin/env bash
# Slurm batch submission script template for the MDTF-diagnostics ESM-Intake catalog builder:
# Usage:
# > cd /glade/work/jshin/mdtf/MDTF-diagnostics/tools/catalog_builder
# > sbatch WBC_var/catalog_builder_slurm.sh --config WBC_var/example_builder_config.yml
#SBATCH --job-name=esm_cat_builder
#SBATCH --chdir=/glade/work/jshin/mdtf/MDTF-diagnostics/tools/catalog_builder/WBC_var
#SBATCH --output=/glade/work/jshin/mdtf/MDTF-diagnostics/tools/catalog_builder/WBC_var/logs/slurm_%x.%A_%a.out
#SBATCH --error=/glade/work/jshin/mdtf/MDTF-diagnostics/tools/catalog_builder/WBC_var/logs/slurm_%x.%A_%a.err
#SBATCH --time=1:00:00
#SBATCH --ntasks=8
#SBATCH --constraint=bigmem
#
module load conda
local_repo="/glade/work/jshin/mdtf/MDTF-diagnostics/tools/catalog_builder"
_mdtf="/glade/work/jshin/mdtf/MDTF-diagnostics"
#source "${_mdtf}/src/conda/conda_init.sh" -q "/glade/u/apps/opt/conda/condabin/conda"
conda activate _MDTF_base
python3 "${local_repo}/catalog_builder.py" "$@"
exit $?
