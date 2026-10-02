f = addfile(getenv("PR_FILE"),"r")
t = f->time
n = dimsizes(t)
print("n="+n+"  calendar="+t@calendar)
ymd = cd_calendar(t,-2)
print("first="+ymd(0)+"  last="+ymd(n-1))
print("idx2213="+ymd(2213)+"  idx2214="+ymd(2214))
print("monotonic diffs min/max: "+min(t(1:)-t(:n-2))+" "+max(t(1:)-t(:n-2)))
