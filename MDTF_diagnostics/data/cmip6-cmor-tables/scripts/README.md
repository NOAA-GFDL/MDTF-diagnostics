# Updating the CV

## Make sure tables from DRS are up to date

Follow directions at: 
https://github.com/PCMDI/xml-cmor3-database/blob/master/README.md

## Update CV

Essentially:

First clone the cmip6-cmor-tables repo
```bash
git clone git://github.com/pcmdi/cmip6-cmor-tables
cd cmip6-cmor-tables
```

Then run the CMIP6_CV_cron_github.sh script

```bash
bash scripts/CMIP6_CV_cron_github.sh /path/to/cmip6-cmor-tables
```
