import os
import intake
from src import util
def query_catalog(case_list: dict, catalog_path: str):
    # build list of case names with wild card appended
    cases = [c + "*" for c in case_list.keys()]
    # open the csv file using information provided by the catalog definition file
    cat = intake.open_esm_datastore(catalog_path)
    sub_cat = cat.search('file_name'=cases)
    return sub_cat