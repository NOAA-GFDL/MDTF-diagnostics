'''
This file is part of the precip_buoy_diag module of the MDTF code
package (see mdtf/MDTF-diagnostics/LICENSE.txt).

DESCRIPTION:


REQUIRED MODULES:

AUTHORS: Fiaz Ahmed

LAST EDIT:

REFERENCES: 

'''

from precip_buoy_diag_util import precipbuoy


### Feed the temporary output directory ###
### 

### initialize pod
pb_pod=precipbuoy()

if pb_pod.binned:
    print('BINNED OUTPUT AVAILABLE. MOVING ONTO PLOTTING...')
    pb_pod.plot()

else:
    print('BINNED OUTPUT UNAVAILABLE. CHECKING FOR PREPROCESSED FILES')
        
    ### Check if pre-processed files are available.

    if pb_pod.preprocessed:
        print('PREPROCESSED FILES AVAILABLE. MOVING ONTO BINNING...')
        pb_pod.bin()
        print('BINNING DONE. NOW PLOTTING...')
        pb_pod.plot()
    
    else:
        print('PREPROCESSING REQUIRED....')
        pb_pod.preprocess()
        print('PREPROCESSING DONE. NOW BINNING...')
        pb_pod.bin()
        print('BINNING DONE. NOW PLOTTING...')
        pb_pod.plot()



