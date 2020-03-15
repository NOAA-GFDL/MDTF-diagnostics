Environment variables for MDTF diagnostics
==========================================

Paths
-----

- ``OBS_DATA``: Top-level directory for any observational data you provide as the POD's author. This should be treated as read-only, and PODs shouldn't
- ``POD_HOME``: Top-level directory of POD's code (of the form ``.../MDTF-diagnostics/diagnostics/<your POD's name>``).
- ``DATADIR``: Top-level directory for
- ``WK_DIR``: Top-level working directory , which is also the location that final results should be written to.


Variables
---------


Coordinate axes
---------------




Model run information
---------------------

- ``CASENAME``: User-provided label for the model run being analyzed.
- ``FIRSTYR``, ``LASTYR``: Four-digit years describing the analysis period.