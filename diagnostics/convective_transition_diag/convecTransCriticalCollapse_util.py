# This file is part of the convective_transition_diag module of the MDTF code package (see LICENSE.txt)

# ======================================================================
# convecTransCriticalCollapse_util.py
#   
#   Provide functions called by convecTransCriticalCollapse_util.py
#
#   This file is part of the Convective Transition Diagnostic Package 
#    and the MDTF code package. See LICENSE.txt for the license.
#
#   Including:
#    (1) convecTransCriticalCollapse_loadAnalyzedData
#    (2) convecTransCriticalCollapse_fitCritical
#    (3) convecTransCriticalCollapse_plot
#    
# ======================================================================
# Import standard Python packages
import numpy
import scipy
from scipy.interpolate import interp1d
from netCDF4 import Dataset
import matplotlib.pyplot as mp
import matplotlib.cm as cm
import networkx
import warnings

# ======================================================================
# convecTransCriticalCollapse_loadAnalyzedData
#  loads the binned output calculated from convecTransBasic.py
#  and prepares it for fitting/plotting
# This script is almost identical to convecTransBasic_loadAnalyzedData
#  in convectTransBasic_util.py

def convecTransCriticalCollapse_loadAnalyzedData(*argsv):

    bin_output_list,\
    TAVE_VAR,\
    QSAT_INT_VAR,\
    BULK_TROPOSPHERIC_TEMPERATURE_MEASURE=argsv[0]
    
    if len(bin_output_list)!=0:

        bin_output_filename=bin_output_list[0]    
        
        print("   Loading "+bin_output_filename)        

        if bin_output_filename.split('.')[-1]=='nc':
            bin_output_netcdf=Dataset(bin_output_filename, "r")

            cwv_bin_center=numpy.asarray(bin_output_netcdf.variables["cwv"][:], dtype="float")
            P0=numpy.asarray(bin_output_netcdf.variables["P0"][:,:,:], dtype="float")
            P1=numpy.asarray(bin_output_netcdf.variables["P1"][:,:,:], dtype="float")
            P2=numpy.asarray(bin_output_netcdf.variables["P2"][:,:,:], dtype="float")
            PE=numpy.asarray(bin_output_netcdf.variables["PE"][:,:,:], dtype="float")
            PRECIP_THRESHOLD=bin_output_netcdf.getncattr("PRECIP_THRESHOLD")
            if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
                temp_bin_center=numpy.asarray(bin_output_netcdf.variables[TAVE_VAR][:], dtype="float")
                Q0=numpy.asarray(bin_output_netcdf.variables["Q0"][:,:], dtype="float")
                Q1=numpy.asarray(bin_output_netcdf.variables["Q1"][:,:], dtype="float")
            elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
                temp_bin_center=numpy.asarray(bin_output_netcdf.variables[QSAT_INT_VAR][:], dtype="float")
                Q0=[]
                Q1=[]
            CWV_BIN_WIDTH=cwv_bin_center[1]-cwv_bin_center[0]
            bin_output_netcdf.close()
            
        elif bin_output_filename.split('.')[-1]=='mat':
            matfile=scipy.io.loadmat(bin_output_filename)

            cwv_bin_center=matfile['cwv']
            P0=matfile['P0'].astype(float)
            P1=matfile['P1']
            P2=matfile['P2']
            PE=matfile['PE'].astype(float)
            PRECIP_THRESHOLD=matfile['PRECIP_THRESHOLD'][0,0]
            if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
                temp_bin_center=matfile[TAVE_VAR]
                Q0=matfile['Q0'].astype(float)
                Q1=matfile['Q1']
            elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
                temp_bin_center=matfile[QSAT_INT_VAR]
                Q0=[]
                Q1=[]
            CWV_BIN_WIDTH=cwv_bin_center[1][0]-cwv_bin_center[0][0]
    
        # Return CWV_BIN_WIDTH & PRECIP_THRESHOLD to make sure that
        #  user-specified parameters are consistent with existing data
        print("...Loaded!")
        return cwv_bin_center, temp_bin_center, P0, P1, P2, PE, Q0, Q1, CWV_BIN_WIDTH, PRECIP_THRESHOLD
    # If the binned model/obs data does not exist
    else:
        return numpy.array([]), numpy.array([]), numpy.array([]), numpy.array([]), numpy.array([]), \
            numpy.array([]), numpy.array([]), numpy.array([]), numpy.array([]), numpy.array([])

# ======================================================================
# convecTransCriticalCollapse_fitCritical
#  fits the binned output to determine the critical CWV
#  and prepares for plotting
# Part of the code (for determining t_reg_I) is is similar to 
#  (but different from) convecTransBasic_plot in convecTransBasic_util.py
#  with more restricted conditions here for robustness


