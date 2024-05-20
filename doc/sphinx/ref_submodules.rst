Running Submodules
===============================
Functions from external packages can be called by MDTF with their inclusion in the json or yml file supplied to the framework.

Inclusion in JSON file
------------------------------
The following block in your JSON or yml file is required for the submodule to launch:

.. code-block:: js

  "module_list":
   {
     "${MODULE_NAME}":
       {
         "${FUNCTION_NAME}":
	   {
	     "args":
               {
                 "arguments go here"
               }
           }
       }
   },

Where, ${MODULE_NAME} is the name for the package you want to launch a function from, ${FUNCTION_NAME} is the function you want to call, and ${FUNCTION_ARGS} is the arguments to be passed to the function.

TempestExtremes Example
------------------------
As an example, we will build and run TempestExtremes (TE) from MDTF. First, clone the latest TE with a python wrapper. As of writing, this can be found 'here <https://github.com/amberchen122/tempestextremes/>'_
In the cloned directory, it can be built using the commands:

.. code-block::

   python setup.py build_ext
   python setup.py install

Now, in our JSON file we can call the function DetectNodes by including the following:

.. code-block:: js

   "module_list":
     {
     "TempestExtremes":
       {
         "DetectNodes":
	   {
	     "args":
               {
                 "--in_data":"./test/cn_files/outCSne30_test2.nc",
                 "--timefilter":"6hr",
                 "--out":"out1.dat",
                 "--searchbymin":"MSL",
		 "--closedcontourcmd": "PRMSL_L101,200.,4,0;TMP_L100,-0.4,8.0,1.1",
                 "--mergedist":"6.0",
                 "--outputcmd": "MSL,min,0;_VECMAG(VAR_10U,VAR_10V),max,2;ZS,min,0",
                 "--latname":"lat",
                 "--lonname":"lon"
               }
           }
       }
   },

Multiple packages can be ran if they are nested in "module_list". Multiple functions can be called or even the same one again.