Flow-Dependent Model Diagnostic Documentation
================================

Last update: 5/14/2021

The flow-dependent model diagnostics compares daily atmospheric circulation patterns, or weather types, characteristics in reanalyses and models to analyze misrepresented physical processes related to spatiotemporal systematic errors in those models. Relationships between these biases and climate teleconnections (e.g., SST patterns, ENSO, MJO, etc.) can be explored in different models.

Version & Contact info
----------------------

.. '-' starts items in a bulleted list:
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#bullet-lists

- Version/revision information: version 1 (5/14/2021)
- PI (Ángel G. Muñoz, IRI Columbia University, agmunoz@iri.columbia.edu)
- Developer/point of contact (Ángel G. Muñoz, agmunoz@iri.columbia.edu and Andrew W. Robertson, awr@iri.columbia.edu, IRI Columbia University)
- Other contributors (Drew Resnick, IRI Columbia University, drewr@iri.columbia, James Doss-Gollin)

.. Underline with '^'s to make a third-level heading.

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).

Functionality
-------------

The currently package consists of following functionalities:

(1) Calculation of climatologies and anomalies for the input fields (ClimAnom_func.py)

(2) Calculation of weather types spatial patterns (WeatherTypes.py)

(3) Calculation of weather types temporal characteristics (to be added soon)

(4) Procrustes analysis (to be added soon)

(**) cropping.py can be referenced if code is needed to either shift the grid of your data
or to crop your data to a specified region

As a module of the MDTF code package, all scripts of this package can be found under
``mdtf/MDTF_$ver/diagnostics/flow_dep_diag``

.. and pre-digested observational data under mdtf/inputdata/obs_data/convective_transition_diag