def convecTransCriticalCollapse_fitCritical(argsv1, *argsv2):
    cwv_bin_center,\
    temp_bin_center,\
    P0,\
    P1,\
    P2,\
    PE,\
    Q0,\
    Q1,\
    CWV_BIN_WIDTH,\
    PRECIP_THRESHOLD = argsv1

    PDF_THRESHOLD,\
    CWV_RANGE_THRESHOLD,\
    CP_THRESHOLD,\
    CWV_FIT_RANGE_MIN,\
    CWV_FIT_RANGE_MAX,\
    PRECIP_REF,\
    PRECIP_FIT_MIN,\
    PRECIP_FIT_MAX = argsv2[0]

    if P0.size != 0:

        P0[P0 == 0.0] = numpy.nan
        P = P1/P0
        CP = PE/P0
        PDF = numpy.zeros(P0.shape)
        for reg in numpy.arange(P0.shape[0]):
            PDF[reg, :, :] = P0[reg, :, :]/numpy.nansum(P0[reg, :, :])/CWV_BIN_WIDTH
        # Bins with PDF>PDF_THRESHOLD
        pdf_gt_th = numpy.zeros(PDF.shape)
        with numpy.errstate(invalid="ignore"):
            pdf_gt_th[PDF > PDF_THRESHOLD] = 1
        P[pdf_gt_th == 0]=numpy.nan
        CP[pdf_gt_th == 0]=numpy.nan
        PDF = numpy.copy(PDF)
        PDF_pe = PDF*CP

        # Indicator of (temp,reg) with wide CWV range
        #  & other criteria specified below
        #  i.e., t_reg_I will be further modified below
        t_reg_I = (numpy.squeeze(numpy.sum(pdf_gt_th, axis=1))*CWV_BIN_WIDTH > CWV_RANGE_THRESHOLD)

        # Connected Component Section
        # The CWV_RANGE_THRESHOLD-Criterion must be satisfied by a connected component
        # Default: off for MODEL/on for OBS/on for Fitting
        # Fot R2TMIv7 (OBS) this doesn't make much difference
        # But when models behave "funny" one may miss by turning on this section
        # For fitting procedure (finding critical CWV at which the precip picks up)
        # Default: on
        for reg in numpy.arange(P0.shape[0]):
            for Tidx in numpy.arange(P0.shape[2]):
                if t_reg_I[reg, Tidx]:
                    dg = networkx.DiGraph()
                    for cwv_idx in numpy.arange(pdf_gt_th.shape[1]-1):
                        if pdf_gt_th[reg, cwv_idx, Tidx] > 0 and pdf_gt_th[reg, cwv_idx+1, Tidx] > 0:
                            networkx.add_path(dg, [cwv_idx, cwv_idx+1])
                    largest = max((dg.subgraph(c) for c in networkx.weakly_connected_components(dg)), key=len)
                    bcc = largest.nodes()  # Biggest Connected Component
                    if sum(pdf_gt_th[reg, bcc, Tidx])*CWV_BIN_WIDTH>CWV_RANGE_THRESHOLD:
                        t_reg_I[reg, Tidx] = True
                        pdf_gt_th[reg, :, Tidx] = 0
                        pdf_gt_th[reg, bcc, Tidx] = 1
                    else:
                        t_reg_I[reg,Tidx]=False
                        pdf_gt_th[reg,:,Tidx]=0
        # End of Connected Component Section
        #
        # Copy P, CP into p, cp for (temp,reg) with "wide CWV range" & "large PDF"
        p=numpy.zeros(P.shape)
        cp=numpy.zeros(P.shape)
        for reg in numpy.arange(P.shape[0]):
            for Tidx in numpy.arange(P.shape[2]):
                if t_reg_I[reg,Tidx]:
                    p[reg,:,Tidx]=numpy.copy(P[reg,:,Tidx])
                    cp[reg,:,Tidx]=numpy.copy(CP[reg,:,Tidx])
        p[pdf_gt_th==0]=numpy.nan
        cp[pdf_gt_th==0]=numpy.nan

        # Discard (temp,reg) if conditional probability < CP_THRESHOLD
        for reg in numpy.arange(P.shape[0]):
            for Tidx in numpy.arange(P.shape[2]):
                if t_reg_I[reg,Tidx] and cp[reg,:,Tidx][cp[reg,:,Tidx]>=0.0].size>0:
                    if numpy.max(cp[reg,:,Tidx][cp[reg,:,Tidx]>=0])<CP_THRESHOLD:
                        t_reg_I[reg,Tidx]=False
                else:
                    t_reg_I[reg,Tidx]=False

        # Find reference CWV (wr) at which P (or p1) equals PRECIP_REF
        wr=numpy.zeros(t_reg_I.shape)
        for reg in numpy.arange(t_reg_I.shape[0]):
            for Tidx in numpy.arange(t_reg_I.shape[1]):
                if t_reg_I[reg,Tidx]:
                    p_gt_pref=p[reg,:,Tidx]>PRECIP_REF
                    if numpy.nonzero(p_gt_pref)[0].size > 0:  # p_gt_pref non-empty
                        wr_idx=numpy.nonzero(p_gt_pref)[0][0]
                        wr_idx -= (p[reg, wr_idx, Tidx]-PRECIP_REF)/(p[reg,wr_idx,Tidx]-p[reg,wr_idx-1,Tidx])
                        wr[reg,Tidx]=(wr_idx+1)*CWV_BIN_WIDTH
                    else:  #p1<PRECIP_REF, wr doesn't exist/noting to fit
                        wr[reg,Tidx] = numpy.nan
                        t_reg_I[reg, Tidx] = False
                else:
                    wr[reg, Tidx] = numpy.nan
        wr[~t_reg_I] = numpy.nan

        # Temperature range for Fitting & Plotting
        TEMP_MIN = numpy.where(numpy.sum(t_reg_I, axis=0) >= 1)[0][0]
        TEMP_MAX = numpy.where(numpy.sum(t_reg_I, axis=0) >= 1)[0][-1]

        # Start fitting to find Critical CWV (wc)
        #  Working with the assumption that the slope of the asymptote
        #  to the pickup curves do not depend on temperature (as in OBS)
        wc = numpy.zeros(t_reg_I.shape)  # Find wc-wr first, then wc=wr-(wr-wc)
        al = numpy.zeros(t_reg_I.shape[0])  # al:alpha, slope of pickup asymptote
        cwvRange = numpy.linspace(CWV_FIT_RANGE_MIN,
                                  CWV_FIT_RANGE_MAX,
                                  int((CWV_FIT_RANGE_MAX-CWV_FIT_RANGE_MIN)/CWV_BIN_WIDTH + 1))

        # Use the 3 most probable Temperature bins only
        #  These should best capture the pickup over tropical oceans
        #  assuming the model behaves
        for reg in numpy.arange(t_reg_I.shape[0]):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                mpdf = numpy.nansum(PDF[reg, :, :], axis=0) # marginal PDF
            mp3t = sorted(range(len(mpdf)), key=lambda k: mpdf[k])[-3:]
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                p_mp3t=numpy.nanmean(numpy.array([
                    interp1d(cwv_bin_center-wr[reg, mp3t[0]], p[reg, :, mp3t[0]], 'linear', 0, True, False)(cwvRange),
                    interp1d(cwv_bin_center-wr[reg, mp3t[1]], p[reg, :, mp3t[1]], 'linear', 0, True, False)(cwvRange),
                    interp1d(cwv_bin_center-wr[reg, mp3t[2]], p[reg, :, mp3t[2]], 'linear', 0, True, False)(cwvRange)
                ]), axis=0)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fitRange=((p_mp3t>PRECIP_FIT_MIN)*(p_mp3t<PRECIP_FIT_MAX))
            if numpy.nonzero(fitRange)[0].size>1: # Fitting requires at least 2 points
                fitResult=numpy.polyfit(cwvRange[fitRange],p_mp3t[fitRange],1)
                wc[reg,:]=wr[reg,:]-fitResult[1]/fitResult[0] # wc=wr-(wr-wc)
                al[reg]=fitResult[0]
            else: # Can't fit
                wc[reg,:]=numpy.nan
                al[reg]=numpy.nan

        return t_reg_I,wc,al,TEMP_MIN,TEMP_MAX,P,CP,PDF,PDF_pe

    else: # binned data doesn't exist
        return (numpy.array([]), numpy.array([]), numpy.array([]),
                numpy.array([]), numpy.array([]), numpy.array([]),
                numpy.array([]), numpy.array([]), numpy.array([]))

# ======================================================================
# convecTransCriticalCollapse_plot
#  plot two sets for figures for MODEL & OBS 
#  (whenever binned output files exist)

