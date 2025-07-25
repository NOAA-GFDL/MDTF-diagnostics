# This file is part of the blocking_neale module of the MDTF code package (see LICENSE.txt)
# ============================================================
# Rich Neale's Blocking Code
# Sample code to call NCL from python 
# ============================================================

import os
import sys
import subprocess
import time
import yaml

# ============================================================
# generate_html_file_header
#
# Note: the structure of the web page changes for multi-case
# in that it is organized by pod/case instead of case/pod.
# The reason this matters is that the MDTF graphic (mdtf_diag_banner)
# is either in the POD WORK_DIR (multi) or one dir up (single)
# so we have to reference it different.
# ============================================================


def generate_html_file_header(f): 
    """generate_html_file: write the html file header
       returns the html_template text/here-file for updating

    Arguments: f (file handle)
    """

# First the part that everyone gets
    html_template = """
<html>
<head>
<title>Blocking Diagnostic (Rich Neale)</title>
</head>
<body>
<h2>Blocking Diagnostic (Rich Neale)</h2>
"""   
    f.write(html_template)

# Now different paths for the different types
    if os.environ["CASE_N"] == "1":
        html_template = """
<img src="../mdtf_diag_banner.png">
"""   
        f.write(html_template)

    else: 
        html_template = """
<img src="mdtf_diag_banner.png">
"""   
        f.write(html_template)

 
# Finish for all
    html_template = """
<h3>Blocking Diagnostic (Rich Neale)</h3>
<p>
The diagnostic evaluates the blocking frequency in a model by longitude and season
as determined by the meridional gradient above a threshold value of daily
500mb height following <a href="https://doi.org/10.1007/s003820050230">D'Andrea et al 1998</a>


The annual cycle of blocking frequency is shown for each analyzed case,
reference ensemble (CESM1) and observational product (ERAI & MERRA)
requested, in individual Hovmüller figures (longitude vs time) and all
comparisons are combined in a line plot showing longitude vs blocking
frequency. Each figure is currently shown for ANN. (Coming soon: DJF & JJA)
</p>
</p>



<TABLE>
<TR>
<TH style='width: 200px' align=left>    Average seasonal cycle(K)
<TD style='width: 200px' align=center>   <A href=model/block_freq_season.png>Combined cases and obs</A>

<TR>
<TD>
<TD>
<TD style='width: 200px' align=center>   <b>Model comparison:</b>
<TD style='width: 100px' align=center>   <b>MDTF cases:</b>

<TR>
<TH style='width: 200px' align=left>      Annual cycle(K)
<TD style='width: 200px' align=center>    <A href=obs/block_freq_anncycle.OBS.png>OBS</A>
<TD style='width: 100px' align=center>    <A href=model/block_freq_anncycle.CAM5.png>CAM5 ensemble</A>

"""   
    f.write(html_template)

# ============================================================
# generate_html_file_case_loop (for multirun)
# ============================================================


def generate_html_file_case_loop(f, case_dict: dict):
    """generate_html_file: write the case information into
    the html template <NOT YET IMPLEMENTED>

    Arguments: f (file handle)
               case_dict (nested dict  [case1, [CASENAME, startdate, enddate],
                                        case2, [ ... ], ..., caseN, [ ... ]]

    Note: safe_substitute could be used; it leaves unmodified anything that doesn't have a match (instead of crashing)
    Note: any other case info in the dict can be replaced, eg:
    case_template = Template("<TD style='width: 200px' align=center><A href=model/block_freq_anncycle.$CASENAME.png>
    $CASENAME ($startdate-$enddate)</A>")

    """
    from string import Template

    case_template = Template("<TR><TD><TD><TD><TD style='width: 200px' align=center>"
                             "<A href=model/block_freq_anncycle.$CASENAME.png>$CASENAME</A>")
    for case_name, case_settings in case_dict.items():
        html_template = case_template.substitute(case_settings)
        f.write(html_template)

    # finalize the figure table, start the case settings table
    html_template = """
    </TABLE>
    </p>
    </p><b> Case settings</b>
    <TABLE>

    """
    f.write(html_template)

    # write the settings per case. First header.
    # This prints the whole thing html_template = str(case_dict)

    case_template = Template("<TR><TD style='width: 100px' align=center><b>$CASENAME")
    settings_template = Template("<TD style='width: 100px' align=center>$startdate - $enddate ")

    for case_name, case_settings in case_dict.items():
        html_template = case_template.safe_substitute(case_settings)
        f.write(html_template)

        html_template = settings_template.safe_substitute(case_settings)
        f.write(html_template)

    html_template = """
    </TABLE>
    </p>
    <TABLE>
    <TR><TH align=left>POD Settings
    """
    f.write(html_template)

