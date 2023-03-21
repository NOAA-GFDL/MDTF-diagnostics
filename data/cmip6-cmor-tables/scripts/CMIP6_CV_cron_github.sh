#!/bin/bash -x
export REPO_PATH=${1:-"${HOME}/cmip6-cmor-tables"}
echo ${REPO_PATH}
cd ${REPO_PATH}
git remote ad cmor_tables 
git fetch -u cmor_tables
git pull
cd scripts
python3 createCMIP6CV.py
mv ${REPO_PATH}/scripts/CMIP6_CV.json  ${REPO_PATH}/Tables
msg="cron: update CMIP6_CV -- "`date +%Y-%m-%dT%H:%M`
echo $msg
cd ../../
git commit -am "$msg"
git push
git remote rm cmor_tables