def convecTransCriticalCollapse_plot(argsv1,argsv2,argsv3,argsv4,argsv5,argsv6):

    print("Plotting...")

    cwv_bin_center,\
    temp_bin_center,\
    P0,\
    P1,\
    P2,\
    PE,\
    Q0,\
    Q1,\
    CBW,\
    PT=argsv1

    t_reg_I,\
    wc,\
    al,\
    TEMP_MIN,\
    TEMP_MAX,\
    p1,\
    cp,\
    pdf,\
    pdf_pe=argsv2
    
    cwv_bin_center_obs,\
    temp_bin_center_obs,\
    P0_obs,\
    P1_obs,\
    P2_obs,\
    PE_obs,\
    Q0_obs,\
    Q1_obs,\
    CBW_obs,\
    PT_obs=argsv3

    t_reg_I_obs,\
    wc_obs,\
    al_obs,\
    TEMP_MIN_obs,\
    TEMP_MAX_obs,\
    p1_obs,\
    cp_obs,\
    pdf_obs,\
    pdf_pe_obs=argsv4

    NUMBER_OF_REGIONS,\
    REGION_STR,\
    FIG_OUTPUT_DIR,\
    FIG_FILENAME_CTS,\
    FIG_FILENAME_WC,\
    MODEL,\
    FIG_OBS_DIR,\
    FIG_OBS_FILENAME_CTS,\
    FIG_OBS_FILENAME_WC,\
    OBS,\
    RES,\
    USE_SAME_COLOR_MAP,\
    OVERLAY_OBS_ON_TOP_OF_MODEL_FIG,\
    BULK_TROPOSPHERIC_TEMPERATURE_MEASURE=argsv5
    
    fig_params=argsv6
    
    if p1_obs.size!=0:
        # ======================================================================
        # ======================Start Plot OBS Binned Data======================
        # ======================================================================
        NoC=TEMP_MAX_obs-TEMP_MIN_obs+1 # Number of Colors
        scatter_colors = cm.jet(numpy.linspace(0,1,NoC,endpoint=True))

        axes_fontsize, legend_fonsize, marker_size, xtick_pad, figsize1, figsize2 = fig_params['f0']

        print("   Plotting OBS Figure..."),

        ##### Figure Convective Transition Statistics (CTS) #####
        # create figure canvas
        fig_obs_cts = mp.figure(figsize=(figsize1,figsize2))

        fig_obs_cts.suptitle('Convective Transition Collapsed Statistics'
                             '('+OBS+', '+RES+'$^{\circ}$)', y=1.02, fontsize=16) ##Change y=1.04 to 1.02 for Python3.

        for reg in numpy.arange(NUMBER_OF_REGIONS):
            # create figure 1
            ax1 = fig_obs_cts.add_subplot(NUMBER_OF_REGIONS,4,1+reg*NUMBER_OF_REGIONS)
            ax1.set_xlim(fig_params['f1'][0])
            ax1.set_ylim(fig_params['f1'][1])
            ax1.set_xticks(fig_params['f1'][4])
            ax1.set_yticks(fig_params['f1'][5])
            ax1.tick_params(labelsize=axes_fontsize)
            ax1.tick_params(axis="x", pad=10)
            for Tidx in numpy.arange(TEMP_MIN_obs,TEMP_MAX_obs+1):
                if t_reg_I_obs[reg,Tidx]:
                    if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
                        ax1.scatter(cwv_bin_center_obs-wc_obs[reg,Tidx],p1_obs[reg,:,Tidx],
                                    edgecolor="none",facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:],
                                    s=marker_size,clip_on=True,zorder=3,
                                    label="{:.0f}".format(temp_bin_center_obs[Tidx]))
                    elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
                        ax1.scatter(cwv_bin_center_obs-wc_obs[reg,Tidx],p1_obs[reg,:,Tidx],
                                    edgecolor="none",facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:],
                                    s=marker_size,clip_on=True,zorder=3,
                                    label="{:.1f}".format(temp_bin_center_obs[Tidx]))
            for Tidx in numpy.arange(TEMP_MIN_obs,TEMP_MAX_obs+1):
                if t_reg_I_obs[reg,Tidx]:
                    if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
                        ax1.scatter(Q1_obs[reg,Tidx]/Q0_obs[reg,Tidx]-wc_obs[reg,Tidx],fig_params['f1'][1][1]*0.98,
                                    edgecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:]/2,
                                    facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:],
                                    s=marker_size, clip_on=True, zorder=3, marker="^",
                                    label=': $\widehat{q_{sat}}-w_c$; '\
                                          +'$\widehat{q_{sat}}$: '\
                                           'Column-integrated Saturation Specific Humidity w.r.t. Liquid; '\
                                          +'$w_c$: Estimated Critical Column Water Vapor.')
                    elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
                        ax1.scatter(temp_bin_center_obs[Tidx]-wc_obs[reg,Tidx],fig_params['f1'][1][1]*0.98,
                                    edgecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:]/2,
                                    facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:],
                                    s=marker_size, clip_on=True, zorder=3, marker="^",
                                    label=': $\widehat{q_{sat}}-w_c$; '\
                                          +'$\widehat{q_{sat}}$:'
                                           ' Column-integrated Saturation Specific Humidity w.r.t. Liquid; '\
                                          +'$w_c$: Estimated Critical Column Water Vapor.')
            ax1.plot(numpy.arange(0.,fig_params['f1'][0][1],0.1),
                     al_obs[reg]*numpy.arange(0.,fig_params['f1'][0][1],0.1),
                    '--',color='0.5', zorder=4)
            ax1.set_xlabel(fig_params['f1'][2], fontsize=axes_fontsize)
            ax1.set_ylabel(fig_params['f1'][3], fontsize=axes_fontsize)
            ax1.text(0.4, 0.95, "Slope="+"{:.2f}".format(al_obs[reg]) , transform=ax1.transAxes, fontsize=12, verticalalignment="top")
            ax1.grid()
            ax1.grid(visible=True, which='minor', color='0.8', linestyle='-')
            ax1.set_axisbelow(True)

            handles, labels = ax1.get_legend_handles_labels()
            num_handles = sum(t_reg_I_obs[reg,:])
            leg = ax1.legend(handles[0:num_handles], labels[0:num_handles], fontsize=axes_fontsize,
                             bbox_to_anchor = (0.05, 0.95),
                             bbox_transform=ax1.transAxes, loc="upper left", borderaxespad=0, labelspacing=0.1,
                             fancybox=False,scatterpoints=1,  framealpha=0, borderpad=0,
                             handletextpad=0.1, markerscale=1, ncol=1, columnspacing=0.25)
            ax1.add_artist(leg)
            if reg==0:
                ax1.text(s='Precip. cond. avg. on CWV', x=0.5, y=1.05, transform=ax1.transAxes,
                         fontsize=12, ha='center', va='bottom')

            # create figure 2 (probability pickup)
            ax2 = fig_obs_cts.add_subplot(NUMBER_OF_REGIONS,4,2+reg*NUMBER_OF_REGIONS)
            ax2.set_xlim(fig_params['f2'][0])
            ax2.set_ylim(fig_params['f2'][1])
            ax2.set_xticks(fig_params['f2'][4])
            ax2.set_yticks(fig_params['f2'][5])
            ax2.tick_params(labelsize=axes_fontsize)
            ax2.tick_params(axis="x", pad=xtick_pad)
            for Tidx in numpy.arange(TEMP_MIN_obs,TEMP_MAX_obs+1):
                if t_reg_I_obs[reg,Tidx]:
                    ax2.scatter(cwv_bin_center_obs-wc_obs[reg,Tidx],cp_obs[reg,:,Tidx],
                                edgecolor="none", facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:],
                                s=marker_size, clip_on=True, zorder=3)
            for Tidx in numpy.arange(TEMP_MIN_obs,TEMP_MAX_obs+1):
                if t_reg_I_obs[reg,Tidx]:
                    if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
                        ax2.scatter(Q1_obs[reg,Tidx]/Q0_obs[reg,Tidx]-wc_obs[reg,Tidx],fig_params['f2'][1][1]*0.98,
                                    edgecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:]/2,
                                    facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:],
                                    s=marker_size, clip_on=True, zorder=3, marker="^")
                    elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
                        ax2.scatter(temp_bin_center_obs[Tidx]-wc_obs[reg,Tidx],fig_params['f2'][1][1]*0.98,
                                    edgecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:]/2,
                                    facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:],
                                    s=marker_size,clip_on=True,zorder=3,marker="^")
            ax2.set_xlabel(fig_params['f2'][2], fontsize=axes_fontsize)
            ax2.set_ylabel(fig_params['f2'][3], fontsize=axes_fontsize)
            ax2.text(0.05, 0.95, REGION_STR[reg], transform=ax2.transAxes,
                     fontsize=12, fontweight="bold", verticalalignment="top")
            ax2.grid()
            ax2.grid(visible=True, which='minor', color='0.8', linestyle='-')
            ax2.set_axisbelow(True)
            if reg==0:
                ax2.text(s='Prob. of Precip.>'+str(PT_obs)+'mm/h', x=0.5, y=1.05,
                         transform=ax2.transAxes, fontsize=12, ha='center', va='bottom')

            # create figure 3 (normalized PDF)
            ax3 = fig_obs_cts.add_subplot(NUMBER_OF_REGIONS,4,3+reg*NUMBER_OF_REGIONS)
            ax3.set_yscale("log")
            ax3.set_xlim(fig_params['f3'][0])
            ax3.set_ylim(fig_params['f3'][1])
            ax3.set_xticks(fig_params['f3'][4])
            ax3.tick_params(labelsize=axes_fontsize)
            ax3.tick_params(axis="x", pad=xtick_pad)
            for Tidx in numpy.arange(TEMP_MIN_obs,TEMP_MAX_obs+1):
                if t_reg_I_obs[reg,Tidx]:
                    PDFNormalizer=pdf_obs[reg,numpy.where(cwv_bin_center_obs<=wc_obs[reg,Tidx])[0][-1],Tidx]
                    ax3.scatter(cwv_bin_center_obs-wc_obs[reg,Tidx],pdf_obs[reg,:,Tidx]/PDFNormalizer,
                                edgecolor="none", facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:],
                                s=marker_size, clip_on=True, zorder=3)
            for Tidx in numpy.arange(TEMP_MIN_obs, TEMP_MAX_obs+1):
                if t_reg_I_obs[reg,Tidx]:
                    if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
                        ax3.scatter(Q1_obs[reg,Tidx]/Q0_obs[reg,Tidx]-wc_obs[reg, Tidx], fig_params['f3'][1][1]*0.83,
                                    edgecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC, :]/2,
                                    facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC, :],
                                    s=marker_size, clip_on=True, zorder=3, marker="^")
                    elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
                        ax3.scatter(temp_bin_center_obs[Tidx]-wc_obs[reg, Tidx], fig_params['f3'][1][1]*0.83,
                                    edgecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC, :]/2,
                                    facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC, :],
                                    s=marker_size,clip_on=True,zorder=3,marker="^")
            ax3.set_xlabel(fig_params['f3'][2], fontsize=axes_fontsize)
            ax3.set_ylabel(fig_params['f3'][3], fontsize=axes_fontsize)
            ax3.grid()
            ax3.grid(visible=True, which='minor', color='0.8', linestyle='-')
            ax3.set_axisbelow(True)
            if reg == 0:
                ax3.text(s='PDF of CWV', x=0.5, y=1.05, transform=ax3.transAxes,
                         fontsize=12, ha='center', va='bottom')

            # create figure 4 (normalized PDF - precipitation)
            ax4 = fig_obs_cts.add_subplot(NUMBER_OF_REGIONS, 4, 4 + reg*NUMBER_OF_REGIONS)
            ax4.set_yscale("log")
            ax4.set_xlim(fig_params['f4'][0])
            ax4.set_ylim(fig_params['f4'][1])
            ax4.set_xticks(fig_params['f4'][4])
            ax4.tick_params(labelsize=axes_fontsize)
            ax4.tick_params(axis="x", pad=xtick_pad)
            for Tidx in numpy.arange(TEMP_MIN_obs, TEMP_MAX_obs+1):
                if t_reg_I_obs[reg,Tidx]:
                    PDFNormalizer=pdf_obs[reg, numpy.where(cwv_bin_center_obs <= wc_obs[reg,Tidx])[0][-1], Tidx]
                    ax4.scatter(cwv_bin_center_obs-wc_obs[reg,Tidx],pdf_pe_obs[reg, :, Tidx]/PDFNormalizer,
                                edgecolor="none", facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC, :],
                                s=marker_size, clip_on=True, zorder=3)
            for Tidx in numpy.arange(TEMP_MIN_obs,TEMP_MAX_obs+1):
                if t_reg_I_obs[reg,Tidx]:
                    if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
                        ax4.scatter(Q1_obs[reg,Tidx]/Q0_obs[reg,Tidx]-wc_obs[reg, Tidx],
                                    fig_params['f4'][1][1]*0.83,
                                    edgecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC, :]/2,
                                    facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC, :],
                                    s=marker_size, clip_on=True, zorder=3, marker="^")
                    elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
                        ax4.scatter(temp_bin_center_obs[Tidx]-wc_obs[reg,Tidx], fig_params['f4'][1][1]*0.83,
                                    edgecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:]/2,
                                    facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:],
                                    s=marker_size, clip_on=True, zorder=3, marker="^")
            ax4.set_xlabel(fig_params['f4'][2], fontsize=axes_fontsize)
            ax4.set_ylabel(fig_params['f4'][3], fontsize=axes_fontsize)
            ax4.text(0.05, 0.95, "Precip > "+str(PT_obs)+" mm h$^-$$^1$",
                     transform=ax4.transAxes, fontsize=12, verticalalignment="top")
            ax4.grid()
            ax4.grid(visible=True, which='minor', color='0.8', linestyle='-')
            ax4.set_axisbelow(True)
            if reg==0:
                ax4.text(s='PDF of CWV for Precip.>'+str(PT_obs)+'mm/hr', x=0.49, y=1.05,
                         transform=ax4.transAxes, fontsize=12, ha='center', va='bottom')

        if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
            temp_str='$\widehat{T}$ (1000-200hPa Mass-weighted Column Average Temperature)' \
                     ' used as the bulk tropospheric temperature measure'
        elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
            temp_str='$\widehat{q_{sat}}$ (1000-200hPa Column-integrated Saturation Specific Humidity)' \
                     'used as the bulk tropospheric temperature measure'
        fig_obs_cts.text(s=temp_str, x=0, y=0, ha='left', va='top', transform=fig_obs_cts.transFigure, fontsize=12)

        triag_qsat_str = '$\Delta$: $\widehat{q_{sat}}-w_c$;' \
                         ' $\widehat{q_{sat}}$: 1000-200hPa Column-integrated Saturation Specific Humidity' \
                         ' w.r.t. Liquid; $w_c$: Estimated Critical Column Water Vapor; units: mm.'
        triag_qsat_str += '\n$w_c$ estimated by fitting (dashed) the average precip.' \
                          ' pickup curves for the 3 most probable temperature bins'
        fig_obs_cts.text(s=triag_qsat_str, x=0, y=-0.02, ha='left', va='top',
                         transform=fig_obs_cts.transFigure, fontsize=12)

        # set layout to tight (so that space between figures is minimized)
        fig_obs_cts.tight_layout()
        fig_obs_cts.savefig(FIG_OBS_DIR+"/"+FIG_OBS_FILENAME_CTS, bbox_inches="tight")

        # Figure Critical CWV (WC) #####
        fig_obs_wc = mp.figure(figsize=(figsize1/1.5, figsize2/2.6))

        fig_obs_wc.suptitle('Critical CWV, Col. Satn., & Critical Col. RH (' + OBS + ', ' + RES + '$^{\circ}$)',
                            y=1.02, fontsize=16)

        reg_color=[-1,-2,-3,0]

        # create figure 5: wc
        ax1 = fig_obs_wc.add_subplot(1,2,1)
        ax1.set_xlim(fig_params['f5'][0])
        ax1.set_ylim(fig_params['f5'][1])
        ax1.set_xticks(fig_params['f5'][4])
        ax1.set_yticks(fig_params['f5'][5])
        ax1.tick_params(labelsize=axes_fontsize)
        ax1.tick_params(axis="x", pad=10)
        ax1.set_aspect(float(fig_params['f5'][0][1]-fig_params['f5'][0][0])/float(fig_params['f5'][1][1]
                                                                                  -fig_params['f5'][1][0]))
        for reg in numpy.arange(NUMBER_OF_REGIONS):
            ax1.plot(temp_bin_center_obs,wc_obs[reg,:],'-',color=scatter_colors[reg_color[reg],:])
            if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    ax1.plot(temp_bin_center_obs,Q1_obs[reg,:]/Q0_obs[reg,:], '-',
                             color=scatter_colors[reg_color[reg],:])
            elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
                ax1.plot(temp_bin_center_obs,temp_bin_center_obs,'-',color='0.4')
            ax1.scatter(temp_bin_center_obs,wc_obs[reg,:],color=scatter_colors[reg_color[reg],:],
                        s=marker_size,clip_on=True,zorder=3,label=REGION_STR[reg])
        handles, labels = ax1.get_legend_handles_labels()
        leg = ax1.legend(handles, labels, fontsize=axes_fontsize, bbox_to_anchor=(0.05,0.95),
                         bbox_transform=ax1.transAxes, loc="upper left", borderaxespad=0, labelspacing=0.5,
                         fancybox=False,scatterpoints=1,  framealpha=0, borderpad=0,
                         handletextpad=0.1, markerscale=1, ncol=1, columnspacing=0.25)
        ax1.text(0.3, 0.2, OBS, transform=ax1.transAxes, fontsize=12, fontweight="bold", verticalalignment="top")
        ax1.text(0.3, 0.1, RES+"$^{\circ}$", transform=ax1.transAxes, fontsize=12,
                 fontweight="bold", verticalalignment="top")
        ax1.set_xlabel(fig_params['f5'][2], fontsize=axes_fontsize)
        ax1.set_ylabel(fig_params['f5'][3], fontsize=axes_fontsize)
        ax1.grid()
        ax1.set_axisbelow(True)
        ax1.text(s='Critical CWV & Col. Satn.', x=0.5, y=1.02, transform=ax1.transAxes,
                 fontsize=12, ha='center', va='bottom')

        # create figure 6: wc/qsat_int
        ax2 = fig_obs_wc.add_subplot(1,2,2)
        ax2.set_xlim(fig_params['f6'][0])
        ax2.set_ylim(fig_params['f6'][1])
        ax2.set_xticks(fig_params['f6'][4])
        ax2.set_yticks(fig_params['f6'][5])
        ax2.tick_params(labelsize=axes_fontsize)
        ax2.tick_params(axis="x", pad=10)
        ax2.set_aspect(float(fig_params['f6'][0][1]-fig_params['f5'][0][0])/float(fig_params['f6'][1][1]
                                                                                  -fig_params['f6'][1][0]))
        for reg in numpy.arange(NUMBER_OF_REGIONS):
            if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    ax2.plot(temp_bin_center_obs,wc_obs[reg,:]/(Q1_obs[reg,:]/Q0_obs[reg,:]),'-',
                             color=scatter_colors[reg_color[reg],:])
                    ax2.scatter(temp_bin_center_obs,wc_obs[reg,:]/(Q1_obs[reg,:]/Q0_obs[reg,:]),
                                color=scatter_colors[reg_color[reg],:],
                                s=marker_size,clip_on=True,zorder=3,label=REGION_STR[reg])
            elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
                ax2.plot(temp_bin_center_obs,wc_obs[reg,:]/temp_bin_center_obs,'-',
                         color=scatter_colors[reg_color[reg],:])
                ax2.scatter(temp_bin_center_obs,wc_obs[reg,:]/temp_bin_center_obs,
                            color=scatter_colors[reg_color[reg],:],
                            s=marker_size, clip_on=True, zorder=3, label=REGION_STR[reg])
        handles, labels = ax2.get_legend_handles_labels()
        leg = ax2.legend(handles, labels, fontsize=axes_fontsize, bbox_to_anchor=(0.6, 0.95),
                         bbox_transform=ax2.transAxes, loc="upper left", borderaxespad=0, labelspacing=0.5,
                         fancybox=False,scatterpoints=1,  framealpha=0, borderpad=0,
                         handletextpad=0.1, markerscale=1, ncol=1, columnspacing=0.25)
        ax2.text(0.15, 0.2, OBS, transform=ax2.transAxes, fontsize=12, fontweight="bold", verticalalignment="top")
        ax2.text(0.15, 0.1, RES+"$^{\circ}$", transform=ax2.transAxes,
                 fontsize=12, fontweight="bold", verticalalignment="top")
        ax2.set_xlabel(fig_params['f6'][2], fontsize=axes_fontsize)
        ax2.set_ylabel(fig_params['f6'][3], fontsize=axes_fontsize)
        ax2.grid()
        ax2.set_axisbelow(True)
        ax2.text(s='Critical Col. RH', x=0.5, y=1.02, transform=ax2.transAxes,
                 fontsize=12, ha='center', va='bottom')

        footnote_str='Solid line: $\widehat{q_{sat}}$' \
                     ' (1000-200hPa Column-integrated Saturation Specific Humidity w.r.t. Liquid)\n'
        if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
            footnote_str+='$\widehat{T}$' \
                          ' (1000-200hPa Mass-weighted Column Average Temperature)' \
                          ' as the bulk tropospheric temperature measure'
        elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
            footnote_str+='$\widehat{q_{sat}}$ (1000-200hPa Column-integrated Saturation Specific Humidity)' \
                          ' as the bulk tropospheric temperature measure'
        footnote_str+='\n$w_c$ estimated by fitting (dashed) the average precip. ' \
                      'pickup curves for the 3 most probable temperature bins'
        #ax1.text(s=footnote_str, x=0, y=-0.02, transform=fig_obs_wc.transFigure, ha='left', va='top', fontsize=12)

        # set layout to tight (so that space between figures is minimized)
        fig_obs_wc.tight_layout()
        fig_obs_wc.savefig(FIG_OBS_DIR+"/"+FIG_OBS_FILENAME_WC, bbox_inches="tight")

        print("...Completed!")
        print("      OBS Figure saved as "+FIG_OBS_DIR+"/"+FIG_OBS_FILENAME_CTS+"!")
        print("      OBS Figure saved as "+FIG_OBS_DIR+"/"+FIG_OBS_FILENAME_WC+"!")
        # ======================================================================
        # =======================End Plot OBS Binned Data=======================
        # ======================================================================    

    # Use OBS to set colormap (but if they don't exist or users don't want to...)
    if p1_obs.siz == 0 or not  USE_SAME_COLOR_MAP:
        TEMP_MIN_obs = TEMP_MIN
        TEMP_MAX_obs = TEMP_MAX

    # ======================================================================
    # =====================Start Plot MODEL Binned Data=====================
    # ======================================================================
    NoC = TEMP_MAX_obs-TEMP_MIN_obs + 1  # Number of Colors
    scatter_colors = cm.jet(numpy.linspace(0, 1, NoC, endpoint=True))

    axes_fontsize, legend_fonsize, marker_size, xtick_pad, figsize1, figsize2 = fig_params['f0']

    print("   Plotting MODEL Figure..."),

    # Figure Convective Transition Statistics (CTS) #####
    # create figure canvas
    fig_cts = mp.figure(figsize=(figsize1, figsize2))
    
    fig_cts.suptitle('Convective Transition Collapsed Statistics (' + MODEL + ')', y=1.02, fontsize=16)

    for reg in numpy.arange(NUMBER_OF_REGIONS):
        # create figure 1
        ax1 = fig_cts.add_subplot(NUMBER_OF_REGIONS, 4, 1 + reg*NUMBER_OF_REGIONS)
        ax1.set_xlim(fig_params['f1'][0])
        ax1.set_ylim(fig_params['f1'][1])
        ax1.set_xticks(fig_params['f1'][4])
        ax1.set_yticks(fig_params['f1'][5])
        ax1.tick_params(labelsize=axes_fontsize)
        ax1.tick_params(axis="x", pad=10)
        for Tidx in numpy.arange(TEMP_MIN, TEMP_MAX + 1):
            if t_reg_I[reg, Tidx]:
                if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE == 1:
                    ax1.scatter(cwv_bin_center-wc[reg, Tidx], p1[reg, :, Tidx],
                                edgecolor="none", facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC, :],
                                s=marker_size, clip_on=True, zorder=3,
                                label="{:.0f}".format(temp_bin_center[Tidx]))
                elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE == 2:
                    ax1.scatter(cwv_bin_center-wc[reg,Tidx],p1[reg,:,Tidx],
                                edgecolor="none",facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC, :],
                                s=marker_size,clip_on=True,zorder=3,
                                label="{:.1f}".format(temp_bin_center[Tidx]))
        for Tidx in numpy.arange(TEMP_MIN, TEMP_MAX+1):
            if t_reg_I[reg, Tidx]:
                if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE == 1:
                    ax1.scatter(Q1[reg,Tidx]/Q0[reg,Tidx]-wc[reg,Tidx],fig_params['f1'][1][1]*0.98,
                                edgecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC, :]/2,
                                facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC, :],
                                s=marker_size,clip_on=True,zorder=3,marker='^',
                                label=': $\widehat{q_{sat}}-w_c$; ' +\
                                      '$\widehat{q_{sat}}$: Column-integrated Saturation Specific Humidity' +\
                                      ' w.r.t. Liquid; ' +\
                                      '$w_c$: Estimated Critical Column Water Vapor.')
                elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
                    ax1.scatter(temp_bin_center[Tidx]-wc[reg,Tidx],fig_params['f1'][1][1]*0.98,
                                edgecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:]/2,
                                facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:],
                                s=marker_size,clip_on=True,zorder=3,marker='^',
                                label=': $\widehat{q_{sat}}-w_c$; '\
                                      +'$\widehat{q_{sat}}$: Column-integrated Saturation Specific Humidity'
                                       ' w.r.t. Liquid; '\
                                      +'$w_c$: Estimated Critical Column Water Vapor.')
        ax1.plot(numpy.arange(0.,fig_params['f1'][0][1],0.1),al[reg]*numpy.arange(0.,fig_params['f1'][0][1],0.1),
                    '--',color='0.5', zorder=4)
        ax1.set_xlabel(fig_params['f1'][2], fontsize=axes_fontsize)
        ax1.set_ylabel(fig_params['f1'][3], fontsize=axes_fontsize)
        ax1.text(0.4, 0.95, "Slope="+"{:.2f}".format(al[reg]), transform=ax1.transAxes,
                 fontsize=12, verticalalignment="top")
        ax1.grid()
        ax1.grid(visible=True, which='minor', color='0.8', linestyle='-')
        ax1.set_axisbelow(True)

        handles, labels = ax1.get_legend_handles_labels()
        num_handles = sum(t_reg_I[reg,:])
        leg = ax1.legend(handles[0:num_handles], labels[0:num_handles], fontsize=axes_fontsize,
                         bbox_to_anchor=(0.05,0.95),
                         bbox_transform=ax1.transAxes, loc="upper left", borderaxespad=0, labelspacing=0.1,
                         fancybox=False,scatterpoints=1,  framealpha=0, borderpad=0,
                         handletextpad=0.1, markerscale=1, ncol=1, columnspacing=0.25)
        ax1.add_artist(leg)
        if reg==0:
            ax1.text(s='Precip. cond. avg. on CWV', x=0.5, y=1.05, transform=ax1.transAxes,
                     fontsize=12, ha='center', va='bottom')
        # create figure 2 (probability pickup)
        ax2 = fig_cts.add_subplot(NUMBER_OF_REGIONS,4,2+reg*NUMBER_OF_REGIONS)
        ax2.set_xlim(fig_params['f2'][0])
        ax2.set_ylim(fig_params['f2'][1])
        ax2.set_xticks(fig_params['f2'][4])
        ax2.set_yticks(fig_params['f2'][5])
        ax2.tick_params(labelsize=axes_fontsize)
        ax2.tick_params(axis="x", pad=xtick_pad)
        for Tidx in numpy.arange(TEMP_MIN,TEMP_MAX+1):
            if t_reg_I[reg,Tidx]:
                ax2.scatter(cwv_bin_center-wc[reg,Tidx],cp[reg,:,Tidx],
                            edgecolor="none",facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:],
                            s=marker_size,clip_on=True,zorder=3)
        for Tidx in numpy.arange(TEMP_MIN,TEMP_MAX+1):
            if t_reg_I[reg,Tidx]:
                if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
                    ax2.scatter(Q1[reg,Tidx]/Q0[reg,Tidx]-wc[reg,Tidx],fig_params['f2'][1][1]*0.98,
                                edgecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:]/2,
                                facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:],
                                s=marker_size,clip_on=True,zorder=3,marker="^")
                elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
                    ax2.scatter(temp_bin_center[Tidx]-wc[reg,Tidx],fig_params['f2'][1][1]*0.98,
                                edgecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:]/2,
                                facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:],
                                s=marker_size,clip_on=True,zorder=3,marker="^")
        ax2.set_xlabel(fig_params['f2'][2], fontsize=axes_fontsize)
        ax2.set_ylabel(fig_params['f2'][3], fontsize=axes_fontsize)
        ax2.text(0.05, 0.95, REGION_STR[reg], transform=ax2.transAxes,
                 fontsize=12, fontweight="bold", verticalalignment="top")
        ax2.grid()
        ax2.grid(visible=True, which='minor', color='0.8', linestyle='-')
        ax2.set_axisbelow(True)
        if reg==0:
            ax2.text(s='Prob. of Precip.>'+str(PT)+'mm/h', x=0.5, y=1.05,
                     transform=ax2.transAxes, fontsize=12, ha='center', va='bottom')

        # create figure 3 (normalized PDF)
        ax3 = fig_cts.add_subplot(NUMBER_OF_REGIONS,4,3+reg*NUMBER_OF_REGIONS)
        ax3.set_yscale("log")
        ax3.set_xlim(fig_params['f3'][0])
        ax3.set_ylim(fig_params['f3'][1])
        ax3.set_xticks(fig_params['f3'][4])
        ax3.tick_params(labelsize=axes_fontsize)
        ax3.tick_params(axis="x", pad=xtick_pad)
        for Tidx in numpy.arange(TEMP_MIN,TEMP_MAX+1):
            if t_reg_I[reg,Tidx]:
                PDFNormalizer=pdf[reg,numpy.where(cwv_bin_center<=wc[reg,Tidx])[0][-1],Tidx]
                ax3.scatter(cwv_bin_center-wc[reg,Tidx],pdf[reg,:,Tidx]/PDFNormalizer,
                            edgecolor="none",facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:],
                            s=marker_size,clip_on=True,zorder=3)
        for Tidx in numpy.arange(TEMP_MIN,TEMP_MAX+1):
            if t_reg_I[reg,Tidx]:
                if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
                    ax3.scatter(Q1[reg,Tidx]/Q0[reg,Tidx]-wc[reg,Tidx],fig_params['f3'][1][1]*0.83,
                                edgecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:]/2,
                                facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:],
                                s=marker_size,clip_on=True,zorder=3,marker="^")
                elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
                    ax3.scatter(temp_bin_center[Tidx]-wc[reg,Tidx],fig_params['f3'][1][1]*0.83,
                                edgecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:]/2,
                                facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:],
                                s=marker_size,clip_on=True,zorder=3,marker="^")
        ax3.set_xlabel(fig_params['f3'][2], fontsize=axes_fontsize)
        ax3.set_ylabel(fig_params['f3'][3], fontsize=axes_fontsize)
        ax3.grid()
        ax3.grid(visible=True, which='minor', color='0.8', linestyle='-')
        ax3.set_axisbelow(True)
        if reg==0:
            ax3.text(s='PDF of CWV', x=0.5, y=1.05, transform=ax3.transAxes, fontsize=12, ha='center', va='bottom')

        # create figure 4 (normalized PDF - precipitation)
        ax4 = fig_cts.add_subplot(NUMBER_OF_REGIONS,4,4+reg*NUMBER_OF_REGIONS)
        ax4.set_yscale("log")
        ax4.set_xlim(fig_params['f4'][0])
        ax4.set_ylim(fig_params['f4'][1])
        ax4.set_xticks(fig_params['f4'][4])
        ax4.tick_params(labelsize=axes_fontsize)
        ax4.tick_params(axis="x", pad=xtick_pad)
        for Tidx in numpy.arange(TEMP_MIN,TEMP_MAX+1):
            if t_reg_I[reg,Tidx]:
                PDFNormalizer=pdf[reg, numpy.where(cwv_bin_center <= wc[reg,Tidx])[0][-1], Tidx]
                ax4.scatter(cwv_bin_center-wc[reg,Tidx],pdf_pe[reg, :, Tidx]/PDFNormalizer,
                            edgecolor="none", facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC, :],
                            s=marker_size, clip_on=True, zorder=3)
        for Tidx in numpy.arange(TEMP_MIN, TEMP_MAX + 1):
            if t_reg_I[reg, Tidx]:
                if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE == 1:
                    ax4.scatter(Q1[reg,Tidx]/Q0[reg,Tidx]-wc[reg,Tidx],fig_params['f4'][1][1]*0.83,
                                edgecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC, :]/2,
                                facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC, :],
                                s=marker_size, clip_on=True, zorder=3, marker="^")
                elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE == 2:
                    ax4.scatter(temp_bin_center[Tidx]-wc[reg, Tidx], fig_params['f4'][1][1]*0.83,
                                edgecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:]/2,
                                facecolor=scatter_colors[(Tidx-TEMP_MIN_obs)%NoC,:],
                                s=marker_size,clip_on=True,zorder=3,marker="^")
        ax4.set_xlabel(fig_params['f4'][2], fontsize=axes_fontsize)
        ax4.set_ylabel(fig_params['f4'][3], fontsize=axes_fontsize)
        ax4.text(0.05, 0.95, "Precip > "+str(PT)+" mm hr$^-$$^1$",
                 transform=ax4.transAxes, fontsize=12, verticalalignment="top")
        ax4.grid()
        ax4.grid(visible=True, which='minor', color='0.8', linestyle='-')
        ax4.set_axisbelow(True)
        if reg==0:
            ax4.text(s='PDF of CWV for Precip.>'+str(PT)+'mm/hr', x=0.49, y=1.05, transform=ax4.transAxes, fontsize=12,
                     ha='center', va='bottom')

    if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
        temp_str='$\widehat{T}$ (1000-200hPa Mass-weighted Column Average Temperature)' \
                 ' used as the bulk tropospheric temperature measure'
    elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
        temp_str='$\widehat{q_{sat}}$ (1000-200hPa Column-integrated Saturation Specific Humidity)' \
                 ' used as the bulk tropospheric temperature measure'
    fig_cts.text(s=temp_str, x=0, y=0, ha='left', va='top', transform=fig_cts.transFigure, fontsize=12)

    triag_qsat_str = '$\Delta$: $\widehat{q_{sat}}-w_c$; $\widehat{q_{sat}}$:' \
                     ' 1000-200hPa Column-integrated Saturation Specific Humidity w.r.t.' \
                     ' Liquid; $w_c$: Estimated Critical Column Water Vapor; units: mm.'
    triag_qsat_str += '\n$w_c$ estimated by fitting (dashed) the average precip.' \
                      ' pickup curves for the 3 most probable temperature bins'
    fig_cts.text(s=triag_qsat_str, x=0, y=-0.02, ha='left', va='top', transform=fig_cts.transFigure, fontsize=12)

    # set layout to tight (so that space between figures is minimized)
    fig_cts.tight_layout()
    fig_cts.savefig(FIG_OUTPUT_DIR+"/"+FIG_FILENAME_CTS, bbox_inches="tight")

    ##### Figure Critical CWV (WC) #####
    fig_wc = mp.figure(figsize=(figsize1/1.5,figsize2/2.6))

    fig_wc.suptitle('Critical CWV, Col. Satn., & Critical Col. RH ('+MODEL+')', y=1.02, fontsize=16)

    reg_color=[-1,-2,-3,0]

    # create figure 5: wc
    ax1 = fig_wc.add_subplot(1,2,1)
    ax1.set_xlim(fig_params['f5'][0])
    ax1.set_ylim(fig_params['f5'][1])
    ax1.set_xticks(fig_params['f5'][4])
    ax1.set_yticks(fig_params['f5'][5])
    ax1.tick_params(labelsize=axes_fontsize)
    ax1.tick_params(axis="x", pad=10)
    ax1.set_aspect(float(fig_params['f5'][0][1]-fig_params['f5'][0][0])/float(fig_params['f5'][1][1]
                                                                              -fig_params['f5'][1][0]))
    if OVERLAY_OBS_ON_TOP_OF_MODEL_FIG and p1_obs.size != 0:
        for reg in numpy.arange(NUMBER_OF_REGIONS):
            ax1.plot(temp_bin_center_obs,wc_obs[reg,:],'-',color='0.6')
            ax1.scatter(temp_bin_center_obs,wc_obs[reg,:],color='0.6',s=marker_size,clip_on=True,zorder=3)
            if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    ax1.plot(temp_bin_center_obs,Q1_obs[reg,:]/Q0_obs[reg,:],'-',color='0.6')
    for reg in numpy.arange(NUMBER_OF_REGIONS):
        ax1.plot(temp_bin_center,wc[reg, :],'-',color=scatter_colors[reg_color[reg],:])
        if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE == 1:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ax1.plot(temp_bin_center,Q1[reg,:]/Q0[reg,:],'-',color=scatter_colors[reg_color[reg],:])
        elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE == 2:
            ax1.plot(temp_bin_center,temp_bin_center,'-',color='0.4')
        ax1.scatter(temp_bin_center,wc[reg,:],color=scatter_colors[reg_color[reg], :],
                    s=marker_size,clip_on=True,zorder=3, label=REGION_STR[reg])
    handles, labels = ax1.get_legend_handles_labels()
    leg = ax1.legend(handles, labels, fontsize=axes_fontsize, bbox_to_anchor=(0.05, 0.95),
                     bbox_transform=ax1.transAxes, loc="upper left", borderaxespad=0, labelspacing=0.5,
                     fancybox=False,scatterpoints=1,  framealpha=0, borderpad=0,
                     handletextpad=0.1, markerscale=1, ncol=1, columnspacing=0.25)

    if OVERLAY_OBS_ON_TOP_OF_MODEL_FIG and p1_obs.size != 0:
        ax1.text(0.3, 0.2, OBS, transform=ax1.transAxes, fontsize=12,
                 fontweight="bold", verticalalignment="top", color='0.6')
        ax1.text(0.3, 0.1, RES+"$^{\circ}$", transform=ax1.transAxes,
                 fontsize=12, fontweight="bold", verticalalignment="top", color='0.6')
    ax1.set_xlabel(fig_params['f5'][2], fontsize=axes_fontsize)
    ax1.set_ylabel(fig_params['f5'][3], fontsize=axes_fontsize)
    ax1.grid()
    ax1.set_axisbelow(True)
    ax1_text = ax1.text(s='Critical CWV & Col. Satn.', x=0.5, y=1.02,
                        transform=ax1.transAxes, fontsize=12,
                        ha='center', va='bottom')

    # create figure 6: wc/qsat_int
    ax2 = fig_wc.add_subplot(1, 2, 2)
    ax2.set_xlim(fig_params['f6'][0])
    ax2.set_ylim(fig_params['f6'][1])
    ax2.set_xticks(fig_params['f6'][4])
    ax2.set_yticks(fig_params['f6'][5])
    ax2.tick_params(labelsize=axes_fontsize)
    ax2.tick_params(axis="x", pad=10)
    ax2.set_aspect(float(fig_params['f6'][0][1]-fig_params['f5'][0][0])/float(fig_params['f6'][1][1]
                                                                              -fig_params['f6'][1][0]))
    if OVERLAY_OBS_ON_TOP_OF_MODEL_FIG and p1_obs.size!=0:
        for reg in numpy.arange(NUMBER_OF_REGIONS):
            if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    ax2.plot(temp_bin_center_obs, wc_obs[reg,:]/(Q1_obs[reg,:]/Q0_obs[reg,:]),'-',color='0.6')
                    ax2.scatter(temp_bin_center_obs, wc_obs[reg,:]/(Q1_obs[reg,:]/Q0_obs[reg,:]),color='0.6',
                            s=marker_size,clip_on=True,zorder=3)
            elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
                ax2.plot(temp_bin_center_obs,wc_obs[reg,:]/temp_bin_center_obs,'-',color='0.6')
                ax2.scatter(temp_bin_center_obs,wc_obs[reg,:]/temp_bin_center_obs,color='0.6',
                            s=marker_size,clip_on=True,zorder=3)
    for reg in numpy.arange(NUMBER_OF_REGIONS):
        if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
            with warnings.catch_warnings():
              warnings.simplefilter("ignore")
              ax2.plot(temp_bin_center ,wc[reg,:]/(Q1[reg, :]/Q0[reg, :]),'-', color=scatter_colors[reg_color[reg], :])
              ax2.scatter(temp_bin_center, wc[reg, :]/(Q1[reg,:]/Q0[reg, :]), color=scatter_colors[reg_color[reg], :],
                          s=marker_size,clip_on=True,zorder=3,label=REGION_STR[reg])
        elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
            ax2.plot(temp_bin_center, wc[reg, :]/temp_bin_center, '-', color=scatter_colors[reg_color[reg], :])
            ax2.scatter(temp_bin_center, wc[reg, :]/temp_bin_center, color=scatter_colors[reg_color[reg], :],
                        s=marker_size, clip_on=True,zorder=3, label=REGION_STR[reg])
    leg = ax2.legend(handles, labels, fontsize=axes_fontsize, bbox_to_anchor=(0.6, 0.95),
                     bbox_transform=ax2.transAxes, loc="upper left", borderaxespad=0, labelspacing=0.5,
                     fancybox=False,scatterpoints=1,  framealpha=0, borderpad=0,
                     handletextpad=0.1, markerscale=1, ncol=1, columnspacing=0.25)
    if OVERLAY_OBS_ON_TOP_OF_MODEL_FIG and p1_obs.size != 0:
        ax2.text(0.15, 0.2, OBS, transform=ax2.transAxes, fontsize=12, fontweight="bold",
                 verticalalignment="top",color='0.6')
        ax2.text(0.15, 0.1, RES + "$^{\circ}$", transform=ax2.transAxes, fontsize=12, fontweight="bold",
                 verticalalignment="top",color='0.6')
    ax2.set_xlabel(fig_params['f6'][2], fontsize=axes_fontsize)
    ax2.set_ylabel(fig_params['f6'][3], fontsize=axes_fontsize)
    ax2.grid()
    ax2.set_axisbelow(True)
    ax2_text = ax2.text(s='Critical Col. RH', x=0.5, y=1.02, transform=ax2.transAxes, fontsize=12, ha='center',
                        va='bottom')

    footnote_str = ('Solid line: $\widehat{q_{sat}}$ (1000-200hPa Column-integrated Saturation'
                    ' Specific Humidity w.r.t. Liquid)\n')
    if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE == 1:
        footnote_str += ('$\widehat{T}$ (1000-200hPa Mass-weighted Column Average Temperature)'
                         ' as the bulk tropospheric temperature measure')
    elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE == 2:
        footnote_str += ('$\widehat{q_{sat}}$ (1000-200hPa Column-integrated Saturation Specific Humidity)'
                         ' as the bulk tropospheric temperature measure')
    footnote_str += ('\n$w_c$ estimated by fitting (dashed) the average precip.'
                   ' pickup curves for the 3 most probable temperature bins')
    if OVERLAY_OBS_ON_TOP_OF_MODEL_FIG and p1_obs.size != 0:
        footnote_str += ('\nCorresponding results from ' + OBS +
                         ' (spatial resolution: ' + RES + '$^{\circ}$) plotted in gray')

    # set layout to tight (so that space between figures is minimized)
    fig_wc.tight_layout()
    fig_wc.savefig(FIG_OUTPUT_DIR + "/" + FIG_FILENAME_WC, bbox_inches="tight")
    
    print("...Completed!")
    print(" MODEL Figure saved as " + FIG_OUTPUT_DIR + "/" + FIG_FILENAME_CTS + "!")
    print(" MODEL Figure saved as " + FIG_OUTPUT_DIR + "/" + FIG_FILENAME_WC + "!")
    # ======================================================================
    # ======================End Plot MODEL Binned Data======================
    # ======================================================================
