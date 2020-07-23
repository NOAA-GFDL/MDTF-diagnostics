Developer's quickstart guide
============================

This walkthrough contains information for developers wanting to contribute a process-oriented diagnostic (POD) module to the MDTF framework. We assume that you have read the `Getting Started <https://mdtf-diagnostics.readthedocs.io/en/latest/_static/MDTF_getting_started.pdf>`__, and have followed the instructions therein for installing and testing the MDTF package, thus having some idea about the package structure and how it works. We further recommend running the framework on the sample model data with both ``save_ps`` and ``save_nc`` in the configuration input ``src/default_tests.jsonc`` set to ``true``. This will preserve directories and files created by individual PODs, and help you understand how a POD is expected to write output.

For developers already familiar with version 2.0 of the framework, :doc:`section 2 <dev_migration>` concisely summarizes changes from v2.0 to facilitate migration to v3.0. New developers can skip this section, as the rest of this walkthrough is self-contained.

For new developers, :doc:`section 3 <dev_checklist>` provides a to-do list of steps for implementing and integrating a POD into the framework, with more technical details in subsequent sections.

We require developers to manage POD codes and submit them through `GitHub <https://github.com/NOAA-GFDL/MDTF-diagnostics>`__. See :doc:`section 8 <dev_git_intro>` for how to manage code through the GitHub website and, for motivated developers, how to manage using the ``git`` command.
