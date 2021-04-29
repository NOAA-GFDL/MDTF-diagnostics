import numpy,math
from numpy import ma
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap, shiftgrid, addcyclic

# 10-08 fixed memory leak, moved using plt.close() and moving basemap instantiation.

class plotmap():
    """Class to create simple pcolor map (Cylindrical Equidistant, global )"""

    __author__  = "Mike Bauer  <mbauer@giss.nasa.gov>"
    __status__  = "alpha"
    __version__ = "0.1 "+__status__
    __license__ = "GNU General Public License"
    __date__    = "Created: 16 April 2008             Updated:"

    def __init__(self,**kwargs):
        """Create an instance to plot full global field. Note z not passed in
        as we only need to create a map object once (for looping efficiency).
        """

        if 'lon_0' in kwargs:
            self.lon_0 = kwargs['lon_0']
        else:
            self.lon_0 = 180.0

        #if 'color_scheme' in kwargs:
        #    self.color_scheme = plt.cm.__dict__[kwargs['color_scheme']]
        #else:
        #    self.color_scheme = plt.cm.bone

        if 'discrete' in kwargs:
            self.discrete = kwargs['discrete']
        else:
            self.discrete = 0

        if 'color_scheme' in kwargs:
            if self.discrete:
                # Make non-continuous
                self.color_scheme = plt.cm.get_cmap(kwargs['color_scheme'],self.discrete)
            else:
                self.color_scheme = plt.cm.__dict__[kwargs['color_scheme']]
        else:
            if self.discrete:
                # Make non-continuous
                self.color_scheme = plt.cm.get_cmap('bone',self.discrete)
            else:  
                self.color_scheme = plt.cm.bone

        # Set color for masked values
        self.color_scheme.set_bad('grey')

        if 'cints' in kwargs:
            self.cints = kwargs['cints']
        else:
            self.cints = None

        if 'clevs' in kwargs:
            self.clevs = kwargs['clevs']
        else:
            self.clevs = None

        if 'missing' in kwargs:
            self.missing = kwargs['missing']
        else:
            self.missing = None

        if 'nocolorbar' in kwargs:
            self.cbar = False
        else:
            self.cbar = True

        # Default Cylindrical Equidistant, global
        self.m = Basemap(resolution='c',projection='cyl',
                         lon_0=self.lon_0,
                         area_thresh=300000)
        
        ## Lambert Conformal: the projection is conformal, or shape-preserving
        ## Set resolution=None skips processing of boundary datasets to save time.
        ## Centered on lon_0,lat_0 and of size base_width,base_height this sets
        ## the size and location of the composite
        ## Mediterranean
        #base_width = 15000000 # 15000 km wide
        #base_height = 7500000 # 7500 km tall
        #self.m = Basemap(lat_0=35,lon_0=20,projection='lcc',
        #                 width=base_width,height=base_height,resolution='c',area_thresh=300000)
#         # South-Polar Stereographic
#         self.m = Basemap(resolution='i',projection="spstere",
#                          boundinglat = -30,
#                          lat_1=-90.,lon_0=0.,
#                          area_thresh=100000)

    def create_fig(self):
        # Create figure.
        golden_ratio = 1.61803399
#         # for imovie at 120 dpi, want 960x540
#         golden_ratio =  1.77777777
#         width = 8

        width = 10
        hieght = width/golden_ratio

        # Create basis for map
#        self.fig = plt.figure(figsize=(width,hieght),frameon=False) # frameon transparent background
        self.fig = plt.figure(figsize=(width,hieght),frameon=True)

        ## Set axis
        #if self.cbar:
        #    # color bar
        #    self.ax = self.fig.add_axes([0.08,0.05,0.9,0.9])
        #else:
        #    # no color bar
        #    self.ax = self.fig.add_axes([0.08,0.05,0.9,0.9])
        self.ax = self.fig.add_subplot(1,1,1) # 1 row, 1 column, first plot

        self.shifted = False

    def add_field(self,x,y,z,**kwargs):

        self.x = numpy.array(x) # 1d array of longiudes
        self.y = numpy.array(y) # 1d array of latitudes
        self.im = len(x)
        self.jm = len(y)
        self.z = z # 2d array of data

        if 'ptype' in kwargs:
            self.ptype = kwargs['ptype']
        else:
            self.ptype = 'pcolor'

        if 'colorbar_label' in kwargs:
            self.colorbar_label =  kwargs['colorbar_label']
        else:
            self.colorbar_label = ""

        # Tweak Data for ploting
        
        # Reshape z
        self.z.shape = (self.jm,self.im)

        # Add cyclic longitude to data and longitudes
        self.z,self.x = addcyclic(self.z,self.x)

        # JJ fix to issue of not having longitudes not increasing 
        if (self.x[-1] < self.x[-2]):
          self.x[-1] += 360.

        # Shift data and longitudes to start at start_lon
        # also converts 0-360 to +-180 format, skip if unneeded.
        #dx = abs(self.x[0]-self.x[1])
        #if abs(self.x[0]-self.lon_0) > dx:
        #    self.z,self.x = shiftgrid(self.lon_0,self.z,self.x,start=False)
        
        # Compute map projection coordinates of grid
        lons,lats,self.xx,self.yy = self.m.makegrid(len(self.x),len(self.y), returnxy=True)

        if self.ptype == 'pcolor':
            # The NRA grid is a rectangular grid of lat/lon (i.e. not really a
            # projection at all, with each data row is along a line of constant
            # latitude, each column a line of equal longitude). However,
            # p_color draws a panel between the (i,j),(i+1,j),(i+1,j+1),(i,j+1) coordinates
            # of the X/Y matrices with a color corresponding to the data value at (i,j). Thus
            # everything will appear shifted by one half a pixel spacing.
            # In short, p_color is pixel registered (lon,lat give the edges of the grid).
            #
            # Simple fix that likely works to to shift self.z via averaging.
            # 


            # This seems to work best for maps, although averaging means this
            #   is an imperfect method. Still otherwise, using self.z the 
            #   whole thing is offset a partial grid and you skip the north
            #   pole. pcolormesh works better with missing values.
            z = 0.5*(self.z[:-1,:-1]+self.z[1:,1:])
            # Mask missing (shiftgrid removes original masking)
            if self.missing != None:
                z = numpy.ma.masked_where(z <= self.missing,z)
            #self.the_image = self.m.pcolor(self.xx,self.yy,z,shading='flat',
            #        cmap=self.color_scheme)
            self.the_image = self.m.pcolormesh(self.x,self.y,z,shading='flat',
                                            cmap=self.color_scheme)

            # Mask missing (shiftgrid removes original masking)
            #if self.missing != None:
            #    self.z = numpy.ma.masked_where(self.z <= self.missing,self.z)


            #self.the_image = self.m.pcolormesh(self.xx,self.yy,self.z,shading='flat',
            #                                cmap=self.color_scheme)


#            self.the_image = self.m.pcolormesh(self.x,self.y,self.z,shading='flat',
#                                            cmap=self.color_scheme)

#            self.shifted = True

            # Adjust range of colors.
            if self.cints:
                self.the_image.set_clim(self.cints[0],self.cints[1])

        elif self.ptype == 'imshow':

            # Heavy grid marks
            self.the_image = self.m.imshow(self.z,cmap=self.color_scheme,ax=self.ax)
            # Adjust range of colors.
            if self.cints:
                self.the_image.set_clim(self.cints[0],self.cints[1])

        elif self.ptype == 'contour':
        
            # Mask missing (shiftgrid removes original masking)
            if self.missing != None:
                self.z = numpy.ma.masked_where(self.z <= self.missing,self.z)

            lw = 1.0
            contours = range(self.clevs[0],self.clevs[1],self.clevs[2])

            scale = 2 # amount smoothed
            if self.m.projection=='cyl':
                # projection in degrees longitude, so just scale grid
                nx = (len(self.x)-1)*scale
                ny = len(self.y)*scale
            else:
                # if self.m.xmax not in degrees longitude, then do this.
#                 dx = 2.*math.pi*self.m.rmajor/((len(self.x)-1)*scale)
#                 nx = int((self.m.xmax-self.m.xmin)/dx)+1
#                 ny = int((self.m.ymax-self.m.ymin)/dx)+1
#                 print nx,ny,dx

                nx = int((self.m.xmax-self.m.xmin)/40000.)+1; ny = int((self.m.ymax-self.m.ymin)/40000.)+1
                # Shift data and longitudes to start at start_lon
                # also converts 0-360 to +-180 format, skip if unneeded.
                dx = abs(self.x[0]-self.x[1])
                if abs(self.x[0]-self.lon_0) > dx:
                    self.z,self.x = shiftgrid(self.lon_0,self.z,self.x,start=False)

            #self.z = self.m.transform_scalar(self.z,self.x,self.y,nx,ny)
            #self.xx = self.x
            #self.yy = self.y

            self.z,self.xx,self.yy = self.m.transform_scalar(
                self.z,self.x,self.y,nx,ny,returnxy=True)

            self.the_image = self.m.contourf(self.xx,self.yy,self.z,contours,
                                             cmap=self.color_scheme,ax=self.ax)
            self.the_image2 = self.m.contour(self.xx,self.yy,self.z,contours,
                                             colors ='k',linewidths=lw,ax=self.ax)

            #print dir(self.the_image2)
            #print self.the_image2.collections
            #print
            #for x in self.the_image2.collections:
            #    
            #    print dir(x)
            #    print
            #    print x.get_paths

            #    import sys; sys.exit("Stop Here")


            # label the contours
            labels = []
            for label in range(self.clevs[0],self.clevs[1],self.clevs[2]*2):
                labels.append(label)
            self.the_image3 = plt.clabel(self.the_image2,labels,fmt = '%d')

        # draw coastlines
        self.m.drawcoastlines(linewidth=0.25,ax=self.ax)

        # setup grids
        delat = 30.
        circles = numpy.arange(0.,90.+delat,delat).tolist()+\
                  numpy.arange(-delat,-90.-delat,-delat).tolist()
        delon = 60.
#        meridians = numpy.arange(-180,180,delon)
        meridians = numpy.arange(0,360,delon)

        # draw parallelsleft, right, top or bottom
        self.m.drawparallels(circles,labels=[1,0,0,0],ax=self.ax)

        # draw meridians
        self.m.drawmeridians(meridians,labels=[0,0,0,1],ax=self.ax)

        if self.cbar:
            # add a colorbar.
            if self.discrete:
                self.extend = 'neither'
            else:
                self.extend = 'both'
            aa = self.fig.colorbar(self.the_image,orientation='horizontal',
                    extend=self.extend,spacing='uniform',ticks=None,
                    fraction=0.1,pad=0.09,aspect=40)
            if self.colorbar_label:
                aa.ax.set_xlabel(self.colorbar_label,fontsize='small')

#            pos = self.ax.get_position()
#            l, b, w, h = pos.bounds
#            #self.cax = plt.axes([l, b-0.1, w, 0.03],frameon=False) # setup colorbar axes horizontal
#            self.cax = plt.axes(frameon=False) # setup colorbar axes horizontal

##            self.cax = plt.axes([l+w+0.075, b, 0.05, h],frameon=False) # setup colorbar axes vertical
#            self.fig.colorbar(self.the_image,cax=self.cax,
#                              orientation='horizontal',extend=self.extend,
#                              spacing='uniform',ticks=None)
#            #self.fig.colorbar(self.the_image,cax=self.cax,
#            #                  orientation='horizontal',extend='both',
#            #                  spacing='proportional',ticks=None) 

#            if self.colorbar_label:
#                self.cax.set_xlabel(self.colorbar_label,verticalalignment='bottom',fontsize='small')

#            plt.axes(self.ax)  # make the original axes current again

    def finish(self,pname,title=None):

        # Add title
        if title:
            plt.title(title,fontsize='small')

        if pname.endswith("png"):
            self.dpi = 140
#             # for movies
#             self.dpi = 240
        else:
            self.dpi = 144
            #self.dpi = 300

        # If too much crop set pad_inches=0.03
        self.fig.savefig(pname,
                         dpi=self.dpi,
                         facecolor='w',
                         edgecolor='w',
                         orientation='landscape',
                         bbox_inches='tight', pad_inches=0.03)

        ## Trim white space
        #if pname.endswith("png"):
        #    import os
        #    (dirName, fileName) = os.path.split(pname)
        #    (fileBaseName, fileExtension)=os.path.splitext(fileName)
        #    tmp = '%s/%s%s' % (dirName,'t',fileExtension)
        #    cmd = 'convert %s -trim -trim %s' % (pname,tmp)
        #    os.system(cmd)
        #    os.rename(tmp,pname)
        #elif pname.endswith("eps"):
        #    import os
        #    (dirName, fileName) = os.path.split(pname)
        #    (fileBaseName, fileExtension)=os.path.splitext(fileName)
        #    cmd = 'ps2eps -B -C %s' % (pname)
        #    os.system(cmd)
        #    tmp = pname+".eps"
        #    os.rename(tmp,pname)

## cut sometimes
#         # Trim white space
#         import os
#         cmd = 'convert %s -trim -trim %s' % (pname,'t.png')
#         os.system(cmd)
#         os.rename('t.png',pname)

        #self.fig.clf() # clear figure
        plt.close('all')  # kill all objects for this instance.

    def finish_nokill(self,pname,title=None):

        # Add title
        if title:
            plt.title(title)

        if pname.endswith("png"):
            self.dpi = 140
#             # for movies
#             self.dpi = 240
        else:
            self.dpi = 144

        # If too much crop set pad_inches=0.03
        self.fig.savefig(pname,
                         dpi=self.dpi,
                         facecolor='w',
                         edgecolor='w',
                         orientation='landscape',
                        bbox_inches='tight', pad_inches=0.0)
        
        ## Trim white space
        #if pname.endswith("png"):
        #    import os
        #    (dirName, fileName) = os.path.split(pname)
        #    (fileBaseName, fileExtension)=os.path.splitext(fileName)
        #    tmp = '%s/%s%s' % (dirName,'t',fileExtension)
        #    cmd = 'convert %s -trim -trim %s' % (pname,tmp)
        #    os.system(cmd)
        #    os.rename(tmp,pname)
        #elif pname.endswith("eps"):
        #    import os
        #    (dirName, fileName) = os.path.split(pname)
        #    (fileBaseName, fileExtension)=os.path.splitext(fileName)
        #    cmd = 'ps2eps -B -C %s' % (pname)
        #    os.system(cmd)
        #    tmp = pname+".eps"
        #    os.rename(tmp,pname)


    def add_contour(self,x,y,z,**kwargs):

        self.cx = numpy.array(x) # 1d array of longiudes
        self.cy = numpy.array(y) # 1d array of latitudes
        self.cz = z # 2d array of data

        # Reshape z
        self.cz.shape = (self.jm,self.im)

        # Add cyclic longitude to data and longitudes
        self.cz,self.cx = addcyclic(self.cz,self.cx)

        # Shift data and longitudes to start at start_lon
        # also converts 0-360 to +-180 format
        self.cz,self.cx = shiftgrid(180.0,self.cz,self.cx,start=False)

        # transform to nx x ny regularly spaced native projection grid
        # nx and ny chosen to have roughly the same horizontal res as original image
        # times scale

        # Smooth
        scale = 2.0 # amount smoothed

        # For Cylindrical Equidistant, global this works
        nx = int(len(self.cx)*scale)
        ny = int(len(self.cy)*scale)

#         # if not cyl
#         dx = 2.0*math.pi*self.m.rmajor/len(self.cx)
#         nx = int((self.m.xmax-self.m.xmin)/dx)+1 
#         ny = int((self.m.ymax-self.m.ymin)/dx)+1

        self.czz,self.cxx,self.cyy = self.m.transform_scalar(
            self.cz,self.cx,self.cy,nx,ny,returnxy=True)

        if 'linewidths' in kwargs:
            lw = kwargs['linewidths']
        else:
            lw = 1.0
        if 'clevs' in kwargs:
            contours = range(kwargs['clevs'][0],kwargs['clevs'][1],kwargs['clevs'][2])
            if 'filled' in kwargs:
                self.the_image = self.m.contourf(self.cxx,self.cyy,self.czz,contours,
                                                 cmap=self.color_scheme)
            else:
                if 'cmap' in kwargs:
                    self.the_image = self.m.contour(self.cxx,self.cyy,self.czz,contours,
                                                    cmap=self.color_scheme,linewidths=lw)
                else:
                    self.the_image = self.m.contour(self.cxx,self.cyy,self.czz,contours,
                                                    colors ='k',linewidths=lw)
        else:
            if 'filled' in kwargs:
                self.the_image = self.m.contourf(self.cxx,self.cyy,self.czz,
                                                 cmap=self.color_scheme)
            else:
                if 'cmap' in kwargs:
                    self.the_image = self.m.contour(self.cxx,self.cyy,self.czz,
                                                    cmap=self.color_scheme,linewidths=lw)
                else:
                    self.the_image = self.m.contour(self.cxx,self.cyy,self.czz,
                                                    colors ='k',linewidths=lw)

    def add_pnts(self,*args,**kwargs):
        self.p = args[0] # 1d array of pnt (lon,lat) tuples

        if len(args) > 1:
            # list of point labels
            self.pnt_names = args[1]

        if 'marker' in kwargs:
            self.marker = kwargs['marker']
        else:
            self.marker = 'x'

        if 'msize' in kwargs:
            self.msize = kwargs['msize']
        else:
            self.msize = None

        if 'mfc' in kwargs:
            self.mfc = kwargs['mfc']
        else:
            self.mfc = None

        if 'mec' in kwargs:
            self.mec = kwargs['mec']
        else:
            self.mec = None

        if 'lw' in kwargs:
            self.lw = kwargs['lw']
        else:
            self.lw = None
        
        if 'zorder' in kwargs:
            # used to order pnt and contours
            self.zorder = kwargs['zorder']
        else:
            self.zorder = None

        # prep pnts
        self.pnt_x = [x[0] for x in self.p]
        self.pnt_y = [x[1] for x in self.p]

        # Pcolor requires that everything be shifted by a half grid inc
        # so the grids have moved to line up correctly I need to do the same
        if self.shifted:
            delon = self.x[1]-self.x[0]
            delat = self.y[1]-self.y[0]
            x = self.pnt_x[:]
            self.pnt_x = x - 0.5*delon
            y = self.pnt_y[:]
            self.pnt_y = y + 0.5*delat

        # Compute native map projection coordinates for lat/lon grid.
        self.pnt_x, self.pnt_y = self.m(self.pnt_x,self.pnt_y)
        # plot pnts over map/image
        if self.zorder:
            self.pnt_image = self.m.plot(self.pnt_x,self.pnt_y,self.marker,
                                   markersize=self.msize,
                                   markerfacecolor=self.mfc,
                                   markeredgecolor=self.mec,
                                   linewidth=self.lw,zorder=self.zorder)
        else:
            self.pnt_image = self.m.plot(self.pnt_x,self.pnt_y,self.marker,
                                               markersize=self.msize,
                                               markerfacecolor=self.mfc,
                                               markeredgecolor=self.mec,
                                               linewidth=self.lw)
        # Add label to point
        if len(args) > 1:
            for self.i in range(len(self.pnt_x)):
                self.pnt_image = plt.text(self.pnt_x[self.i],self.pnt_y[self.i],
                                          "  %d" % self.pnt_names[self.i],size='xx-small')

class plotmap_polar(plotmap):
    """Create an instance to plot polar """

    def __init__(self,**kwargs):
        """Create an instance to plot full global field. Note z not passed in
        as we only need to create a map object once (for looping efficiency).
        """

        if 'lon_0' in kwargs:
            self.lon_0 = kwargs['lon_0']
        else:
            self.lon_0 = 180.0

        if 'discrete' in kwargs:
            self.discrete = kwargs['discrete']
        else:
            self.discrete = 0
        
        # Discrete w/ arrows on colorbar
        if 'discretee' in kwargs:
            self.discretee = kwargs['discretee']
        else:
            self.discretee = None 

        if 'color_scheme' in kwargs:
            if self.discrete:
                # Make non-continuous
                self.color_scheme = plt.cm.get_cmap(kwargs['color_scheme'],self.discrete)
            else:
                self.color_scheme = plt.cm.__dict__[kwargs['color_scheme']]
        else:
            if self.discrete:
                # Make non-continuous
                self.color_scheme = plt.cm.get_cmap('bone',self.discrete)
            else:  
                self.color_scheme = plt.cm.bone

        # Control how colorbar ends work
        if self.discrete:
            self.extend = 'neither'
        else:
            self.extend = 'both'

        # Set color for masked values
        self.color_scheme.set_bad('grey')
        # Set colors of out of bounds colorbars
        self.color_scheme.set_under('white')
        self.color_scheme.set_over('black')
        
        if 'colorbar_label' in kwargs:
            self.colorbar_label =  kwargs['colorbar_label']
        else:
            self.colorbar_label = ""

        if 'cints' in kwargs:
            self.cints = kwargs['cints']
        else:
            self.cints = None

        if 'clevs' in kwargs:
            self.clevs = kwargs['clevs']
        else:
            self.clevs = None

        if 'missing' in kwargs:
            self.missing = kwargs['missing']
        else:
            self.missing = None

        if 'nocolorbar' in kwargs:
            self.cbar = False
        else:
            self.cbar = True

        if 'clabels' in kwargs:
            self.clabels = kwargs['clabels']
        else:
            self.clabels = False

        if 'hemi' in kwargs:
            self.hemi = kwargs['hemi']
        else:
            self.hemi = 'nh'

        # these are the 4 polar projections
        projs = ['laea','stere','aeqd','ortho']

        if 'mproj' in kwargs:
            if self.hemi == 'sh':
                self.mproj = 'sp'+kwargs['mproj']
            else:
                self.mproj = 'np'+kwargs['mproj']
        else:
            self.mproj = 'nplaea'

        if self.mproj == 'spstere' and self.hemi == 'nh':
            import sys; sys.exit("Hemisphere Projection Miss Match")
        if self.mproj == 'npstere' and self.hemi == 'sh':
            import sys; sys.exit("Hemisphere Projection Miss Match")
        
        self.lat_0 = 90.
        self.polarity = 1.0
        if self.hemi == 'sh':
            self.polarity = -1.0
            self.lat_0 = -90.
            
        if 'bounding_lat' in kwargs:
            self.bounding_lat = kwargs['bounding_lat']
        else:
            # Default is 
            self.bounding_lat = 30.0*self.polarity

        if self.bounding_lat < 0.0 and self.hemi == 'nh':
            import sys; sys.exit("Hemisphere Bounding_Lat Miss Match")
        if self.bounding_lat > 0.0 and self.hemi == 'sh':
            import sys; sys.exit("Hemisphere Bounding_Lat Miss Match")

        # 'Lambert Azimuthal Equal Area' laea
        # It accurately represents area in all regions of the sphere, but it does not
        #   does not preserve angular relationships among curves on the sphere. 
        # The longitude lon_0 is at 6-o'clock, and the latitude circle boundinglat 
        #   is tangent to the edge  of the map at lon_0.

        # 'Stereographic' Equal-Angle 'npstere','spstere'
        # It is conformal, meaning that it preserves angles. It is neither isometric nor 
        #   area-preserving: that is, it preserves neither distances nor the areas of figures.
        # Its main use is for mapping the polar regions. In the polar aspect all meridians
        #   are straight lines and parallels are arcs of circles.
        # The longitude lon_0 is at 6-o'clock, and the
        #   latitude circle boundinglat is tangent to the edge  
        #   of the map at lon_0. Default value of lat_ts
        #   (latitude of true scale) is pole.

        # 'Azimuthal Equidistant' aeqd
        #   The most noticeable feature of this azimuthal projection is the fact that
        #       distances measured from the center are true. Therefore, a circle about 
        #       the projection center defines the locus of points that are equally far 
        #       away from the plot origin. Furthermore, directions from the center are also true. 
        #   all distances measured from the center of the map along any longitudinal line are accurate
        #   Distortion of areas and shapes increases dramatically, the further away one gets from center point.
        # The longitude lon_0 is at 6-o'clock, and the
        #   latitude circle boundinglat is tangent to the edge  
        #   of the map at lon_0.

        # 'Orthographic' ortho
        #   The orthographic azimuthal projection is a perspective projection from infinite distance.
        #       It is therefore often used to give the appearance of a globe viewed from outer space.
        #   The projection is neither equal-area nor conformal, and much distortion is introduced
        #       near the edge of the hemisphere. The directions from the center of projection are true. 
        #  lon_0, lat_0 are the center point of the projection.

        area_thresh=100000.
        #area_thresh=10000

        if self.mproj.find('ortho') != -1:
            self.m = Basemap(projection='ortho',
                    lat_0=self.lat_0,lon_0=180+self.lon_0,
                    resolution='i',area_thresh=area_thresh)
        else: 
            self.m = Basemap(projection=self.mproj,lat_0=self.lat_0,
                    boundinglat=self.bounding_lat,lon_0=self.lon_0,
                    resolution='i',area_thresh=area_thresh)
        self.shifted = False


    def create_fig(self):
            # Create figure.
            width = 4*2
            hieght = 4*2

            # Create basis for map
            # frameon=True gives transparent background
            self.fig = plt.figure(figsize=(width,hieght),frameon=False)
            #self.fig = plt.figure(figsize=(width,hieght),frameon=True)
            # Set axis 1 row, 1 column, first plot
            self.ax = self.fig.add_subplot(1,1,1) 

    def add_pcolor(self,x,y,z):
        
        self.x = numpy.array(x) # 1d array of longiudes
        self.y = numpy.array(y) # 1d array of latitudes
        self.z = z # 2d array of data

        # Reshape z
        self.z.shape = (len(self.y),len(self.x))

        # Add cyclic longitude to data and longitudes
        self.z,self.x = addcyclic(self.z,self.x)

        # Shift data and longitudes to start at start_lon
        # also converts 0-360 to +-180 format
        self.z,self.x = shiftgrid(180.0,self.z,self.x,start=False)
                    
        # compute native map projection coordinates for lat/lon grid.
        self.x,self.y = self.m(*numpy.meshgrid(self.x,self.y))

        # Mask missing (shiftgrid removes original masking)
        if self.missing != None:
            self.z = numpy.ma.masked_where(self.z <= self.missing,self.z)
        self.the_image = self.m.pcolormesh(self.x,self.y,self.z,
                edgecolors='None',linewidth=0.01,cmap=self.color_scheme)
        # adjust range of colors.
        if self.cints:
            self.the_image.set_clim(self.cints[0],self.cints[1])

    def add_contour(self,x,y,z,no_fill,zorder):

        self.x = numpy.array(x) # 1d array of longiudes
        self.y = numpy.array(y) # 1d array of latitudes
        self.z = z # 2d array of data
        self.no_fill = no_fill 
        self.zorder = zorder

        # Reshape z
        self.z.shape = (len(self.y),len(self.x))

        # Add cyclic longitude to data and longitudes
        self.z,self.x = addcyclic(self.z,self.x)

        # Shift data and longitudes to start at start_lon
        # also converts 0-360 to +-180 format
        self.z,self.x = shiftgrid(180.0,self.z,self.x,start=False)

        # compute native map projection coordinates for lat/lon grid.
        self.x,self.y = self.m(*numpy.meshgrid(self.x,self.y))

        # Mask missing (shiftgrid removes original masking)
        if self.missing != None:
            self.z = numpy.ma.masked_where(self.z <= self.missing,self.z)

        lw = 1.0
        lw = 0.25
        if self.clevs:
            contours = range(self.clevs[0],self.clevs[1],self.clevs[2])
