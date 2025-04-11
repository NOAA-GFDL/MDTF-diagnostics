# run-MDTF
MDTF shell driver to assist model development at the GFDL <br />
Command-line usage:
```
run-mdtf.sh -i /path/to/pp/dir/pp -o out_dir/mdtf -s startyr -e endyr
```
This script requires a user inputted `pod_config.json`. One is supplied by default, but may need to be updated in order to launch more PODs or update realm information!
A new one can be supplied with the `-l` OPTARG.
