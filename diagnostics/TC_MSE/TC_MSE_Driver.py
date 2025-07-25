# Import necessary module(s)
import os

# Run through the necessary script(s)

# This will read in track data and create the TC snapshots and calculate MSE variables as well as save TC characteristic variables
print("Running the TC snapshotting code")
print("==============================================")

os.system("python " +  os.environ["POD_HOME"]+"/TC_snapshot_MSE_calc.py")

print("Snapshotting code has finished!")
print("==============================================")

# This will take the files created from above section and bin the variables as well as composite them
print("Running the binning and compositing code")
print("==============================================")

os.system("python " + os.environ["POD_HOME"]+"/Binning_and_compositing.py")

print("Binning and compositing code has finished!")
print("==============================================")

# This will create the various plots which allow for comparison to the 5 reanalysis datasets
print("Running the plotting code")
print("==============================================")

os.system("python "+ os.environ["POD_HOME"]+"/Plotting.py")

print("Plotting code has finished!")
print("==============================================")

# Message noting that the framework has been completed
print("TC MSE POD has been completed successfully!")
