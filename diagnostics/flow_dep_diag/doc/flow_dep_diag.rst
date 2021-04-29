Flow-Dependent, Cross-Timescale Model Diagnostics Documentation
================================

Last update: 01/02/2021

The flow-dependent model diagnostics compares daily atmospheric circulation pattern,
or weather types, characteristics in reanalyses and models to analyze misrepresented physical
processes related to spatiotemporal systematic errors in those models. Relationships between these
biases and climate teleconnections (e.g., SST patterns, ENSO, MJO, etc.) can be explored in different
models.


Version & Contact info
----------------------

- Developer/point of contact: Ángel G. Muñoz (agmunoz@iri.columbia.edu) and Andrew W. Robertson (awr@iri.columbia.edu)

- Other contributors: Drew Resnick (drewr@iri.columbia.edu)


Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).


Required programming language and libraries
-------------------------------------------

Programming language: Python3

Python Libraries used: Xarray, numpy, pandas, sklearn, cartopy, matplotlib, PyWR

Required model output variables
-------------------------------

Geopotential height anomalies at 500 hPa

Rainfall

2-m temperature


References
----------

_ref-Muñoz:

Muñoz, Á. G., Yang, X., Vecchi, G. A., Robertson, A. W., & Cooke, W. F. (2017): PA Weather-Type-Based Cross-Time-Scale Diagnostic Framework for Coupled Circulation Models. *Journal of Climate*, **30** (22), 8951–8972,
`doi:10.1175/JCLI-D-17-0115.1 <https://doi.org/10.1175/JCLI-D-17-0115.1>`__.
