def error_plot(pname,plot,slp_step,lons,lats,center_loc,stormy_loc,
               atts_loc,empty_loc,prob_loc,msg,discard_loc=[],d_colors=[]):
    plot.create_fig()
    plot.add_field(lons,lats,slp_step,ptype='pcolor')
    if stormy_loc:
        plot.add_pnts(stormy_loc,marker='o',msize=2.,
                      mfc='yellow',mec='yellow',lw=1.)
    if atts_loc:
        plot.add_pnts(atts_loc,marker='o',msize=2.,
                      mfc='red',mec='red',lw=1.)
    if empty_loc:
        plot.add_pnts(empty_loc,marker='o',msize=5.,
                      mfc='black',mec='black',lw=1.)
        plot.add_pnts(empty_loc,marker='o',msize=3.,
                      mfc='white',mec='white',lw=1.)
        plot.add_pnts(empty_loc,marker='x',msize=2.5,
                      mfc='black',mec='black',lw=1.)
    if center_loc:
        plot.add_pnts(center_loc,marker='s',msize=3.,
                      mfc='black',mec='black',lw=1.)
        plot.add_pnts(center_loc,marker='x',msize=2.5,
                      mfc='black',mec='white',lw=1.)
    if prob_loc:
        plot.add_pnts(prob_loc,marker='o',msize=1.,
                      mfc='black',mec='black',lw=1.)
    if discard_loc:
        if d_colors:
            i = 0
            for pnt in discard_loc:
                pnts = (pnt,)
                plot.add_pnts(pnts,marker='o',msize=3.0,
                              mfc='black',mec='black',lw=1.)
                plot.add_pnts(pnts,marker='o',msize=2.5,
                              mfc=d_colors[i],mec=d_colors[i],lw=1.)
                i += 1
        else:
            plot.add_pnts(discard_loc,marker='o',msize=5.,
                          mfc='red',mec='red',lw=1.)
            plot.add_pnts(discard_loc,marker='o',msize=3.,
                          mfc='yellow',mec='yellow',lw=1.)
            plot.add_pnts(discard_loc,marker='x',msize=2.5,
                          mfc='black',mec='black',lw=1.)   

#    plot.finish_nokill(pname,title=msg)
    plot.finish(pname,title=msg)
    return "\tmMade figure: %s" % (pname)

# special version for center_finder
def error_plot_cf(pname,plot,slp_step,lons,lats,center_loc,
           discard_loc,msg,c_colors=[],d_colors=[]):
    plot.create_fig()
    plot.add_field(lons,lats,slp_step,ptype='pcolor')
    if discard_loc:
        if d_colors:
            i = 0
            for pnt in discard_loc:
                pnts = (pnt,)
                plot.add_pnts(pnts,marker='o',msize=3.0,
                              mfc='black',mec='black',lw=1.)
                plot.add_pnts(pnts,marker='o',msize=2.5,
                              mfc=d_colors[i],mec=d_colors[i],lw=1.)
                i += 1
        else:
            plot.add_pnts(discard_loc,marker='o',msize=2.,
                          mfc='red',mec='red',lw=1.)
    if center_loc:
        if c_colors:
            i = 0
            for pnt in center_loc:
                pnts = (pnt,)
                plot.add_pnts(pnts,marker='s',msize=3.,
                              mfc=c_colors[i],mec=c_colors[i],lw=1.)
                plot.add_pnts(pnts,marker='x',msize=2.5,
                              mfc='black',mec='white',lw=1.)
                i += 1
        else:
            plot.add_pnts(center_loc,marker='s',msize=3.,
                          mfc='black',mec='black',lw=1.)
            plot.add_pnts(center_loc,marker='x',msize=2.5,
                          mfc='black',mec='white',lw=1.)

    plot.finish(pname,title=msg)
    #plot.finish_nokill(pname,title=msg)

    return "\tmMade Error Figure: %s" % (pname)


