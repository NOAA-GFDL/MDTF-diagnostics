Western Boundary Current (WBC) Diagnostics
==========================================
Last update: 12/16/2025

This diagnostic package provides a set of analyses of Western Boundary Currents (WBCs) after their separation from the coast, focusing on five major regions:

- Gulf Stream
- Kuroshio Extension
- Brazil Current
- Agulhas Current
- East Australia Current

Contact info
------------

- PI: Young-Oh Kwon, WHOI
- Current Developer: Jongsoo Shin (<200b>jongsoo.shin@whoi.edu<200b>), WHOI
- Contributors: Lilli Enders, MIT-WHOI Joint Program

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).


Functionality
-------------

All scripts can be found at: ``mdtf/MDTF_$ver/var_code/WBC_var``

1. Main script: WBC_var.py
2. Preprocessing script: postprocessing.py
4. Calculating index: calculate_index.py
3. Plotting script: draw_figure.py

| Preprocessed observational data from CMEMS satellite altimeter and HighResMIP ``mdtf/inputdata/obs_data/WBC_var/``.
| Place your input data at: ``mdtf/inputdata/model/WBC_var/``
| index.html can be found at: ``mdtf/MDTF_$ver/wkdir/MDTF_$model_name``
Dataset is available at https://10.6084/m9.figshare.30219853.

Required Programming Language and libraries
------------------------------------------

 Python Version 3.7 or higher is required.
 Required Python packages: eofs,statsmodels

Required input data to the module
---------------------------------

The following 3-D (time-lat-lon) Sea Surface Height fields are required with monthly mean temporal resolution

1. Sea Surface Height (units: m)

Data respository: https://10.6084/m9.figshare.30892322 

Available Analyses
------------------

1. **WBC Index**  
- Comparison of the spatial maps of the mean WBC path, which are defined as the locations of maximum SSH anomalies at each longitude, on top of the mean and standard deviations of SSH anomalies.   
- Comparison of the WBC indices, which are time series of SSH anomalies averaged along the mean WBC path, representing meridional displacement of the currents.

2. **WBC Path Variability**  
-  Comparison of the amplitudes of variability in the WBC path, calculated from the SSH anomalies along the WBC mean path.
-  Comparison of the temporal characteristics of the WBC indices, represented by the auto-correlations of the WBC indices.
- Comparison of the e-folding time scales of the auto-correlation functions of the WBC indices.

3. **WBC EOF Analysis**  
 - Comparison of the leading Empirical Orthogonal Function (EOF) mode of SSH anomalies along the WBC mean path.
- Comparison of the portion of total variance explained by the leading EOFs.
- Comparison of the waviness of the spatial patterns of the leading EOFs.
- Comparison of the spatial auto-correlation of the leading EOF patterns.
- Comparison of the e-folding length scales of the spatial auto-correlation functions of the leading EOF patterns.

Each diagnostic is available for the five WBC regions, with separate figures for each metric.

Methodology
-----------

**Preprocessing**

- Use monthly mean sea surface height (SSH) anomalies.
- Remove the climatological mean monthly means.

**Mean WBC Path Identification**

- For each longitude within a region, locate the latitude where the standard deviation of SSH anomalies is maximum.
- Select the climatological mean SSH isoline closest to those latitudes.
- This isoline defines the **Mean WBC Path**.
- This is a slight modification of the method proposed by Pérez-Hernández and Joyce (2014), to make it more readily applicable to the climate models with biases in the WBC paths.


**WBC Index**

- Compute monthly SSH anomaly averages along the mean WBC path.
- The resulting time series forms the **WBC Index**, primarily indicative of meridional shifts in the current.

Regions Analyzed
----------------

- **Gulf Stream**: Longitude 51-70W, Latitude 33–42N
- **Kuroshio Extension**: Longitude 145–157E, Latitude 31–45N
- **Brazil Current**: Longitude 30-45W, Latitude 33 to 44S
- **Agulhas Current**: Longitude 25–36E, Latitude 37 to 45S
- **East Australia Current**: Longitude 157–168E, Latitude 30 to 40S

Output Directory Structure
--------------------------

Figures are stored in the following pattern:

- `obs/WBCI.<region>.png` — WBC Index
- `obs/Amplitude_path_variability.<region>.png` — Path variability
- `obs/EOF_path_variability.<region>.png` — EOF analysis

Each `<region>` is one of: `gulf`, `kuroshio`, `brazil`, `agulhas`, `australia`.


References
----------

1. Pérez-Hernández, M. D., & Joyce, T. M. (2014). Two modes of Gulf Stream variability revealed in the last two decades of satellite altimeter data. Journal of Physical Oceanography, 44(1), 149-163.


More About the Diagnostic
-------------------------

Some examples are provided below:
**WBC Index Example**

.. image:: WBCI.gulf.png
   :align: center
   :width: 75 %

**WBC Path Variability Example**

.. image:: Amplitude_path_variability.gulf.png
   :align: center
   :width: 75 %

**WBC EOF Analysis Example**

.. image:: EOF_path_variability.gulf.png
   :align: center
   :width: 75 %

