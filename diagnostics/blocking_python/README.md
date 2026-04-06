# Diurnal Cycle of Precipitation Analysis

This tool analyzes the diurnal (daily) cycle of precipitation by comparing Climate Model output (e.g., SPEAR) against Satellite Observations (GPM IMERG).

## Functionality
1. **Preprocessing:** Converts raw half-hourly satellite HDF5 files into 3-hourly seasonal climatologies (JJA/DJF).
2. **Analysis:** Performs Fourier analysis to determine the Phase (timing of peak rainfall) and Amplitude (strength of cycle).
3. **Visualization:** Generates side-by-side comparison maps for Phase, Amplitude, Variance Explained, and Mean Precipitation.

## Installation

```bash
conda env create -f environment.yml
conda activate diurnal_cycle
```

## How to run
1. Run the satellite_preprocessing.py to process raw satellite data first. Depending on the computing resources, this may take a while.
2. After completing the preprocessing, run the analyze_cycle.py or analyze_phase.py according to your requirements.
These scripts are dask integrated. Use the config.yaml file to set your parameters and the number of dask workers.
