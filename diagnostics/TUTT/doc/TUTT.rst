Tropical Upper Tropospheric Trough Diagnostic Documentation
================================

Last update: 7/2/2021

Tropical upper-tropospheric troughs (TUTTs) are part of summertime stationary waves and provide a unified framework that can be used to better understand tropical cyclone (TC) variability over different basins. TUTTs are modulated by diabatic heating in the tropics, and they are also preferred regions for extratropical Rossby wave breaking (RWB). A stronger TUTT is associated with frequent occurrences of RWB, enhanced vertical wind shear, and reduced tropospheric moisture. Variations in these environmental conditions lead to suppressed basin-wide TC activity on the seasonal timescale. Identifying deficiencies in representing TUTTs has important implications for the improved regional TC simulation in climate models. A better understanding of how TUTTs will change as climate warms also increases our confidence in future TC projection. This diagnostic package is used to evaluate 200-hPa TUTT area in both climate models and reanalysis datasets.

Version & Contact info
----------------------

.. '-' starts items in a bulleted list:
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#bullet-lists

- Version/revision information: version 1.0 (7/2/2021)
- PI: Zhuo Wang, zhuowang@illinois.edu, DAS UIUC)
- Developer/point of contact (Zhuo Wang, Gan Zhang, Chuan-Chieh Chang, and Jiacheng Ye/Zhuo Wang, zhuowang@illinois.edu, DAS UIUC)

.. Underline with '^'s to make a third-level heading.

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).

Functionality
-------------

The current package consists of following functionalities:

(1) Calculates geostrophic zonal winds (Ug) using 200-hPa geopotential height with a fixed Coriolis parameter at 15N.

(2) Identifies positions of the circumglobal contour of the long-term seasonal-mean Ug. The value of Ug can be specified by the user, usually ranges from 1 to 2 m/s. The zonal-mean latitude of the circumglobal contour is chosen as the reference latitude.

(3) The TUTT index is estimated from the area where the circumglobal contour of seasonal-mean Ug extends southward of the reference latitude.

(4) In addition to TUTT area, the package also calculates the strengths and central locations of TUTTs.

(5) The reference latitude, area, strength, central location of TUTT, as well as the positions of circumglobal Ug contour can be saved as .txt files. User can choose whether the aforementioned information is outputted or not.

(**) cropping.py can be referenced if code is needed to either shift the grid of your data
or to crop your data to a specified region

As a module of the MDTF code package, all scripts of this package can be found under
``mdtf/MDTF_$ver/diagnostics/TUTT

Required programming language and libraries
-------------------------------------------

Python3 packages: "netCDF4", "skimage", "numpy", "scipy", "shapely.geometry", "cartopy"

Required model input variables
-------------------------------

Time-varying 2-D geopotential height fields at 200 hPa (unit: gpm). 200-hPa geopotneitla height should be the monthly-mean field. Horizontal resolution of the geopotential height data can be deceided by the user. Note that the longitude index of the data must goes from west to east (0-360E).


References
----------

.. _ref-Muñoz1:

Wang, Z., Zhang, G., Dunkerton, T. J., & Jin, F. F. (2020). Summertime stationary waves integrate tropical and extratropical impacts on tropical cyclone activity. Proceedings of the National Academy of Sciences of the United States of America, 117(37), 22720-22726. https://doi.org/10.1073/pnas.2010547117

Chuan-Chieh Chang and Zhuo's paper is under developing...



More about this diagnostic
--------------------------

a. Weak westerly wind sometimes extends southward of the equator and connects to the westerlies over the Southern Hemisphere in reanalysis datasets. We therefore choose to use the zonal geostrophic wind with a fixed Coriolis parameter instead of the total zonal wind.

b. Pacific TUTT and Atlantic TUTT sometimes are connected to each other. This has been observed during the years when the 200-hPa anticyclone over the Central America is weak. The longitude used to divide two TUTTs can be decided by the following options:

    1. The script calculates the averaged 200-hPa geopotential height between 20 to 30 N, and then searches the longitude where the averaged 200-hPa geopotential height is the largest between 120 W to 80 W.   This option uses the approximate location of subtropical ridge over the North America as the dividing longitude.
    2. The dividing longitude is specified by the user.

.. figure:: TUTT_example.png
   :align: center
   :width: 75 %
   

   Figure 1. Solid gray curve denotes the postions where the climatological seasonal-mean Ug equals 2 m/s in JRA-55 reanalysis from 1958 to 2014. Dashed white line indicates the reference latitude. Estimated Pacific TUTT and Atlantic TUTT indices are shown above the figure. Background shaded field is climatolgoical 200-hPa geopotential height (gpm). 
   

Descriptions of outputted .txt files:

TUTT_contour_lat_1958-Ug_2.0.txt/TUTT_contour_lon_1958-Ug_2.0.txt
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The corrdinates (latitude and longitude) of TUTT contour given by 200 hPa zonal geostrophic wind (Ug) at value 2 m/s.

TUTT_ref_lat_1958-Ug_2.0.txt/TUTT_contour_lon_1958-Ug_2.0.txt
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The corrdinates (latitude and longitude) of reference latitude.


TUTT_contour_length_1958-Ug_2.0.txt
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Length (i.e., number of points) of TUTT contour.

tutt_Area_lat-1958-1958JASO-Ug_2.0.txt/tutt_Area_lon-1958-1958JASO-Ug_2.0.txt
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The central locations (latitude and longitude) of Pacific and Atlantic TUTTs. When calculating averaged latitude/longitude, each grid point has the same weighting.

tutt_UG.wt_lat-1958-1958JASO-Ug_2.0.txt/tutt_UG.wt_lon-1958-1958JASO-Ug_2.0.txt
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The central locations (latitude and longitude) of Pacific and Atlantic TUTTs. When calculating averaged latitude/longitude, each grid point is weighted by the value of Ug.


tutt_area-1958-1958JASO-Ug_2.0.txt
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The area of Pacific and Atlantic TUTTs.

tutt_intensity-1958-1958JASO-Ug_2.0.txt
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The intensity/strength of Pacific and Atlantic TUTTs.

tutt_ref.latitude-1958-1958JASO-Ug_2.0.txt
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The value of reference latitude.
