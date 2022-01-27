Multi-Case Example Diagnostic Documentation
================================

Last update: Feb-2022

This POD illustrates how multiple cases (experiments) can be analyzed together. The
muliple cases are specified to the MDTF Framework where they are initialized and
preprocessed independently. The framework then passes off a dictionary metadata
information for each case that can then be used byt the POD.

.. note::
  This POD assumes familiarity with the single-case example diagnostic

Version & Contact info
----------------------

- Version/revision information: version 1 (Feb-2021)
- Model Development Task Force Framework Team

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 
Unless you've distributed your script elsewhere, you don't need to change this.

Functionality
-------------

In this example POD, near-surface air temperature is read from multiple cases. The
POD time averages the data and calculates the anomaly relative to the global mean.
The anomalies are zonally-averaged and the results from all cases are shown
on a single plot.

Required programming language and libraries
-------------------------------------------

* Python >= 3.7
* xarray
* matplotlib

Required model output variables
-------------------------------

* tas - Surface (2-m) air temperature (CF: air_temperature)

References
----------

1. E. D. Maloney et al. (2019): Process-Oriented Evaluation of Climate and
Weather Forecasting Models. *BAMS*, **100** (9), 1665–1686,
`doi:10.1175/BAMS-D-18-0042.1 <https://doi.org/10.1175/BAMS-D-18-0042.1>`__.

