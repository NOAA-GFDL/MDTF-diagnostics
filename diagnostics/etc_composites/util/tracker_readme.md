# MCMS TRACKER

***Created by: Jeyavinoth Jeyaratnam***

***Last Modified: March 16th, 2022***

***Branched off from Mike Bauer's MCMS Tracking Algorithm***

This code is modified version of Mike Bauer's MCMS Tracking Algorithm using Python.

The "tracker" folder contains the MCMS Cyclone Tracker. 
The "datacyc" folder contains the code to grab data around the tracked cyclones. 

#### Notes: 
1) Current version of the code runs on Python 3 
This code was tested on v3.6, because netcdftime is run on this version under the conda environment. This might cause issues with the basemap library (check below).

This code was tested on v3.6, because netcdftime is run on this version under the conda environment. This might cause issues with the basemap library (check below).

#### Changes to Mike's code
* necessary integer division was changed in the code
* cPickle was changed to pickle (should not be an issue)
* hard coded in some imports, cuz of the way "exec" command works in python3
* dictionaries in python2 are not ordered dicts, so the keys were sorted in python2 code and python3 code to compare consistently
* tree\_travesal\_v4.py code had issues with the list being not ordered in python2, so I changed the python2 code to have an ordered dict for fair comparison of the python3 tracker 


## Installation of necesssary libraries

You can setup conda to run python on your machine.

Then create a new conda environment with Python version 3.6. 

* <p>conda create -n tracker python=3.6</p>

Activate the conda environment in your terminal using:

* <p>conda activate tracker</p>

Then install the following libraries: 

* <p>conda install scipy</p>

* <p>conda install matplotlib</p>

* <p>conda install numpy</p>

* <p>conda install basemap</p>

* <p>conda install proj4</p>
  
* <p>conda install netcdf4</p>

* <p>conda install cython</p> - this is needed to create the \*.so files below

* <p>conda install -c conda-forge netcdftime</p>


Then you have to run the following (make sure to cd into your tracker folder):

* python3 setup\_g2l\_v4.py build\_ext --inplace

* python3 setup\_gcd\_v4.py build\_ext --inplace

* python3 setup\_rhumb\_line\_nav\_v4.py build\_ext --inplace

These commands create 3 \*.so (shared objects) operators in the current directory. You have to rename the appropriate \*.so file. 

* g2l\_v4.cpython......so -> g2l\_v4.so

* gcd\_v4.cpython.....so -> gcd\_v4.so

* rhumb\_line\_nav\_v4.cpython......so -> rhumb\_line\_nav\_v4.so

Note that in the current directory, these \*.so files already exist, just to show an example of what they look like.

# Additional issues faced when setting up and running the code

netcdftime library requires 3.6, so conda will downgrade your version of python to 3.6

In python3.6 right now, basemap has an issue that is not fixed, so you will have to edit line 5111 from <environment\_base\_folder>/lib/python3.6/site-packages/mpl\_toolkits/basemap/\_\_init\_\_.py file, where for example the envrionment\_base\_folder=/home/USER/anaconda3/envs/tracker

from:

  return list(map(\_addcyclic,arr[:-1]) + [\_addcyclic\_lon(arr[-1])])

to:

  return list(map(\_addcyclic,arr[:-1])) + [\_addcyclic\_lon(arr[-1])]

Also, you will have to edit line 5096 in the above file (if not the code will print out repeated warnings on this issue).

from:

  return npsel.concatenate((a,a[slicer]),axis=axis)

to:

  return npsel.concatenate((a,a[tuple(slicer)]),axis=axis)



# MAC OSX specific issues 

In order to run this tracker code, you will have to run it using:

You will have to update GCC libraries by installing xcode from the terminal

"xcode-select --install"

and installing the SDK headers from the terminal

"open /Library/Developer/CommandLineTools/Packages/macOS\_SDK\_headers\_for\_macOS\_10.14.pkg"

In MAC OSX, you might face an issue with the plots created using matplotlib library in python. 

You have to add the following lines in setup\_cam6\_v4.py file, make sure the following lines are in the correct order:

import matplotlib

matplotlib.use('TKAgg')

import matplotlib.pyplot as plt


## Pre-Setup of Sea Level Pressure data files

Convert all the SLP files into the appropriate 6 hourly slp.YEAR.nc files (where YEAR varies). This has to be done by the user, and the slp files should in the correct format for the tracker. 

SLP netcdf files should have the following variables: lat (degrees\_north), lon (degrees\_east), time(hours since start\_year/01/01 00:00:00), slp (3d array with dimensions [time, lat, lon], with units "mb").

In the netcdf the "calendar" type has to be set for the time variables. 
The time calendar must be set as "365\_day" or "proleptic\_gregorian," depending on your data. 


***Internal Note:*** 

*Some of the SLP convert code I created is in the folder /slp_converts/<model_name>*

*For Vee’s data I created a file that converts year 11 to 41, given a start year to the appropriate slp files.
This file is in the folder, called “convert\_vee.py”*

*In this file, you have to change the output folder location, input folder location, start\_year (the year to start labelling the slp files from) and the model year range (model years go from 00 to 40).*

*Additionally adjust in\_file\_format variable to indicate the format in which the file is organized. The %04d in the file\_format will be replaced by the model years within the range given in the model\_year\_range variable.*

*out\_file\_format can be changed as well, but for this tracker it should be kept as slp.YEAR.nc.*

*After setting up the variables on the top of convert\_vee.py, run the python code using 
“Python convert\_vee.py” → this should create slp.YEAR.nc files in the output folder.*


## Setting up the Tracker 

Edit the defines.py file, to make sure that you point to the correct folders. 
This file contains all the variables that need to be setup to run the MCMS tracker.

***Setup defines.py***

* source\_code\_folder -> ‘/mnt/drive1/jj/MCMS/V1/tracker’ the main source code location for the tracker, this will be the folder in which you clone this repository into. 

* slp\_data\_direcotry -> directory containing the slp data in the format needed by the tracker

* topo\_file → path to the topographic file that is in the format of the slp data

* model → model name that is provided to the tracker code, all folders created will be related to this 

* main\_folder\_location -> location in which to create a directory to setup the tracker code

* over\_write\_years -> years to which to run the tracker code

<br>
***Explanation of the additional directories:***

The remaining locations are auto calculated by the defnes.py code. 

Source code folder is the directory extension of the code location given above (/mnt/drive1/jj/MCMS/V1/tracker). 

The code in this folder will be copied into the new directory specified by main\_folder\_location and model. 

In the main\_folder\_location, the code will create a folder with the name “model”, and copy over the contents of the code into this folder. 

For now: over\_write\_years should be specified to indicate the range of years to track cyclones for. 
Future: over\_write\_years can be left as an empty array, the code will find the min and max years for slp and track the data for all the available years in the folder.

The necessary folder path needed by the tracker are auto computed by defines.py. 

**Additional Options**

create\_matlab\_dictionaries is a flag that is set to convert the tracked cyclones into matlab dictionaries. This is needed if you want to run the grab datacycs code. 

### Running the Tracker

Run the tracker code after setting up the defines.py file. “python3 run\_tracker.py.”

This will create the necessary folders and run the tracker code.

The output files are then converted to readable formats. 

You have to run read\_mcms\_v4.py with template\_temp\_multi\_1.py first, followed by template\_temp\_multi\_2.py. This is automatically done by run\_tracker.py.

Finally the outputs are converted to matlab dictionaries using main\_create\_dicts.py. This step can be controlled using the create\_matlab\_dictionaries flag in defines.py.



