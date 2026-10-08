#!/usr/bin/env bash
set -e
umask 000
eval "$(micromamba shell hook --shell bash)"
micromamba activate _MDTF_base
mdtf -f /proj/wkdir/esmnew.json
