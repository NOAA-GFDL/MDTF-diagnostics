# script to make the MDTF runtime configs for each realm/freq to run requested PODs
import sys
import os
import json
import copy

# load pod information
with open(sys.argv[2]) as f:
    pods = json.load(f)

# load template config information
with open(sys.argv[1]+'template_config.jsonc') as f:
    template_config = json.load(f)    

# create dict object for each pod
config_files = {}
for p in pods:
    config_name = f'{p}_config'
    config_realm = pods[p]['realm']
    config_files[config_name] = copy.deepcopy(template_config)
    config_files[config_name]['case_list']['case_name']['realm'] = config_realm
    config_files[config_name]['case_list'][config_realm] = config_files[config_name]['case_list'].pop('case_name')

# add pods to cooresponding config file
for p in pods:
    config_file = f"{p}_config"    
    config_files[config_file]['pod_list'].append(p) 
    
#write out config files
for c in config_files:
    with open(sys.argv[1]+f"config/{c}.jsonc", "w") as f:
        f.write(json.dumps(config_files[c], indent=2))     
