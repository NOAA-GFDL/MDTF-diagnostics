import json
import pandas as pd
import os
import requests
import re
from datetime import datetime
from jinja2 import Template

base_url = "https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics"
api_url = "https://api.github.com/repos/NOAA-GFDL/MDTF-diagnostics/contents/diagnostics"

#edit if you would like to save csv for each POD
save_csv = False

def good_status(code):
    # 2xx is a positive completion return code
    if str(code)[0] == '2':
        return True
    else:
        return False

def get_json_content(url):
    response = requests.get(url)
    if good_status(response.status_code):
        try:
            raw_url = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob', '')
            response = requests.get(raw_url)
            if good_status(response.status_code):
                # Remove comments from JSONC content, this part is important otherwise the attributes could not be extracted correctly
                jsonc_content = response.text
                json_content = re.sub(r'//.*?\n|/\*.*?\*/', '', jsonc_content, flags=re.S)
                json_content = re.sub(r',\s*([}\]])', r'\1', json_content)
                return json.loads(json_content)
            else:
                print(f"Cannot get content from URL: {raw_url}, Status code: {response.status_code}")
                return None
        except json.JSONDecodeError:
            print(f"Error decoding JSON from URL: {url}")
            return None
    else:
        print(f"Failure in function get_json_content()!")
        return None

def get_folders_via_api():
    response = requests.get(api_url)
    if good_status(response.status_code):
        data = response.json()
        folders = [item['name'] for item in data if item['type'] == 'dir']
        return folders
    else:
        print(f"Failure in function get_folders_via_api()!")
        return []

def process_settings_jsonc(folder_name, json_content):
    frequency = json_content.get("data", {}).get("frequency", "N/A")
    convention = json_content.get("settings", {}).get("convention", "N/A")
    # Extract varlist
    df_data = []
    for var, attributes in json_content.get("varlist", {}).items():
        if frequency == 'N/A' and 'frequency' in attributes:
            frequency = attributes.get("frequency", "N/A")
        df_data.append([
            var,
            attributes.get("units", "N/A"),
            attributes.get("realm", "N/A"),
            ', '.join(attributes.get("dimensions", [])),
            frequency,
            attributes.get("standard_name", "N/A"),
            convention
        ])
    
    # move the freq before standard name  
    columns = ["Variable", "Units", "Realm", "Dimensions", "Frequency", "Standard Name", "Convention"]
    df = pd.DataFrame(df_data, columns=columns)
    
    if save_csv:
        # Save the file in case we want to make use of it to modity the XML files later 
        csv_filename = f"{folder_name}_varlist.csv"
        df.to_csv(csv_filename, index=False)
    
    return df

# Two ways to get the folder names, one is automatic search (cons: may include those example PODs and some incomplete PODs), one is to add manully 
folders = get_folders_via_api()

# Check if folders were found
if not folders:
    print("-----------------------------------------------------------------")
    print("No folders found under the diagnostics directory. Please check!!!")
    print("-----------------------------------------------------------------")
else:
    # Get the time
    current_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")    
    # Initialize HTML 
    html_template = Template("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MDTF PODs Variable Lists (Tables For Individual POD and Combined All PODs)</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            table, th, td {
                border: 1px solid black;
            }
            th, td {
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            .timestamp {
                font-size: smaller;
                color: #555;
            }            
        </style>
    </head>
    <body>
        <h1>MDTF PODs Variable Lists (Tables For Individual POD and Combined All PODs)</h1>
        <p class="timestamp">Generated at {{ current_time }}. For questions, contact Wenhao.Dong@noaa.gov</p>        
        {% for folder_name, table_html in tables.items() %}
            <h2>POD: {{ folder_name }}</h2>
            <div>{{ table_html | safe }}</div>
        {% endfor %}
        <h2>All PODs</h2>
        <div>{{ all_pods_table | safe }}</div>
    </body>
    </html>
    """)

    # Loop through each POD and generate tables
    tables = {}
    all_data = []
    for folder in folders:
        settings_url = f"{base_url}/{folder}/settings.jsonc"
        json_content = get_json_content(settings_url)
        if json_content:
            df = process_settings_jsonc(folder, json_content)
            tables[folder] = df.to_html(classes='table table-striped', index=False)
            df['Used by'] = folder  # Add 'Used by' column only for the combined table
            all_data.append(df)
        else:
            print(f"No settings.jsonc found for folder: {folder}")

    # Merge the data for all PODs 
    if all_data:
        all_pods_df = pd.concat(all_data)
        all_pods_df = all_pods_df.groupby(["Variable", "Units", "Realm", "Dimensions", "Frequency", "Standard Name"])['Used by'].apply(lambda x: ', '.join(sorted(set(x)))).reset_index()
        columns = ["Variable", "Units", "Realm", "Dimensions", "Frequency", "Standard Name", "Used by"]
        all_pods_df = all_pods_df[columns]
        all_pods_table = all_pods_df.to_html(classes='table table-striped', index=False)    

    else:
        all_pods_table = "<p>No single data available</p>"

    html_content = html_template.render(tables=tables, all_pods_table=all_pods_table, current_time=current_time)    
    with open("MDTF_Variable_Lists.html", "w") as f:
        f.write(html_content)

    print("\nHTML file 'MDTF_Variable_Lists.html'")
    print("Well Done!!!")
