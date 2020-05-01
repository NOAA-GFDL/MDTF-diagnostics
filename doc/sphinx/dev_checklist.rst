Development Checklist
=====================

The following are the necessary steps for the module implementation and integration into the framework. The POD name tag used in the code should closely resemble the full POD name but should not contain any space bar or special characters. Note that the convective_transition_diag tag here is used repeatedly and consistently for the names of sub-directories, script, and html template. Please follow this convention so that mdtf.py can automatically process through the PODs. 

All the modules currently included in the code package have the same structure, and hence the descriptions below apply: 

1. Provide all the scripts for the convective_transition_diag POD in the sub-directory DIAG_HOME/var_code/convective_transition_diag. Among the provided scripts, there should be a template html file convective_transition_diag.html, and a main script convective_transition_diag.py that calls the other scripts in the same sub-directory for analyzing, plotting, and finalizing html. 

2. Provide all the pre-digested observation data/figures in the sub-directory DATA_IN/obs_data/convective_transition_diag. One can create a new html template by simply copying and modifying the example templates in DIAG_HOME/var_code/html/html_template_examples. Note that scripts therein are exact replications of the html-related scripts in the example PODs, serving merely as a reference, and are not called by ``mdtf.py``. 

3. Provide documentation following the templates: 

   A. Provide a comprehensive POD documentation, including a one-paragraph synopsis of the POD, developers’ contact information, required programming language and libraries, and model output variables, a brief summary of the presented diagnostics as well as references in which more in-depth discussions can be found (see an example). 

   B. All scripts should be self-documenting by including in-line comments. The main script convective_transition_diag.py should contain a comprehensive header providing information that contains the same items as in the POD documentation, except for the "More about this diagnostic" section. 

   C. The one-paragraph POD synopsis (in the POD documentation) as well as a link to the Full Documentation should be placed at the top of the template convective_transition_diag.html (see example).  

4. Test before distribution. It is important that developers test their POD before sending it to the MDTF contact. Please take the time to go through the following procedures:  

   A. Test how the POD fails. Does it stop with clear errors if it doesn’t find the files it needs? How about if the dates requested are not presented in the model data? Can developers run it on data from another model? If it fails, does it stop the whole `mdtf.py` script? (It should contain an error-handling mechanism so the main script can continue). Have developers added any code to `mdtf.py`? (Do not change `mdtf.py`! — if you find some circumstance where it is essential, it should only be done in consultation with the MDTF contact). 

   B. Make a clean tar file. For distribution, a tar file with obs_data/, var_code/, namelist, and model data that developers have thoroughly tested is needed. These should not include any extraneous files (output NetCDF, output figures, backups, ``pyc``, ``*~``, or ``#`` files). The model data used to test (if different from what is provided by the MDTF page) will need to be in its own tar file. Use ``tar -tf`` to see what is in the tar file. Developers might find it helpful to consult the script used to make the overall distributions mdtf/make_tars.sh.
   
   C. Final testing: Once a tar file is made, please test it in a clean location where developers haven’t run it before. If it fails, repeat steps 1)-3) until it passes. Next, ask a colleague or assign a group member not involved in the development to test it as well — download to a new machine to install, run, and ask for comments on whether they can understand the documentation. 

#. Post on an ftp site and/or email the MDTF contact. 