#tmp make high pressure contours solid and low pressure dashed
        high_c = [x for x in contours if x >= 1013]
        low_c = [x for x in contours if x not in high_c]

        # make filled contour plot and overlay contour lines
        if self.clevs:
            if self.no_fill:
#tmp make high pressure contours solid and low pressure dashed
                contours = high_c
                self.the_image1 = self.m.contour(self.x,self.y,self.z,
                        contours,colors='k',linewidths=lw,linestyles='dotted',
                         zorder=self.zorder)
                contours = low_c
                self.the_image2 = self.m.contour(self.x,self.y,self.z,
                        contours,colors='k',linewidths=lw,linestyles='solid',
                        zorder=self.zorder)

                #self.the_image2 = self.m.contour(self.x,self.y,self.z,
                #        contours,colors ='k',linewidths=lw)
            else:
                self.the_image= self.m.contourf(self.x,self.y,self.z,
                        contours,cmap=self.color_scheme)
                # Adjust colors for contours
                self.the_image.set_clim(self.the_image.cvalues[1],
                        self.the_image.cvalues[-2])
                self.the_image2 = self.m.contour(self.x,self.y,self.z,
                        contours,colors ='k',linewidths=lw)
            if self.clabels:
                # label the contours
                labels = []
#tmp make high pressure contours solid and low pressure dashed
                for label in range(high_c[0],high_c[-1],self.clevs[2]*2):
                    labels.append(label)
                self.the_image3 = plt.clabel(self.the_image1,labels,
                        fontsize=5,inline=1,inline_spacing=0,fmt = '%d')
                labels = []
                for label in range(low_c[0],low_c[-1],self.clevs[2]*2):
                    labels.append(label)
                self.the_image4 = plt.clabel(self.the_image2,labels,
                        fontsize=5,inline=1,inline_spacing=0,fmt = '%d')

                #for label in range(self.clevs[0],self.clevs[1],self.clevs[2]*2):
                #    labels.append(label)
                #self.the_image3 = plt.clabel(self.the_image2,labels,
                #        fontsize=5,inline=1,inline_spacing=0,fmt = '%d')
        else:
            if self.no_fill:
                self.the_image2 = self.m.contour(self.x,self.y,self.z,
                        colors ='k',linewidths=lw)
            else:
                self.the_image = self.m.contourf(self.x,self.y,self.z,
                        cmap=self.color_scheme)
                self.the_image2 = self.m.contour(self.x,self.y,self.z,
                        colors ='k',linewidths=lw)

    def add_extras(self):
        # draw coastlines
        self.m.drawcoastlines(linewidth=0.25,ax=self.ax)

        # setup grids
        delat = 30.0*self.polarity
        if self.hemi == 'sh':
            circles = numpy.arange(self.bounding_lat,-90,delat).tolist()
        else:
            circles = numpy.arange(self.bounding_lat,90,delat).tolist()
        delon = 60.
        meridians = numpy.arange(0,360,delon)

        # draw parallelsleft, right, top or bottom
        #self.m.drawparallels(circles,labels=[0,0,0,0],ax=self.ax)
        # draw meridians
        #self.m.drawmeridians(meridians,labels=[0,0,0,0],ax=self.ax)

        if self.no_fill:
            self.cbar = 0
            # Fill Continents
            self.m.fillcontinents(color='0.9')

        if self.cbar:
            # add a colorbar.
            if self.colorbar_label:
                aa = self.fig.colorbar(self.the_image,orientation='horizontal',
                    extend=self.extend,spacing='uniform',ticks=None,
                    fraction=0.1,pad=0.09,aspect=40)
                aa.ax.set_xlabel(self.colorbar_label,fontsize='small')
            else:
                if self.extend == 'both':
                    aa = self.fig.colorbar(self.the_image,orientation='horizontal',
                        extend=self.extend,spacing='uniform',ticks=None,
                        fraction=0.021,pad=0.03,aspect=40)
                else:
                    aa = self.fig.colorbar(self.the_image,orientation='horizontal',
                        extend=self.extend,spacing='uniform',ticks=None,
                        fraction=0.0225,pad=0.03,aspect=40)


