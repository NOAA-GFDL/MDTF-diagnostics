Migration from framework v2.0
=============================

In this section we summarize issues to be aware of for developers familiar with the organization of version 2.0 of the framework. New developers can skip this section, as the rest of this documentation is self-contained.

Getting Started and Developer's Walkthrough
-------------------------------------------

A main source of documentation for v2.0 of the framework were the "Getting Started" and "Developer's Walkthrough" documents. Updated versions of these documents are:

- `Getting Started v3.0 (PDF) <https://mdtf-diagnostics.readthedocs.io/en/latest/_static/MDTF_getting_started.pdf>`__
- `Developer's Walkthrough v3.0 (PDF) <https://mdtf-diagnostics.readthedocs.io/en/latest/_static/MDTF_walkthrough.pdf>`__

**Note**: these documents contain a *subset* of information available on this website, rather than new material: the text is reorganized to be placed in the same order as the v2.0 documents, for ease of comparison.

Checklist for migrating a POD from v2.0
---------------------------------------

Here we list the broad set of tasks needed to update a POD written for v2.0 of the framework to v3.0.

- **Update settings and varlist files**: In v3.0 these have been combined into a single ``settings.jsonc`` file. See the settings file :doc:`guide <./dev_settings_quick>`, :doc:`reference <./ref_settings>`, and `example <https://github.com/NOAA-GFDL/MDTF-diagnostics/tree/main/diagnostics/example/settings.jsonc>`__ for descriptions of the new format.
- **Update references to framework environment variables**: See the table below for an overview, and the :doc:`reference <./ref_envvars>` for complete information on what environment variables the framework sets. *Note* that your POD should not use any hard-coded paths or variable names, but should read this information in from the framework's environment variables.
- **Resubmit digested observational data**: To minimize the size of supporting data users need to download, we ask that you only supply observational data specifically needed for plotting (preferably size within MB range), as well as any code used to perform that data reduction from raw sources.
- **Remove HTML templating code**: Version 2.0 of the framework required that your POD's top-level driver script take particular steps to assemble its HTML file. In v3.0 these tasks are done by the framework: all that your POD needs to do is generate figures of the appropriate formats and names in the specified folders, and the framework will convert and link them appropriately.

Conversion from v2.0 environment variables
------------------------------------------

In v3.0, the paths referred to by the framework's environment variables have been changed to be specific to your POD. The variables themselves have been renamed to avoid possible confusion. Here's a table of the appropriate substitutions to make:

.. list-table:: Environment variable name conversion
   :header-rows: 1

   * - Path Description
     - v2.0 environment variable expression
     - Equivalent v3.0 variable
   * - Top-level code repository
     - ``$DIAG_HOME``
     - No variable set: PODs should not access files outside of their own source code directory within ``$POD_HOME``
   * - POD's source code
     - ``$VARCODE``/<pod name>
     - ``$POD_HOME``
   * - POD's observational/supporting data
     - ``$VARDATA``/<pod name>
     - ``$OBS_DATA``
   * - POD's working directory
     - ``$variab_dir``/<pod name>
     - ``$WK_DIR``
   * - Path to requested NetCDF data file for <variable name> at date frequency <freq>
     - Currently unchanged: ``$DATADIR``/<freq>/``$CASENAME``.<variable name>.<freq>.nc
     -
   * - Other v2.0 paths
     - ``$DATA_IN``, ``$DIAG_ROOT``, ``$WKDIR``
     - No equivalent variable set. PODs shouldn’t access files outside of their own directories; instead use one of the quantities above.
