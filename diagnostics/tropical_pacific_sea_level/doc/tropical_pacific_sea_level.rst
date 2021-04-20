.. This is a comment in RestructuredText format (two periods and a space).

.. Note that all "statements" and "paragraphs" need to be separated by a blank 
   line. This means the source code can be hard-wrapped to 80 columns for ease 
   of reading. Multi-line comments or commands like this need to be indented by
   exactly three spaces.

.. Underline with '='s to set top-level heading: 
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#section-structure

Tropical Pacific Sea Level Diagnostic Documentation 
================================

Last update: 11/16/2020

Sea level rise is closely related to climate variability and change. It has 
important socio-economic impacts on many coastal cities and island nations. 
The largest sea level variability occurs in the tropical Pacific, with a 
magnitude of ~200mm on interannual timescales during El Niño. This sea level 
variability is superimposed on long-term sea level trends and closely related
to global temperature evolution and other climate indices. A detailed 
understanding of climate model’s ability in simulating sea level variability 
and change in the tropical Pacific is crucial for future projections of 
climate and sea level.     


.. Underline with '-'s to make a second-level heading.

Version & Contact info
----------------------

.. '-' starts items in a bulleted list: 
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#bullet-lists


- Version/revision information: version 1 (11/16/2020)
- PI (Jianjun Yin, University of Arizona, yin@arizona.edu)
- Developer/point of contact (Chia-Wei Hsu, University of Arizona, chiaweih@arizona.edu)


.. Underline with '^'s to make a third-level heading.

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 
Unless you've distirbuted your script elsewhere, you don't need to change this.

Functionality
-------------

The main script generates the tropical Pacific dynamic sea level
and wind stress curl scatter plots at different time scales
due to their strong dependency from Ekman pumping/suction
and barotropic response over the ocean.

Python function used
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- spherical_area.cal_area     : generate area array based on the lon lat of data
- dynamical_balance2.curl_var_3d : calculate wind stress curl in obs (for Dataset with time dim)
- dynamical_balance2.curl_var    : calculate wind stress curl in obs (for Dataset without time dim)
- dynamical_balance2.curl_tau_3d : calculate wind stress curl in model (for Dataset with time dim)
- dynamical_balance2.curl_tau    : calculate wind stress curl in model (for Dataset without time dim)
- xr_ufunc.da_linregress : linregress for Dataset with time dim



Required programming language and libraries
-------------------------------------------

The programming language is python version 3 or up. The third-party libraries
include "matplotlib", "xarray", "cartopy","cftime","numpy". The conda environment
can be set to _MDTF_python3_base.

Required model output variables
-------------------------------

With monthly frequency from the model output. This diagnostic needs

input model variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- tauuo (surface wind stress in the x direction from native model output resolution/grid) 
- tauvo (surface wind stress in the y direction from native model output resolution/grid) 
- zos (dynamic sea level height in the model from native model output resolution/grid) 

The script is written based on the CESM2-OMIP1 download provided by CMIP6-OMIP 
hosted by WCRP.

The dimension of all variable is 3-D with (time,nlat,nlon) in dimension and 2-D 
array for lat and lon as coordinate.


Required observational data 
-------------------------------

This diagnostic needs

input observational variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- adt (absolute dynamic topography from CMEMS)
    preprocessing from daily to monthly mean is needed (use 'io_cmems_adt.py')
- tx (surface wind stress in the x direction from WASwind)
    no preprocessing needed
- ty (surface wind stress in the y direction from WASwind)
    no preprocessing needed

data access :
**********************
     
- adt : 
    Ftp server is the fastest way to manage download
    `http://marine.copernicus.eu/services-portfolio/access-to-products/  <http://marine.copernicus.eu/services-portfolio/access-to-products/>`_
    search for product ID - "SEALEVEL_GLO_PHY_L4_REP_OBSERVATIONS_008_047"
    Need to download the daily data with adt (absolute dynamic topography) available 
    
- tx,ty :
    `https://www.riam.kyushu-u.ac.jp/oed/tokinaga/waswind.html  <https://www.riam.kyushu-u.ac.jp/oed/tokinaga/waswind.html>`_
    

The dimension of all variable is 3-D with 2-D in space and time

References
----------

.. Note this syntax, which sets the "anchor" for the hyperlink: two periods, one
   space, one underscore, the reference tag, and a colon, then a blank line.

.. _ref-Hsu: 
   
1. C.-W. Hsu et al. (2020): A Mechanistic Analysis of Tropical Pacific Dynamic 
   Sea Level in GFDL-OM4 under OMIP-I and OMIP-II Forcings. *GMD*, under review.
   
2. S. M. Griffies et al. (2016): OMIP contribution to CMIP6: experimental and 
   diagnostic protocol for the physical component of the Ocean Model Intercomparison 
   Project. *GMD*, `https://doi.org/10.5194/gmd-9-3231-2016 <https://doi.org/10.5194/gmd-9-3231-2016>`_
   
3. S. Kobayashi et al., (2015): The JRA-55 Reanalysis: General Specifications and Basic Characteristics.
   *Journal of the Meteorological Society of Japan. Ser. II*, 
   `https://doi.org/10.2151/jmsj.2015-001<https://doi.org/10.2151/jmsj.2015-001>`_ 
   
4. W. G. Large and S. G. Yeager, (2009): The global climatology of an interannually varying air–sea flux data set.
   *Climate Dynamics*,`https://doi.org/10.1007/s00382-008-0441-3<https://doi.org/10.1007/s00382-008-0441-3>`_


More about this diagnostic
--------------------------

The sea level over the tropical Pacific is a key indicator reflecting vertically 
integrated heat distribution over the ocean. We find persisting mean state dynamic
sea level (DSL) bias along 9◦N even with updated wind forcing in JRA55-do relative to CORE.
The mean state bias is related to biases in wind stress forcing and geostrophic currents 
in the 4◦N to 9◦N latitudinal band. The simulation forced by JRA55-do significantly reduces 
the bias in DSL trend over the northern tropical Pacific relative to CORE. In the CORE forcing, 
the anomalous westerly wind trend in the eastern tropical Pacific causes an underestimated 
DSL trend across the entire Pacific basin along 10◦N. The simulation forced by JRA55-do 
significantly reduces the bias in DSL trend over the northern tropical Pacific relative to CORE. 
We also identify a bias in the 10 easterly wind trend along 20◦N in both JRA55-do and CORE, 
thus motivating future improvement. In JRA55-do, an accurate Rossby wave initiated in the eastern 
tropical Pacific at seasonal time scale corrects a biased seasonal variability of the northern 
equatorial counter-current in the CORE simulation. Both CORE and JRA55-do generate realistic 
DSL variation during El Niño. We find an asymmetry in the DSL pattern on two sides of the equator
is strongly related to wind stress curl that follows the sea level pressure evolution during El Niño.
