# Changes made to the code outside of the "eulerian-storm-track" folder

These changes were necessary to get the code running from the "develop" branch from MDTF-diagnostics github repo.

When I run the code using the "master" branch, I get the following error:



    ==== Starting src/mdtf.py
    Found /mnt/home/jj/jimmy/mdtf/MDTF-diagnostics
    Found /mnt/home/jj/jimmy/mdtf/inputdata/model
    Found /mnt/home/jj/jimmy/mdtf/inputdata/obs_data
    Found /mnt/home/jj/jimmy/mdtf/MDTF-diagnostics/wkdir
    Found /mnt/home/jj/jimmy/mdtf/MDTF-diagnostics/wkdir
    Traceback (most recent call last):
      File "src/mdtf.py", line 106, in <module>
        config = argparse_wrapper()
      File "src/mdtf.py", line 99, in argparse_wrapper
        config.verbose = verbose
    AttributeError: 'dict' object has no attribute 'verbose'


So in order to avoid the above error, I use the develop branch, even though it is not a stable release.

## List of changes:

1. I don't run my code with conda, instead I use virtualenv. Hence I change the **src/mdtf_settings.json** file. The documentation states to change **src/config.yml**, but that file doesn't exist in the **develop** branch. In the **src/mdtf_settings.json**, I change the environment_manager to **None**. 
2. In the same **src/mdtf_settings.json** file, I change the **pod_list** in **case_list** to only run for **Wheeler_Kiladis** and **eulerian-strom-track** (my code). This is just for testing purposes.
3. In addition, I turn off **CASENAME: "Lmon_GISS...."**
4. There may be additional changes to the code, just revert back to the original if needed and add in **eulerian-storm-track** to your **pod_list**.

