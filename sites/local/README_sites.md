Site-specific configuration README
----------------------------------

To enable more consistent treatment of site-specific code, v3.0 beta 3 introduces
a "--site/-s" command-line option to the top-level script at src/mtdf.py. When 
set, it adds code and configuration files in the chosen subdirectory of sites/
to the general framework code in src/, allowing site-specific customizations to
the MDTF framework (eg, enabling data search from a lab's internally-accessible
filesystem.)

The default value for the "--sites" flag is "local": any user can place their
customized configuration files in this directory, and the values in those files 
will override the framework defaults in src/. This lets you set unchanging 
configuration options (eg, `OBS_DATA_ROOT`, the path to your local copy of the
supporting observational data) once, in a file in this directory, without having
to worry about passing the value for these options every time you call the 
framework.

In turn, options you explicitly specify on the command line will override any
defaults defined from files in this directory.

This feature will be fully documented and announced in v3.0 beta 4.
