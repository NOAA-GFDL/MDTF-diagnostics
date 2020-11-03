**Description**
Include a summary of the change, and link the associated issue (if applicable).  
List any dependencies that are required for this change.

Fixes # (issue)  

**How Has This Been Tested?**
Please describe the tests that you ran to verify your changes in enough detail that  
someone can reproduce them. Include any relevant details for your test configuration  
such as the compiler, operating system, and netcdf version. 

**Checklist:**
- [ ] I have performed a self-review of the code
- [ ] All of my scripts are in the diagnostics/ subdirectory, and include a main_driver script  
      template html, and settings.jsonc
- [ ] The main_driver script header has all of the information in the POD documentation,  
      excluding the "More about this diagnostic" section
- [ ] The POD directory and html template have the same short name as my POD
- [ ] The html template has a 1-paragraph synopsis of the POD and links to the main documentation
- [ ] If applicable, I've added a .yml file to src/conda, and my environment builds with  
      conda_env_setup.sh 
- [ ] I have commented the code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation in the POD's doc/ subdirectory
- [ ] I have created the directory input_data/obs_data/[pod short name] with all numerical digested data
- [ ] Each digested data file is 3 MB or less

