# Import Plotting Functions
import Plotting_Functions as plot

# Leave or comment out which plots you do not want to make

# This will plot the spatial composite panels (4 plot files saved)
plot.SpatialCompositePanels()

# This will plot the azimuthal mean line plots (1 plot file saved)
plot.AzmeanPlotting()

# This will plot the non-normalized and normalized box-averaged feedbacks 
# as a function of bin. (2 plot files saved)
plot.BoxAvLinePlotting()

# This will plot the scattering of non-normalized and normalized
# box-averaged feedbacks and percent of storms intensifying from one
# bin to the next. (1 plot file saved)
plot.BoxAvScatter()