# ============================================================
# generate_html_file_case_single (NOT multirun)
# ============================================================


def generate_html_file_case_single(f):
    """generate_html_file: write a template file that the framework will replace
    
    Arguments: f (file handle)
    """
    # Write the Annual Cycle figure. Leave replacements to the framework (for now)
    # see case_multi for how to substitute eventually
    html_template = \
        "<TD style='width: 200px' align=center><A href=model/block_freq_anncycle.{{CASENAME}}.png>{{CASENAME}}</A>"
    f.write(html_template)

    # finalize the figure table, start the case settings table
    html_template = """
    </TABLE>
    </p>
    </p><b> Case settings</b>
    <TABLE>

    """
    f.write(html_template)

    # Write the settings per case. First header.
    # NOTE: to print the whole thing: html_template = str(case_dict)

    html_template = "<TR><TD style='width: 100px' align=center><b>{{CASENAME}}"
    f.write(html_template)

    html_template = "<TD style='width: 100px' align=center>{{startdate}} - {{enddate}} "
    f.write(html_template)

    # Finish the table 
    html_template = """
    </TABLE>
    </p>
    """
    f.write(html_template)

# ============================================================
# generate_html_file_footer
# ============================================================


def generate_html_file_footer(f):
    """generate_html_file_footer: write the footer to the
    the html template 

    Arguments: f (file handle)
    """

    # Finish off the website with all the settings from the run
    # The following are replaced by the framework in a call from environment_manager.py
    # It would be great to just dump the dict but it isn't accessible here
    # maybe python codes are called with the pod object

    html_template = """
<TABLE style="font-size:12px; color:gray">
   <TR><TH align=left>POD Settings

<TR><TD> SEASON <TD> ANN
<TR><TD> MDTF_BLOCKING_OBS <TD> "{{MDTF_BLOCKING_OBS}}"
<TR><TD> MDTF_BLOCKING_CAM3 <TD> "{{MDTF_BLOCKING_CAM3}}"
<TR><TD> MDTF_BLOCKING_CAM4 <TD> "{{MDTF_BLOCKING_CAM4}}"
<TR><TD> MDTF_BLOCKING_CAM5 <TD> "{{MDTF_BLOCKING_CAM5}}"
<TR><TD> MDTF_BLOCKING_OBS_USE_CASE_YEARS <TD> "{{MDTF_BLOCKING_OBS_USE_CASE_YEARS}}"
<TR><TD> MDTF_BLOCKING_OBS_CAM5 STARTDATE - ENDDATE  <TD> "{{MDTF_BLOCKING_OBS_CAM5_STARTDATE}} - {{MDTF_BLOCKING_OBS_CAM5_ENDDATE}}"
<TR><TD> MDTF_BLOCKING_OBS_ERA  STARTDATE - ENDDATE  <TD> "{{MDTF_BLOCKING_OBS_ERA_STARTDATE }} - {{MDTF_BLOCKING_OBS_ERA_ENDDATE}}"
<TR><TD> MDTF_BLOCKING_OBS_MERRA  STARTDATE - ENDDATE <TD> "{{MDTF_BLOCKING_OBS_MERRA_STARTDATE}} - {{MDTF_BLOCKING_OBS_MERRA_ENDDATE}}"

<TR><TD> MDTF_BLOCKING_READ_DIGESTED	<TD> "{{MDTF_BLOCKING_READ_DIGESTED}}"
<TR><TD> MDTF_BLOCKING_WRITE_DIGESTED	<TD> "{{MDTF_BLOCKING_WRITE_DIGESTED}}"
<TR><TD> MDTF_BLOCKING_DEBUG <TD> "{{MDTF_BLOCKING_DEBUG}}"

<TR><TD> MDTF_NC_FORMAT <TD> "{{MDTF_NC_FORMAT}}"
<TR><TD> MODEL_DATA_PATH <TD> "{{MODEL_DATA_PATH}}"
<TR><TD> OBS_DATA <TD> "{{OBS_DATA}}"
<TR><TD> POD_HOME <TD> "{{POD_HOME}}"
<TR><TD> WORK_DIR <TD> "{{WORK_DIR}}"
<TR><TD> case_env_file <TD> "{{case_env_file}}"
<TR><TD> zg_var <TD> "{{zg_var}}"


</table>
</body>
</html>
"""
  
    # writing the code into the file
    f.write(html_template)
  
