;----------------------------------------------------------------------
; These functions and procedures are for paneling two sets of contour
; plots each with their own labelbar. The two sets of plots can be
; paneled side-by-side in a "horizontal" configuration, with the
; labelbars appearing at the bottom, or in a top-and-bottom "vertical"
; configuration, with the labelbars appearing at the right.
;
; For a horizontal configuration, the two sets of plots must each be
; paneled using the same number of rows.
;
; For a vertical configuration, the two plots must have must be
; paneled using the same number of columns.
;----------------------------------------------------------------------

;----------------------------------------------------------------------
; Given two sets of nrow x ncol dimensions, return an orientation to 
; use for paneling plots given these dimensions.
;----------------------------------------------------------------------
setfileoption("nc", "Format", getenv("MDTF_NC_FORMAT"))

undef("get_orientation")
function get_orientation(dims1[2]:numeric,dims2[2]:numeric)
local ncols1, ncols2, nrows1, nrows2
begin
  nrows1 = dims1(0)
  ncols1 = dims1(1)
  nrows2 = dims2(0)
  ncols2 = dims2(1)
  if(nrows1.eq.nrows2) then
    return("horizontal")
  else if(ncols1.eq.ncols2) then
    return("vertical")
  else 
    print("get_orientation: Neither the # of rows or # of columns are the same.")
    print("                 Can't determine orientation.")
    exit
  end if
  end if
end

;----------------------------------------------------------------------
; Given two sets of nrow x ncol dimensions and an orientation, return
; a single nrow x ncol dimension array to be used for a single panel
;
; Example:
;   If you want a vertical orientation of:
;     - a set of 4 x 3 plots on the top
;     - a set of 2 x 3 plots on the bottom 
;   this function returns 6 x 3
;
;   If you want a horizontal orientation of:
;     - a set of 2 x 4 plots on the left
;     - a set of 2 x 3 plots on the right 
;   this function returns 2 x 7
; 
; The assumption is that the columns are the same for a vertical
; orientation, and the rows are the same for a horizontal 
; orientation.
;----------------------------------------------------------------------
undef("get_dims")
function get_dims(dims1[2]:numeric,dims2[2]:numeric,orientation[1]:string)
local ncols1, ncols2, nrows1, nrows1, total_rows, total_cols
begin
  nrows1 = dims1(0)
  ncols1 = dims1(1)
  nrows2 = dims2(0)
  ncols2 = dims2(1)
  if(orientation.eq."vertical") then
    total_rows = nrows1 + nrows2
    total_cols = ncols1
  else
    total_rows = nrows1
    total_cols = ncols1 + ncols2
  end if
  return((/total_rows,total_cols/))
end

;----------------------------------------------------------------------
; Given a set of dimensions for paneling two sets of plots, this 
; function sets the gsnPanelTop/Bottom/Right/Left resources and
; adds a gsnPanelMid resource that marks the line between the two sets
; of paneled plots.
;----------------------------------------------------------------------
undef("set_panel_res")
function set_panel_res(pres,dims1,dims2,dims,orientation)
local hgt, wdt
begin
  pres_new = True
  pres_new@gsnPanelTop    = get_res_value_keep(pres,"gsnPanelTop",1.0)
  pres_new@gsnPanelBottom = get_res_value_keep(pres,"gsnPanelBottom",0.0)
  pres_new@gsnPanelLeft   = get_res_value_keep(pres,"gsnPanelLeft",0.0)
  pres_new@gsnPanelRight  = get_res_value_keep(pres,"gsnPanelRight",1.0)

  hgt = pres_new@gsnPanelTop   - pres_new@gsnPanelBottom        ; Get full  area of unit square 
  wdt = pres_new@gsnPanelRight - pres_new@gsnPanelLeft        ; sets of  plots need to be drawn in.

  if(orientation.eq."vertical") then
    pres_new@gsnPanelMid = pres_new@gsnPanelTop -    (dims1(0)/tofloat(dims(0)))*hgt
  else
    pres_new@gsnPanelMid = pres_new@gsnPanelLeft +    (dims1(1)/tofloat(dims(1)))*wdt
  end if
  return(pres_new)
end

