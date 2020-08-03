.. _ref-dev-extra-tips:

Extra tips for POD implementation
=================================


Other tips on implementation:
-----------------------------

#. Structure of the code package: Implementing the constituent PODs in accordance with the structure described in earlier sections makes it easy to pass the package (or just part of it) to other groups.

#. Robustness to model file/variable names: Each POD should be robust to modest changes in the file/variable names of the model output; see :doc:`Getting Started <start_config>` regarding the model data filename structure, :ref:`ref-example-env-vars` and :ref:`ref-Checklist` regarding using the environment variables and robustness tests. Also, it would be easier to apply the code package to a broader range of model output.

#. Save digested data after analysis: Can be used, e.g., to save time when there is a substantial computation that can be re-used when re-running or re-plotting diagnostics. See :ref:`ref-output-cleanup` regarding where to save the output.

#. Self-documenting: For maintenance and adaptation, to provide references on the scientific underpinnings, and for the code package to work out of the box without support. See :ref:`ref-Checklist`.

#. Handle large model data: The spatial resolution and temporal frequency of climate model output have increased in recent years. As such, developers should take into account the size of model data compared with the available memory. For instance, the example POD precip_diurnal_cycle and Wheeler_Kiladis only analyze part of the available model output for a period specified by the environment variables ``FIRSTYR`` and ``LASTYR``, and the convective_transition_diag module reads in data in segments.

#. Basic vs. advanced diagnostics (within a POD): Separate parts of diagnostics, e.g, those might need adjustment when model performance out of obs range.

#. Avoid special characters (``!@#$%^&*``) in file/script names.


See :ref:`ref-execute` and :doc:` framework operation walkthrough <dev_walkthrough>` for details on how the package is called. See the :doc:`command line reference <ref_cli>` for documentation on command line options (or run ``mdtf --help``).

Avoid making assumptions about the machine on which the framework will run beyond what’s listed here; a development priority is to interface the framework with cluster and cloud job schedulers to enable individual PODs to run in a concurrent, distributed manner.
