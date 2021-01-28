'''
This file is part of the precip_buoy_diag module of the MDTF code
package (see mdtf/MDTF-diagnostics/LICENSE.txt).

DESCRIPTION:


REQUIRED MODULES:

AUTHORS: Fiaz Ahmed

LAST EDIT:

REFERENCES: 

'''

import os
from precip_buoy_diag_util import precipbuoy


### Feed input paths and temporary output directory ###
input_paths=[os.environ["ta_file"],os.environ["hus_file"],
os.environ["pr_file"],os.environ["ps_file"]]

### initialize pod
pb_pod=precipbuoy(os.environ["temp_file"])

### Check if pre-processed files are available.
### This is done crudely: we check if the temp_dir is empty.
if pb_pod.preprocessed:
    print('PREPROCESSED FILES AVAILABLE. MOVING ONTO BINNING...')
else:
    print('PREPROCESSING REQUIRED....')
    pb_pod.preprocess()