;----------------------------------------------------------------------
; This function creates (but doesn't draw) a single panel plot of the 
; given plots with the requested oriented labelbar and panel area, and
; returns the resized plots and labelbar as an array of graphical
; object ids. This is to help determine the locations to use for the
; two sets of panels.
;----------------------------------------------------------------------
undef("create_single_panel")
function create_single_panel(wks,plots,dims,pres,orientation)
local tmp_pres, paneled_plots
begin
  tmp_pres                  = True
  tmp_pres@lbOrientation    = orientation
  tmp_pres@gsnPanelLabelBar = True
  tmp_pres@gsnDraw          = False
  tmp_pres@gsnFrame         = False
  tmp_pres@gsnPanelTop      = pres@gsnPanelTop
  tmp_pres@gsnPanelBottom   = pres@gsnPanelBottom
  tmp_pres@gsnPanelLeft     = pres@gsnPanelLeft
  tmp_pres@gsnPanelRight    = pres@gsnPanelRight

  paneled_plots = gsn_panel_return(wks,plots,dims,tmp_pres)
  return(paneled_plots)
end

;----------------------------------------------------------------------
; This function combines two arrays of plots into a single array of
; plots depending on whether they are going to be vertically or
; horizontally stacked.
;----------------------------------------------------------------------
undef("combine_plots_single_array")
function combine_plots_single_array(plots1,dims1,plots2,dims2,orientation)
local nrows1, nrows2, ncols1, ncols2, nplots1, nplots2, nplots, \
all_plots, i, np, nr, nc, dims
begin
  nrows1 = dims1(0)
  ncols1 = dims1(1)
  nrows2 = dims2(0)
  ncols2 = dims2(1)

  nplots1 = dimsizes(plots1)
  nplots2 = dimsizes(plots2)
  nplots  = nplots1+nplots2
  all_plots = new(nplots,graphic)
  if(orientation.eq."vertical") then
    dims = (/nrows1+nrows2,ncols1/)
    all_plots(0:nplots1-1) = plots1
    all_plots(nplots1:)    = plots2
  else
    dims = (/nrows1,ncols1+ncols2/)
    np = 0
    do nr=0,nrows1-1
      do i=0,ncols1-1
        all_plots(np) = plots1(i+(nr*ncols1))
        np = np + 1
      end do
      do i=0,ncols2-1
        all_plots(np) = plots2(i+(nr*ncols2))
        np = np + 1
      end do
    end do
  end if
  return(all_plots)
end

;----------------------------------------------------------------------
; This function panels two sets of plots as a single panel of plots
; with a single labelbar, in order to calculate new values for 
; gsnPanel/Top/Bottom/Left/Right and gsnPanelMid that will be used
; later to panel these plots as two panels on the same page, but 
; with two different labelbars.
;----------------------------------------------------------------------
undef("set_new_panel_res")
function set_new_panel_res(wks,plots1,plots2,dims1,dims2,dims,\
                           pres[1]:logical,orientation[1]:string)
local bb, plots_top, plots_bot, plots_lft, plots_rgt, all_plots,\
panel_plots, bot_row1, top_row2, row_diff, rgt_col1,  lft_col2, col_diff, hgt, wdt
begin
  all_plots   = combine_plots_single_array(plots1,dims1,plots2,dims2,orientation)
  panel_plots = create_single_panel(wks,all_plots,dims,pres,orientation)

  pres_new = pres

  nplots = dimsizes(panel_plots)-1        ; skip last plotid, which is a  labelbar
  bb = NhlGetBB(all_plots(0:nplots-1))
  if(orientation.eq."vertical") then
    plots_top = max(bb(:,0))              ; get full area of paneled plots
    plots_bot = min(bb(:,1))

    bot_row1  = max(bb(0,1))              ; get bottom of first row
    top_row2  = min(bb(dims(1),0))        ; get top of second row
    row_diff  = (bot_row1 - top_row2)/2.  ; half the distance b/w rows

    pres_new@gsnPanelTop    = min((/1.,plots_top + row_diff/))
    pres_new@gsnPanelBottom = max((/0.,plots_bot - row_diff/))
    hgt = pres_new@gsnPanelTop - pres_new@gsnPanelBottom
    pres_new@gsnPanelMid = pres_new@gsnPanelTop -    (dims1(0)/tofloat(dims(0)))*hgt
  else
    plots_lft = min(bb(:,2))              ; get full area of paneled plots
    plots_rgt = max(bb(:,3))

    rgt_col1  = bb(0,3)                   ; get right of first column
    lft_col2  = bb(1,2)                   ; get left of second column
    col_diff  = (lft_col2 - rgt_col1)/2.  ; half the distance b/w columns

    pres_new@gsnPanelLeft  = max((/0.,plots_lft - col_diff/))
    pres_new@gsnPanelRight = min((/1.,plots_rgt + col_diff/))
    wdt = pres_new@gsnPanelRight - pres_new@gsnPanelLeft
    pres_new@gsnPanelMid   = pres_new@gsnPanelLeft +    (dims1(1)/tofloat(dims(1)))*wdt
  end if
  return(pres_new)
end

;----------------------------------------------------------------------
; Given two sets of plots, a panel dimension array for each, and
; a desired "stacking" (horizontal or vertical), this procedure
; panels both sets of plots in a single panel, each with its own
; labelbar.
;   plots1 - first set of plots to panel 
;   plots2 - second set of plots to panel 
;   dims1  - nrows x ncols for first set of plots
;   dims2  - nrows x ncols for second set of plots
;   pres1  - resources applied to first set of plots
;   pres   - Use to set gsnPanelTop / gsnPanelBottom / 
;                       gsnPanelLeft / gsnPanelRight
;            if want values other than the default of 1 / 0 / 0 / 1
;---------------------------------------------------------------------- 
undef("panel_two_sets")
procedure panel_two_sets(wks,plots1[*]:graphic,plots2[*]:graphic,\
                         dims1[2]:integer,dims2[2]:integer,\
                         plots1_res:logical,plots2_res:logical,\
                         panel_size_res[1]:logical)
local orientation, dims, plots1_res_tmp, plots2_res_tmp, panel_size_res_tmp1, panel_size_res_tmp2
begin
  orientation = get_orientation(dims1,dims2)
  dims = get_dims(dims1,dims2,orientation)

;---Calculate new set of panel resources that encompasses both sets of    plots
  panel_size_res_tmp1 =    set_panel_res(panel_size_res,dims1,dims2,dims,orientation)
  panel_size_res_tmp2 =    set_new_panel_res(wks,plots1,plots2,dims1,dims2,dims,panel_size_res_tmp1,orientation)

;---These are the individual resource lists for each panel
  plots1_res_tmp = plots1_res
  plots2_res_tmp = plots2_res
  plots1_res_tmp@gsnPanelLabelBar = True
  plots2_res_tmp@gsnPanelLabelBar = True

  if(orientation.eq."vertical") then
    plots1_res_tmp@gsnFrame          = False
    plots1_res_tmp@lbOrientation     = orientation
    plots1_res_tmp@gsnPanelTop       = panel_size_res_tmp2@gsnPanelTop
    plots1_res_tmp@gsnPanelBottom    = panel_size_res_tmp2@gsnPanelMid
    plots1_res_tmp@gsnPanelLeft      = panel_size_res_tmp2@gsnPanelLeft
    plots1_res_tmp@gsnPanelRight     = panel_size_res_tmp2@gsnPanelRight
    plots1_res_tmp@gsnPanelBottom    = panel_size_res_tmp2@gsnPanelMid
    plots1_res_tmp@pmLabelBarHeightF =    get_res_value_keep(plots1_res,"pmLabelBarHeightF",\
                                       0.8*(plots1_res_tmp@gsnPanelTop - plots1_res_tmp@gsnPanelBottom))

    gsn_panel(wks,plots1,dims1,plots1_res_tmp)

    plots2_res_tmp@gsnFrame          = False
    plots2_res_tmp@lbOrientation     = orientation
    plots2_res_tmp@gsnPanelTop       = panel_size_res_tmp2@gsnPanelMid
    plots2_res_tmp@gsnPanelBottom    = panel_size_res_tmp2@gsnPanelBottom
    plots2_res_tmp@gsnPanelLeft      = panel_size_res_tmp2@gsnPanelLeft
    plots2_res_tmp@gsnPanelRight     = panel_size_res_tmp2@gsnPanelRight
    plots2_res_tmp@pmLabelBarHeightF =  \
        get_res_value_keep(plots2_res,"pmLabelBarHeightF", \
                           0.8*(plots2_res_tmp@gsnPanelTop -  plots2_res_tmp@gsnPanelBottom))

    gsn_panel(wks,plots2,dims2,plots2_res_tmp)
  else
    plots1_res_tmp                   = plots1_res
    plots1_res_tmp@lbOrientation     = orientation
    plots1_res_tmp@gsnFrame          = False
    plots1_res_tmp@gsnPanelTop       = panel_size_res_tmp2@gsnPanelTop
    plots1_res_tmp@gsnPanelBottom    = panel_size_res_tmp2@gsnPanelBottom
    plots1_res_tmp@gsnPanelLeft      = panel_size_res_tmp2@gsnPanelLeft
    plots1_res_tmp@gsnPanelRight     = panel_size_res_tmp2@gsnPanelMid
    plots1_res_tmp@pmLabelBarWidthF  =  get_res_value_keep(plots1_res,"pmLabelBarWidthF",\
                    0.8*(plots1_res_tmp@gsnPanelRight -  plots1_res_tmp@gsnPanelLeft))

    gsn_panel(wks,plots1,dims1,plots1_res_tmp)

    plots2_res_tmp@gsnFrame          = False
    plots2_res_tmp@lbOrientation     = orientation
    plots2_res_tmp@gsnPanelTop       = panel_size_res_tmp2@gsnPanelTop
    plots2_res_tmp@gsnPanelBottom    = panel_size_res_tmp2@gsnPanelBottom
    plots2_res_tmp@gsnPanelLeft      = panel_size_res_tmp2@gsnPanelMid
    plots2_res_tmp@gsnPanelRight     = panel_size_res_tmp2@gsnPanelRight
    plots2_res_tmp@pmLabelBarWidthF  =    get_res_value_keep(plots2_res,"pmLabelBarWidthF",\
                      0.8*(plots2_res_tmp@gsnPanelRight -    plots2_res_tmp@gsnPanelLeft))

    gsn_panel(wks,plots2,dims2,plots2_res_tmp)
  end if
  frame(wks)

end
