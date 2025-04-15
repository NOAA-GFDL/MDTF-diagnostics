# run-MDTF
Shell driver script to run the MDTF-diagnostics package with the GFDL FRE workflow <br />

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
