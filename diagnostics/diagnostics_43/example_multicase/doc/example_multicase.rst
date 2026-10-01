Multi-Case Example Diagnostic Documentation
===========================================

Last update: Apr 2024

This POD illustrates how multiple cases (experiments) can be analyzed together. The
muliple cases are specified to the MDTF Framework where they are initialized and
preprocessed independently.

.. note::
  This POD assumes familiarity with the single-case example diagnostic

Version & Contact info
----------------------

- Version/revision information: version 1.1 (Oct 2022)
- Model Development Task Force Framework Team

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).
Unless you've distributed your script elsewhere, you don't need to change this.

Functionality
-------------
The framework generates yaml file called *case_info.yml* with environment variables
for the file paths and variable information for each case. The **example_multicase** POD reads the yaml file
information into a dictionary, and loops through the dictionary to read near-surface air temperature (TAS) data
for each case. The POD time averages the data and calculates the anomaly relative to the global mean.
The anomalies are zonally-averaged and the results from all cases are shown on a single plot.

Required programming language and libraries
-------------------------------------------

* Python >= 3.11
* xarray
* numpy
* matplotlib
* yaml
* sys

Required model output variables
-------------------------------

* tas - Surface (2-m) air temperature (CF: air_temperature)

References
----------

1. E. D. Maloney et al. (2019): Process-Oriented Evaluation of Climate and
Weather Forecasting Models. *BAMS*, **100** (9), 1665–1686,
`doi:10.1175/BAMS-D-18-0042.1 <https://doi.org/10.1175/BAMS-D-18-0042.1>`__.
