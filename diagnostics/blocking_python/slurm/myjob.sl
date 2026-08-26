#!/bin/bash
#SBATCH -A gfdl_a
#SBATCH -J sat_proc
#SBATCH -o %x_%j.out
#SBATCH -e %x_%j.err
#SBATCH -p analysis
#SBATCH -t 00:30:00
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mail-user=soelem.bhuiyan@noaa.gov
#SBATCH --mail-type=BEGIN,END,FAIL

# --- Ensure the script runs from the submission directory ---
cd $SLURM_SUBMIT_DIR

# --- Environment Setup ---
module purge
module load conda
conda activate gfdl

# --- Execute the Python script ---
echo "Starting Python script..."
python pr_diurnal_phase_comparisonv2.py -c config.yaml
echo "Script finished."