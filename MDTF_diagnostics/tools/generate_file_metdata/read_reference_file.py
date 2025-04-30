# Inspired by: https://github.com/agstephens/kerchunk-intake-sandbox/blob/main/test-intake-ipsl.py
# Read a reference file generated with kerchunk into an intake-esm datastore
# conda activate _MDTF_base
import os

import intake
import click
import sys

@click.option("--input_file",
              type=click.Path(),
              required=True,
              default = '/net/jml/mdtf/combined.json',
              help="Full path to input metadata json file."
              )

@click.command()
def run(input_file: click.Path):
    config = dict({'input_file': input_file})
    assert os.path.isfile(config['input_file']), f"file {config['input_file']} does not exist"
    cat = intake.open_esm_datastore(config['input_file'])

    cat_subset = cat.search(
        experiment_id=["historical", "ssp585"],
        table_id="Oyr",
        variable_id="o2",
        grid_label="gn",
    )

    dset_dict = cat_subset.to_dataset_dict(
        xarray_open_kwargs={"decode_times": False, "use_cftime": True}
    )


    ds2 = dset_dict["CMIP6.ScenarioMIP.IPSL.IPSL-CM6A-LR.ssp585.r1i1p1f1.Oyr.o2.gn.latest"]

    float(ds2.o2[:,0,0,0])
    return 0

if __name__ == '__main__':
    exit_code = run(prog_name='read reference file')
    sys.exit(exit_code)