# run-MDTF
Shell driver script to run the MDTF-diagnostics package with the GFDL FRE workflow <br />
This script automatially generates an intake-ESM catalog with files in the target directory
using the GFDL catalogBuilder tool with --slow option to ensure that all required variable
metadata are populated. If a catalog exists in the input data directory or the output directory,
 the script will skip the catalog generation step.

Command-line usage:

```
$ run-mdtf.sh -i /path/to/pp/dir/pp -o out_dir/mdtf -s startyr -e endyr
```

Input: 
- A user-specified configuration file `pod_config.json` located in the **config** directory that is run
   by default. Users should modify this template to run their desired POD(s) and update query parameters such as *realm*
   A different configuration file can be supplied with the `-l` OPTARG.
- `-i`: path to the input directory ending in /pp with the target dataset
- `-o`: path to directory to write the output
- `-s`: start year of the dataset
- `-e`: end year of the dataset
- `-c`: (optional) data convention, cmip (default), gfdl, or cesm

Example using GFDL central MDTF-diagnostics installation. Note that the resulting catalog will not include static files with
variables required by the example mar SST_bias_NOAA_OISSTvs notebook. In the following example, the information for `ocean_monthly.static.nc`
needs to be entered manually at this time, so the user needs to call `run-MDTF.sh` twice:

```
$ /home/oar.gfdl.mdtf/mdtf/MDTF-diagnostics/tools/run-MDTF/run-MDTF.sh
-i /archive/John.Krasting/fre_om5/FMS2024.02_om5_20250206/om5_b08/gfdl.ncrc5-intel23-prod/pp/ocean_monthly/ts
-o ~/mdtf_test_out -s 1978 -e 1988 -l config/pod_config.json
```
