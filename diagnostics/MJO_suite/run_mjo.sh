#!/bin/bash
# run_mjo.sh  -- usage: run_mjo.sh <framework_output_dir> <workdir>
# e.g. run_mjo.sh /work/a1r/mdtf/out_new/MDTF_output.v47 /work/a1r/mdtf/scratch/MJO_v47

# (delete the line:  set -u )

set +u    # conda/NCL activate scripts reference unset variables

V=${1:?framework output dir}
S=${2:?scratch work dir}
CASE=ESM4.5-historical-defobbfix
D=$(ls -d $V/MDTF_${CASE}_*/day | head -1)      # preprocessed data

# 1. Clean work dir. Stale *.day.nc / *.anom.nc are silently reused, which hides changes.
rm -rf "$S"; mkdir -p "$S/model/PS" "$S/model/netCDF" "$S/obs"
cp "$V/MJO_suite/case_info.yml" "$S/" 2>/dev/null

# 2. Environment (same init lines as the framework command)
export CODE_ROOT=/proj/MDTF-diagnostics
export CONDA_ENV_DIR=/opt/conda/envs
export POD_HOME=$CODE_ROOT/diagnostics/MJO_suite
export WORK_DIR=$S DATADIR=$S case_env_file=$S/case_info.yml

source $CODE_ROOT/src/conda/micromamba_init.sh \
  --micromamba_exe /usr/local/bin/micromamba --micromamba_root /opt/conda
micromamba activate $CONDA_ENV_DIR/_MDTF_NCL_base || exit 1
$CODE_ROOT/src/validate_environment.sh -v -p python3 -p ncl \
  -b contributed -b gsn_code -b gsn_csm -b shea_util -b diagnostics_cam || exit 1


# 3. POD inputs. The "cannot open <missing>" error came from leaving these unset.
export CASENAME=$CASE startdate=2002 enddate=2008
export lat_coord=lat lon_coord=lon time_coord=time
export pr_var=pr rlut_var=rlut u200_var=u200 u850_var=u850 v200_var=v200 v850_var=v850
for v in pr rlut u200 u850 v200 v850; do
  export ${v^^}_FILE=$D/$CASE.$v.day.nc
done

# 4. Run from $S: the NCL scripts use relative paths like model//
cd "$S"
PYTHONUNBUFFERED=1 python -u $POD_HOME/MJO_suite.py 2>&1 | tee "$S/pod.log"

# 5. MJO_suite.py prints "finished" even when NCL dies, so check the log yourself
grep -nE "^fatal|Error:|ERROR" "$S/pod.log" && echo ">>> POD had errors"

# 6. PS -> PNG with gs (flags are my guess; replace with eps_convert_flags from output_manager.py)
GS=/opt/conda/envs/_MDTF_base/bin/gs
for f in model/PS/*.ps; do
  $GS -q -dNOPAUSE -dBATCH -dSAFER -sDEVICE=png16m -r150 -dEPSCrop \
      -sOutputFile="model/$(basename ${f%.ps}).png" "$f"
done
ls model/*.png | wc -l