# ============================================================
# generate_html_file
# ============================================================


def generate_html_file(html_page: str, case_dict=None):
    """generate_html_file: write the html file template
    with generic variable names, for the correct cases
   
    Arguments: html_page(string): file name full path
               case_dict (nested dict)
    """

    f = open(html_page, "w")
    generate_html_file_header(f)
    if os.environ["CASE_N"] == "1":
        generate_html_file_case_single(f)

    else: 
        generate_html_file_case_loop(f, case_dict)
    generate_html_file_footer(f)

    # close the file
    f.close()

# ============================================================
# generate_ncl_plots - call a nclPlotFile via subprocess call
# ============================================================


def generate_ncl_plots(nclPlotFile):
    """generate_plots_call - call a nclPlotFile via subprocess call
   
    Arguments:
    nclPlotFile (string) - full path to ncl plotting file name
    """
    # check if the nclPlotFile exists - 
    # don't exit if it does not exists just print a warning.
    try:
        pipe = subprocess.Popen(['ncl {0}'.format(nclPlotFile)], shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()[0].decode()
        print('NCL routine {0} \n {1}'.format(nclPlotFile, output))
        while pipe.poll() is None:
            time.sleep(0.5)
    except OSError as e:
        print('WARNING', e.errno, e.strerror)

    return 0

############################################################
# MAIN
############################################################

# ============================================================
# Translate yaml file variables to environment variables for 
# NCL programs to read
# ============================================================

# Check for $WORK_DIR/case_env.yaml, as sign of multiple cases


print("blocking_neale.py looking for possible multicase case_env_file")
env_var = "case_env_file"
if env_var in os.environ:
    case_env_file = os.environ.get("case_env_file")
    print("blocking_neale.py case_env_file found? ",case_env_file)

    if os.path.isfile(case_env_file):
        with open(case_env_file, 'r') as stream:
            try:
                case_info = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        print("blocking_neale.py read multicase yaml file, setting env vars for NCL")

        icase = 0  # index for cases, needed to save numbered env vars
        for case_name, case_settings in case_info.items():
            icase = icase + 1
            print("case ", icase, ": ", case_name)
            for k, v in case_settings.items():
                casei_env_var_name = "CASE" + str(icase) + "_" + str(k)
                os.environ[casei_env_var_name] = str(v)
                print("setenv ", casei_env_var_name, "\t ", v)

        os.environ["CASE_N"] = str(icase)
        print("setenv ", "CASE_N", "\t ", icase)
else:
    print("No multicase case_env_file found so proceeding as single case")
    os.environ["CASE_N"] = "1"

# ============================================================
# Call NCL code here
# ============================================================
if not os.path.exists(os.path.join(os.environ['DATADIR'], 'day')):
    os.makedirs(os.path.join(os.environ['DATADIR'], 'day'))

print("blocking_neale.py calling blocking.ncl")
generate_ncl_plots(os.environ["POD_HOME"]+"/blocking.ncl")

# ============================================================
# Generate HTML page with correct number of cases
# ============================================================
# This is the proper place but the framework fails if there isn't something
# in the POD_HOME dir, and placing a stub file there ends up overwriting this!
# html_page = os.environ["WORK_DIR"]+"/blocking_neale.html"

html_page = os.environ["POD_HOME"]+"/blocking_neale.html"
print("blocking_neale.py generating dynamic webpage ", html_page)


if os.environ["CASE_N"] == "1":
    generate_html_file(html_page)
else:
    generate_html_file(html_page, case_info)

# ============================================================

print("blocking_neale.py finished.")
sys.exit(0)
