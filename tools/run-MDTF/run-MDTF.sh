#!/bin/bash -f
#SBATCH --job-name=run-MDTF.sh
#SBATCH --time=4:00:00
#set -x

# dir references
run_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
mdtf_dir=/home/oar.gfdl.mdtf/mdtf/MDTF-diagnostics
#mdtf_dir=/home/Jacob.Mims/mdtf/MDTF-diagnostics
activate=/home/oar.gfdl.mdtf/miniconda3/bin/activate

#TEST: /archive/jpk/fre/FMS2024.02_OM5_20240819/CM4.5v01_om5b06_piC_noBLING_xrefine_test4/gfdl.ncrc5-intel23-prod-openmp/pp/ starts 0001

#TEST 2: /archive/djp/am5/am5f7b12r1/c96L65_am5f7b12r1_amip/gfdl.ncrc5-intel23-classic-prod-openmp/pp/ starts 1990

usage() {
   echo "USAGE: run-mdtf.sh -i /path/to/pp/dir/pp -o out_dir/mdtf -s startyr -e endyr"
   echo "ADDITONAL OPTS:"
   echo "-l: custom config file for pods (default: config/pod_config.json) this can be used to set which PODs you would like to run and define the realm to grab vars from"
}

# handle arguments
tempdir=""
pod_config=""
declare -a pods=()
while getopts "hi:o:s:e:p:t:l:" arg; do
   case "${arg}" in
      h) 
         usage
	 exit 
         ;;
      i) 
         if [ -d $OPTARG ]; then
            ppdir="${OPTARG}"
         else
            echo "ERROR: $1 is not a directory"
            usage
            exit
         fi
         ;;
      o)
         if [ -d "${OPTARG}" ]; then
            outdir="${OPTARG}"
         else
            mkdir -p "${OPTARG}"
            outdir="${OPTARG}"
         fi
         ;;      
      s)
         startyr="${OPTARG}"
         ;;
      e)
         endyr="${OPTARG}"
         ;;
      p)
         pods+=("$OPTARG")
         ;;
      t)
         tempdir="${OPTARG}"
         ;;
      l)
         pod_config="${OPTARG}"
   esac
done
shift $((OPTIND-1))
if ! [ -d $outdir/config ]; then
   mkdir -p $outdir/config
fi
if [ -z $tempdir ]; then
   wkdir=$outdir
else
   wkdir=$tempdir
fi
if [ -z $pod_config ]; then 
   pod_config="$run_dir/config/pod_config.json"
fi

# check to see if catalog exists
#  ^..^
# /o  o\   
# oo--oo~~~
echo "looking for catalog in $ppdir"
cat=$(grep -s -H "esmcat_version" $ppdir/*.json  | cut -d: -f1)
if [[ "$cat" == "" ]]; then
   env=/nbhome/fms/conda/envs/fre-2025.01
   source $activate $env
   fre catalog builder --overwrite $ppdir $outdir/catalog 
   cat=$outdir/catalog.json
   echo "new catalog generated: $cat"
else
   echo "found catalog: $cat"
fi

# edit template config file
cp $run_dir/config/template_config.jsonc $outdir
f=$outdir/template_config.jsonc
if [ ! -f $f ]; then
   echo "ERROR: failed to find $f"
   exit 0
fi
config='"DATA_CATALOG": "",'
config_edit='"DATA_CATALOG": "'"${cat}"'",'
sed -i "s|$config|$config_edit|ig" $f
config='"WORK_DIR": "",'
config_edit='"WORK_DIR": "'"${wkdir}"'",'
sed -i "s|$config|$config_edit|ig" $f
config='"OUTPUT_DIR": "",'
config_edit='"OUTPUT_DIR": "'"${outdir}"'",'
sed -i "s|$config|$config_edit|ig" $f
config='"startdate": "",'
config_edit='"startdate": "'"${startyr}"'",'
sed -i "s|$config|$config_edit|ig" $f
config='"enddate": ""'
config_edit='"enddate": "'"${endyr}"'"'
sed -i "s|$config|$config_edit|ig" $f
echo "edited file $f"

# load mdtf base conda env
env=/home/oar.gfdl.mdtf/miniconda3/envs/_MDTF_base
source $activate $env
#generate config files
python $run_dir/scripts/gen_config.py $outdir/ $pod_config

# launch the mdtf with the config files
for f in $(ls ${outdir}/config) ; do
   echo "launching MDTF with $f"
   "$mdtf_dir"/mdtf -f $outdir/config/$f
done

# consolidate outputs into index
cp $run_dir/scripts/index.html $outdir/
cp $run_dir/scripts/mdtf_diag_banner.png $outdir/
python $run_dir/scripts/gen_index.py $outdir/ $pod_config

exit 0
