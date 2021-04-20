# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import sys
import json
import pdb
import requests
from collections import OrderedDict


# List of files needed from github for CMIP6 CV
# ---------------------------------------------
filelist = [ 
        "CMIP6_required_global_attributes.json",
        "CMIP6_activity_id.json",
        "CMIP6_institution_id.json",
        "CMIP6_source_id.json",
        "CMIP6_source_type.json",
        "CMIP6_frequency.json",
        "CMIP6_grid_label.json",
        "CMIP6_nominal_resolution.json",
        "CMIP6_realm.json",
        "CMIP6_table_id.json",
        "CMIP6_license.json",
        "mip_era.json",
        "CMIP6_sub_experiment_id.json",
        "CMIP6_experiment_id.json"
        ]
# Github repository with CMIP6 related Control Vocabulary files
# -------------------------------------------------------------
githubRepo = "https://raw.githubusercontent.com/WCRP-CMIP/CMIP6_CVs/master/"

class readWCRP():
    def __init__(self):
        pass

    def createSource(self,myjson):
        root = myjson['source_id']
        for key in root.keys():
            root[key]['source']=root[key]['label'] + ' (' + root[key]['release_year'] + '): ' + chr(10)
            for realm in root[key]['model_component'].keys():
                if( root[key]['model_component'][realm]['description'].find('None') == -1):
                    root[key]['source'] += realm + ': ' 
                    root[key]['source'] += root[key]['model_component'][realm]['description'] + chr(10)
            root[key]['source'] = root[key]['source'].rstrip()
            del root[key]['label']
            del root[key]['release_year']
            del root[key]['label_extended']
            del root[key]['model_component']

    def createExperimentID(self,myjson):
        #
        # Delete undesirable attribute for experiement_id
        #
        root = myjson['experiment_id']
        for key in root.keys():
            del root[key]['tier']
            del root[key]['start_year']
            del root[key]['end_year']
            del root[key]['description']
            del root[key]['min_number_yrs_per_sim']

    def readGit(self):
        Dico = OrderedDict()
        for file in filelist:
            url = githubRepo + file 
            response = requests.get(url)
            print(url)
            urlJson = response.content.decode('utf-8')
            myjson = json.loads(urlJson, object_pairs_hook=OrderedDict)
            if(file == 'CMIP6_source_id.json'):
                self.createSource(myjson)
            if(file == 'CMIP6_experiment_id.json'):
                self.createExperimentID(myjson)
            Dico.update(myjson)
         
        finalDico = OrderedDict()
        finalDico['CV'] = Dico
        return finalDico

def run():
    f = open("CMIP6_CV.json", "w")
    gather = readWCRP()
    CV = gather.readGit()
    regexp = OrderedDict()
    regexp["license"] = [ "^CMIP6 model data produced by .* is licensed under a Creative Commons Attribution.*ShareAlike 4.0 International License .https://creativecommons.org/licenses.* *Consult https://pcmdi.llnl.gov/CMIP6/TermsOfUse for terms of use governing CMIP6 output, including citation requirements and proper acknowledgment\\. *Further information about this data, including some limitations, can be found via the further_info_url (recorded as a global attribute in this file).*\\. *The data producers and data providers make no warranty, either express or implied, including, but not limited to, warranties of merchantability and fitness for a particular purpose\\. *All liabilities arising from the supply of the information (including any liability arising in negligence) are excluded to the fullest extent permitted by law\\.$" ]
    regexp["mip_era"] = [ "CMIP6" ]
    regexp["product"] = [ "model-output" ]
    regexp["tracking_id"] = [ "hdl:21.14100/.*" ]  
    regexp["further_info_url"] = [ "https://furtherinfo.es-doc.org/.*" ]
    regexp["realization_index"] = [ "^\\[\\{0,\\}[[:digit:]]\\{1,\\}\\]\\{0,\\}$" ]
    regexp["variant_label"] = ["r[[:digit:]]\\{1,\\}i[[:digit:]]\\{1,\\}p[[:digit:]]\\{1,\\}f[[:digit:]]\\{1,\\}$" ]
    regexp["data_specs_version"] = [ "^[[:digit:]]\\{2,2\\}\\.[[:digit:]]\\{2,2\\}\\.[[:digit:]]\\{2,2\\}$" ]
    regexp["Conventions"] = [ "^CF-1.7 CMIP-6.[0-2]\\( UGRID-1.0\\)\\{0,\\}$" ]
    regexp["forcing_index"] = [ "^\\[\\{0,\\}[[:digit:]]\\{1,\\}\\]\\{0,\\}$" ]
    regexp["initialization_index"] = [ "^\\[\\{0,\\}[[:digit:]]\\{1,\\}\\]\\{0,\\}$" ]
    regexp["physics_index"] = [ "^\\[\\{0,\\}[[:digit:]]\\{1,\\}\\]\\{0,\\}$" ]


    CV['CV'].update(regexp)
    for exp in CV["CV"]["experiment_id"]:
        CV["CV"]["experiment_id"][exp]["activity_id"] = [ " ".join(CV["CV"]["experiment_id"][exp]["activity_id"])]
        print("AC ID:",CV["CV"]["experiment_id"][exp]["activity_id"])
    f.write(json.dumps(CV, indent=4, separators=(',', ':'), sort_keys=False) )

    f.close()

if __name__ == '__main__':
    run()
