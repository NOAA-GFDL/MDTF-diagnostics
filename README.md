<div class="row">
<div class="col-lg-8">
<div class="post-image">
<div class="post-heading">
<h1>MDTF-diagnostics</h1>
</div>
</div>
The MDTF diagnostic package is portable, extensible, usable, and open for contribution from the community. A goal is to allow diagnostics to be repeatable inside, or outside, of modeling center workflows. These are diagnostics focused on model improvement, and as such a slightly different focus from other efforts. The code runs on CESM model output, as well as on GFDL and CF-compliant model output.

The MDTF Diagnostic Framework consists of multiple modules, each of which is developed by an individual research group or user. Modules are independent of each other, each module:
<ol type="1">
 	<li>Produces its own html file (webpage) as the final product</li>
 	<li>Consists of a set of process-oriented diagnostics</li>
 	<li>Produces a figures or multiple figures that can be displayed by the html in a browser</li>
</ol>

<h2>Diagnostics in Package</h2>
<div class="post-border-bottom">

Follow the links in the table below to view sample output, including a brief description and a link to the full documentation for each diagnostic.
<table class="table table-striped sort">
<thead>
<tr>
<th class="header">Diagnostic</th>
<th class="header">Contributor</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><a href="http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/convective_transition_diag/convective_transition_diag.html">Convective Transition Diagnostics</a></td>
<td>J. David Neelin (UCLA)</td>
</tr>
<tr class="even">
<td><a href="http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/MJO_teleconnection/MJO_teleconnection.html">MJO Teleconnections</a></td>
<td>Eric Maloney (CSU)</td>
</tr>
<tr class="odd">
<td><a href="http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/EOF_500hPa/EOF_500hPa.html">Extratropical Variance (EOF 500hPa Height)</a></td>
<td>CESM/AMWG (NCAR)</td>
</tr>
<tr class="even">
<td><a href="http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/Wheeler_Kiladis/Wheeler_Kiladis.html">Wavenumber-Frequency Spectra</a></td>
<td>CESM/AMWG (NCAR)</td>
</tr>
<tr class="odd">
<td><a href="http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/MJO_suite/MJO_suite.html">MJO Spectra and Phasing</a></td>
<td>CESM/AMWG (NCAR)</td>
</tr>
<tr class="even">
<td><a href="http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/precip_diurnal_cycle/precip_diurnal_cycle.html">Diurnal Cycle of Precipitation</a></td>
<td>Rich Neale (NCAR)</td>
</tr>
<tr class="odd">
<td><a href="http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_GFDL.CM4.c96L32.am4g10r8/MJO_prop_amp/MJO_prop_amp.html">MJO Propagation and Amplitude</a> (example with GFDL CM4 data)</td>
<td>Xianan Jiang (UCLA)</td>
</tr>
<tr class="even">
<td><a href="http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_GFDL-CM2p1/transport_onto_TS/transport_onto_TS.html">AMOC 3D structure</a> (implementation in progress, example with GFDL CM2 model data)</td>
<td>Xiaobiao Xu (FSU/COAPS)</td>
</tr>
<tr class="odd">
<td><a href="http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_CCSM4/MSE_diag/MSE_diag.html">ENSO Moist Static Energy budget</a> (implementation in progress, example with CCSM4 data)</td>
<td>Hariharasubramanian Annamalai (U. Hawaii)</td>
</tr>
<tr class="even">
<td><a href="http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/warm_rain_microphysics/documentation">Warm Rain Microphysics</a> (implementation in progress)</td>
<td>Kentaroh Suzuki (AORI, U. Tokyo)</td>
</tr>
</tbody>
</table>
</div>
<div class="post-border-bottom">
<h2>Sample Output Webpage</h2>
<a href="http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/">Latest complete package based on a CESM-CAM run</a>



</div>
<div class="post-border-bottom">
<h2>Downloading and Running</h2>
<ul>
 	<li><a href="http://www.cesm.ucar.edu/working_groups/Atmosphere/mdtf-diagnostics-package/Getting_started_v2.0.pdf">Getting Started</a></li>
 	<li><a href="ftp://ftp.cgd.ucar.edu/archive/mdtf/MDTF_v2.0.var_code.tar">Latest code</a> (2 MB)</li>
 	<li><a href="ftp://ftp.cgd.ucar.edu/archive/mdtf/MDTF_v2.0.obs_data.tar">Pre-digested observational data</a> (300 MB)</li>
 	<li>Sample model data
<ul>
 	<li><a href="ftp://ftp.cgd.ucar.edu/archive/mdtf/model.QBOi.EXP1.AMIP.001.tar">NCAR-CESM-CAM</a> (13G)</li>
 	<li><a href="ftp://ftp.cgd.ucar.edu/archive/mdtf/model.GFDL.CM4.c96L32.am4g10r8.tar">NOAA-GFDL-CM4 </a> For MJO_prop_amp module (5G)</li>
</ul>
</li>
</ul>
</li>
</ul>
</li>
</ul>
</div>
<div class="post-border-bottom">
<h2>Developer’s Information</h2>
<ul>
 	<li><a href="http://www.cesm.ucar.edu/working_groups/Atmosphere/mdtf-diagnostics-package/Developers_walkthrough_v2.0.pdf">Developer's Walk-through (v2.0)</a></li>
</ul>
</div>
</div>
<!-- WG Info Include -->
<div class="widget"></div>
<!-- end WG Include -->

</div>
