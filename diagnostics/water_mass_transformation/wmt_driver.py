import os
import matplotlib

matplotlib.use("Agg")  # non-X windows backend
import numpy as np
import xarray as xr  # python library we use to read netcdf files
import matplotlib.pyplot as plt  # python library we use to make plots

from xwmt.preprocessing import preprocessing
from xwmt.swmt import swmt

input_path = [
    os.environ["AREACELLO_FILE"],
    os.environ["TOS_FILE"],
    os.environ["SOS_FILE"],
    os.environ["HFDS_FILE"],
    os.environ["SFDSI_FILE"],
    os.environ["WFO_FILE"],
]

ds = xr.open_mfdataset(input_path, use_cftime=True)

ds = ds.rename(
    {
        os.environ["areacello_var"]: "areacello",
        os.environ["tos_var"]: "tos",
        os.environ["sos_var"]: "sos",
        os.environ["wfo_var"]: "wfo",
        os.environ["hfds_var"]: "hfds",
        os.environ["sfdsi_var"]: "sfdsi",
    }
)

ds = xr.Dataset(
    {
        "tos": ds.tos,
        "sos": ds.sos,
        "wfo": ds.wfo,
        "hfds": ds.hfds,
        "sfdsi": ds.sfdsi,
        "areacello": ds.areacello,
        "deptho": ds.deptho,
        "geolon": ds.geolon,
        "geolat": ds.geolat,
    }
)

ds = preprocessing(ds, grid=ds, decode_times=False, verbose=False)
bins = np.arange(20, 30, 0.1)
group_tend = False
G = swmt(ds).G("sigma0", bins=bins, group_tend=group_tend)

# Don't plot first or last bin (expanded to capture full range)
G = G.isel(sigma0=slice(1, -1))
levs = G["sigma0"].values

# Take annual mean and load
G = G.mean("time").load()
# Get terms in dataset
terms = list(G.data_vars)

fig, ax = plt.subplots()
# Plot each term
for term in terms:
    if term == "heat":
        color = "tab:red"
    elif term == "salt":
        color = "tab:blue"
    else:
        color = "k"
    ax.plot(levs, G[term], label=term, color=color)

# If terms were not grouped then sum them up to get total
if len(terms) > 1:
    total = xr.zeros_like(G[terms[0]])
    for term in terms:
        total += G[term]
    ax.plot(levs, total, label="total", color="k")

ax.legend()
ax.set_xlabel("SIGMA0")
ax.set_ylabel("TRANSFORMATION ($m^3s^{-1}$)")
ax.autoscale(enable=True, axis="x", tight=True)

plot_path = "{WK_DIR}/model/PS/wmt_model_plot.eps".format(**os.environ)
plt.savefig(plot_path, bbox_inches="tight")

print("Last log message by WMT POD: finished successfully!")