#---Start of main code block.
if __name__=='__main__':

    import numpy,sys

    # Base Definitions
    im = 144
    jm = 73
    maxID = im*jm
    dx = 2.5
    dy = 2.5

    lats = numpy.array([-90.0, -87.5, -85.0, -82.5, -80.0, -77.5, -75.0, -72.5, -70.0,
                        -67.5, -65.0, -62.5, -60.0, -57.5, -55.0, -52.5, -50.0, -47.5, -45.0,
                        -42.5, -40.0, -37.5, -35.0, -32.5, -30.0, -27.5, -25.0, -22.5, -20.0,
                        -17.5, -15.0, -12.5, -10.0, -7.5, -5.0, -2.5, 0.0, 2.5, 5.0, 7.5, 10.0,
                        12.5, 15.0, 17.5, 20.0, 22.5, 25.0, 27.5, 30.0, 32.5, 35.0, 37.5, 40.0,
                        42.5, 45.0, 47.5, 50.0, 52.5, 55.0, 57.5, 60.0, 62.5, 65.0, 67.5, 70.0,
                        72.5, 75.0, 77.5, 80.0, 82.5, 85.0, 87.5, 90.0])

    lons = numpy.array([0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0, 22.5, 25.0,
                        27.5, 30.0, 32.5, 35.0, 37.5, 40.0, 42.5, 45.0, 47.5, 50.0,
                        52.5, 55.0, 57.5, 60.0, 62.5, 65.0, 67.5, 70.0, 72.5, 75.0,
                        77.5, 80.0, 82.5, 85.0, 87.5, 90.0, 92.5, 95.0, 97.5, 100.0,
                        102.5, 105.0, 107.5, 110.0, 112.5, 115.0, 117.5, 120.0, 122.5,
                        125.0, 127.5, 130.0, 132.5, 135.0, 137.5, 140.0, 142.5, 145.0,
                        147.5, 150.0, 152.5, 155.0, 157.5, 160.0, 162.5, 165.0, 167.5,
                        170.0, 172.5, 175.0, 177.5, 180.0, 182.5, 185.0, 187.5, 190.0,
                        192.5, 195.0, 197.5, 200.0, 202.5, 205.0, 207.5, 210.0, 212.5,
                        215.0, 217.5, 220.0, 222.5, 225.0, 227.5, 230.0, 232.5, 235.0,
                        237.5, 240.0, 242.5, 245.0, 247.5, 250.0, 252.5, 255.0, 257.5,
                        260.0, 262.5, 265.0, 267.5, 270.0, 272.5, 275.0, 277.5, 280.0,
                        282.5, 285.0, 287.5, 290.0, 292.5, 295.0, 297.5, 300.0, 302.5,
                        305.0, 307.5, 310.0, 312.5, 315.0, 317.5, 320.0, 322.5, 325.0,
                        327.5, 330.0, 332.5, 335.0, 337.5, 340.0, 342.5, 345.0, 347.5,
                        350.0, 352.5, 355.0, 357.5])

    slp = numpy.array([100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0,
        100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100347.0, 100240.0,
        100280.0, 100325.0, 100365.0, 100405.0, 100445.0, 100485.0, 100520.0,
        100560.0, 100595.0, 100625.0, 100657.0, 100690.0, 100720.0, 100747.0,
        100775.0, 100800.0, 100825.0, 100850.0, 100872.0, 100897.0, 100917.0,
        100940.0, 100955.0, 100975.0, 100992.0, 101012.0, 101027.0, 101045.0,
        101060.0, 101075.0, 101090.0, 101102.0, 101115.0, 101125.0, 101135.0,
        101147.0, 101157.0, 101162.0, 101172.0, 101180.0, 101180.0, 101182.0,
        101185.0, 101190.0, 101187.0, 101185.0, 101182.0, 101180.0, 101172.0,
        101162.0, 101157.0, 101145.0, 101132.0, 101120.0, 101105.0, 101090.0,
        101070.0, 101050.0, 101030.0, 101005.0, 100982.0, 100960.0, 100930.0,
        100902.0, 100875.0, 100845.0, 100815.0, 100782.0, 100752.0, 100717.0,
        100682.0, 100647.0, 100615.0, 100575.0, 100540.0, 100500.0, 100462.0,
        100427.0, 100387.0, 100347.0, 100312.0, 100270.0, 100230.0, 100192.0,
        100152.0, 100115.0, 100075.0, 100037.0, 100000.0, 99962.0, 99927.0,
        99890.0, 99860.0, 99825.0, 99795.0, 99760.0, 99730.0, 99702.0, 99675.0,
        99650.0, 99627.0, 99602.0, 99580.0, 99560.0, 99542.0, 99525.0, 99512.0,
        99497.0, 99485.0, 99472.0, 99465.0, 99455.0, 99447.0, 99442.0, 99440.0,
        99440.0, 99440.0, 99442.0, 99450.0, 99457.0, 99465.0, 99477.0, 99492.0,
        99510.0, 99532.0, 99550.0, 99577.0, 99605.0, 99632.0, 99665.0, 99697.0,
        99732.0, 99770.0, 99807.0, 99850.0, 99890.0, 99932.0, 99975.0, 100017.0,
        100062.0, 100105.0, 100150.0, 100197.0, 100277.0, 100352.0, 100427.0,
        100495.0, 100555.0, 100612.0, 100665.0, 100715.0, 100760.0, 100800.0,
        100837.0, 100870.0, 100902.0, 100932.0, 100955.0, 100985.0, 101010.0,
        101035.0, 101057.0, 101085.0, 101112.0, 101137.0, 101165.0, 101197.0,
        101225.0, 101260.0, 101292.0, 101327.0, 101360.0, 101395.0, 101432.0,
        101465.0, 101500.0, 101532.0, 101565.0, 101592.0, 101625.0, 101650.0,
        101672.0, 101695.0, 101715.0, 101732.0, 101740.0, 101755.0, 101762.0,
        101770.0, 101775.0, 101772.0, 101770.0, 101767.0, 101755.0, 101747.0,
        101735.0, 101715.0, 101697.0, 101675.0, 101650.0, 101620.0, 101590.0,
        101555.0, 101517.0, 101480.0, 101440.0, 101395.0, 101355.0, 101310.0,
        101267.0, 101220.0, 101177.0, 101130.0, 101085.0, 101042.0, 100995.0,
        100950.0, 100907.0, 100860.0, 100812.0, 100765.0, 100720.0, 100667.0,
        100617.0, 100567.0, 100510.0, 100452.0, 100395.0, 100332.0, 100272.0,
        100205.0, 100140.0, 100070.0, 100002.0, 99932.0, 99865.0, 99800.0,
        99730.0, 99665.0, 99600.0, 99540.0, 99485.0, 99435.0, 99385.0, 99345.0,
        99310.0, 99280.0, 99252.0, 99227.0, 99202.0, 99177.0, 99147.0, 99117.0,
        99087.0, 99055.0, 99017.0, 98975.0, 98940.0, 98897.0, 98862.0, 98832.0,
        98802.0, 98782.0, 98770.0, 98767.0, 98772.0, 98790.0, 98812.0, 98845.0,
        98890.0, 98937.0, 98995.0, 99055.0, 99122.0, 99192.0, 99272.0, 99347.0,
        99430.0, 99515.0, 99602.0, 99685.0, 99772.0, 99865.0, 99950.0, 100035.0,
        100117.0, 100200.0, 100355.0, 100452.0, 100547.0, 100637.0, 100715.0,
        100790.0, 100857.0, 100910.0, 100960.0, 101000.0, 101025.0, 101052.0,
        101075.0, 101090.0, 101102.0, 101110.0, 101122.0, 101135.0, 101147.0,
        101165.0, 101190.0, 101217.0, 101255.0, 101295.0, 101347.0, 101405.0,
        101470.0, 101537.0, 101615.0, 101687.0, 101765.0, 101845.0, 101920.0,
        101995.0, 102062.0, 102125.0, 102182.0, 102232.0, 102272.0, 102307.0,
        102332.0, 102350.0, 102367.0, 102375.0, 102380.0, 102377.0, 102372.0,
        102367.0, 102355.0, 102335.0, 102310.0, 102280.0, 102245.0, 102207.0,
        102165.0, 102117.0, 102067.0, 102020.0, 101967.0, 101920.0, 101865.0,
        101820.0, 101767.0, 101717.0, 101667.0, 101615.0, 101562.0, 101505.0,
        101452.0, 101397.0, 101342.0, 101290.0, 101237.0, 101190.0, 101137.0,
        101087.0, 101040.0, 100990.0, 100940.0, 100892.0, 100842.0, 100792.0,
        100747.0, 100702.0, 100652.0, 100605.0, 100550.0, 100495.0, 100430.0,
        100357.0, 100277.0, 100185.0, 100085.0, 99977.0, 99865.0, 99745.0,
        99617.0, 99497.0, 99380.0, 99267.0, 99172.0, 99092.0, 99035.0, 99000.0,
        98970.0, 98950.0, 98932.0, 98910.0, 98872.0, 98817.0, 98752.0, 98675.0,
        98587.0, 98505.0, 98430.0, 98365.0, 98317.0, 98285.0, 98280.0, 98287.0,
        98315.0, 98362.0, 98427.0, 98510.0, 98605.0, 98712.0, 98820.0, 98935.0,
        99037.0, 99132.0, 99217.0, 99287.0, 99355.0, 99412.0, 99472.0, 99532.0,
        99602.0, 99677.0, 99762.0, 99850.0, 99947.0, 100047.0, 100152.0,
        100252.0, 100205.0, 100345.0, 100482.0, 100617.0, 100745.0, 100860.0,
        100967.0, 101055.0, 101127.0, 101182.0, 101220.0, 101242.0, 101250.0,
        101250.0, 101240.0, 101230.0, 101215.0, 101210.0, 101205.0, 101212.0,
        101227.0, 101260.0, 101302.0, 101365.0, 101442.0, 101535.0, 101640.0,
        101752.0, 101872.0, 101992.0, 102112.0, 102235.0, 102352.0, 102467.0,
        102570.0, 102667.0, 102750.0, 102817.0, 102870.0, 102910.0, 102937.0,
        102950.0, 102960.0, 102962.0, 102960.0, 102955.0, 102947.0, 102937.0,
        102925.0, 102905.0, 102877.0, 102840.0, 102787.0, 102730.0, 102652.0,
        102572.0, 102487.0, 102402.0, 102325.0, 102257.0, 102205.0, 102155.0,
        102117.0, 102082.0, 102042.0, 102000.0, 101950.0, 101892.0, 101827.0,
        101755.0, 101682.0, 101612.0, 101545.0, 101482.0, 101422.0, 101367.0,
        101310.0, 101252.0, 101195.0, 101127.0, 101055.0, 100975.0, 100895.0,
        100807.0, 100727.0, 100652.0, 100587.0, 100527.0, 100480.0, 100437.0,
        100385.0, 100327.0, 100245.0, 100145.0, 100017.0, 99862.0, 99690.0,
        99497.0, 99297.0, 99095.0, 98900.0, 98722.0, 98565.0, 98435.0, 98312.0,
        98210.0, 98112.0, 98007.0, 97897.0, 97772.0, 97640.0, 97517.0, 97410.0,
        97325.0, 97267.0, 97245.0, 97250.0, 97280.0, 97340.0, 97427.0, 97557.0,
        97720.0, 97930.0, 98175.0, 98445.0, 98720.0, 98972.0, 99182.0, 99332.0,
        99417.0, 99440.0, 99420.0, 99377.0, 99337.0, 99315.0, 99320.0, 99352.0,
        99412.0, 99495.0, 99587.0, 99695.0, 99810.0, 99937.0, 100067.0, 99827.0,
        100032.0, 100235.0, 100437.0, 100620.0, 100785.0, 100932.0, 101062.0,
        101162.0, 101240.0, 101302.0, 101340.0, 101360.0, 101372.0, 101377.0,
        101377.0, 101390.0, 101400.0, 101420.0, 101447.0, 101485.0, 101535.0,
        101610.0, 101705.0, 101822.0, 101960.0, 102102.0, 102245.0, 102387.0,
        102522.0, 102652.0, 102777.0, 102907.0, 103032.0, 103155.0, 103265.0,
        103360.0, 103442.0, 103507.0, 103562.0, 103597.0, 103617.0, 103620.0,
        103610.0, 103585.0, 103545.0, 103495.0, 103445.0, 103395.0, 103345.0,
        103295.0, 103247.0, 103192.0, 103122.0, 103032.0, 102940.0, 102832.0,
        102730.0, 102632.0, 102557.0, 102507.0, 102482.0, 102475.0, 102472.0,
        102470.0, 102462.0, 102437.0, 102402.0, 102342.0, 102272.0, 102192.0,
        102110.0, 102025.0, 101942.0, 101862.0, 101775.0, 101677.0, 101575.0,
        101465.0, 101352.0, 101240.0, 101127.0, 101017.0, 100910.0, 100807.0,
        100705.0, 100612.0, 100520.0, 100432.0, 100352.0, 100275.0, 100195.0,
        100110.0, 100007.0, 99885.0, 99740.0, 99557.0, 99350.0, 99115.0,
        98860.0, 98595.0, 98327.0, 98072.0, 97840.0, 97642.0, 97482.0, 97337.0,
        97227.0, 97125.0, 97027.0, 96930.0, 96832.0, 96757.0, 96705.0, 96687.0,
        96697.0, 96732.0, 96782.0, 96850.0, 96940.0, 97077.0, 97277.0, 97550.0,
        97890.0, 98282.0, 98682.0, 99047.0, 99327.0, 99490.0, 99527.0, 99440.0,
        99285.0, 99092.0, 98925.0, 98800.0, 98742.0, 98740.0, 98785.0, 98865.0,
        98972.0, 99105.0, 99260.0, 99435.0, 99627.0, 99375.0, 99612.0, 99855.0,
        100090.0, 100312.0, 100520.0, 100707.0, 100867.0, 101002.0, 101112.0,
        101202.0, 101280.0, 101352.0, 101420.0, 101487.0, 101557.0, 101635.0,
        101707.0, 101785.0, 101862.0, 101937.0, 102017.0, 102115.0, 102227.0,
        102355.0, 102490.0, 102627.0, 102757.0, 102882.0, 103012.0, 103145.0,
        103285.0, 103427.0, 103562.0, 103692.0, 103807.0, 103902.0, 103982.0,
        104040.0, 104090.0, 104135.0, 104165.0, 104190.0, 104200.0, 104180.0,
        104125.0, 104045.0, 103955.0, 103847.0, 103730.0, 103615.0, 103507.0,
        103410.0, 103317.0, 103217.0, 103120.0, 103020.0, 102927.0, 102852.0,
        102802.0, 102782.0, 102792.0, 102832.0, 102892.0, 102962.0, 103017.0,
        103062.0, 103082.0, 103072.0, 103035.0, 102982.0, 102912.0, 102830.0,
        102727.0, 102607.0, 102462.0, 102292.0, 102107.0, 101917.0, 101735.0,
        101570.0, 101417.0, 101282.0, 101155.0, 101037.0, 100922.0, 100812.0,
        100697.0, 100582.0, 100465.0, 100345.0, 100225.0, 100112.0, 99997.0,
        99872.0, 99735.0, 99580.0, 99390.0, 99167.0, 98915.0, 98640.0, 98342.0,
        98052.0, 97782.0, 97557.0, 97385.0, 97255.0, 97185.0, 97142.0, 97117.0,
        97082.0, 97040.0, 96982.0, 96920.0, 96885.0, 96850.0, 96835.0, 96842.0,
        96865.0, 96877.0, 96907.0, 96967.0, 97082.0, 97280.0, 97580.0, 97972.0,
        98417.0, 98847.0, 99180.0, 99347.0, 99325.0, 99145.0, 98885.0, 98632.0,
        98447.0, 98337.0, 98292.0, 98300.0, 98352.0, 98437.0, 98567.0, 98732.0,
        98930.0, 99145.0, 99057.0, 99242.0, 99462.0, 99712.0, 99977.0, 100230.0,
        100462.0, 100660.0, 100840.0, 100995.0, 101135.0, 101270.0, 101397.0,
        101520.0, 101647.0, 101782.0, 101927.0, 102075.0, 102217.0, 102345.0,
        102450.0, 102537.0, 102617.0, 102692.0, 102780.0, 102877.0, 102982.0,
        103095.0, 103212.0, 103337.0, 103465.0, 103600.0, 103732.0, 103865.0,
        103985.0, 104095.0, 104180.0, 104245.0, 104287.0, 104312.0, 104325.0,
        104330.0, 104327.0, 104317.0, 104300.0, 104265.0, 104220.0, 104165.0,
        104102.0, 104025.0, 103940.0, 103842.0, 103735.0, 103597.0, 103452.0,
        103315.0, 103197.0, 103117.0, 103070.0, 103052.0, 103067.0, 103112.0,
        103165.0, 103235.0, 103317.0, 103405.0, 103492.0, 103560.0, 103602.0,
        103622.0, 103625.0, 103615.0, 103582.0, 103510.0, 103412.0, 103272.0,
        103105.0, 102920.0, 102725.0, 102535.0, 102355.0, 102177.0, 102010.0,
        101840.0, 101665.0, 101490.0, 101315.0, 101152.0, 101007.0, 100867.0,
        100732.0, 100597.0, 100455.0, 100300.0, 100145.0, 99980.0, 99810.0,
        99620.0, 99405.0, 99162.0, 98895.0, 98597.0, 98295.0, 97997.0, 97745.0,
        97552.0, 97422.0, 97357.0, 97347.0, 97390.0, 97467.0, 97570.0, 97667.0,
        97727.0, 97722.0, 97650.0, 97537.0, 97377.0, 97240.0, 97152.0, 97127.0,
        97127.0, 97122.0, 97115.0, 97170.0, 97385.0, 97810.0, 98380.0, 98920.0,
        99212.0, 99145.0, 98800.0, 98395.0, 98130.0, 98055.0, 98105.0, 98187.0,
        98257.0, 98320.0, 98400.0, 98502.0, 98620.0, 98755.0, 98895.0, 98942.0,
        99067.0, 99275.0, 99560.0, 99867.0, 100157.0, 100427.0, 100690.0,
        100945.0, 101170.0, 101365.0, 101542.0, 101705.0, 101855.0, 101997.0,
        102140.0, 102287.0, 102447.0, 102602.0, 102735.0, 102842.0, 102920.0,
        102970.0, 103012.0, 103055.0, 103107.0, 103177.0, 103265.0, 103365.0,
        103470.0, 103580.0, 103690.0, 103782.0, 103865.0, 103942.0, 104037.0,
        104172.0, 104300.0, 104337.0, 104302.0, 104252.0, 104217.0, 104192.0,
        104172.0, 104135.0, 104087.0, 104032.0, 103985.0, 103967.0, 103980.0,
        104025.0, 104070.0, 104052.0, 103962.0, 103827.0, 103687.0, 103577.0,
        103502.0, 103470.0, 103465.0, 103465.0, 103467.0, 103480.0, 103527.0,
        103615.0, 103722.0, 103815.0, 103860.0, 103877.0, 103877.0, 103887.0,
        103895.0, 103897.0, 103867.0, 103800.0, 103702.0, 103575.0, 103430.0,
        103285.0, 103160.0, 103045.0, 102930.0, 102810.0, 102685.0, 102550.0,
        102407.0, 102250.0, 102080.0, 101897.0, 101705.0, 101500.0, 101280.0,
        101042.0, 100797.0, 100572.0, 100370.0, 100197.0, 100032.0, 99852.0,
        99642.0, 99415.0, 99172.0, 98915.0, 98657.0, 98390.0, 98145.0, 97935.0,
        97785.0, 97705.0, 97692.0, 97740.0, 97842.0, 97995.0, 98155.0, 98285.0,
        98352.0, 98350.0, 98260.0, 98072.0, 97822.0, 97580.0, 97425.0, 97310.0,
        97162.0, 97037.0, 97117.0, 97532.0, 98190.0, 98795.0, 99055.0, 98872.0,
        98410.0, 97980.0, 97792.0, 97852.0, 98005.0, 98140.0, 98240.0, 98347.0,
        98472.0, 98602.0, 98717.0, 98805.0, 98865.0, 98985.0, 99127.0, 99370.0,
        99685.0, 100012.0, 100362.0, 100782.0, 101215.0, 101555.0, 101755.0,
        101865.0, 101965.0, 102077.0, 102180.0, 102277.0, 102390.0, 102517.0,
        102655.0, 102805.0, 102955.0, 103080.0, 103167.0, 103212.0, 103245.0,
        103270.0, 103290.0, 103312.0, 103337.0, 103375.0, 103430.0, 103507.0,
        103600.0, 103692.0, 103772.0, 103850.0, 103962.0, 104175.0, 104380.0,
        104427.0, 104275.0, 104070.0, 103930.0, 103887.0, 103922.0, 103985.0,
        104002.0, 103972.0, 103957.0, 103975.0, 104037.0, 104145.0, 104235.0,
        104227.0, 104162.0, 104082.0, 103997.0, 103912.0, 103850.0, 103820.0,
        103800.0, 103770.0, 103735.0, 103737.0, 103797.0, 103895.0, 103980.0,
        104010.0, 103990.0, 103952.0, 103950.0, 103987.0, 104032.0, 104035.0,
        103972.0, 103882.0, 103800.0, 103697.0, 103557.0, 103395.0, 103255.0,
        103145.0, 103042.0, 102977.0, 102940.0, 102940.0, 102940.0, 102907.0,
        102810.0, 102660.0, 102477.0, 102262.0, 102007.0, 101710.0, 101410.0,
        101142.0, 100920.0, 100735.0, 100580.0, 100427.0, 100272.0, 100110.0,
        99935.0, 99752.0, 99540.0, 99300.0, 99035.0, 98785.0, 98570.0, 98397.0,
        98282.0, 98207.0, 98167.0, 98170.0, 98212.0, 98302.0, 98415.0, 98542.0,
        98665.0, 98690.0, 98475.0, 98100.0, 97780.0, 97550.0, 97282.0, 97145.0,
        97430.0, 97895.0, 98017.0, 97747.0, 97452.0, 97350.0, 97390.0, 97485.0,
        97605.0, 97742.0, 97842.0, 97917.0, 97985.0, 98090.0, 98245.0, 98440.0,
        98642.0, 98795.0, 98897.0, 99312.0, 99512.0, 99762.0, 100025.0,
        100327.0, 100745.0, 101192.0, 101527.0, 101700.0, 101782.0, 101852.0,
        101922.0, 102002.0, 102080.0, 102175.0, 102307.0, 102452.0, 102622.0,
        102807.0, 102980.0, 103105.0, 103202.0, 103300.0, 103410.0, 103522.0,
        103615.0, 103632.0, 103590.0, 103547.0, 103517.0, 103510.0, 103552.0,
        103630.0, 103720.0, 103797.0, 103880.0, 103987.0, 104155.0, 104257.0,
        104202.0, 104045.0, 103900.0, 103865.0, 103985.0, 104127.0, 104105.0,
        103970.0, 103947.0, 104070.0, 104262.0, 104412.0, 104370.0, 104187.0,
        104092.0, 104132.0, 104235.0, 104352.0, 104402.0, 104352.0, 104252.0,
        104160.0, 104085.0, 104030.0, 104010.0, 104030.0, 104075.0, 104097.0,
        104055.0, 103965.0, 103907.0, 103912.0, 103940.0, 103922.0, 103865.0,
        103792.0, 103722.0, 103632.0, 103485.0, 103295.0, 103107.0, 102950.0,
        102840.0, 102770.0, 102715.0, 102687.0, 102717.0, 102787.0, 102857.0,
        102905.0, 102925.0, 102902.0, 102780.0, 102512.0, 102135.0, 101760.0,
        101465.0, 101260.0, 101100.0, 100977.0, 100860.0, 100745.0, 100632.0,
        100512.0, 100355.0, 100142.0, 99887.0, 99620.0, 99350.0, 99077.0,
        98802.0, 98580.0, 98465.0, 98477.0, 98590.0, 98717.0, 98805.0, 98882.0,
        98985.0, 99032.0, 98832.0, 98410.0, 98052.0, 97722.0, 97340.0, 97470.0,
        98287.0, 98532.0, 97530.0, 96495.0, 96327.0, 96665.0, 96995.0, 97255.0,
        97507.0, 97740.0, 97892.0, 97962.0, 97970.0, 97992.0, 98115.0, 98362.0,
        98655.0, 98927.0, 99135.0, 100062.0, 100247.0, 100395.0, 100575.0,
        100865.0, 101175.0, 101375.0, 101512.0, 101667.0, 101817.0, 101940.0,
        102005.0, 102025.0, 102027.0, 102072.0, 102165.0, 102280.0, 102412.0,
        102565.0, 102722.0, 102862.0, 103012.0, 103182.0, 103362.0, 103490.0,
        103512.0, 103485.0, 103470.0, 103492.0, 103547.0, 103605.0, 103662.0,
        103732.0, 103820.0, 103902.0, 103950.0, 103962.0, 103982.0, 104035.0,
        104077.0, 104060.0, 103995.0, 103967.0, 104057.0, 104215.0, 104257.0,
        104120.0, 103982.0, 104040.0, 104227.0, 104367.0, 104250.0, 104025.0,
        103995.0, 104135.0, 104415.0, 104775.0, 104960.0, 104885.0, 104722.0,
        104565.0, 104337.0, 104030.0, 103820.0, 103807.0, 103890.0, 103965.0,
        104017.0, 104065.0, 104097.0, 104112.0, 104075.0, 103987.0, 103915.0,
        103877.0, 103825.0, 103707.0, 103515.0, 103295.0, 103105.0, 103002.0,
        102942.0, 102772.0, 102417.0, 101992.0, 101725.0, 101762.0, 102072.0,
        102490.0, 102850.0, 103107.0, 103232.0, 103087.0, 102660.0, 102185.0,
        101850.0, 101652.0, 101520.0, 101432.0, 101360.0, 101287.0, 101230.0,
        101177.0, 101075.0, 100875.0, 100625.0, 100380.0, 100142.0, 99890.0,
        99597.0, 99295.0, 99075.0, 99015.0, 99135.0, 99290.0, 99335.0, 99290.0,
        99235.0, 99165.0, 98975.0, 98627.0, 98287.0, 97937.0, 97467.0, 97270.0,
        97482.0, 97260.0, 96415.0, 95920.0, 96090.0, 96447.0, 96827.0, 97247.0,
        97660.0, 98002.0, 98237.0, 98335.0, 98385.0, 98482.0, 98700.0, 99005.0,
        99332.0, 99620.0, 99855.0, 100810.0, 100915.0, 101000.0, 101115.0,
        101260.0, 101365.0, 101442.0, 101590.0, 101767.0, 101927.0, 102032.0,
        102025.0, 101945.0, 101897.0, 101927.0, 102002.0, 102085.0, 102155.0,
        102255.0, 102382.0, 102507.0, 102635.0, 102827.0, 103092.0, 103287.0,
        103327.0, 103282.0, 103267.0, 103332.0, 103450.0, 103527.0, 103570.0,
        103620.0, 103710.0, 103840.0, 103997.0, 104110.0, 104130.0, 104122.0,
        104165.0, 104230.0, 104190.0, 104035.0, 103957.0, 104077.0, 104257.0,
        104295.0, 104197.0, 104125.0, 104212.0, 104362.0, 104327.0, 104127.0,
        104007.0, 104055.0, 104122.0, 104087.0, 103935.0, 103790.0, 103735.0,
        103692.0, 103595.0, 103535.0, 103622.0, 103785.0, 103865.0, 103845.0,
        103817.0, 103837.0, 103885.0, 103902.0, 103882.0, 103872.0, 103892.0,
        103907.0, 103870.0, 103760.0, 103600.0, 103435.0, 103277.0, 103127.0,
        102875.0, 102322.0, 101470.0, 100635.0, 100097.0, 99940.0, 100202.0,
        100750.0, 101335.0, 101825.0, 102275.0, 102625.0, 102632.0, 102375.0,
        102142.0, 102007.0, 101910.0, 101810.0, 101710.0, 101625.0, 101572.0,
        101525.0, 101447.0, 101315.0, 101120.0, 100890.0, 100670.0, 100477.0,
        100310.0, 100130.0, 99920.0, 99750.0, 99670.0, 99692.0, 99772.0,
        99840.0, 99852.0, 99760.0, 99492.0, 99050.0, 98602.0, 98242.0, 97907.0,
        97567.0, 97277.0, 97007.0, 96795.0, 96770.0, 96927.0, 97245.0, 97645.0,
        98027.0, 98322.0, 98530.0, 98687.0, 98845.0, 99060.0, 99350.0, 99685.0,
        100010.0, 100292.0, 100507.0, 100675.0, 101442.0, 101457.0, 101472.0,
        101477.0, 101497.0, 101567.0, 101687.0, 101837.0, 101980.0, 102097.0,
        102170.0, 102145.0, 102052.0, 101982.0, 101965.0, 101980.0, 101985.0,
        101990.0, 102015.0, 102057.0, 102082.0, 102112.0, 102220.0, 102460.0,
        102727.0, 102867.0, 102877.0, 102855.0, 102842.0, 102875.0, 102967.0,
        103145.0, 103347.0, 103472.0, 103520.0, 103627.0, 103850.0, 104040.0,
        104080.0, 104080.0, 104185.0, 104365.0, 104477.0, 104442.0, 104352.0,
        104310.0, 104290.0, 104215.0, 104107.0, 104095.0, 104220.0, 104335.0,
        104225.0, 103917.0, 103672.0, 103590.0, 103527.0, 103410.0, 103287.0,
        103205.0, 103137.0, 103097.0, 103167.0, 103342.0, 103492.0, 103490.0,
        103417.0, 103380.0, 103382.0, 103365.0, 103327.0, 103325.0, 103387.0,
        103467.0, 103502.0, 103492.0, 103470.0, 103442.0, 103375.0, 103210.0,
        102935.0, 102560.0, 102070.0, 101482.0, 100920.0, 100515.0, 100285.0,
        100225.0, 100332.0, 100500.0, 100645.0, 100857.0, 101250.0, 101622.0,
        101752.0, 101802.0, 101912.0, 102007.0, 102020.0, 101980.0, 101970.0,
        101975.0, 101915.0, 101802.0, 101702.0, 101607.0, 101435.0, 101180.0,
        100945.0, 100782.0, 100657.0, 100510.0, 100372.0, 100267.0, 100230.0,
        100300.0, 100450.0, 100560.0, 100497.0, 100205.0, 99790.0, 99377.0,
        99015.0, 98727.0, 98527.0, 98417.0, 98357.0, 98322.0, 98335.0, 98445.0,
        98670.0, 98930.0, 99120.0, 99197.0, 99242.0, 99372.0, 99625.0, 99950.0,
        100255.0, 100537.0, 100805.0, 101075.0, 101287.0, 101400.0, 101997.0,
        101925.0, 101892.0, 101872.0, 101872.0, 101917.0, 102027.0, 102147.0,
        102215.0, 102252.0, 102275.0, 102282.0, 102252.0, 102217.0, 102185.0,
        102157.0, 102152.0, 102145.0, 102100.0, 102005.0, 101917.0, 101875.0,
        101900.0, 102032.0, 102222.0, 102342.0, 102362.0, 102375.0, 102412.0,
        102452.0, 102482.0, 102620.0, 102872.0, 103065.0, 103132.0, 103227.0,
        103495.0, 103847.0, 104095.0, 104177.0, 104172.0, 104217.0, 104342.0,
        104442.0, 104360.0, 104042.0, 103832.0, 103890.0, 103990.0, 103970.0,
        103910.0, 103882.0, 103770.0, 103477.0, 103222.0, 103202.0, 103197.0,
        103055.0, 102910.0, 102812.0, 102757.0, 102740.0, 102812.0, 102942.0,
        102942.0, 102770.0, 102625.0, 102532.0, 102450.0, 102372.0, 102352.0,
        102412.0, 102515.0, 102592.0, 102652.0, 102752.0, 102902.0, 103020.0,
        103022.0, 102902.0, 102715.0, 102497.0, 102220.0, 101887.0, 101545.0,
        101252.0, 101022.0, 100825.0, 100665.0, 100555.0, 100480.0, 100400.0,
        100412.0, 100537.0, 100657.0, 100780.0, 100985.0, 101240.0, 101442.0,
        101575.0, 101737.0, 101947.0, 102040.0, 101960.0, 101862.0, 101817.0,
        101732.0, 101560.0, 101415.0, 101322.0, 101182.0, 100987.0, 100857.0,
        100847.0, 100880.0, 100927.0, 100980.0, 101080.0, 101147.0, 101022.0,
        100727.0, 100442.0, 100180.0, 99910.0, 99702.0, 99602.0, 99595.0,
        99625.0, 99690.0, 99795.0, 99930.0, 100060.0, 100137.0, 100165.0,
        100215.0, 100365.0, 100612.0, 100880.0, 101107.0, 101337.0, 101600.0,
        101860.0, 102037.0, 102065.0, 102285.0, 102250.0, 102240.0, 102237.0,
        102212.0, 102215.0, 102302.0, 102425.0, 102465.0, 102425.0, 102372.0,
        102337.0, 102335.0, 102385.0, 102430.0, 102417.0, 102407.0, 102420.0,
        102380.0, 102270.0, 102182.0, 102162.0, 102162.0, 102160.0, 102200.0,
        102247.0, 102200.0, 102067.0, 102005.0, 102040.0, 102055.0, 102037.0,
        102142.0, 102392.0, 102665.0, 102942.0, 103197.0, 103392.0, 103695.0,
        104345.0, 104867.0, 104500.0, 104090.0, 104002.0, 103860.0, 103480.0,
        103200.0, 103297.0, 103570.0, 103720.0, 103680.0, 103630.0, 103575.0,
        103437.0, 103235.0, 103057.0, 102907.0, 102757.0, 102645.0, 102575.0,
        102515.0, 102472.0, 102447.0, 102387.0, 102207.0, 101960.0, 101725.0,
        101527.0, 101395.0, 101350.0, 101372.0, 101407.0, 101415.0, 101437.0,
        101542.0, 101745.0, 101995.0, 102207.0, 102367.0, 102495.0, 102585.0,
        102577.0, 102437.0, 102227.0, 102027.0, 101870.0, 101717.0, 101535.0,
        101322.0, 101095.0, 100895.0, 100740.0, 100627.0, 100577.0, 100567.0,
        100555.0, 100597.0, 100722.0, 100865.0, 101005.0, 101197.0, 101482.0,
        101787.0, 101940.0, 101967.0, 101947.0, 101852.0, 101675.0, 101547.0,
        101500.0, 101430.0, 101292.0, 101207.0, 101240.0, 101350.0, 101430.0,
        101462.0, 101517.0, 101600.0, 101595.0, 101460.0, 101250.0, 101012.0,
        100812.0, 100657.0, 100550.0, 100502.0, 100525.0, 100615.0, 100725.0,
        100807.0, 100875.0, 100952.0, 101040.0, 101130.0, 101240.0, 101392.0,
        101590.0, 101805.0, 102025.0, 102205.0, 102307.0, 102337.0, 102327.0,
        102470.0, 102472.0, 102475.0, 102502.0, 102492.0, 102467.0, 102540.0,
        102642.0, 102637.0, 102575.0, 102527.0, 102457.0, 102350.0, 102320.0,
        102340.0, 102332.0, 102360.0, 102470.0, 102570.0, 102590.0, 102580.0,
        102592.0, 102557.0, 102472.0, 102415.0, 102402.0, 102332.0, 102160.0,
        102002.0, 102012.0, 102155.0, 102297.0, 102392.0, 102522.0, 102777.0,
        103427.0, 103750.0, 103345.0, 103110.0, 103452.0, 104297.0, 104367.0,
        103982.0, 103862.0, 103832.0, 103355.0, 102867.0, 102810.0, 103115.0,
        103397.0, 103472.0, 103500.0, 103475.0, 103402.0, 103302.0, 103060.0,
        102690.0, 102412.0, 102275.0, 102172.0, 102092.0, 102042.0, 101965.0,
        101812.0, 101572.0, 101287.0, 100990.0, 100722.0, 100552.0, 100495.0,
        100462.0, 100375.0, 100262.0, 100242.0, 100387.0, 100655.0, 100967.0,
        101305.0, 101640.0, 101930.0, 102142.0, 102297.0, 102430.0, 102512.0,
        102510.0, 102420.0, 102267.0, 102087.0, 101897.0, 101667.0, 101410.0,
        101160.0, 100940.0, 100770.0, 100700.0, 100717.0, 100767.0, 100827.0,
        100837.0, 100785.0, 100807.0, 100975.0, 101290.0, 101580.0, 101700.0,
        101725.0, 101725.0, 101650.0, 101505.0, 101405.0, 101380.0, 101390.0,
        101397.0, 101395.0, 101412.0, 101490.0, 101625.0, 101695.0, 101670.0,
        101625.0, 101590.0, 101532.0, 101455.0, 101387.0, 101320.0, 101230.0,
        101177.0, 101200.0, 101267.0, 101325.0, 101360.0, 101400.0, 101480.0,
        101590.0, 101707.0, 101845.0, 102010.0, 102165.0, 102272.0, 102352.0,
        102407.0, 102420.0, 102412.0, 102432.0, 102680.0, 102647.0, 102665.0,
        102795.0, 102857.0, 102795.0, 102742.0, 102697.0, 102602.0, 102522.0,
        102535.0, 102377.0, 102017.0, 101747.0, 101680.0, 101762.0, 101962.0,
        102227.0, 102422.0, 102510.0, 102552.0, 102617.0, 102657.0, 102647.0,
        102602.0, 102530.0, 102480.0, 102450.0, 102385.0, 102322.0, 102280.0,
        102265.0, 102290.0, 102355.0, 102427.0, 102715.0, 103265.0, 103480.0,
        103327.0, 103347.0, 103687.0, 103770.0, 103667.0, 103622.0, 103452.0,
        102810.0, 102327.0, 102290.0, 102627.0, 102852.0, 102950.0, 103117.0,
        103252.0, 103200.0, 103120.0, 102875.0, 102472.0, 102197.0, 101987.0,
        101780.0, 101642.0, 101585.0, 101490.0, 101327.0, 101145.0, 100952.0,
        100717.0, 100447.0, 100190.0, 99992.0, 99847.0, 99690.0, 99480.0,
        99335.0, 99412.0, 99732.0, 100177.0, 100635.0, 101047.0, 101395.0,
        101692.0, 101977.0, 102257.0, 102465.0, 102572.0, 102630.0, 102652.0,
        102590.0, 102425.0, 102205.0, 101972.0, 101742.0, 101527.0, 101335.0,
        101167.0, 101090.0, 101105.0, 101137.0, 101145.0, 101037.0, 100862.0,
        100875.0, 101082.0, 101342.0, 101445.0, 101402.0, 101330.0, 101282.0,
        101217.0, 101192.0, 101205.0, 101265.0, 101342.0, 101427.0, 101550.0,
        101710.0, 101890.0, 101997.0, 101987.0, 101965.0, 101902.0, 101802.0,
        101755.0, 101752.0, 101702.0, 101612.0, 101572.0, 101590.0, 101597.0,
        101590.0, 101620.0, 101700.0, 101835.0, 102007.0, 102162.0, 102282.0,
        102375.0, 102430.0, 102427.0, 102445.0, 102537.0, 102645.0, 102687.0,
        102690.0, 102830.0, 102782.0, 102707.0, 102702.0, 102695.0, 102637.0,
        102642.0, 102682.0, 102617.0, 102490.0, 102235.0, 101822.0, 101462.0,
        101222.0, 101172.0, 101330.0, 101567.0, 101862.0, 102040.0, 102162.0,
        102317.0, 102437.0, 102492.0, 102555.0, 102602.0, 102532.0, 102407.0,
        102347.0, 102312.0, 102312.0, 102360.0, 102310.0, 102252.0, 102367.0,
        102552.0, 102665.0, 102765.0, 102987.0, 103215.0, 103395.0, 103542.0,
        103630.0, 103587.0, 103345.0, 102960.0, 102510.0, 102060.0, 101977.0,
        102217.0, 102292.0, 102365.0, 102642.0, 103030.0, 103112.0, 102960.0,
        102647.0, 102387.0, 102220.0, 101972.0, 101657.0, 101455.0, 101335.0,
        101155.0, 100957.0, 100820.0, 100717.0, 100622.0, 100487.0, 100265.0,
        99997.0, 99787.0, 99587.0, 99300.0, 99047.0, 99075.0, 99432.0, 99917.0,
        100350.0, 100732.0, 101132.0, 101527.0, 101872.0, 102150.0, 102365.0,
        102545.0, 102715.0, 102812.0, 102790.0, 102675.0, 102545.0, 102397.0,
        102195.0, 101975.0, 101800.0, 101617.0, 101515.0, 101555.0, 101555.0,
        101560.0, 101547.0, 101322.0, 101075.0, 101067.0, 101195.0, 101302.0,
        101320.0, 101232.0, 101147.0, 101152.0, 101240.0, 101355.0, 101457.0,
        101540.0, 101660.0, 101832.0, 101965.0, 102040.0, 102127.0, 102217.0,
        102225.0, 102150.0, 102047.0, 101990.0, 101947.0, 101840.0, 101687.0,
        101607.0, 101585.0, 101577.0, 101630.0, 101747.0, 101910.0, 102125.0,
        102355.0, 102500.0, 102522.0, 102502.0, 102535.0, 102605.0, 102682.0,
        102760.0, 102842.0, 102862.0, 102845.0, 102855.0, 102682.0, 102530.0,
        102497.0, 102565.0, 102557.0, 102437.0, 102355.0, 102440.0, 102387.0,
        101932.0, 101570.0, 101382.0, 101250.0, 101297.0, 101492.0, 101682.0,
        102020.0, 102072.0, 101920.0, 102065.0, 102265.0, 102365.0, 102410.0,
        102470.0, 102435.0, 102345.0, 102410.0, 102382.0, 102242.0, 102335.0,
        102510.0, 102700.0, 102837.0, 102832.0, 102760.0, 102627.0, 102590.0,
        102730.0, 102960.0, 103127.0, 103217.0, 103220.0, 103067.0, 102895.0,
        102675.0, 102337.0, 102097.0, 102052.0, 102080.0, 102185.0, 102505.0,
        102840.0, 102850.0, 102662.0, 102442.0, 102292.0, 102167.0, 101915.0,
        101630.0, 101492.0, 101375.0, 101142.0, 100907.0, 100735.0, 100612.0,
        100575.0, 100572.0, 100457.0, 100240.0, 100030.0, 99812.0, 99545.0,
        99340.0, 99377.0, 99645.0, 100002.0, 100375.0, 100775.0, 101200.0,
        101572.0, 101872.0, 102150.0, 102425.0, 102652.0, 102802.0, 102870.0,
        102862.0, 102820.0, 102755.0, 102640.0, 102452.0, 102255.0, 102092.0,
        101902.0, 101872.0, 101947.0, 101745.0, 101510.0, 101422.0, 101412.0,
        101287.0, 101065.0, 100985.0, 101050.0, 101140.0, 101207.0, 101302.0,
        101450.0, 101587.0, 101702.0, 101827.0, 101915.0, 101977.0, 102070.0,
        102125.0, 102147.0, 102192.0, 102220.0, 102165.0, 102085.0, 101992.0,
        101877.0, 101760.0, 101642.0, 101527.0, 101470.0, 101490.0, 101612.0,
        101812.0, 102030.0, 102237.0, 102407.0, 102520.0, 102590.0, 102652.0,
        102702.0, 102770.0, 102857.0, 102882.0, 102852.0, 102877.0, 102975.0,
        102967.0, 102750.0, 102650.0, 102585.0, 102517.0, 102495.0, 102460.0,
        102305.0, 102092.0, 102020.0, 102050.0, 101885.0, 101730.0, 101625.0,
        101607.0, 101632.0, 101770.0, 102027.0, 102365.0, 102365.0, 101970.0,
        101937.0, 102067.0, 102152.0, 102282.0, 102330.0, 102255.0, 102272.0,
        102422.0, 102407.0, 102785.0, 102900.0, 102512.0, 102457.0, 102525.0,
        102562.0, 102555.0, 102592.0, 102565.0, 102437.0, 102502.0, 102660.0,
        102815.0, 102820.0, 102752.0, 102722.0, 102607.0, 102335.0, 102075.0,
        101965.0, 101987.0, 102152.0, 102460.0, 102680.0, 102722.0, 102650.0,
        102500.0, 102305.0, 102082.0, 101822.0, 101580.0, 101457.0, 101357.0,
        101182.0, 101000.0, 100837.0, 100720.0, 100697.0, 100697.0, 100622.0,
        100515.0, 100400.0, 100250.0, 100080.0, 99962.0, 99952.0, 100067.0,
        100302.0, 100605.0, 100932.0, 101265.0, 101610.0, 101940.0, 102222.0,
        102447.0, 102617.0, 102752.0, 102892.0, 102980.0, 102962.0, 102857.0,
        102722.0, 102592.0, 102440.0, 102202.0, 101912.0, 101705.0, 101747.0,
        101735.0, 101447.0, 101180.0, 101135.0, 101330.0, 101207.0, 100900.0,
        100885.0, 101035.0, 101227.0, 101457.0, 101690.0, 101837.0, 101945.0,
        102087.0, 102207.0, 102220.0, 102265.0, 102307.0, 102270.0, 102195.0,
        102067.0, 101907.0, 101782.0, 101655.0, 101527.0, 101472.0, 101467.0,
        101495.0, 101575.0, 101712.0, 101912.0, 102107.0, 102255.0, 102410.0,
        102545.0, 102592.0, 102622.0, 102750.0, 102890.0, 102942.0, 102930.0,
        102892.0, 102815.0, 102850.0, 103117.0, 103035.0, 102770.0, 102710.0,
        102632.0, 102545.0, 102442.0, 102377.0, 102307.0, 102177.0, 102020.0,
        101895.0, 101780.0, 101690.0, 101627.0, 101562.0, 101602.0, 101837.0,
        101992.0, 102020.0, 102150.0, 102130.0, 101925.0, 101967.0, 102035.0,
        102180.0, 102257.0, 102282.0, 102300.0, 102360.0, 102565.0, 103567.0,
        103512.0, 102415.0, 102220.0, 102320.0, 102202.0, 102460.0, 102807.0,
        102970.0, 103055.0, 102890.0, 102542.0, 102537.0, 102680.0, 102665.0,
        102570.0, 102400.0, 102247.0, 102145.0, 102040.0, 102070.0, 102227.0,
        102380.0, 102527.0, 102620.0, 102585.0, 102475.0, 102282.0, 102087.0,
        101837.0, 101522.0, 101337.0, 101287.0, 101217.0, 101087.0, 100960.0,
        100882.0, 100850.0, 100807.0, 100760.0, 100715.0, 100637.0, 100545.0,
        100490.0, 100447.0, 100440.0, 100507.0, 100650.0, 100835.0, 101050.0,
        101310.0, 101615.0, 101890.0, 102087.0, 102272.0, 102495.0, 102702.0,
        102847.0, 102922.0, 102945.0, 102922.0, 102850.0, 102725.0, 102540.0,
        102257.0, 101970.0, 101750.0, 101620.0, 101710.0, 101535.0, 101205.0,
        101067.0, 101192.0, 101170.0, 100837.0, 100845.0, 101137.0, 101427.0,
        101600.0, 101732.0, 101857.0, 101990.0, 102150.0, 102260.0, 102292.0,
        102367.0, 102370.0, 102287.0, 102175.0, 102020.0, 101852.0, 101722.0,
        101625.0, 101595.0, 101630.0, 101670.0, 101742.0, 101870.0, 102000.0,
        102137.0, 102265.0, 102345.0, 102450.0, 102615.0, 102765.0, 102840.0,
        102895.0, 102960.0, 102950.0, 102875.0, 102767.0, 102655.0, 102592.0,
        102707.0, 102787.0, 102717.0, 102747.0, 102722.0, 102610.0, 102490.0,
        102395.0, 102262.0, 102102.0, 101980.0, 101907.0, 101825.0, 101722.0,
        101652.0, 101615.0, 101607.0, 101727.0, 101855.0, 101785.0, 101812.0,
        102012.0, 102152.0, 102112.0, 102080.0, 102087.0, 102157.0, 102115.0,
        102172.0, 102470.0, 102447.0, 102462.0, 103107.0, 103872.0, 103912.0,
        103480.0, 103427.0, 104000.0, 104555.0, 104505.0, 104317.0, 103832.0,
        103287.0, 102945.0, 102710.0, 102570.0, 102485.0, 102335.0, 102197.0,
        102125.0, 102060.0, 102095.0, 102155.0, 102182.0, 102310.0, 102422.0,
        102355.0, 102177.0, 102027.0, 101945.0, 101735.0, 101422.0, 101225.0,
        101165.0, 101090.0, 101002.0, 100960.0, 100945.0, 100925.0, 100895.0,
        100892.0, 100885.0, 100830.0, 100795.0, 100790.0, 100770.0, 100755.0,
        100737.0, 100737.0, 100870.0, 101130.0, 101390.0, 101582.0, 101727.0,
        101847.0, 102015.0, 102255.0, 102505.0, 102720.0, 102885.0, 102977.0,
        102990.0, 102895.0, 102735.0, 102570.0, 102382.0, 102155.0, 101962.0,
        101792.0, 101650.0, 101510.0, 101400.0, 101262.0, 101115.0, 101005.0,
        100972.0, 101097.0, 101370.0, 101597.0, 101680.0, 101737.0, 101845.0,
        102007.0, 102167.0, 102252.0, 102287.0, 102302.0, 102287.0, 102252.0,
        102190.0, 102082.0, 101985.0, 101927.0, 101885.0, 101880.0, 101900.0,
        101932.0, 102020.0, 102140.0, 102225.0, 102287.0, 102365.0, 102462.0,
        102582.0, 102707.0, 102825.0, 102887.0, 102865.0, 102812.0, 102762.0,
        102655.0, 102452.0, 102285.0, 102235.0, 102382.0, 102605.0, 102762.0,
        102800.0, 102712.0, 102592.0, 102495.0, 102385.0, 102290.0, 102195.0,
        102085.0, 101977.0, 101882.0, 101795.0, 101740.0, 101700.0, 101632.0,
        101730.0, 101815.0, 101720.0, 101655.0, 101682.0, 101897.0, 102235.0,
        102107.0, 102045.0, 102067.0, 101930.0, 101857.0, 102157.0, 102067.0,
        102177.0, 101947.0, 102390.0, 103812.0, 103807.0, 102847.0, 102560.0,
        103105.0, 104050.0, 104415.0, 104162.0, 103507.0, 102712.0, 102447.0,
        102377.0, 102412.0, 102340.0, 102190.0, 102105.0, 102022.0, 101970.0,
        101925.0, 101932.0, 102025.0, 102115.0, 102072.0, 101932.0, 101822.0,
        101750.0, 101600.0, 101322.0, 101037.0, 100825.0, 100695.0, 100655.0,
        100697.0, 100795.0, 100892.0, 100945.0, 100962.0, 100967.0, 100975.0,
        100987.0, 100970.0, 100940.0, 100912.0, 100850.0, 100830.0, 100965.0,
        101200.0, 101382.0, 101492.0, 101567.0, 101625.0, 101725.0, 101910.0,
        102180.0, 102507.0, 102775.0, 102907.0, 102917.0, 102850.0, 102735.0,
        102597.0, 102430.0, 102217.0, 102032.0, 101912.0, 101832.0, 101757.0,
        101667.0, 101482.0, 101217.0, 101090.0, 101167.0, 101340.0, 101525.0,
        101647.0, 101695.0, 101762.0, 101895.0, 102040.0, 102192.0, 102285.0,
        102272.0, 102235.0, 102245.0, 102245.0, 102207.0, 102152.0, 102105.0,
        102092.0, 102085.0, 102072.0, 102100.0, 102162.0, 102217.0, 102270.0,
        102345.0, 102407.0, 102427.0, 102472.0, 102597.0, 102677.0, 102677.0,
        102677.0, 102665.0, 102595.0, 102517.0, 102427.0, 102262.0, 102047.0,
        101982.0, 102240.0, 102560.0, 102462.0, 102545.0, 102532.0, 102387.0,
        102242.0, 102187.0, 102167.0, 102145.0, 102060.0, 101902.0, 101815.0,
        101787.0, 101710.0, 101637.0, 101690.0, 101830.0, 101840.0, 101777.0,
        101635.0, 101587.0, 101587.0, 101917.0, 102142.0, 102147.0, 102120.0,
        101987.0, 101940.0, 101995.0, 101905.0, 101872.0, 101957.0, 101940.0,
        102140.0, 103112.0, 103912.0, 104052.0, 103972.0, 103385.0, 102755.0,
        102942.0, 103140.0, 102420.0, 102367.0, 102245.0, 102210.0, 102232.0,
        102137.0, 102052.0, 101957.0, 101827.0, 101740.0, 101767.0, 101835.0,
        101915.0, 101920.0, 101820.0, 101715.0, 101637.0, 101510.0, 101260.0,
        100955.0, 100717.0, 100585.0, 100537.0, 100587.0, 100735.0, 100900.0,
        101007.0, 101057.0, 101087.0, 101080.0, 101060.0, 101042.0, 101027.0,
        100985.0, 100920.0, 100935.0, 101077.0, 101270.0, 101427.0, 101512.0,
        101495.0, 101440.0, 101500.0, 101720.0, 102005.0, 102297.0, 102535.0,
        102702.0, 102807.0, 102812.0, 102737.0, 102600.0, 102442.0, 102297.0,
        102175.0, 102067.0, 101947.0, 101805.0, 101685.0, 101570.0, 101437.0,
        101292.0, 101327.0, 101477.0, 101620.0, 101725.0, 101772.0, 101825.0,
        101942.0, 102077.0, 102190.0, 102280.0, 102292.0, 102282.0, 102300.0,
        102310.0, 102287.0, 102242.0, 102182.0, 102142.0, 102142.0, 102162.0,
        102215.0, 102287.0, 102335.0, 102342.0, 102347.0, 102367.0, 102397.0,
        102425.0, 102475.0, 102515.0, 102500.0, 102457.0, 102425.0, 102380.0,
        102315.0, 102252.0, 102190.0, 102047.0, 102057.0, 102222.0, 102362.0,
        102035.0, 102005.0, 102067.0, 101992.0, 101872.0, 101895.0, 101922.0,
        101935.0, 101937.0, 101832.0, 101735.0, 101680.0, 101585.0, 101472.0,
        101460.0, 101617.0, 101795.0, 101825.0, 101780.0, 101615.0, 101592.0,
        101552.0, 101655.0, 101777.0, 101852.0, 101890.0, 101892.0, 101872.0,
        101787.0, 101642.0, 101547.0, 101742.0, 101917.0, 101797.0, 101830.0,
        102120.0, 102292.0, 102102.0, 101945.0, 101885.0, 102445.0, 102425.0,
        102260.0, 102075.0, 101977.0, 102055.0, 101970.0, 101922.0, 101857.0,
        101717.0, 101625.0, 101610.0, 101667.0, 101737.0, 101717.0, 101665.0,
        101650.0, 101620.0, 101515.0, 101342.0, 101137.0, 100935.0, 100772.0,
        100685.0, 100720.0, 100807.0, 100872.0, 100932.0, 101017.0, 101077.0,
        101075.0, 101062.0, 101052.0, 101032.0, 101002.0, 100985.0, 101035.0,
        101175.0, 101335.0, 101432.0, 101457.0, 101427.0, 101400.0, 101452.0,
        101605.0, 101832.0, 102105.0, 102365.0, 102552.0, 102647.0, 102637.0,
        102590.0, 102527.0, 102437.0, 102312.0, 102190.0, 102117.0, 102047.0,
        101915.0, 101760.0, 101620.0, 101562.0, 101522.0, 101452.0, 101487.0,
        101595.0, 101717.0, 101830.0, 101892.0, 101980.0, 102092.0, 102167.0,
        102247.0, 102295.0, 102282.0, 102280.0, 102270.0, 102217.0, 102157.0,
        102120.0, 102132.0, 102162.0, 102192.0, 102217.0, 102237.0, 102262.0,
        102277.0, 102245.0, 102190.0, 102210.0, 102272.0, 102275.0, 102242.0,
        102245.0, 102222.0, 102145.0, 102102.0, 102090.0, 102050.0, 102010.0,
        102017.0, 102037.0, 102060.0, 102080.0, 101617.0, 101580.0, 101620.0,
        101647.0, 101622.0, 101635.0, 101635.0, 101657.0, 101692.0, 101667.0,
        101622.0, 101540.0, 101430.0, 101307.0, 101255.0, 101287.0, 101565.0,
        101747.0, 101802.0, 101767.0, 101580.0, 101545.0, 101502.0, 101535.0,
        101597.0, 101580.0, 101537.0, 101452.0, 101400.0, 101477.0, 101625.0,
        101597.0, 101537.0, 101740.0, 101930.0, 101887.0, 101687.0, 101630.0,
        101645.0, 101630.0, 101777.0, 101905.0, 101837.0, 101722.0, 101772.0,
        101810.0, 101782.0, 101790.0, 101720.0, 101597.0, 101542.0, 101492.0,
        101487.0, 101475.0, 101407.0, 101397.0, 101465.0, 101482.0, 101455.0,
        101382.0, 101247.0, 101102.0, 100985.0, 100905.0, 100885.0, 100882.0,
        100885.0, 100915.0, 100965.0, 101010.0, 101020.0, 101005.0, 100965.0,
        100932.0, 100965.0, 101027.0, 101120.0, 101262.0, 101362.0, 101402.0,
        101422.0, 101442.0, 101457.0, 101487.0, 101580.0, 101782.0, 102025.0,
        102220.0, 102350.0, 102435.0, 102495.0, 102500.0, 102450.0, 102370.0,
        102285.0, 102205.0, 102122.0, 102022.0, 101892.0, 101737.0, 101582.0,
        101457.0, 101555.0, 101650.0, 101520.0, 101630.0, 101757.0, 101870.0,
        101950.0, 101990.0, 102042.0, 102082.0, 102115.0, 102130.0, 102107.0,
        102100.0, 102102.0, 102075.0, 102050.0, 102047.0, 102062.0, 102072.0,
        102090.0, 102122.0, 102130.0, 102092.0, 102060.0, 102055.0, 102047.0,
        102022.0, 102027.0, 102042.0, 102002.0, 101955.0, 101937.0, 101897.0,
        101832.0, 101790.0, 101762.0, 101757.0, 101795.0, 101812.0, 101780.0,
        101702.0, 101417.0, 101407.0, 101380.0, 101387.0, 101412.0, 101392.0,
        101392.0, 101460.0, 101487.0, 101485.0, 101547.0, 101457.0, 101290.0,
        101167.0, 101115.0, 101210.0, 101305.0, 101580.0, 101695.0, 101715.0,
        101647.0, 101527.0, 101485.0, 101450.0, 101435.0, 101460.0, 101470.0,
        101402.0, 101215.0, 101145.0, 101392.0, 101655.0, 101657.0, 101537.0,
        101417.0, 101377.0, 101427.0, 101387.0, 101407.0, 101447.0, 101552.0,
        101610.0, 101592.0, 101630.0, 101682.0, 101665.0, 101672.0, 101640.0,
        101517.0, 101450.0, 101392.0, 101345.0, 101342.0, 101290.0, 101217.0,
        101207.0, 101257.0, 101302.0, 101320.0, 101292.0, 101210.0, 101142.0,
        101067.0, 101000.0, 100975.0, 100950.0, 100947.0, 100957.0, 100965.0,
        100992.0, 100990.0, 100947.0, 100920.0, 100947.0, 101005.0, 101052.0,
        101155.0, 101287.0, 101352.0, 101400.0, 101452.0, 101470.0, 101457.0,
        101485.0, 101607.0, 101775.0, 101937.0, 102065.0, 102170.0, 102260.0,
        102315.0, 102302.0, 102232.0, 102192.0, 102172.0, 102122.0, 102017.0,
        101885.0, 101770.0, 101662.0, 101540.0, 101462.0, 101477.0, 101775.0,
        101702.0, 101647.0, 101755.0, 101785.0, 101865.0, 101895.0, 101910.0,
        101932.0, 101912.0, 101880.0, 101867.0, 101870.0, 101877.0, 101895.0,
        101920.0, 101925.0, 101920.0, 101930.0, 101930.0, 101930.0, 101940.0,
        101942.0, 101905.0, 101855.0, 101850.0, 101842.0, 101797.0, 101770.0,
        101747.0, 101697.0, 101660.0, 101645.0, 101562.0, 101440.0, 101390.0,
        101460.0, 101517.0, 101552.0, 101562.0, 101485.0, 101217.0, 101270.0,
        101282.0, 101292.0, 101310.0, 101235.0, 101185.0, 101277.0, 101337.0,
        101332.0, 101352.0, 101252.0, 101095.0, 101035.0, 101085.0, 101162.0,
        101232.0, 101427.0, 101622.0, 101620.0, 101642.0, 101567.0, 101482.0,
        101482.0, 101467.0, 101355.0, 101272.0, 101295.0, 101327.0, 101245.0,
        101290.0, 101397.0, 101462.0, 101547.0, 101610.0, 101587.0, 101502.0,
        101350.0, 101235.0, 101200.0, 101282.0, 101455.0, 101562.0, 101607.0,
        101592.0, 101570.0, 101540.0, 101432.0, 101370.0, 101362.0, 101272.0,
        101265.0, 101250.0, 101180.0, 101167.0, 101160.0, 101187.0, 101225.0,
        101215.0, 101202.0, 101185.0, 101142.0, 101065.0, 101010.0, 101005.0,
        100985.0, 100962.0, 100945.0, 100942.0, 100950.0, 100937.0, 100925.0,
        100940.0, 100990.0, 101052.0, 101125.0, 101237.0, 101330.0, 101367.0,
        101382.0, 101397.0, 101435.0, 101472.0, 101530.0, 101602.0, 101692.0,
        101817.0, 101940.0, 102025.0, 102085.0, 102102.0, 102102.0, 102082.0,
        102047.0, 101985.0, 101900.0, 101842.0, 101782.0, 101697.0, 101607.0,
        101485.0, 101405.0, 101415.0, 101590.0, 101832.0, 101770.0, 101672.0,
        101717.0, 101775.0, 101777.0, 101735.0, 101712.0, 101670.0, 101647.0,
        101647.0, 101667.0, 101710.0, 101742.0, 101750.0, 101735.0, 101735.0,
        101740.0, 101740.0, 101737.0, 101720.0, 101725.0, 101755.0, 101732.0,
        101670.0, 101655.0, 101642.0, 101562.0, 101525.0, 101530.0, 101495.0,
        101440.0, 101360.0, 101225.0, 101125.0, 101197.0, 101297.0, 101325.0,
        101325.0, 101257.0, 101020.0, 101110.0, 101155.0, 101205.0, 101217.0,
        101140.0, 101070.0, 101042.0, 101087.0, 101207.0, 101252.0, 101160.0,
        101015.0, 100897.0, 100952.0, 101092.0, 101220.0, 101277.0, 101627.0,
        101575.0, 101570.0, 101515.0, 101415.0, 101387.0, 101392.0, 101382.0,
        101312.0, 101185.0, 101127.0, 101162.0, 101315.0, 101402.0, 101332.0,
        101325.0, 101415.0, 101402.0, 101277.0, 101152.0, 101042.0, 101040.0,
        101150.0, 101267.0, 101380.0, 101455.0, 101457.0, 101395.0, 101310.0,
        101230.0, 101227.0, 101222.0, 101205.0, 101227.0, 101177.0, 101137.0,
        101155.0, 101142.0, 101162.0, 101150.0, 101110.0, 101105.0, 101085.0,
        101065.0, 101052.0, 101007.0, 100942.0, 100902.0, 100907.0, 100925.0,
        100932.0, 100937.0, 100960.0, 100987.0, 101002.0, 101030.0, 101077.0,
        101145.0, 101207.0, 101260.0, 101322.0, 101365.0, 101387.0, 101422.0,
        101447.0, 101487.0, 101560.0, 101650.0, 101740.0, 101787.0, 101822.0,
        101892.0, 101945.0, 101930.0, 101880.0, 101835.0, 101810.0, 101777.0,
        101727.0, 101655.0, 101545.0, 101495.0, 101477.0, 101457.0, 101495.0,
        101472.0, 101560.0, 101757.0, 101625.0, 101627.0, 101697.0, 101675.0,
        101635.0, 101560.0, 101510.0, 101510.0, 101495.0, 101492.0, 101545.0,
        101572.0, 101565.0, 101547.0, 101532.0, 101507.0, 101495.0, 101530.0,
        101565.0, 101542.0, 101532.0, 101567.0, 101547.0, 101487.0, 101472.0,
        101452.0, 101415.0, 101405.0, 101395.0, 101335.0, 101230.0, 101100.0,
        100975.0, 100975.0, 101070.0, 101097.0, 101060.0, 101005.0, 100870.0,
        100927.0, 100972.0, 101070.0, 101110.0, 101057.0, 101015.0, 100935.0,
        100937.0, 101147.0, 101210.0, 101102.0, 100982.0, 100720.0, 100685.0,
        101020.0, 101162.0, 101247.0, 101507.0, 101480.0, 101417.0, 101397.0,
        101422.0, 101360.0, 101260.0, 101182.0, 101202.0, 101202.0, 101105.0,
        101050.0, 101090.0, 101305.0, 101390.0, 101355.0, 101287.0, 101212.0,
        101170.0, 101152.0, 101085.0, 101040.0, 101070.0, 101075.0, 101150.0,
        101312.0, 101292.0, 101202.0, 101137.0, 101130.0, 101110.0, 101137.0,
        101137.0, 101087.0, 101052.0, 101087.0, 101055.0, 101030.0, 101047.0,
        101037.0, 101040.0, 101032.0, 101000.0, 100985.0, 100955.0, 100890.0,
        100835.0, 100827.0, 100832.0, 100827.0, 100847.0, 100885.0, 100925.0,
        100950.0, 100975.0, 101030.0, 101075.0, 101122.0, 101177.0, 101215.0,
        101252.0, 101285.0, 101330.0, 101367.0, 101382.0, 101427.0, 101482.0,
        101530.0, 101567.0, 101620.0, 101682.0, 101712.0, 101722.0, 101720.0,
        101705.0, 101690.0, 101660.0, 101605.0, 101550.0, 101525.0, 101505.0,
        101457.0, 101440.0, 101417.0, 101397.0, 101452.0, 101425.0, 101427.0,
        101437.0, 101492.0, 101605.0, 101565.0, 101512.0, 101422.0, 101365.0,
        101345.0, 101360.0, 101367.0, 101392.0, 101402.0, 101390.0, 101372.0,
        101370.0, 101375.0, 101357.0, 101317.0, 101342.0, 101390.0, 101360.0,
        101315.0, 101320.0, 101317.0, 101305.0, 101327.0, 101325.0, 101292.0,
        101280.0, 101250.0, 101150.0, 101015.0, 100895.0, 100840.0, 100855.0,
        100870.0, 100847.0, 100830.0, 100765.0, 100800.0, 100847.0, 100965.0,
        101012.0, 100950.0, 100910.0, 100862.0, 100847.0, 100987.0, 101040.0,
        100962.0, 100860.0, 100655.0, 100630.0, 101125.0, 101282.0, 101245.0,
        101297.0, 101365.0, 101387.0, 101345.0, 101315.0, 101265.0, 101247.0,
        101147.0, 101070.0, 101080.0, 101092.0, 101117.0, 101072.0, 101197.0,
        101152.0, 101132.0, 101097.0, 101065.0, 101010.0, 101000.0, 101025.0,
        100990.0, 100965.0, 100972.0, 101005.0, 101112.0, 101092.0, 101042.0,
        100995.0, 100980.0, 100972.0, 101007.0, 101007.0, 100962.0, 101000.0,
        101020.0, 100967.0, 100967.0, 100960.0, 100962.0, 100977.0, 100920.0,
        100905.0, 100905.0, 100852.0, 100812.0, 100790.0, 100787.0, 100790.0,
        100792.0, 100815.0, 100845.0, 100880.0, 100895.0, 100927.0, 100962.0,
        101002.0, 101062.0, 101122.0, 101157.0, 101172.0, 101200.0, 101245.0,
        101272.0, 101310.0, 101347.0, 101367.0, 101400.0, 101440.0, 101480.0,
        101502.0, 101507.0, 101540.0, 101582.0, 101592.0, 101572.0, 101517.0,
        101485.0, 101472.0, 101455.0, 101460.0, 101422.0, 101397.0, 101407.0,
        101382.0, 101385.0, 101390.0, 101397.0, 101392.0, 101350.0, 101340.0,
        101300.0, 101330.0, 101295.0, 101220.0, 101142.0, 101152.0, 101197.0,
        101255.0, 101282.0, 101267.0, 101220.0, 101192.0, 101190.0, 101207.0,
        101202.0, 101170.0, 101187.0, 101207.0, 101157.0, 101122.0, 101162.0,
        101177.0, 101180.0, 101192.0, 101195.0, 101152.0, 101090.0, 101042.0,
        100955.0, 100847.0, 100790.0, 100760.0, 100750.0, 100750.0, 100740.0,
        100772.0, 100757.0, 100785.0, 100857.0, 100922.0, 100895.0, 100837.0,
        100775.0, 100755.0, 100832.0, 100882.0, 100825.0, 100692.0, 100657.0,
        100782.0, 101247.0, 101350.0, 101222.0, 101207.0, 101252.0, 101290.0,
        101287.0, 101260.0, 101140.0, 101082.0, 101067.0, 101060.0, 101040.0,
        100987.0, 100987.0, 101037.0, 101125.0, 101145.0, 101060.0, 100970.0,
        100952.0, 100945.0, 100952.0, 100982.0, 100965.0, 100945.0, 100940.0,
        100920.0, 100920.0, 100930.0, 100910.0, 100880.0, 100870.0, 100870.0,
        100865.0, 100907.0, 100922.0, 100945.0, 100902.0, 100905.0, 100907.0,
        100865.0, 100887.0, 100890.0, 100845.0, 100830.0, 100810.0, 100802.0,
        100795.0, 100752.0, 100740.0, 100740.0, 100742.0, 100747.0, 100767.0,
        100815.0, 100855.0, 100887.0, 100912.0, 100962.0, 101025.0, 101057.0,
        101077.0, 101092.0, 101130.0, 101167.0, 101180.0, 101190.0, 101185.0,
        101225.0, 101292.0, 101330.0, 101340.0, 101345.0, 101365.0, 101410.0,
        101427.0, 101412.0, 101402.0, 101402.0, 101422.0, 101427.0, 101385.0,
        101375.0, 101372.0, 101342.0, 101342.0, 101350.0, 101350.0, 101337.0,
        101340.0, 101317.0, 101302.0, 101277.0, 101190.0, 101190.0, 101175.0,
        101075.0, 101007.0, 100955.0, 101090.0, 101115.0, 101122.0, 101145.0,
        101127.0, 101130.0, 101100.0, 101052.0, 101087.0, 101107.0, 101060.0,
        101037.0, 101050.0, 101017.0, 101010.0, 101030.0, 101050.0, 101062.0,
        101070.0, 101042.0, 100980.0, 100952.0, 100912.0, 100820.0, 100800.0,
        100812.0, 100795.0, 100790.0, 100800.0, 100820.0, 100780.0, 100752.0,
        100760.0, 100812.0, 100852.0, 100787.0, 100687.0, 100692.0, 100757.0,
        100750.0, 100690.0, 100612.0, 100710.0, 100907.0, 101220.0, 101297.0,
        101130.0, 101070.0, 101120.0, 101127.0, 101127.0, 101155.0, 101142.0,
        101072.0, 100992.0, 100960.0, 101005.0, 101057.0, 101025.0, 100977.0,
        100982.0, 101002.0, 101002.0, 100962.0, 100905.0, 100877.0, 100872.0,
        100850.0, 100840.0, 100867.0, 100870.0, 100860.0, 100840.0, 100800.0,
        100792.0, 100815.0, 100835.0, 100820.0, 100787.0, 100857.0, 100860.0,
        100837.0, 100812.0, 100825.0, 100812.0, 100815.0, 100820.0, 100795.0,
        100785.0, 100770.0, 100767.0, 100792.0, 100762.0, 100740.0, 100742.0,
        100717.0, 100705.0, 100725.0, 100772.0, 100810.0, 100820.0, 100840.0,
        100875.0, 100915.0, 100957.0, 101000.0, 101020.0, 101010.0, 101015.0,
        101052.0, 101102.0, 101132.0, 101142.0, 101187.0, 101220.0, 101235.0,
        101267.0, 101287.0, 101290.0, 101302.0, 101347.0, 101385.0, 101377.0,
        101370.0, 101352.0, 101355.0, 101362.0, 101357.0, 101340.0, 101317.0,
        101312.0, 101325.0, 101332.0, 101350.0, 101357.0, 101325.0, 101297.0,
        101250.0, 101205.0, 101177.0, 101090.0, 101010.0, 100945.0, 101050.0,
        101145.0, 100982.0, 100962.0, 101052.0, 101075.0, 101060.0, 101057.0,
        101027.0, 100972.0, 100960.0, 100977.0, 100930.0, 100925.0, 100955.0,
        100960.0, 100962.0, 100975.0, 101005.0, 100985.0, 100975.0, 100960.0,
        100917.0, 100892.0, 100857.0, 100830.0, 100870.0, 100870.0, 100812.0,
        100817.0, 100847.0, 100832.0, 100787.0, 100782.0, 100875.0, 100932.0,
        100840.0, 100700.0, 100680.0, 100737.0, 100737.0, 100722.0, 100717.0,
        100770.0, 100875.0, 101005.0, 101010.0, 100902.0, 100902.0, 101010.0,
        101087.0, 101070.0, 101025.0, 101032.0, 101047.0, 101022.0, 100965.0,
        100910.0, 100940.0, 100985.0, 101005.0, 100982.0, 100910.0, 100862.0,
        100837.0, 100807.0, 100782.0, 100785.0, 100777.0, 100802.0, 100842.0,
        100867.0, 100827.0, 100755.0, 100727.0, 100765.0, 100847.0, 100857.0,
        100787.0, 100740.0, 100737.0, 100762.0, 100762.0, 100755.0, 100745.0,
        100750.0, 100785.0, 100765.0, 100750.0, 100750.0, 100715.0, 100742.0,
        100760.0, 100720.0, 100717.0, 100697.0, 100680.0, 100710.0, 100750.0,
        100777.0, 100795.0, 100815.0, 100832.0, 100862.0, 100895.0, 100917.0,
        100932.0, 100932.0, 100952.0, 100992.0, 101027.0, 101055.0, 101065.0,
        101090.0, 101130.0, 101172.0, 101207.0, 101205.0, 101200.0, 101232.0,
        101260.0, 101310.0, 101327.0, 101277.0, 101295.0, 101332.0, 101337.0,
        101322.0, 101285.0, 101302.0, 101335.0, 101367.0, 101365.0, 101335.0,
        101335.0, 101322.0, 101302.0, 101287.0, 101245.0, 101217.0, 101180.0,
        101110.0, 101092.0, 101012.0, 101245.0, 101107.0, 100917.0, 100907.0,
        101042.0, 101072.0, 101017.0, 100960.0, 100957.0, 100955.0, 100880.0,
        100845.0, 100842.0, 100837.0, 100860.0, 100890.0, 100912.0, 100900.0,
        100942.0, 100965.0, 100940.0, 100942.0, 100927.0, 100912.0, 100885.0,
        100872.0, 100880.0, 100885.0, 100850.0, 100825.0, 100832.0, 100820.0,
        100810.0, 100847.0, 100885.0, 100925.0, 100872.0, 100805.0, 100742.0,
        100737.0, 100755.0, 100802.0, 100867.0, 100857.0, 100925.0, 101007.0,
        100912.0, 100837.0, 100912.0, 100995.0, 101007.0, 101042.0, 101022.0,
        100980.0, 100937.0, 100947.0, 100990.0, 100997.0, 100965.0, 100925.0,
        100925.0, 100932.0, 100912.0, 100882.0, 100855.0, 100847.0, 100840.0,
        100840.0, 100830.0, 100845.0, 100847.0, 100810.0, 100775.0, 100737.0,
        100752.0, 100785.0, 100920.0, 100837.0, 100790.0, 100730.0, 100700.0,
        100717.0, 100735.0, 100710.0, 100705.0, 100715.0, 100697.0, 100700.0,
        100747.0, 100755.0, 100735.0, 100745.0, 100720.0, 100722.0, 100732.0,
        100707.0, 100715.0, 100717.0, 100740.0, 100770.0, 100775.0, 100795.0,
        100805.0, 100840.0, 100895.0, 100927.0, 100942.0, 100947.0, 100977.0,
        100997.0, 101007.0, 101020.0, 101040.0, 101072.0, 101087.0, 101112.0,
        101127.0, 101132.0, 101172.0, 101217.0, 101232.0, 101260.0, 101272.0,
        101275.0, 101287.0, 101297.0, 101295.0, 101277.0, 101295.0, 101332.0,
        101320.0, 101300.0, 101290.0, 101302.0, 101322.0, 101317.0, 101307.0,
        101285.0, 101260.0, 101225.0, 101182.0, 101177.0, 101102.0, 101137.0,
        101072.0, 100942.0, 100920.0, 100910.0, 100930.0, 100930.0, 100955.0,
        100910.0, 100897.0, 100890.0, 100857.0, 100797.0, 100780.0, 100797.0,
        100807.0, 100812.0, 100880.0, 100905.0, 100907.0, 100940.0, 100937.0,
        100955.0, 100965.0, 100947.0, 100922.0, 100910.0, 100897.0, 100885.0,
        100880.0, 100852.0, 100857.0, 100870.0, 100850.0, 100842.0, 100825.0,
        100885.0, 100855.0, 100817.0, 100787.0, 100795.0, 100817.0, 100892.0,
        100987.0, 100947.0, 101082.0, 101125.0, 100895.0, 100862.0, 100947.0,
        101012.0, 100977.0, 100945.0, 100937.0, 100967.0, 100972.0, 100950.0,
        100907.0, 100907.0, 100947.0, 100950.0, 100927.0, 100875.0, 100835.0,
        100820.0, 100817.0, 100810.0, 100780.0, 100770.0, 100775.0, 100810.0,
        100842.0, 100815.0, 100785.0, 100780.0, 100762.0, 100780.0, 100800.0,
        100750.0, 100775.0, 100730.0, 100672.0, 100687.0, 100707.0, 100712.0,
        100690.0, 100685.0, 100705.0, 100737.0, 100730.0, 100727.0, 100755.0,
        100752.0, 100727.0, 100730.0, 100727.0, 100737.0, 100737.0, 100697.0,
        100732.0, 100785.0, 100777.0, 100777.0, 100790.0, 100830.0, 100867.0,
        100892.0, 100920.0, 100955.0, 100990.0, 100990.0, 100982.0, 100980.0,
        101002.0, 101045.0, 101052.0, 101060.0, 101072.0, 101120.0, 101167.0,
        101167.0, 101185.0, 101212.0, 101237.0, 101260.0, 101260.0, 101285.0,
        101292.0, 101282.0, 101312.0, 101327.0, 101310.0, 101307.0, 101302.0,
        101320.0, 101320.0, 101302.0, 101312.0, 101297.0, 101277.0, 101227.0,
        101205.0, 101237.0, 101237.0, 101217.0, 100897.0, 100862.0, 100855.0,
        100862.0, 100885.0, 100840.0, 100845.0, 100877.0, 100880.0, 100852.0,
        100825.0, 100812.0, 100780.0, 100750.0, 100792.0, 100820.0, 100862.0,
        100907.0, 100897.0, 100902.0, 100917.0, 100952.0, 100957.0, 100945.0,
        100927.0, 100917.0, 100920.0, 100897.0, 100872.0, 100852.0, 100870.0,
        100882.0, 100872.0, 100847.0, 100827.0, 100877.0, 100860.0, 100782.0,
        100770.0, 100812.0, 100870.0, 100992.0, 101122.0, 101012.0, 101090.0,
        101085.0, 100935.0, 100930.0, 100950.0, 100975.0, 101002.0, 101010.0,
        100960.0, 100922.0, 100902.0, 100937.0, 100937.0, 100900.0, 100872.0,
        100862.0, 100897.0, 100892.0, 100870.0, 100842.0, 100842.0, 100872.0,
        100860.0, 100835.0, 100822.0, 100827.0, 100817.0, 100817.0, 100767.0,
        100747.0, 100717.0, 100690.0, 100690.0, 100692.0, 100767.0, 100687.0,
        100637.0, 100665.0, 100682.0, 100690.0, 100702.0, 100735.0, 100770.0,
        100730.0, 100722.0, 100765.0, 100765.0, 100740.0, 100750.0, 100740.0,
        100735.0, 100750.0, 100732.0, 100720.0, 100727.0, 100722.0, 100737.0,
        100762.0, 100777.0, 100810.0, 100850.0, 100887.0, 100912.0, 100932.0,
        100985.0, 101002.0, 100990.0, 100967.0, 100975.0, 101012.0, 101017.0,
        101035.0, 101057.0, 101105.0, 101147.0, 101180.0, 101230.0, 101235.0,
        101230.0, 101235.0, 101262.0, 101312.0, 101307.0, 101295.0, 101317.0,
        101335.0, 101337.0, 101317.0, 101300.0, 101312.0, 101305.0, 101305.0,
        101327.0, 101315.0, 101302.0, 101262.0, 101250.0, 101265.0, 101290.0,
        101082.0, 100835.0, 100795.0, 100777.0, 100770.0, 100800.0, 100862.0,
        100830.0, 100837.0, 100872.0, 100870.0, 100817.0, 100787.0, 100775.0,
        100712.0, 100740.0, 100827.0, 100860.0, 100882.0, 100887.0, 100902.0,
        100920.0, 100952.0, 100960.0, 100952.0, 100950.0, 100920.0, 100917.0,
        100917.0, 100890.0, 100872.0, 100900.0, 100895.0, 100885.0, 100867.0,
        100820.0, 100800.0, 100860.0, 100835.0, 100815.0, 100817.0, 100835.0,
        100905.0, 101047.0, 101072.0, 101075.0, 101000.0, 100920.0, 100905.0,
        100967.0, 100960.0, 100922.0, 100910.0, 100902.0, 100927.0, 100897.0,
        100867.0, 100847.0, 100852.0, 100865.0, 100840.0, 100812.0, 100782.0,
        100787.0, 100805.0, 100815.0, 100830.0, 100815.0, 100790.0, 100787.0,
        100790.0, 100770.0, 100772.0, 100767.0, 100740.0, 100705.0, 100670.0,
        100630.0, 100612.0, 100612.0, 100565.0, 100590.0, 100647.0, 100682.0,
        100682.0, 100697.0, 100782.0, 100842.0, 100850.0, 100832.0, 100755.0,
        100742.0, 100735.0, 100742.0, 100730.0, 100747.0, 100755.0, 100745.0,
        100770.0, 100752.0, 100760.0, 100797.0, 100790.0, 100777.0, 100782.0,
        100815.0, 100857.0, 100887.0, 100920.0, 100965.0, 100977.0, 100977.0,
        100997.0, 101032.0, 101065.0, 101047.0, 101042.0, 101060.0, 101105.0,
        101157.0, 101205.0, 101222.0, 101232.0, 101290.0, 101305.0, 101310.0,
        101305.0, 101287.0, 101335.0, 101370.0, 101397.0, 101395.0, 101390.0,
        101417.0, 101422.0, 101410.0, 101400.0, 101405.0, 101400.0, 101387.0,
        101350.0, 101312.0, 101292.0, 101315.0, 101112.0, 100842.0, 100782.0,
        100777.0, 100835.0, 100737.0, 100752.0, 100840.0, 100862.0, 100815.0,
        100827.0, 100822.0, 100800.0, 100797.0, 100772.0, 100760.0, 100820.0,
        100892.0, 100887.0, 100880.0, 100912.0, 100935.0, 100975.0, 100985.0,
        100965.0, 100967.0, 100957.0, 100942.0, 100930.0, 100920.0, 100907.0,
        100965.0, 100952.0, 100910.0, 100887.0, 100845.0, 100827.0, 100910.0,
        100920.0, 100887.0, 100870.0, 100850.0, 100872.0, 100957.0, 101042.0,
        101002.0, 100910.0, 100892.0, 100880.0, 100925.0, 100935.0, 100905.0,
        100855.0, 100815.0, 100840.0, 100875.0, 100857.0, 100775.0, 100717.0,
        100707.0, 100735.0, 100762.0, 100767.0, 100792.0, 100835.0, 100862.0,
        100855.0, 100827.0, 100795.0, 100790.0, 100797.0, 100777.0, 100747.0,
        100710.0, 100687.0, 100667.0, 100630.0, 100585.0, 100575.0, 100577.0,
        100562.0, 100595.0, 100637.0, 100667.0, 100677.0, 100677.0, 100680.0,
        100685.0, 100717.0, 100837.0, 100790.0, 100717.0, 100715.0, 100715.0,
        100715.0, 100715.0, 100695.0, 100715.0, 100732.0, 100730.0, 100785.0,
        100795.0, 100785.0, 100805.0, 100807.0, 100842.0, 100872.0, 100902.0,
        100937.0, 100965.0, 101000.0, 101027.0, 101055.0, 101067.0, 101070.0,
        101090.0, 101100.0, 101117.0, 101145.0, 101170.0, 101205.0, 101227.0,
        101270.0, 101315.0, 101307.0, 101335.0, 101345.0, 101360.0, 101382.0,
        101372.0, 101412.0, 101440.0, 101505.0, 101542.0, 101505.0, 101487.0,
        101462.0, 101452.0, 101455.0, 101432.0, 101395.0, 101345.0, 101352.0,
        101312.0, 101350.0, 100772.0, 100730.0, 100707.0, 100742.0, 100822.0,
        100787.0, 100772.0, 100830.0, 100835.0, 100800.0, 100797.0, 100820.0,
        100820.0, 100825.0, 100852.0, 100910.0, 100925.0, 100910.0, 100912.0,
        100950.0, 100982.0, 101035.0, 101050.0, 101037.0, 101012.0, 101000.0,
        101012.0, 101015.0, 101015.0, 100980.0, 101040.0, 101017.0, 100970.0,
        100927.0, 100865.0, 100845.0, 100940.0, 101012.0, 100955.0, 100935.0,
        100915.0, 100955.0, 101000.0, 100985.0, 100897.0, 100810.0, 100845.0,
        100890.0, 100860.0, 100815.0, 100795.0, 100815.0, 100835.0, 100820.0,
        100807.0, 100820.0, 100805.0, 100747.0, 100670.0, 100615.0, 100602.0,
        100637.0, 100702.0, 100782.0, 100850.0, 100860.0, 100840.0, 100807.0,
        100792.0, 100787.0, 100762.0, 100715.0, 100657.0, 100625.0, 100617.0,
        100585.0, 100547.0, 100532.0, 100557.0, 100567.0, 100587.0, 100602.0,
        100622.0, 100622.0, 100625.0, 100645.0, 100667.0, 100692.0, 100685.0,
        100725.0, 100717.0, 100682.0, 100682.0, 100702.0, 100697.0, 100682.0,
        100690.0, 100682.0, 100705.0, 100762.0, 100780.0, 100807.0, 100812.0,
        100800.0, 100847.0, 100897.0, 100947.0, 100965.0, 100987.0, 101030.0,
        101055.0, 101100.0, 101142.0, 101160.0, 101172.0, 101177.0, 101170.0,
        101165.0, 101185.0, 101225.0, 101277.0, 101320.0, 101342.0, 101370.0,
        101410.0, 101405.0, 101412.0, 101420.0, 101437.0, 101497.0, 101515.0,
        101570.0, 101572.0, 101562.0, 101585.0, 101545.0, 101540.0, 101525.0,
        101492.0, 101470.0, 101385.0, 101392.0, 101295.0, 101447.0, 100970.0,
        100720.0, 100812.0, 100710.0, 100730.0, 100820.0, 100792.0, 100757.0,
        100785.0, 100742.0, 100740.0, 100827.0, 100867.0, 100897.0, 100940.0,
        100960.0, 100982.0, 101000.0, 101015.0, 101032.0, 101070.0, 101127.0,
        101132.0, 101140.0, 101125.0, 101092.0, 101107.0, 101097.0, 101092.0,
        101070.0, 101187.0, 101152.0, 101090.0, 101022.0, 100927.0, 100832.0,
        101015.0, 101097.0, 100982.0, 100927.0, 100920.0, 100965.0, 100917.0,
        100877.0, 100890.0, 100827.0, 100787.0, 100842.0, 100862.0, 100830.0,
        100792.0, 100775.0, 100830.0, 100880.0, 100890.0, 100855.0, 100787.0,
        100722.0, 100692.0, 100680.0, 100655.0, 100660.0, 100725.0, 100802.0,
        100867.0, 100872.0, 100845.0, 100847.0, 100865.0, 100862.0, 100835.0,
        100777.0, 100697.0, 100632.0, 100597.0, 100560.0, 100522.0, 100490.0,
        100452.0, 100430.0, 100480.0, 100565.0, 100595.0, 100592.0, 100605.0,
        100617.0, 100600.0, 100600.0, 100642.0, 100667.0, 100670.0, 100685.0,
        100705.0, 100675.0, 100650.0, 100662.0, 100640.0, 100625.0, 100650.0,
        100697.0, 100772.0, 100817.0, 100792.0, 100797.0, 100825.0, 100865.0,
        100947.0, 100987.0, 101037.0, 101090.0, 101107.0, 101145.0, 101180.0,
        101200.0, 101210.0, 101212.0, 101212.0, 101215.0, 101242.0, 101260.0,
        101285.0, 101320.0, 101367.0, 101415.0, 101430.0, 101445.0, 101475.0,
        101485.0, 101510.0, 101545.0, 101582.0, 101640.0, 101637.0, 101640.0,
        101630.0, 101592.0, 101617.0, 101577.0, 101567.0, 101567.0, 101482.0,
        101442.0, 101427.0, 101340.0, 101412.0, 100917.0, 100695.0, 100747.0,
        100660.0, 100697.0, 100747.0, 100700.0, 100677.0, 100677.0, 100715.0,
        100822.0, 100887.0, 100955.0, 100992.0, 101000.0, 101045.0, 101080.0,
        101102.0, 101122.0, 101162.0, 101230.0, 101240.0, 101240.0, 101237.0,
        101232.0, 101240.0, 101207.0, 101192.0, 101207.0, 101312.0, 101277.0,
        101217.0, 101120.0, 101005.0, 100887.0, 100932.0, 100895.0, 100837.0,
        100815.0, 100820.0, 100840.0, 100762.0, 100730.0, 100765.0, 100790.0,
        100832.0, 100837.0, 100800.0, 100887.0, 100972.0, 100957.0, 100932.0,
        100917.0, 100927.0, 100950.0, 100940.0, 100880.0, 100807.0, 100780.0,
        100780.0, 100787.0, 100820.0, 100857.0, 100897.0, 100927.0, 100940.0,
        100962.0, 100987.0, 100962.0, 100907.0, 100845.0, 100767.0, 100690.0,
        100600.0, 100527.0, 100497.0, 100447.0, 100362.0, 100335.0, 100477.0,
        100620.0, 100645.0, 100637.0, 100625.0, 100622.0, 100597.0, 100567.0,
        100612.0, 100635.0, 100667.0, 100710.0, 100740.0, 100710.0, 100692.0,
        100700.0, 100680.0, 100662.0, 100657.0, 100690.0, 100772.0, 100802.0,
        100795.0, 100812.0, 100822.0, 100880.0, 100947.0, 100972.0, 101037.0,
        101102.0, 101157.0, 101195.0, 101207.0, 101240.0, 101255.0, 101267.0,
        101282.0, 101295.0, 101310.0, 101320.0, 101365.0, 101405.0, 101430.0,
        101450.0, 101480.0, 101542.0, 101557.0, 101567.0, 101597.0, 101650.0,
        101707.0, 101697.0, 101665.0, 101680.0, 101702.0, 101732.0, 101745.0,
        101697.0, 101685.0, 101652.0, 101605.0, 101545.0, 101472.0, 101422.0,
        101312.0, 101625.0, 101422.0, 100690.0, 100760.0, 100690.0, 100622.0,
        100592.0, 100560.0, 100600.0, 100672.0, 100757.0, 100827.0, 100932.0,
        101017.0, 101062.0, 101105.0, 101170.0, 101197.0, 101247.0, 101290.0,
        101340.0, 101400.0, 101402.0, 101407.0, 101397.0, 101385.0, 101367.0,
        101327.0, 101322.0, 101475.0, 101420.0, 101390.0, 101280.0, 101120.0,
        100970.0, 100792.0, 100702.0, 100715.0, 100690.0, 100710.0, 100800.0,
        100827.0, 100797.0, 100697.0, 100682.0, 100767.0, 100875.0, 100887.0,
        101085.0, 101057.0, 101045.0, 101052.0, 101070.0, 101045.0, 101022.0,
        101005.0, 100987.0, 100962.0, 100925.0, 100915.0, 100915.0, 100917.0,
        100932.0, 100955.0, 100985.0, 101007.0, 101037.0, 101077.0, 101052.0,
        100977.0, 100897.0, 100845.0, 100787.0, 100675.0, 100570.0, 100510.0,
        100447.0, 100385.0, 100380.0, 100545.0, 100715.0, 100717.0, 100687.0,
        100682.0, 100665.0, 100620.0, 100585.0, 100625.0, 100607.0, 100660.0,
        100707.0, 100755.0, 100795.0, 100802.0, 100805.0, 100795.0, 100750.0,
        100715.0, 100737.0, 100795.0, 100832.0, 100860.0, 100860.0, 100865.0,
        100902.0, 100910.0, 100930.0, 101015.0, 101077.0, 101145.0, 101195.0,
        101245.0, 101300.0, 101297.0, 101300.0, 101315.0, 101340.0, 101370.0,
        101377.0, 101402.0, 101425.0, 101467.0, 101522.0, 101557.0, 101577.0,
        101580.0, 101652.0, 101735.0, 101795.0, 101817.0, 101765.0, 101767.0,
        101797.0, 101817.0, 101840.0, 101787.0, 101777.0, 101782.0, 101712.0,
        101722.0, 101652.0, 101545.0, 101557.0, 101452.0, 101257.0, 101460.0,
        101220.0, 100775.0, 100827.0, 100572.0, 100490.0, 100470.0, 100477.0,
        100532.0, 100620.0, 100765.0, 100882.0, 100975.0, 101102.0, 101177.0,
        101272.0, 101290.0, 101337.0, 101417.0, 101465.0, 101530.0, 101545.0,
        101580.0, 101590.0, 101560.0, 101540.0, 101497.0, 101497.0, 101625.0,
        101540.0, 101505.0, 101440.0, 101320.0, 101150.0, 100882.0, 100677.0,
        100625.0, 100607.0, 100637.0, 100745.0, 100837.0, 100780.0, 100737.0,
        100785.0, 100822.0, 100870.0, 100995.0, 101237.0, 101165.0, 101130.0,
        101120.0, 101162.0, 101170.0, 101177.0, 101147.0, 101100.0, 101090.0,
        101075.0, 101067.0, 101057.0, 101042.0, 101045.0, 101070.0, 101120.0,
        101177.0, 101212.0, 101220.0, 101145.0, 101020.0, 100910.0, 100857.0,
        100835.0, 100790.0, 100685.0, 100530.0, 100450.0, 100492.0, 100510.0,
        100597.0, 100722.0, 100777.0, 100795.0, 100807.0, 100795.0, 100732.0,
        100707.0, 100692.0, 100582.0, 100617.0, 100747.0, 100840.0, 100897.0,
        100930.0, 100957.0, 100955.0, 100892.0, 100817.0, 100787.0, 100805.0,
        100875.0, 100947.0, 100982.0, 101000.0, 100975.0, 100932.0, 100952.0,
        101012.0, 101087.0, 101160.0, 101187.0, 101245.0, 101302.0, 101325.0,
        101345.0, 101337.0, 101335.0, 101370.0, 101395.0, 101425.0, 101445.0,
        101505.0, 101560.0, 101567.0, 101580.0, 101615.0, 101687.0, 101745.0,
        101812.0, 101867.0, 101845.0, 101867.0, 101855.0, 101852.0, 101887.0,
        101840.0, 101865.0, 101860.0, 101800.0, 101810.0, 101722.0, 101682.0,
        101575.0, 101445.0, 101580.0, 101222.0, 101490.0, 101085.0, 100940.0,
        100600.0, 100432.0, 100365.0, 100310.0, 100377.0, 100500.0, 100687.0,
        100765.0, 100877.0, 101117.0, 101250.0, 101377.0, 101405.0, 101445.0,
        101545.0, 101607.0, 101677.0, 101705.0, 101747.0, 101782.0, 101762.0,
        101740.0, 101682.0, 101665.0, 101842.0, 101770.0, 101680.0, 101580.0,
        101462.0, 101255.0, 100982.0, 100725.0, 100567.0, 100635.0, 100697.0,
        100742.0, 100767.0, 100677.0, 100737.0, 100857.0, 100917.0, 100860.0,
        100940.0, 101147.0, 101242.0, 101260.0, 101250.0, 101245.0, 101225.0,
        101277.0, 101307.0, 101285.0, 101260.0, 101222.0, 101187.0, 101160.0,
        101115.0, 101110.0, 101162.0, 101260.0, 101332.0, 101347.0, 101315.0,
        101210.0, 101062.0, 100942.0, 100895.0, 100905.0, 100905.0, 100745.0,
        100485.0, 100482.0, 100662.0, 100715.0, 100715.0, 100760.0, 100857.0,
        100972.0, 100970.0, 100907.0, 100840.0, 100820.0, 100782.0, 100632.0,
        100590.0, 100742.0, 100877.0, 100965.0, 101035.0, 101067.0, 101085.0,
        101065.0, 100990.0, 100922.0, 100957.0, 101050.0, 101095.0, 101110.0,
        101105.0, 101070.0, 101042.0, 101015.0, 100990.0, 101035.0, 101100.0,
        101135.0, 101217.0, 101295.0, 101347.0, 101372.0, 101355.0, 101357.0,
        101360.0, 101362.0, 101385.0, 101407.0, 101472.0, 101525.0, 101540.0,
        101552.0, 101545.0, 101577.0, 101660.0, 101785.0, 101887.0, 101895.0,
        101917.0, 101940.0, 101975.0, 102002.0, 101977.0, 101995.0, 101965.0,
        101952.0, 101905.0, 101762.0, 101785.0, 101655.0, 101445.0, 101530.0,
        101210.0, 101575.0, 101135.0, 101015.0, 100645.0, 100505.0, 100382.0,
        100300.0, 100432.0, 100492.0, 100522.0, 100562.0, 100792.0, 101122.0,
        101307.0, 101457.0, 101535.0, 101597.0, 101690.0, 101742.0, 101822.0,
        101880.0, 101935.0, 101980.0, 101972.0, 101960.0, 101915.0, 101872.0,
        102127.0, 102065.0, 101945.0, 101815.0, 101660.0, 101420.0, 101167.0,
        100930.0, 100647.0, 100710.0, 100865.0, 100932.0, 100865.0, 100695.0,
        100737.0, 100850.0, 100897.0, 100865.0, 100947.0, 101175.0, 101342.0,
        101377.0, 101417.0, 101465.0, 101460.0, 101440.0, 101410.0, 101392.0,
        101407.0, 101415.0, 101392.0, 101332.0, 101265.0, 101272.0, 101362.0,
        101477.0, 101542.0, 101545.0, 101492.0, 101377.0, 101207.0, 101052.0,
        100957.0, 100927.0, 100870.0, 100672.0, 100460.0, 100567.0, 100802.0,
        100875.0, 100905.0, 100962.0, 101062.0, 101127.0, 101077.0, 101027.0,
        100980.0, 100937.0, 100890.0, 100777.0, 100747.0, 100832.0, 100917.0,
        100957.0, 101022.0, 101077.0, 101125.0, 101147.0, 101102.0, 101057.0,
        101107.0, 101207.0, 101275.0, 101302.0, 101305.0, 101282.0, 101237.0,
        101160.0, 101095.0, 101060.0, 101027.0, 101040.0, 101117.0, 101190.0,
        101260.0, 101317.0, 101380.0, 101447.0, 101452.0, 101437.0, 101437.0,
        101440.0, 101492.0, 101522.0, 101522.0, 101515.0, 101485.0, 101500.0,
        101552.0, 101630.0, 101762.0, 101872.0, 101950.0, 101992.0, 102025.0,
        102040.0, 102067.0, 102127.0, 102105.0, 102077.0, 102005.0, 101842.0,
        101800.0, 101710.0, 101560.0, 101495.0, 101297.0, 101892.0, 101102.0,
        101080.0, 100767.0, 100730.0, 100560.0, 100495.0, 100640.0, 100540.0,
        100432.0, 100510.0, 100757.0, 101112.0, 101335.0, 101510.0, 101635.0,
        101742.0, 101872.0, 101942.0, 102010.0, 102077.0, 102140.0, 102200.0,
        102202.0, 102195.0, 102200.0, 102167.0, 102427.0, 102342.0, 102200.0,
        102052.0, 101882.0, 101672.0, 101485.0, 101252.0, 100862.0, 100715.0,
        100860.0, 101060.0, 100925.0, 100690.0, 100797.0, 100947.0, 101027.0,
        101002.0, 101087.0, 101292.0, 101485.0, 101592.0, 101620.0, 101635.0,
        101675.0, 101710.0, 101707.0, 101660.0, 101605.0, 101565.0, 101522.0,
        101455.0, 101385.0, 101400.0, 101512.0, 101647.0, 101727.0, 101725.0,
        101655.0, 101530.0, 101367.0, 101200.0, 101047.0, 100922.0, 100805.0,
        100655.0, 100575.0, 100730.0, 100932.0, 101057.0, 101192.0, 101292.0,
        101335.0, 101302.0, 101212.0, 101195.0, 101177.0, 101092.0, 100982.0,
        100877.0, 100945.0, 101080.0, 101077.0, 101025.0, 101030.0, 101090.0,
        101145.0, 101167.0, 101155.0, 101142.0, 101175.0, 101275.0, 101397.0,
        101467.0, 101480.0, 101467.0, 101417.0, 101340.0, 101252.0, 101140.0,
        101047.0, 101040.0, 101077.0, 101120.0, 101162.0, 101222.0, 101350.0,
        101485.0, 101567.0, 101630.0, 101650.0, 101647.0, 101650.0, 101605.0,
        101557.0, 101522.0, 101470.0, 101437.0, 101422.0, 101472.0, 101620.0,
        101762.0, 101872.0, 101940.0, 102012.0, 102122.0, 102212.0, 102275.0,
        102252.0, 102150.0, 102067.0, 101972.0, 101820.0, 101685.0, 101595.0,
        101425.0, 101520.0, 101617.0, 101020.0, 101117.0, 100960.0, 100975.0,
        100765.0, 100780.0, 100895.0, 100735.0, 100637.0, 100695.0, 100920.0,
        101200.0, 101367.0, 101545.0, 101710.0, 101835.0, 101987.0, 102090.0,
        102195.0, 102295.0, 102355.0, 102430.0, 102460.0, 102455.0, 102480.0,
        102482.0, 102702.0, 102630.0, 102482.0, 102290.0, 102085.0, 101887.0,
        101702.0, 101432.0, 101057.0, 100785.0, 100782.0, 100870.0, 100757.0,
        100720.0, 100822.0, 100977.0, 101157.0, 101245.0, 101330.0, 101455.0,
        101610.0, 101780.0, 101877.0, 101920.0, 101940.0, 101937.0, 101920.0,
        101880.0, 101835.0, 101780.0, 101712.0, 101630.0, 101587.0, 101640.0,
        101757.0, 101870.0, 101912.0, 101895.0, 101842.0, 101752.0, 101602.0,
        101415.0, 101197.0, 101007.0, 100882.0, 100825.0, 100845.0, 101005.0,
        101195.0, 101345.0, 101482.0, 101545.0, 101547.0, 101482.0, 101375.0,
        101317.0, 101277.0, 101185.0, 101050.0, 100985.0, 101135.0, 101287.0,
        101202.0, 101087.0, 101025.0, 101010.0, 101030.0, 101077.0, 101112.0,
        101115.0, 101137.0, 101267.0, 101435.0, 101530.0, 101567.0, 101562.0,
        101515.0, 101460.0, 101380.0, 101272.0, 101185.0, 101122.0, 101072.0,
        101057.0, 101037.0, 101082.0, 101292.0, 101530.0, 101717.0, 101847.0,
        101875.0, 101860.0, 101832.0, 101770.0, 101692.0, 101560.0, 101387.0,
        101277.0, 101247.0, 101315.0, 101437.0, 101530.0, 101682.0, 101827.0,
        101915.0, 102040.0, 102162.0, 102285.0, 102350.0, 102250.0, 102140.0,
        102060.0, 101900.0, 101740.0, 101607.0, 101415.0, 101537.0, 101215.0,
        101085.0, 101137.0, 101167.0, 101210.0, 101112.0, 101167.0, 101210.0,
        101092.0, 101015.0, 101035.0, 101147.0, 101310.0, 101392.0, 101537.0,
        101725.0, 101895.0, 102070.0, 102187.0, 102302.0, 102437.0, 102512.0,
        102597.0, 102680.0, 102707.0, 102737.0, 102742.0, 102867.0, 102782.0,
        102670.0, 102512.0, 102312.0, 102080.0, 101825.0, 101525.0, 101252.0,
        101097.0, 100975.0, 100835.0, 100762.0, 100880.0, 101002.0, 101157.0,
        101262.0, 101335.0, 101432.0, 101560.0, 101697.0, 101862.0, 102015.0,
        102130.0, 102192.0, 102200.0, 102192.0, 102185.0, 102175.0, 102112.0,
        101992.0, 101865.0, 101807.0, 101857.0, 101960.0, 102047.0, 102085.0,
        102085.0, 102070.0, 102015.0, 101895.0, 101720.0, 101505.0, 101307.0,
        101175.0, 101107.0, 101137.0, 101307.0, 101495.0, 101627.0, 101772.0,
        101872.0, 101875.0, 101785.0, 101645.0, 101545.0, 101465.0, 101307.0,
        101160.0, 101190.0, 101372.0, 101332.0, 101110.0, 100932.0, 100827.0,
        100762.0, 100772.0, 100877.0, 100985.0, 101017.0, 101040.0, 101145.0,
        101310.0, 101467.0, 101577.0, 101567.0, 101475.0, 101400.0, 101332.0,
        101260.0, 101212.0, 101155.0, 101100.0, 101050.0, 100987.0, 101050.0,
        101297.0, 101577.0, 101825.0, 102000.0, 102060.0, 102055.0, 102012.0,
        101925.0, 101792.0, 101580.0, 101332.0, 101150.0, 101037.0, 101055.0,
        101190.0, 101327.0, 101505.0, 101685.0, 101777.0, 101910.0, 102120.0,
        102317.0, 102445.0, 102392.0, 102285.0, 102152.0, 101960.0, 101732.0,
        101517.0, 101332.0, 101447.0, 101215.0, 101127.0, 101192.0, 101295.0,
        101365.0, 101420.0, 101507.0, 101477.0, 101395.0, 101387.0, 101365.0,
        101397.0, 101467.0, 101495.0, 101582.0, 101750.0, 101922.0, 102110.0,
        102245.0, 102345.0, 102467.0, 102577.0, 102690.0, 102815.0, 102887.0,
        102927.0, 102927.0, 103052.0, 102960.0, 102842.0, 102702.0, 102507.0,
        102275.0, 102025.0, 101770.0, 101562.0, 101422.0, 101292.0, 101130.0,
        101022.0, 101070.0, 101225.0, 101390.0, 101467.0, 101480.0, 101477.0,
        101530.0, 101665.0, 101847.0, 102020.0, 102170.0, 102282.0, 102372.0,
        102437.0, 102462.0, 102457.0, 102430.0, 102375.0, 102292.0, 102237.0,
        102217.0, 102227.0, 102262.0, 102305.0, 102320.0, 102315.0, 102277.0,
        102207.0, 102100.0, 101957.0, 101807.0, 101680.0, 101580.0, 101582.0,
        101710.0, 101855.0, 101960.0, 102082.0, 102167.0, 102165.0, 102082.0,
        101952.0, 101830.0, 101697.0, 101487.0, 101317.0, 101397.0, 101520.0,
        101370.0, 101090.0, 100870.0, 100717.0, 100565.0, 100487.0, 100557.0,
        100737.0, 100897.0, 100977.0, 101052.0, 101192.0, 101372.0, 101507.0,
        101515.0, 101442.0, 101367.0, 101272.0, 101145.0, 101052.0, 101020.0,
        101025.0, 100995.0, 100947.0, 101042.0, 101300.0, 101605.0, 101892.0,
        102100.0, 102202.0, 102222.0, 102175.0, 102077.0, 101920.0, 101652.0,
        101307.0, 101012.0, 100802.0, 100782.0, 100957.0, 101145.0, 101320.0,
        101522.0, 101682.0, 101832.0, 102027.0, 102245.0, 102405.0, 102465.0,
        102417.0, 102267.0, 102075.0, 101775.0, 101440.0, 101210.0, 101267.0,
        101145.0, 101112.0, 101207.0, 101325.0, 101405.0, 101537.0, 101667.0,
        101647.0, 101627.0, 101652.0, 101627.0, 101635.0, 101645.0, 101610.0,
        101647.0, 101762.0, 101885.0, 102020.0, 102152.0, 102265.0, 102385.0,
        102507.0, 102647.0, 102800.0, 102942.0, 103042.0, 103080.0, 103095.0,
        103037.0, 102915.0, 102762.0, 102570.0, 102352.0, 102145.0, 101942.0,
        101762.0, 101602.0, 101455.0, 101357.0, 101370.0, 101452.0, 101517.0,
        101570.0, 101647.0, 101700.0, 101672.0, 101605.0, 101552.0, 101607.0,
        101797.0, 102055.0, 102277.0, 102442.0, 102565.0, 102647.0, 102707.0,
        102755.0, 102757.0, 102720.0, 102672.0, 102640.0, 102620.0, 102627.0,
        102647.0, 102662.0, 102665.0, 102622.0, 102530.0, 102410.0, 102275.0,
        102165.0, 102095.0, 102047.0, 102052.0, 102122.0, 102200.0, 102267.0,
        102342.0, 102377.0, 102367.0, 102325.0, 102220.0, 102092.0, 101972.0,
        101817.0, 101680.0, 101672.0, 101682.0, 101532.0, 101292.0, 101065.0,
        100810.0, 100517.0, 100270.0, 100230.0, 100445.0, 100702.0, 100825.0,
        100895.0, 101080.0, 101305.0, 101440.0, 101457.0, 101417.0, 101355.0,
        101250.0, 101080.0, 100912.0, 100825.0, 100847.0, 100877.0, 100900.0,
        101037.0, 101342.0, 101707.0, 102025.0, 102235.0, 102372.0, 102440.0,
        102407.0, 102315.0, 102160.0, 101885.0, 101507.0, 101115.0, 100802.0,
        100652.0, 100710.0, 100895.0, 101147.0, 101417.0, 101602.0, 101717.0,
        101877.0, 102107.0, 102320.0, 102435.0, 102402.0, 102272.0, 102127.0,
        101852.0, 101480.0, 101180.0, 101067.0, 100927.0, 100962.0, 101027.0,
        101177.0, 101325.0, 101465.0, 101602.0, 101650.0, 101682.0, 101705.0,
        101702.0, 101722.0, 101725.0, 101700.0, 101710.0, 101770.0, 101850.0,
        101937.0, 102025.0, 102117.0, 102225.0, 102330.0, 102457.0, 102632.0,
        102820.0, 102977.0, 103072.0, 102970.0, 102962.0, 102860.0, 102712.0,
        102545.0, 102367.0, 102197.0, 102042.0, 101922.0, 101837.0, 101752.0,
        101677.0, 101657.0, 101697.0, 101752.0, 101790.0, 101797.0, 101780.0,
        101775.0, 101742.0, 101640.0, 101532.0, 101555.0, 101737.0, 102012.0,
        102297.0, 102535.0, 102700.0, 102810.0, 102872.0, 102915.0, 102952.0,
        102982.0, 102992.0, 103002.0, 103002.0, 102985.0, 102952.0, 102907.0,
        102832.0, 102722.0, 102622.0, 102507.0, 102395.0, 102315.0, 102275.0,
        102262.0, 102280.0, 102292.0, 102305.0, 102350.0, 102397.0, 102407.0,
        102377.0, 102300.0, 102207.0, 102125.0, 102027.0, 101920.0, 101857.0,
        101812.0, 101670.0, 101425.0, 101157.0, 100850.0, 100447.0, 100047.0,
        99907.0, 100125.0, 100457.0, 100627.0, 100725.0, 100942.0, 101200.0,
        101340.0, 101365.0, 101322.0, 101232.0, 101090.0, 100900.0, 100695.0,
        100592.0, 100640.0, 100747.0, 100867.0, 101072.0, 101415.0, 101810.0,
        102137.0, 102367.0, 102550.0, 102635.0, 102602.0, 102495.0, 102335.0,
        102102.0, 101817.0, 101500.0, 101160.0, 100865.0, 100710.0, 100740.0,
        100947.0, 101210.0, 101432.0, 101615.0, 101797.0, 101970.0, 102110.0,
        102217.0, 102235.0, 102177.0, 102105.0, 101907.0, 101607.0, 101355.0,
        101140.0, 100867.0, 100805.0, 100877.0, 101017.0, 101145.0, 101247.0,
        101377.0, 101455.0, 101490.0, 101507.0, 101515.0, 101530.0, 101555.0,
        101577.0, 101602.0, 101635.0, 101672.0, 101715.0, 101757.0, 101820.0,
        101915.0, 102025.0, 102140.0, 102292.0, 102485.0, 102692.0, 102867.0,
        102637.0, 102712.0, 102680.0, 102562.0, 102410.0, 102265.0, 102152.0,
        102042.0, 101912.0, 101797.0, 101735.0, 101697.0, 101657.0, 101657.0,
        101720.0, 101792.0, 101812.0, 101795.0, 101785.0, 101757.0, 101672.0,
        101555.0, 101480.0, 101510.0, 101682.0, 101952.0, 102240.0, 102460.0,
        102617.0, 102732.0, 102837.0, 102937.0, 103012.0, 103047.0, 103077.0,
        103097.0, 103082.0, 103020.0, 102932.0, 102827.0, 102720.0, 102612.0,
        102482.0, 102345.0, 102235.0, 102162.0, 102125.0, 102122.0, 102122.0,
        102120.0, 102140.0, 102177.0, 102190.0, 102182.0, 102167.0, 102130.0,
        102067.0, 101987.0, 101920.0, 101882.0, 101832.0, 101682.0, 101455.0,
        101227.0, 100965.0, 100562.0, 100107.0, 99875.0, 100010.0, 100295.0,
        100502.0, 100685.0, 100940.0, 101190.0, 101302.0, 101320.0, 101295.0,
        101202.0, 101012.0, 100757.0, 100535.0, 100432.0, 100475.0, 100605.0,
        100797.0, 101097.0, 101510.0, 101925.0, 102260.0, 102512.0, 102690.0,
        102760.0, 102725.0, 102630.0, 102465.0, 102225.0, 101970.0, 101720.0,
        101467.0, 101215.0, 100995.0, 100835.0, 100810.0, 100932.0, 101137.0,
        101342.0, 101510.0, 101635.0, 101747.0, 101872.0, 101960.0, 101962.0,
        101912.0, 101805.0, 101657.0, 101552.0, 101342.0, 100955.0, 100822.0,
        100857.0, 100935.0, 101020.0, 101115.0, 101192.0, 101207.0, 101175.0,
        101150.0, 101130.0, 101122.0, 101142.0, 101182.0, 101240.0, 101297.0,
        101320.0, 101315.0, 101345.0, 101400.0, 101470.0, 101562.0, 101677.0,
        101810.0, 101987.0, 102217.0, 102460.0, 102077.0, 102222.0, 102290.0,
        102265.0, 102167.0, 102022.0, 101875.0, 101752.0, 101635.0, 101520.0,
        101440.0, 101427.0, 101462.0, 101497.0, 101540.0, 101582.0, 101610.0,
        101627.0, 101617.0, 101570.0, 101475.0, 101365.0, 101285.0, 101275.0,
        101367.0, 101562.0, 101807.0, 102067.0, 102297.0, 102460.0, 102552.0,
        102612.0, 102662.0, 102702.0, 102742.0, 102770.0, 102760.0, 102707.0,
        102625.0, 102512.0, 102390.0, 102265.0, 102137.0, 102025.0, 101940.0,
        101872.0, 101817.0, 101797.0, 101815.0, 101850.0, 101905.0, 101965.0,
        102007.0, 102045.0, 102067.0, 102055.0, 102020.0, 101995.0, 101955.0,
        101875.0, 101737.0, 101555.0, 101377.0, 101225.0, 101057.0, 100800.0,
        100507.0, 100307.0, 100275.0, 100315.0, 100392.0, 100577.0, 100885.0,
        101167.0, 101297.0, 101312.0, 101270.0, 101150.0, 100915.0, 100650.0,
        100460.0, 100410.0, 100452.0, 100570.0, 100792.0, 101150.0, 101590.0,
        102005.0, 102325.0, 102562.0, 102717.0, 102770.0, 102722.0, 102607.0,
        102435.0, 102200.0, 101957.0, 101740.0, 101552.0, 101380.0, 101230.0,
        101072.0, 100937.0, 100892.0, 100937.0, 101017.0, 101122.0, 101250.0,
        101377.0, 101477.0, 101530.0, 101545.0, 101545.0, 101540.0, 101512.0,
        101500.0, 101242.0, 100907.0, 100820.0, 100807.0, 100867.0, 100945.0,
        100985.0, 100962.0, 100897.0, 100830.0, 100765.0, 100702.0, 100677.0,
        100692.0, 100717.0, 100745.0, 100787.0, 100790.0, 100747.0, 100747.0,
        100802.0, 100865.0, 100947.0, 101077.0, 101235.0, 101417.0, 101635.0,
        101872.0, 101442.0, 101627.0, 101730.0, 101760.0, 101752.0, 101680.0,
        101530.0, 101367.0, 101257.0, 101170.0, 101082.0, 101007.0, 100970.0,
        101000.0, 101082.0, 101180.0, 101225.0, 101197.0, 101137.0, 101082.0,
        101025.0, 100947.0, 100857.0, 100812.0, 100857.0, 101002.0, 101207.0,
        101440.0, 101680.0, 101900.0, 102075.0, 102212.0, 102317.0, 102387.0,
        102410.0, 102400.0, 102352.0, 102280.0, 102162.0, 102012.0, 101862.0,
        101735.0, 101625.0, 101520.0, 101435.0, 101382.0, 101367.0, 101390.0,
        101432.0, 101505.0, 101610.0, 101722.0, 101810.0, 101872.0, 101907.0,
        101907.0, 101892.0, 101865.0, 101790.0, 101655.0, 101492.0, 101340.0,
        101200.0, 101072.0, 100950.0, 100825.0, 100690.0, 100575.0, 100477.0,
        100410.0, 100432.0, 100582.0, 100845.0, 101117.0, 101305.0, 101392.0,
        101360.0, 101202.0, 100937.0, 100660.0, 100482.0, 100440.0, 100485.0,
        100605.0, 100827.0, 101180.0, 101607.0, 102012.0, 102315.0, 102517.0,
        102630.0, 102662.0, 102597.0, 102457.0, 102272.0, 102057.0, 101835.0,
        101600.0, 101380.0, 101207.0, 101095.0, 101035.0, 100977.0, 100915.0,
        100857.0, 100830.0, 100852.0, 100905.0, 100942.0, 100975.0, 101020.0,
        101062.0, 101097.0, 101122.0, 101135.0, 101097.0, 100867.0, 100712.0,
        100712.0, 100682.0, 100687.0, 100710.0, 100707.0, 100640.0, 100555.0,
        100472.0, 100365.0, 100232.0, 100150.0, 100142.0, 100152.0, 100175.0,
        100197.0, 100182.0, 100115.0, 100067.0, 100090.0, 100150.0, 100237.0,
        100362.0, 100530.0, 100725.0, 100950.0, 101200.0, 100745.0, 100947.0,
        101072.0, 101130.0, 101167.0, 101182.0, 101115.0, 100977.0, 100817.0,
        100687.0, 100595.0, 100540.0, 100500.0, 100482.0, 100507.0, 100582.0,
        100620.0, 100555.0, 100410.0, 100255.0, 100142.0, 100057.0, 99995.0,
        99972.0, 100032.0, 100192.0, 100415.0, 100657.0, 100902.0, 101142.0,
        101377.0, 101582.0, 101740.0, 101845.0, 101907.0, 101922.0, 101895.0,
        101812.0, 101672.0, 101480.0, 101265.0, 101055.0, 100872.0, 100720.0,
        100617.0, 100587.0, 100620.0, 100700.0, 100805.0, 100930.0, 101072.0,
        101217.0, 101347.0, 101455.0, 101532.0, 101570.0, 101567.0, 101540.0,
        101455.0, 101330.0, 101195.0, 101057.0, 100917.0, 100792.0, 100717.0,
        100662.0, 100610.0, 100557.0, 100520.0, 100525.0, 100590.0, 100715.0,
        100892.0, 101082.0, 101247.0, 101347.0, 101355.0, 101240.0, 101027.0,
        100770.0, 100570.0, 100480.0, 100510.0, 100647.0, 100895.0, 101247.0,
        101645.0, 102005.0, 102260.0, 102405.0, 102470.0, 102462.0, 102387.0,
        102257.0, 102087.0, 101882.0, 101642.0, 101390.0, 101162.0, 100967.0,
        100812.0, 100707.0, 100657.0, 100645.0, 100640.0, 100642.0, 100642.0,
        100625.0, 100602.0, 100602.0, 100612.0, 100597.0, 100570.0, 100577.0,
        100597.0, 100552.0, 100437.0, 100412.0, 100457.0, 100442.0, 100372.0,
        100300.0, 100240.0, 100160.0, 100055.0, 99947.0, 99830.0, 99680.0,
        99550.0, 99487.0, 99495.0, 99530.0, 99562.0, 99565.0, 99520.0, 99467.0,
        99450.0, 99490.0, 99567.0, 99682.0, 99855.0, 100065.0, 100290.0,
        100512.0, 100142.0, 100335.0, 100505.0, 100622.0, 100687.0, 100712.0,
        100685.0, 100597.0, 100457.0, 100297.0, 100150.0, 100050.0, 99992.0,
        99935.0, 99890.0, 99872.0, 99862.0, 99787.0, 99602.0, 99360.0, 99140.0,
        98992.0, 98920.0, 98910.0, 98962.0, 99105.0, 99335.0, 99620.0, 99917.0,
        100212.0, 100507.0, 100792.0, 101045.0, 101237.0, 101350.0, 101367.0,
        101300.0, 101167.0, 100995.0, 100782.0, 100532.0, 100262.0, 100015.0,
        99830.0, 99710.0, 99650.0, 99647.0, 99710.0, 99830.0, 99995.0, 100180.0,
        100375.0, 100565.0, 100725.0, 100837.0, 100897.0, 100922.0, 100920.0,
        100882.0, 100805.0, 100707.0, 100582.0, 100455.0, 100350.0, 100300.0,
        100292.0, 100310.0, 100347.0, 100405.0, 100467.0, 100540.0, 100647.0,
        100800.0, 100957.0, 101085.0, 101175.0, 101220.0, 101220.0, 101132.0,
        100965.0, 100775.0, 100632.0, 100600.0, 100707.0, 100940.0, 101270.0,
        101617.0, 101912.0, 102120.0, 102237.0, 102282.0, 102245.0, 102137.0,
        101982.0, 101795.0, 101587.0, 101362.0, 101127.0, 100900.0, 100677.0,
        100467.0, 100300.0, 100202.0, 100170.0, 100175.0, 100197.0, 100222.0,
        100240.0, 100247.0, 100255.0, 100255.0, 100225.0, 100192.0, 100200.0,
        100197.0, 100120.0, 99990.0, 99945.0, 99980.0, 99990.0, 99927.0,
        99825.0, 99705.0, 99562.0, 99405.0, 99250.0, 99100.0, 98927.0, 98765.0,
        98675.0, 98697.0, 98760.0, 98842.0, 98905.0, 98925.0, 98900.0, 98880.0,
        98897.0, 98955.0, 99065.0, 99242.0, 99487.0, 99732.0, 99950.0, 99640.0,
        99797.0, 99952.0, 100105.0, 100225.0, 100255.0, 100205.0, 100107.0,
        99995.0, 99870.0, 99735.0, 99602.0, 99502.0, 99432.0, 99390.0, 99357.0,
        99305.0, 99192.0, 98965.0, 98640.0, 98297.0, 98022.0, 97865.0, 97830.0,
        97890.0, 98052.0, 98307.0, 98625.0, 98970.0, 99322.0, 99677.0, 100015.0,
        100295.0, 100500.0, 100612.0, 100635.0, 100575.0, 100452.0, 100260.0,
        100015.0, 99727.0, 99420.0, 99130.0, 98887.0, 98717.0, 98620.0, 98597.0,
        98650.0, 98762.0, 98920.0, 99102.0, 99312.0, 99530.0, 99725.0, 99880.0,
        99982.0, 100042.0, 100065.0, 100060.0, 100035.0, 100007.0, 99972.0,
        99927.0, 99877.0, 99837.0, 99822.0, 99830.0, 99885.0, 99980.0, 100092.0,
        100210.0, 100335.0, 100472.0, 100602.0, 100705.0, 100797.0, 100900.0,
        101000.0, 101057.0, 101052.0, 101000.0, 100922.0, 100875.0, 100910.0,
        101062.0, 101302.0, 101565.0, 101787.0, 101940.0, 102022.0, 102032.0,
        101970.0, 101842.0, 101665.0, 101460.0, 101232.0, 100992.0, 100747.0,
        100492.0, 100237.0, 100010.0, 99845.0, 99740.0, 99662.0, 99617.0,
        99612.0, 99645.0, 99692.0, 99725.0, 99752.0, 99777.0, 99792.0, 99790.0,
        99762.0, 99695.0, 99575.0, 99432.0, 99340.0, 99322.0, 99320.0, 99285.0,
        99202.0, 99067.0, 98887.0, 98685.0, 98477.0, 98255.0, 98032.0, 97865.0,
        97812.0, 97877.0, 98022.0, 98195.0, 98367.0, 98487.0, 98530.0, 98522.0,
        98522.0, 98542.0, 98602.0, 98722.0, 98935.0, 99195.0, 99450.0, 99182.0,
        99365.0, 99520.0, 99662.0, 99782.0, 99830.0, 99797.0, 99710.0, 99620.0,
        99545.0, 99457.0, 99352.0, 99227.0, 99107.0, 99010.0, 98945.0, 98905.0,
        98835.0, 98662.0, 98345.0, 97927.0, 97505.0, 97187.0, 97032.0, 97042.0,
        97212.0, 97515.0, 97895.0, 98292.0, 98672.0, 99020.0, 99327.0, 99572.0,
        99752.0, 99862.0, 99907.0, 99882.0, 99762.0, 99550.0, 99265.0, 98960.0,
        98655.0, 98377.0, 98132.0, 97930.0, 97792.0, 97715.0, 97697.0, 97735.0,
        97832.0, 97995.0, 98205.0, 98435.0, 98652.0, 98835.0, 98980.0, 99082.0,
        99142.0, 99182.0, 99205.0, 99222.0, 99222.0, 99215.0, 99217.0, 99237.0,
        99260.0, 99280.0, 99307.0, 99372.0, 99490.0, 99640.0, 99800.0, 99947.0,
        100075.0, 100182.0, 100280.0, 100380.0, 100485.0, 100597.0, 100715.0,
        100827.0, 100910.0, 100962.0, 101020.0, 101112.0, 101245.0, 101390.0,
        101512.0, 101595.0, 101625.0, 101595.0, 101502.0, 101370.0, 101197.0,
        101000.0, 100767.0, 100527.0, 100287.0, 100047.0, 99802.0, 99577.0,
        99395.0, 99270.0, 99180.0, 99127.0, 99105.0, 99110.0, 99120.0, 99130.0,
        99145.0, 99172.0, 99192.0, 99177.0, 99130.0, 99060.0, 98985.0, 98907.0,
        98832.0, 98772.0, 98727.0, 98680.0, 98595.0, 98447.0, 98240.0, 97992.0,
        97710.0, 97420.0, 97167.0, 97042.0, 97080.0, 97252.0, 97497.0, 97767.0,
        98025.0, 98237.0, 98350.0, 98372.0, 98355.0, 98350.0, 98367.0, 98420.0,
        98537.0, 98725.0, 98955.0, 98692.0, 98892.0, 99055.0, 99175.0, 99260.0,
        99317.0, 99352.0, 99360.0, 99327.0, 99260.0, 99172.0, 99067.0, 98960.0,
        98845.0, 98740.0, 98672.0, 98650.0, 98645.0, 98592.0, 98432.0, 98152.0,
        97805.0, 97467.0, 97210.0, 97075.0, 97102.0, 97277.0, 97562.0, 97895.0,
        98222.0, 98530.0, 98817.0, 99075.0, 99270.0, 99382.0, 99397.0, 99325.0,
        99185.0, 98992.0, 98762.0, 98520.0, 98270.0, 98032.0, 97810.0, 97610.0,
        97427.0, 97267.0, 97137.0, 97077.0, 97097.0, 97220.0, 97405.0, 97610.0,
        97805.0, 97977.0, 98120.0, 98242.0, 98335.0, 98415.0, 98472.0, 98512.0,
        98520.0, 98517.0, 98522.0, 98555.0, 98592.0, 98627.0, 98662.0, 98727.0,
        98830.0, 98972.0, 99140.0, 99312.0, 99487.0, 99652.0, 99792.0, 99902.0,
        99992.0, 100092.0, 100207.0, 100335.0, 100460.0, 100567.0, 100675.0,
        100780.0, 100877.0, 100955.0, 101015.0, 101055.0, 101060.0, 101015.0,
        100907.0, 100770.0, 100610.0, 100422.0, 100205.0, 99972.0, 99747.0,
        99535.0, 99325.0, 99120.0, 98947.0, 98810.0, 98720.0, 98657.0, 98607.0,
        98567.0, 98530.0, 98515.0, 98527.0, 98560.0, 98587.0, 98595.0, 98577.0,
        98552.0, 98515.0, 98465.0, 98395.0, 98332.0, 98280.0, 98217.0, 98115.0,
        97952.0, 97727.0, 97450.0, 97130.0, 96812.0, 96595.0, 96560.0, 96727.0,
        97027.0, 97360.0, 97660.0, 97922.0, 98132.0, 98252.0, 98280.0, 98250.0,
        98222.0, 98230.0, 98260.0, 98302.0, 98377.0, 98507.0, 98155.0, 98320.0,
        98500.0, 98665.0, 98802.0, 98927.0, 99030.0, 99095.0, 99102.0, 99050.0,
        98970.0, 98905.0, 98857.0, 98827.0, 98785.0, 98737.0, 98692.0, 98650.0,
        98602.0, 98532.0, 98425.0, 98272.0, 98090.0, 97905.0, 97752.0, 97682.0,
        97712.0, 97840.0, 98037.0, 98255.0, 98470.0, 98670.0, 98837.0, 98942.0,
        98967.0, 98930.0, 98852.0, 98765.0, 98660.0, 98525.0, 98355.0, 98165.0,
        97977.0, 97812.0, 97652.0, 97480.0, 97285.0, 97092.0, 96940.0, 96867.0,
        96890.0, 97002.0, 97170.0, 97367.0, 97562.0, 97727.0, 97840.0, 97897.0,
        97915.0, 97912.0, 97910.0, 97912.0, 97917.0, 97932.0, 97952.0, 97980.0,
        98017.0, 98075.0, 98152.0, 98255.0, 98367.0, 98490.0, 98627.0, 98777.0,
        98937.0, 99082.0, 99207.0, 99327.0, 99445.0, 99557.0, 99665.0, 99765.0,
        99872.0, 99990.0, 100107.0, 100207.0, 100270.0, 100292.0, 100295.0,
        100277.0, 100230.0, 100145.0, 100030.0, 99905.0, 99765.0, 99610.0,
        99437.0, 99260.0, 99085.0, 98915.0, 98752.0, 98595.0, 98455.0, 98332.0,
        98235.0, 98157.0, 98110.0, 98092.0, 98102.0, 98135.0, 98172.0, 98207.0,
        98227.0, 98240.0, 98227.0, 98192.0, 98130.0, 98052.0, 97977.0, 97890.0,
        97792.0, 97675.0, 97542.0, 97385.0, 97207.0, 97012.0, 96837.0, 96750.0,
        96815.0, 97035.0, 97317.0, 97577.0, 97757.0, 97872.0, 97947.0, 97977.0,
        97952.0, 97887.0, 97835.0, 97837.0, 97877.0, 97932.0, 97977.0, 98040.0,
        97750.0, 97945.0, 98187.0, 98440.0, 98667.0, 98835.0, 98947.0, 98992.0,
        98997.0, 98980.0, 98955.0, 98937.0, 98922.0, 98900.0, 98865.0, 98812.0,
        98755.0, 98695.0, 98632.0, 98570.0, 98507.0, 98442.0, 98377.0, 98312.0,
        98250.0, 98197.0, 98180.0, 98217.0, 98312.0, 98450.0, 98592.0, 98715.0,
        98785.0, 98792.0, 98745.0, 98670.0, 98597.0, 98527.0, 98450.0, 98357.0,
        98252.0, 98150.0, 98055.0, 97980.0, 97895.0, 97752.0, 97570.0, 97370.0,
        97197.0, 97100.0, 97087.0, 97160.0, 97290.0, 97445.0, 97580.0, 97682.0,
        97702.0, 97652.0, 97555.0, 97455.0, 97380.0, 97362.0, 97382.0, 97432.0,
        97495.0, 97560.0, 97620.0, 97682.0, 97735.0, 97802.0, 97867.0, 97942.0,
        98037.0, 98147.0, 98260.0, 98370.0, 98472.0, 98580.0, 98687.0, 98792.0,
        98880.0, 98960.0, 99037.0, 99130.0, 99220.0, 99302.0, 99357.0, 99392.0,
        99410.0, 99412.0, 99390.0, 99340.0, 99265.0, 99175.0, 99082.0, 98985.0,
        98892.0, 98800.0, 98702.0, 98600.0, 98492.0, 98382.0, 98265.0, 98162.0,
        98067.0, 97997.0, 97955.0, 97950.0, 97970.0, 97997.0, 98025.0, 98047.0,
        98057.0, 98045.0, 98010.0, 97940.0, 97845.0, 97735.0, 97605.0, 97490.0,
        97380.0, 97305.0, 97277.0, 97272.0, 97282.0, 97287.0, 97287.0, 97312.0,
        97395.0, 97532.0, 97680.0, 97772.0, 97792.0, 97757.0, 97695.0, 97612.0,
        97510.0, 97405.0, 97325.0, 97310.0, 97352.0, 97425.0, 97512.0, 97615.0,
        97885.0, 98125.0, 98385.0, 98630.0, 98817.0, 98935.0, 98977.0, 98972.0,
        98947.0, 98930.0, 98920.0, 98905.0, 98882.0, 98855.0, 98815.0, 98775.0,
        98717.0, 98632.0, 98515.0, 98375.0, 98247.0, 98187.0, 98197.0, 98262.0,
        98332.0, 98367.0, 98392.0, 98422.0, 98480.0, 98547.0, 98605.0, 98630.0,
        98615.0, 98560.0, 98487.0, 98417.0, 98370.0, 98345.0, 98315.0, 98272.0,
        98212.0, 98137.0, 98052.0, 97970.0, 97897.0, 97820.0, 97747.0, 97672.0,
        97612.0, 97585.0, 97592.0, 97630.0, 97690.0, 97757.0, 97790.0, 97752.0,
        97657.0, 97552.0, 97467.0, 97422.0, 97415.0, 97412.0, 97440.0, 97480.0,
        97527.0, 97570.0, 97602.0, 97617.0, 97620.0, 97605.0, 97595.0, 97585.0,
        97575.0, 97567.0, 97552.0, 97547.0, 97552.0, 97570.0, 97617.0, 97682.0,
        97755.0, 97837.0, 97925.0, 98025.0, 98125.0, 98225.0, 98312.0, 98392.0,
        98460.0, 98512.0, 98545.0, 98552.0, 98535.0, 98507.0, 98480.0, 98460.0,
        98445.0, 98435.0, 98422.0, 98402.0, 98367.0, 98322.0, 98265.0, 98207.0,
        98147.0, 98090.0, 98047.0, 98020.0, 98000.0, 97990.0, 97972.0, 97952.0,
        97930.0, 97887.0, 97827.0, 97742.0, 97655.0, 97555.0, 97450.0, 97352.0,
        97285.0, 97262.0, 97275.0, 97320.0, 97382.0, 97450.0, 97512.0, 97562.0,
        97625.0, 97697.0, 97745.0, 97762.0, 97745.0, 97692.0, 97607.0, 97512.0,
        97410.0, 97312.0, 97247.0, 97230.0, 97277.0, 97372.0, 97505.0, 97677.0,
        98675.0, 98862.0, 99032.0, 99152.0, 99237.0, 99275.0, 99285.0, 99270.0,
        99245.0, 99205.0, 99137.0, 99055.0, 98955.0, 98860.0, 98777.0, 98710.0,
        98647.0, 98572.0, 98495.0, 98435.0, 98430.0, 98482.0, 98532.0, 98507.0,
        98400.0, 98282.0, 98267.0, 98362.0, 98477.0, 98530.0, 98517.0, 98497.0,
        98497.0, 98495.0, 98477.0, 98447.0, 98430.0, 98440.0, 98467.0, 98480.0,
        98450.0, 98365.0, 98260.0, 98175.0, 98145.0, 98192.0, 98282.0, 98392.0,
        98480.0, 98525.0, 98530.0, 98517.0, 98515.0, 98517.0, 98497.0, 98420.0,
        98287.0, 98137.0, 98005.0, 97920.0, 97877.0, 97870.0, 97880.0, 97892.0,
        97900.0, 97892.0, 97880.0, 97855.0, 97820.0, 97767.0, 97675.0, 97565.0,
        97435.0, 97287.0, 97135.0, 96982.0, 96842.0, 96727.0, 96650.0, 96607.0,
        96612.0, 96647.0, 96722.0, 96827.0, 96955.0, 97092.0, 97232.0, 97362.0,
        97477.0, 97575.0, 97655.0, 97722.0, 97782.0, 97837.0, 97897.0, 97960.0,
        98022.0, 98080.0, 98125.0, 98157.0, 98167.0, 98155.0, 98125.0, 98085.0,
        98045.0, 98005.0, 97970.0, 97937.0, 97907.0, 97880.0, 97845.0, 97822.0,
        97805.0, 97790.0, 97775.0, 97765.0, 97785.0, 97805.0, 97785.0, 97705.0,
        97607.0, 97522.0, 97472.0, 97432.0, 97425.0, 97442.0, 97480.0, 97517.0,
        97560.0, 97592.0, 97610.0, 97612.0, 97607.0, 97585.0, 97590.0, 97587.0,
        97595.0, 97620.0, 97672.0, 97760.0, 97892.0, 98060.0, 98255.0, 98467.0,
        98982.0, 99035.0, 99080.0, 99117.0, 99167.0, 99235.0, 99322.0, 99430.0,
        99547.0, 99662.0, 99755.0, 99822.0, 99865.0, 99885.0, 99887.0, 99885.0,
        99872.0, 99855.0, 99800.0, 99697.0, 99522.0, 99247.0, 98890.0, 98525.0,
        98252.0, 98140.0, 98190.0, 98315.0, 98435.0, 98540.0, 98665.0, 98825.0,
        98970.0, 99017.0, 98955.0, 98837.0, 98755.0, 98740.0, 98800.0, 98895.0,
        98972.0, 99017.0, 99030.0, 99047.0, 99105.0, 99230.0, 99410.0, 99622.0,
        99802.0, 99910.0, 99907.0, 99802.0, 99635.0, 99440.0, 99247.0, 99080.0,
        98947.0, 98850.0, 98792.0, 98780.0, 98797.0, 98827.0, 98822.0, 98745.0,
        98590.0, 98390.0, 98197.0, 98040.0, 97915.0, 97795.0, 97667.0, 97515.0,
        97350.0, 97182.0, 97015.0, 96845.0, 96680.0, 96520.0, 96382.0, 96267.0,
        96185.0, 96152.0, 96167.0, 96237.0, 96350.0, 96495.0, 96647.0, 96805.0,
        96950.0, 97075.0, 97180.0, 97272.0, 97350.0, 97430.0, 97512.0, 97597.0,
        97680.0, 97757.0, 97822.0, 97867.0, 97892.0, 97892.0, 97882.0, 97865.0,
        97850.0, 97832.0, 97832.0, 97847.0, 97867.0, 97892.0, 97925.0, 97965.0,
        97985.0, 98002.0, 98017.0, 98075.0, 98160.0, 98217.0, 98185.0, 98060.0,
        97900.0, 97765.0, 97675.0, 97597.0, 97542.0, 97500.0, 97485.0, 97477.0,
        97492.0, 97527.0, 97565.0, 97610.0, 97680.0, 97760.0, 97857.0, 97957.0,
        98065.0, 98162.0, 98270.0, 98392.0, 98527.0, 98665.0, 98790.0, 98900.0,
        98877.0, 98825.0, 98795.0, 98800.0, 98872.0, 99012.0, 99210.0, 99445.0,
        99685.0, 99912.0, 100112.0, 100272.0, 100395.0, 100477.0, 100517.0,
        100517.0, 100465.0, 100355.0, 100165.0, 99897.0, 99560.0, 99195.0,
        98852.0, 98587.0, 98427.0, 98392.0, 98450.0, 98582.0, 98767.0, 98990.0,
        99220.0, 99400.0, 99480.0, 99442.0, 99320.0, 99185.0, 99097.0, 99090.0,
        99157.0, 99270.0, 99390.0, 99475.0, 99525.0, 99547.0, 99575.0, 99630.0,
        99725.0, 99842.0, 99957.0, 100030.0, 100020.0, 99920.0, 99742.0,
        99527.0, 99312.0, 99130.0, 98997.0, 98930.0, 98917.0, 98940.0, 98962.0,
        98945.0, 98842.0, 98667.0, 98460.0, 98265.0, 98110.0, 97985.0, 97870.0,
        97712.0, 97535.0, 97350.0, 97185.0, 97040.0, 96917.0, 96810.0, 96707.0,
        96615.0, 96537.0, 96475.0, 96430.0, 96410.0, 96425.0, 96465.0, 96532.0,
        96605.0, 96695.0, 96787.0, 96870.0, 96945.0, 97007.0, 97072.0, 97147.0,
        97230.0, 97317.0, 97407.0, 97497.0, 97585.0, 97667.0, 97742.0, 97810.0,
        97862.0, 97905.0, 97937.0, 97970.0, 98017.0, 98082.0, 98157.0, 98227.0,
        98285.0, 98335.0, 98377.0, 98410.0, 98430.0, 98445.0, 98447.0, 98437.0,
        98395.0, 98320.0, 98227.0, 98137.0, 98072.0, 98000.0, 97935.0, 97875.0,
        97815.0, 97780.0, 97775.0, 97792.0, 97837.0, 97915.0, 98015.0, 98117.0,
        98207.0, 98287.0, 98360.0, 98435.0, 98530.0, 98637.0, 98752.0, 98847.0,
        98910.0, 98935.0, 98920.0, 99232.0, 99135.0, 99052.0, 98990.0, 98957.0,
        98957.0, 98992.0, 99057.0, 99137.0, 99232.0, 99330.0, 99427.0, 99525.0,
        99612.0, 99680.0, 99720.0, 99720.0, 99667.0, 99552.0, 99380.0, 99167.0,
        98945.0, 98745.0, 98600.0, 98530.0, 98542.0, 98632.0, 98790.0, 98992.0,
        99200.0, 99385.0, 99510.0, 99550.0, 99505.0, 99400.0, 99250.0, 99097.0,
        98965.0, 98860.0, 98782.0, 98732.0, 98697.0, 98680.0, 98677.0, 98692.0,
        98725.0, 98770.0, 98812.0, 98850.0, 98855.0, 98830.0, 98767.0, 98685.0,
        98595.0, 98520.0, 98475.0, 98475.0, 98510.0, 98572.0, 98632.0, 98662.0,
        98632.0, 98545.0, 98415.0, 98267.0, 98127.0, 98007.0, 97892.0, 97772.0,
        97622.0, 97462.0, 97305.0, 97172.0, 97065.0, 96975.0, 96917.0, 96887.0,
        96872.0, 96880.0, 96882.0, 96895.0, 96912.0, 96930.0, 96937.0, 96960.0,
        96992.0, 97027.0, 97080.0, 97147.0, 97235.0, 97330.0, 97432.0, 97522.0,
        97595.0, 97647.0, 97677.0, 97697.0, 97727.0, 97765.0, 97827.0, 97907.0,
        98002.0, 98107.0, 98227.0, 98350.0, 98472.0, 98572.0, 98645.0, 98675.0,
        98677.0, 98667.0, 98655.0, 98650.0, 98642.0, 98630.0, 98607.0, 98575.0,
        98527.0, 98475.0, 98422.0, 98360.0, 98310.0, 98262.0, 98225.0, 98202.0,
        98202.0, 98225.0, 98277.0, 98345.0, 98427.0, 98505.0, 98562.0, 98600.0,
        98635.0, 98682.0, 98767.0, 98900.0, 99070.0, 99237.0, 99375.0, 99447.0,
        99457.0, 99410.0, 99327.0, 100085.0, 100070.0, 100042.0, 100017.0,
        99992.0, 99972.0, 99952.0, 99940.0, 99930.0, 99910.0, 99895.0, 99872.0,
        99847.0, 99812.0, 99765.0, 99702.0, 99612.0, 99500.0, 99365.0, 99212.0,
        99050.0, 98892.0, 98757.0, 98657.0, 98595.0, 98590.0, 98632.0, 98720.0,
        98837.0, 98972.0, 99102.0, 99210.0, 99285.0, 99307.0, 99285.0, 99220.0,
        99127.0, 99017.0, 98905.0, 98797.0, 98707.0, 98637.0, 98587.0, 98555.0,
        98532.0, 98520.0, 98502.0, 98482.0, 98447.0, 98400.0, 98345.0, 98282.0,
        98227.0, 98187.0, 98160.0, 98157.0, 98172.0, 98205.0, 98245.0, 98277.0,
        98290.0, 98282.0, 98252.0, 98202.0, 98137.0, 98067.0, 97997.0, 97920.0,
        97852.0, 97765.0, 97677.0, 97590.0, 97507.0, 97440.0, 97387.0, 97355.0,
        97337.0, 97337.0, 97330.0, 97345.0, 97367.0, 97390.0, 97417.0, 97445.0,
        97475.0, 97505.0, 97532.0, 97562.0, 97585.0, 97607.0, 97622.0, 97632.0,
        97637.0, 97647.0, 97655.0, 97670.0, 97700.0, 97742.0, 97802.0, 97892.0,
        98007.0, 98145.0, 98297.0, 98455.0, 98597.0, 98705.0, 98765.0, 98777.0,
        98755.0, 98712.0, 98672.0, 98650.0, 98650.0, 98662.0, 98677.0, 98675.0,
        98660.0, 98630.0, 98590.0, 98547.0, 98502.0, 98475.0, 98460.0, 98455.0,
        98472.0, 98510.0, 98565.0, 98635.0, 98707.0, 98772.0, 98815.0, 98842.0,
        98852.0, 98870.0, 98915.0, 99005.0, 99145.0, 99327.0, 99525.0, 99717.0,
        99875.0, 99987.0, 100057.0, 100085.0, 100032.0, 100007.0, 99965.0,
        99917.0, 99867.0, 99812.0, 99765.0, 99720.0, 99682.0, 99652.0, 99632.0,
        99617.0, 99605.0, 99600.0, 99592.0, 99585.0, 99570.0, 99550.0, 99522.0,
        99495.0, 99462.0, 99430.0, 99400.0, 99375.0, 99362.0, 99360.0, 99372.0,
        99385.0, 99407.0, 99427.0, 99445.0, 99450.0, 99445.0, 99425.0, 99387.0,
        99342.0, 99290.0, 99232.0, 99172.0, 99120.0, 99070.0, 99027.0, 98992.0,
        98962.0, 98940.0, 98912.0, 98892.0, 98867.0, 98840.0, 98815.0, 98785.0,
        98750.0, 98720.0, 98690.0, 98662.0, 98637.0, 98615.0, 98595.0, 98577.0,
        98552.0, 98525.0, 98495.0, 98462.0, 98430.0, 98400.0, 98370.0, 98342.0,
        98320.0, 98305.0, 98290.0, 98277.0, 98262.0, 98252.0, 98235.0, 98217.0,
        98202.0, 98187.0, 98175.0, 98162.0, 98152.0, 98145.0, 98137.0, 98130.0,
        98127.0, 98122.0, 98115.0, 98105.0, 98087.0, 98065.0, 98042.0, 98012.0,
        97985.0, 97947.0, 97912.0, 97882.0, 97870.0, 97870.0, 97890.0, 97935.0,
        98007.0, 98100.0, 98212.0, 98330.0, 98437.0, 98532.0, 98597.0, 98640.0,
        98655.0, 98652.0, 98642.0, 98630.0, 98622.0, 98627.0, 98647.0, 98667.0,
        98692.0, 98712.0, 98727.0, 98732.0, 98735.0, 98730.0, 98722.0, 98720.0,
        98720.0, 98720.0, 98730.0, 98742.0, 98760.0, 98785.0, 98817.0, 98860.0,
        98912.0, 98982.0, 99070.0, 99170.0, 99292.0, 99425.0, 99557.0, 99687.0,
        99807.0, 99905.0, 99977.0, 100020.0, 100037.0, 99987.0, 99960.0,
        99925.0, 99892.0, 99852.0, 99817.0, 99790.0, 99762.0, 99740.0, 99725.0,
        99715.0, 99712.0, 99712.0, 99720.0, 99732.0, 99750.0, 99765.0, 99780.0,
        99797.0, 99807.0, 99815.0, 99810.0, 99807.0, 99790.0, 99762.0, 99725.0,
        99685.0, 99635.0, 99570.0, 99505.0, 99435.0, 99365.0, 99290.0, 99220.0,
        99150.0, 99085.0, 99027.0, 98972.0, 98932.0, 98892.0, 98862.0, 98842.0,
        98830.0, 98827.0, 98832.0, 98845.0, 98862.0, 98890.0, 98922.0, 98957.0,
        98997.0, 99037.0, 99080.0, 99117.0, 99150.0, 99177.0, 99197.0, 99212.0,
        99210.0, 99197.0, 99175.0, 99145.0, 99105.0, 99060.0, 99005.0, 98947.0,
        98890.0, 98832.0, 98782.0, 98727.0, 98680.0, 98640.0, 98602.0, 98572.0,
        98547.0, 98525.0, 98505.0, 98485.0, 98467.0, 98457.0, 98442.0, 98427.0,
        98415.0, 98405.0, 98392.0, 98382.0, 98372.0, 98362.0, 98355.0, 98350.0,
        98350.0, 98350.0, 98360.0, 98377.0, 98402.0, 98432.0, 98472.0, 98517.0,
        98567.0, 98625.0, 98682.0, 98735.0, 98790.0, 98835.0, 98875.0, 98905.0,
        98930.0, 98947.0, 98957.0, 98967.0, 98972.0, 98975.0, 98982.0, 98990.0,
        98995.0, 99005.0, 99012.0, 99022.0, 99032.0, 99042.0, 99052.0, 99067.0,
        99080.0, 99102.0, 99130.0, 99160.0, 99202.0, 99247.0, 99305.0, 99365.0,
        99435.0, 99510.0, 99587.0, 99665.0, 99740.0, 99812.0, 99877.0, 99932.0,
        99975.0, 100007.0, 100025.0, 100035.0, 100030.0, 100012.0, 99935.0,
        99927.0, 99920.0, 99912.0, 99905.0, 99890.0, 99880.0, 99865.0, 99850.0,
        99837.0, 99817.0, 99802.0, 99785.0, 99767.0, 99747.0, 99725.0, 99705.0,
        99682.0, 99657.0, 99632.0, 99602.0, 99575.0, 99547.0, 99515.0, 99482.0,
        99452.0, 99420.0, 99387.0, 99352.0, 99320.0, 99287.0, 99252.0, 99225.0,
        99195.0, 99167.0, 99140.0, 99117.0, 99095.0, 99075.0, 99062.0, 99050.0,
        99042.0, 99035.0, 99032.0, 99032.0, 99040.0, 99047.0, 99057.0, 99067.0,
        99085.0, 99102.0, 99122.0, 99137.0, 99157.0, 99180.0, 99197.0, 99217.0,
        99235.0, 99252.0, 99260.0, 99272.0, 99277.0, 99282.0, 99282.0, 99282.0,
        99277.0, 99267.0, 99257.0, 99247.0, 99232.0, 99217.0, 99207.0, 99187.0,
        99175.0, 99155.0, 99145.0, 99130.0, 99120.0, 99110.0, 99100.0, 99092.0,
        99087.0, 99090.0, 99087.0, 99090.0, 99097.0, 99102.0, 99115.0, 99125.0,
        99137.0, 99152.0, 99172.0, 99190.0, 99207.0, 99230.0, 99250.0, 99275.0,
        99292.0, 99315.0, 99337.0, 99355.0, 99375.0, 99395.0, 99410.0, 99427.0,
        99442.0, 99455.0, 99467.0, 99482.0, 99492.0, 99505.0, 99515.0, 99522.0,
        99535.0, 99542.0, 99555.0, 99565.0, 99577.0, 99587.0, 99600.0, 99612.0,
        99630.0, 99645.0, 99660.0, 99680.0, 99697.0, 99715.0, 99737.0, 99755.0,
        99777.0, 99797.0, 99817.0, 99835.0, 99852.0, 99867.0, 99882.0, 99897.0,
        99912.0, 99922.0, 99930.0, 99932.0, 99935.0, 99937.0, 99937.0, 99515.0,
        99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0,
        99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0,
        99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0,
        99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0,
        99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0,
        99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0,
        99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0,
        99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0,
        99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0,
        99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0,
        99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0,
        99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0,
        99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0,
        99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0,
        99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0,
        99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0,
        99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0,
        99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0, 99515.0])
    field = numpy.multiply(slp,0.01)
    field.shape = (jm,im)
    lats = lats[::-1]

    ## Create a numpy array of the correct size
    #field = numpy.ones((jm,im))
    ## Make Checker Board of 0 and 1
    #im_half = int(im*0.5)
    #for j in range(jm):
    #    if j % 2:
    #        field[j,:] = numpy.array(([0,1]*im_half))
    #    else:
    #        field[j,:] = numpy.array(([1,0]*im_half))
    ## Instantiate matplotlib
    #plot = plotmap(ptype='pcolor',color_scheme="bone")
    ## Start simple loop
    #for step in range(1):
    #    pname = "/Users/mbauer/Desktop/plot_%04d.png" % (step)
    #    plot.create_fig()
    #    plot.add_field(lons,lats,field)
    #    plot.finish(pname)
    #    print "Made",pname


    ## Instantiate matplotlib
    #plot = plotmap(ptype='pcolor',color_scheme="bone")
    #pname = "/Users/mbauer/Desktop/plot_%04d.png" % (0)
    #plot.create_fig()
    #plot.add_field(lons,lats,field)
    #plot.finish(pname)
    #print "Made",pname

    # Instantiate matplotlib
    clevs=[950,1060,5]
    cints=[950.0,1060.0]
    missing=-999.0
    # add missing longitude
    #field[:,0] = missing
    # use discrete colorbar
    d = (clevs[1]-clevs[0])/clevs[2]
    d = ''
    center_loc = ((180.0,-60.0),(180.0,-80.0),(0.0,-90.0))
    for proj in ['laea']:
    #for proj in ['laea','stere','aeqd','ortho']:
        if d:
            pplot = plotmap_polar(mproj=proj,hemi='sh',
                bounding_lat=-30.0,color_scheme="jet",
                clevs=clevs,cints=cints,missing=missing,
                clabels=True,discrete=d)
        else:
            pplot = plotmap_polar(mproj=proj,hemi='sh',
                bounding_lat=-30.0,color_scheme="jet",
                clevs=clevs,cints=cints,missing=missing,
                clabels=True)

        pname = "/Users/mbauer/Desktop/pplot_%s.png" % (proj)
        pplot.create_fig()
        pplot.add_pcolor(lons,lats,field)
        #pplot.add_contour(lons,lats,field)
        pplot.add_pnts(center_loc,lons,lats,marker='o',msize=4,
                       mfc='white',mec='black',lw=1.)
        pplot.add_extras()
        pplot.finish(pname)
        print ("Made",pname)

