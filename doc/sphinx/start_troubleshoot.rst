Troubleshooting
===============

Here we provide a short list of problems the MDTF team had previously encountered.

The error message "convert: not authorized ..." shows up
--------------------------------------------------------

The MDTF package generates figures in the PostScript (PS) format, and then uses the ``convert`` command (from the `ImageMagick <https://imagemagick.org/index.php>`__ software suite) to convert the PS files to PNG files. The convert error can occur after recent updates and can be solved as follows (requires permission): 

In the file ``/etc/ImageMagick/policy.xml``, change the ``<policy domain="coder" rights="none" pattern="PS" />`` to 
``<policy domain="coder" rights="read|write" pattern="PS" />``.

The folder name ``ImageMagick`` may depend on its version, e.g., ``ImageMagick-6``.

Issues with standalone NCL installation
---------------------------------------

Many Linux distributions (Ubuntu, Mint, etc.) have offered a way of installing `NCL <https://www.ncl.ucar.edu/>`__ through their system package manager (apt, yum, etc.) This method of installation is not recommended: users may encounter errors when running the example PODs provided by NCAR, even if the environment variables and search path have been added. 

The recommended method to install standalone NCL is by downloading the pre-compiled binaries from https://www.ncl.ucar.edu/Download/install_from_binary.shtml. Choose a download option according to the Linux distribution and hardware, unzip the file (results in 3 folders: ``bin``, ``include``, ``lib``), create a folder ncl under the directory ``/usr/local`` (requires permission) and move the 3 unzipped folders into ``/usr/local/ncl``. Then add the following lines to the ``.bashrc`` script (under the user’s home directory; may be different if using shells other than bash, e.g., ``.cshrc`` for csh): 

::

   export NCARG_ROOT=/usr/local/ncl 
   export PATH:$NCARG_ROOT/bin:$PATH 

Issues with the convective transition POD
-----------------------------------------

The plotting scripts of this POD may not produce the desired figures with the latest version of matplotlib (because of the default size adjustment settings). The matplotlib version comes with the Anaconda 2 installer, version 5.0.1 has been tested. The readers can switch to this older version.

Depending on the platform and Linux distribution/version, a related error may occur with the error message "... ImportError: libcrypto.so.1.0.0: cannot open shared object file: No such file or directory". One can find the missing object file ``libcrypto.so.1.0.0`` in the subdirectory ``~/anaconda2/pkgs/openssl-1.0.2l-h077ae2c_5/lib/``, where ``~/anaconda2/`` is where Anaconda 2 is installed. The precise names of the object file and openssl-folder may vary. Manually copying the object file to ``~/anaconda2/lib/`` should solve the error. 
