# script to create a simple index.html for automated mdtf runs
import sys
import os
import json

out_dir = sys.argv[1]

# load pod information
with open(sys.argv[2]) as f:
    pods = json.load(f)

index_file = open(f'{out_dir}/index.html', 'a')

pod_htmls = {}
pods = [p for p in pods]
mdtf_outputs = [os.path.join(out_dir, d) for d in os.listdir(out_dir) if 'MDTF_output' in d]

for d in mdtf_outputs:
    list_d = os.listdir(d)
    for p in pods:
        if p in list_d:
            pod_dir = os.path.join(d, p)
            file_path = os.path.join(pod_dir, f'{p}.html')
            if os.path.exists(file_path):
                print(p)
                index_file.write(f'<a href="{file_path}"> {p} </a>')
            
index_file.close()
