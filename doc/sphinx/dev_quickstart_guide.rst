Developer's quickstart guide
============================

This walkthrough contains information for developers wanting to contribute a process-oriented diagnostic (POD) module to the MDTF framework. We assume that you have read the `Getting Started <https://mdtf-diagnostics.readthedocs.io/en/latest/_static/MDTF_getting_started.pdf>`__, and have followed the instructions therein for installing and testing the MDTF package, thus having some idea about the package structure and how it works. We further recommend running the framework on the sample model data with both ``save_ps`` and ``save_nc`` in the configuration input ``src/default_tests.jsonc`` set to ``true``. This will preserve directories and files created by individual PODs, and help you understand how a POD is expected to write output.

For developers already familiar with version 2.0 of the framework, :doc:`section 2 <dev_migration>` concisely summarizes changes from v2.0 to facilitate migration to v3.0. New developers can skip this section, as the rest of this walkthrough is self-contained.

For new developers, :doc:`section 3 <dev_checklist>` provides a to-do list of steps for implementing and integrating a POD into the framework, with more technical details in subsequent sections. :doc:`Section 4 <dev_instruct>` discusses the choice of programming languages, managing language and library dependencies through Conda, how to make use of and extend an existing Conda environment for POD development, and create a new Conda environment if necessary. In :doc:`section 5 <dev_walkthrough>`, we walk the developers through the workflow of the framework, focusing on aspects that are relevant for the operation of individual PODs, and using the `Example Diagnostic POD <https://github.com/NOAA-GFDL/MDTF-diagnostics/tree/main/diagnostics/example>`__ as a concrete example to illustrate how a POD works under the framework.

We require developers to manage POD codes and submit them through `GitHub <https://github.com/NOAA-GFDL/MDTF-diagnostics>`__. See :doc:`section 8 <dev_git_intro>` for how to manage code through the GitHub website and, for motivated developers, how to manage using the ``git`` command.

[@@@Moved from instruct:

Scope of the analysis your POD conducts
---------------------------------------

See the `BAMS article <https://doi.org/10.1175/BAMS-D-18-0042.1>`__ describing version 2.0 of the framework for a description of the project’s scientific goals and what we mean by a “process oriented diagnostic” (POD). We encourage PODs to have a specific, focused scope.

PODs should be relatively lightweight in terms of computation and memory requirements (eg, run time measured in minutes, not hours): this is to enable rapid feedback and iteration cycles to assist users in model development. Bear in mind that your POD may be run on model output of potentially any date range and spatial resolution. Your POD should not require strong assumptions about these quantities, or other details of the model’s operation. @@@]
