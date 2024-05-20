import pandas as pd
#JUST TO QUICKLY BE ABLE TO QUERY THE CSV FILE
df = pd.read_csv('/home/a1r/cure/gfdl_to_cmip5_vars.csv',sep=",", header=0,index_col=False)

print("All atmos fields and their GFDL, CMIP mappings")
print(df[(df.modeling_realm == 'atmos')])


