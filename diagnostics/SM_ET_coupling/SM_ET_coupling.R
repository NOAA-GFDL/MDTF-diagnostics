################################
# .libPaths("/home/water2/ab5/R/x86_64-redhat-linux-gnu-library/3.2")
library(colorRamps)
library(maps)
library(fields)
library(akima)
library(ncdf4)

WK_DIR <- Sys.getenv("WORK_DIR")
OBS_DATA <- Sys.getenv("OBS_DATA")
DATADIR <- Sys.getenv("DATADIR")
CASENAME <- Sys.getenv("CASENAME")
yr1 <- Sys.getenv("startdate")
yr2 <- Sys.getenv("enddate")
MRSOS_FILE <- Sys.getenv("MRSOS_FILE")
EVSPSBL_FILE <- Sys.getenv("EVSPSBL_FILE")
PR_FILE <- Sys.getenv("PR_FILE")

##########################################
print("Taking lon/lat from model")
print(MRSOS_FILE)
data_mrsos <- nc_open(MRSOS_FILE)
lon_model <- ncvar_get(data_mrsos, "lon")
lat_model <- ncvar_get(data_mrsos, "lat")
nc_close(data_mrsos) 

print("Taking soil moisture from model, top-10cm")
print("Taking lon/lat from model")
data_mrsos <- nc_open(MRSOS_FILE)
print("Getting the number of years in the model file... should be 35 (i.e., 1980-2014)" )
## Here we read all years
mrsos <- ncvar_get(data_mrsos, "mrsos")[,,] 
years1 <- dim(mrsos)[3]/12
years2 <- years1 - 1
mrsos_JJA <- array(NA, dim=c(dim(mrsos)[1],dim(mrsos)[2], years1))
mrsos_DJF <- array(NA, dim=c(dim(mrsos)[1],dim(mrsos)[2], years2))
for (t in 1:years1){mrsos_JJA[,,t] <- apply(mrsos[ ,,  (12*(t-1)+6):(12*(t-1)+8)],   c(1,2), mean, na.rm=T)}
for (t in 1:years2){mrsos_DJF[,,t] <- apply(mrsos[ ,,   (12*(t-1)+12):(12*(t-1)+14) ],   c(1,2), mean, na.rm=T)}
nc_close(data_mrsos) 

print("Defining model mask")
mask_model <- mrsos[,,1]
mask_model[which(is.na(mask_model)==F)] <- 1

print("Taking ET from model")
data_evspsbl <- nc_open(EVSPSBL_FILE)
evspsbl <- ncvar_get(data_evspsbl, "evspsbl")[,,] 
evspsbl_JJA <- array(NA, dim=c(dim(mrsos)[1],dim(mrsos)[2], years1))
evspsbl_DJF <- array(NA, dim=c(dim(mrsos)[1],dim(mrsos)[2], years2))
for (t in 1:years1){evspsbl_JJA[,,t] <- apply(evspsbl[ ,,  (12*(t-1)+6):(12*(t-1)+8)],   c(1,2), mean, na.rm=T)}
for (t in 1:years2){evspsbl_DJF[,,t] <- apply(evspsbl[ ,,   (12*(t-1)+12):(12*(t-1)+14) ],   c(1,2), mean, na.rm=T)}
nc_close(data_evspsbl) 


##########################################
print("Correlating SM and ET") 
corr_mrsos_evspsbl <- array(NA, dim=c(length(lon_model), length(lat_model)))
for (i in 1:length(lon_model)){
for (j in 1:floor(length(lat_model)/2)) {
if (is.na(mrsos_DJF[i,j,1])==F) {
corr_mrsos_evspsbl[i,j] <- cor(mrsos_DJF[i,j,],evspsbl_DJF[i,j,], use="complete.obs")}}
for (j in (floor(length(lat_model)/2)+1):length(lat_model) ){
if (is.na(mrsos_JJA[i,j,1])==F) {
corr_mrsos_evspsbl[i,j] <- cor(mrsos_JJA[i,j,],evspsbl_JJA[i,j,], use="complete.obs")}}}

 
##########################################
print("Plotting model correlation")
png(paste(WK_DIR,"/model/corr_mrsos_evspsbl_summer_model.png",sep=""), width=700)
print("plotting model")
lowlat_model <- min(which(lat_model > -60))
highlat_model <- min(which(lat_model > 80))
image.plot(lon_model - 180, lat_model[lowlat_model:highlat_model], (corr_mrsos_evspsbl*mask_model)[ c( (length(lon_model)/2+1):length(lon_model), 1:(length(lon_model)/2)),lowlat_model:highlat_model], zlim=c(-1,1),  breaks=seq(-1,1, by=0.1), col=matlab.like(20), xlab="", ylab="", main="cor(SM,ET), summer, model years, Model")
map(add=T)  ; abline(h=0, lwd=.2)
dev.off()



##########################################

### Compare to GLEAM: map GLEAM
load(paste(OBS_DATA, "/corr_smsurf_E_GLEAM_1980_2014.RData", sep=""))
load(paste(OBS_DATA, "/lon_GLEAM.RData", sep=""))
load(paste(OBS_DATA, "/lat_GLEAM.RData", sep=""))
corr_mrsos_evspsbl_GLEAM <- corr_smsurf_E_GLEAM
print("Regridding GLEAM to same as model")
corr_mrsos_evspsbl_GLEAM_corrected <- corr_smsurf_E_GLEAM
corr_mrsos_evspsbl_GLEAM_corrected[which(is.na(corr_smsurf_E_GLEAM)==T)] <- 0
corr_mrsos_evspsbl_GLEAM_modelres <- bicubic.grid(lon_GLEAM, lat_GLEAM, corr_mrsos_evspsbl_GLEAM_corrected[,], xlim=range(lon_GLEAM), ylim=range(lat_GLEAM), dx=(lon_model[3]-lon_model[2]),  dy=(lat_model[3]-lat_model[2]) )$z

print("Plotting GLEAM correlation")
png(paste(WK_DIR,"/obs/corr_mrsos_evspsbl_summer_GLEAM_modelres.png",sep=""), width=700)
print("plotting obs")
image.plot(lon_model - 180, lat_model[lowlat_model:highlat_model], corr_mrsos_evspsbl_GLEAM_modelres[,lowlat_model:highlat_model]*mask_model[ c((length(lon_model)/2+1):length(lon_model), 1:(length(lon_model)/2)),lowlat_model:highlat_model], zlim=c(-1,1), breaks=seq(-1,1, by=0.1),  col=matlab.like(20), xlab="", ylab="", main="cor(SM,ET), summer, 1980-2014, GLEAM (regridded to model res.)")
map(add=T)  ; abline(h=0, lwd=.2)
dev.off()

######################
print("Plotting MODEL - GLEAM correlation")
png(paste(WK_DIR,"/model/corr_mrsos_evspsbl_summer_model_GLEAM_diff.png",sep=""), width=700)
diff <- (corr_mrsos_evspsbl[c((length(lon_model)/2+1):length(lon_model), 1:(length(lon_model)/2)),lowlat_model:highlat_model] - corr_mrsos_evspsbl_GLEAM_modelres[,lowlat_model:highlat_model]) * mask_model[ c((length(lon_model)/2+1):length(lon_model), 1:(length(lon_model)/2)),lowlat_model:highlat_model]
image.plot(lon_model - 180, lat_model[lowlat_model:highlat_model], diff, zlim=c(-2,2), breaks=seq(-2,2, by=0.1),  col=matlab.like(40), xlab="", ylab="", main="cor(SM,ET), summer, Model - GLEAM (regridded to model res.)")
map(add=T)  ; abline(h=0, lwd=.2); rm(diff)
dev.off()

##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
### Next:
### Plot  mean summertime precipitation from model, and from GLEAM observations
### Model:

print("Take precipitation from model")
data_pr <- nc_open(PR_FILE)
pr <- ncvar_get(data_pr, "pr")[,,] *86400
pr_JJA <- array(NA, dim=c(dim(pr)[1],dim(pr)[2], years1))
pr_DJF <- array(NA, dim=c(dim(pr)[1],dim(pr)[2], years2))
for (t in 1:years1){pr_JJA[,,t] <- apply(pr[ ,,  (12*(t-1)+6):(12*(t-1)+8)],   c(1,2), mean, na.rm=T)}
for (t in 1:years2){pr_DJF[,,t] <- apply(pr[ ,,   (12*(t-1)+12):(12*(t-1)+14) ],   c(1,2), mean, na.rm=T)}
nc_close(data_pr) 

mean_pr_summer_model <- array(NA, dim=dim(pr)[1:2])
mean_pr_summer_model[,1:floor(length(lat_model)/2)] <- apply(pr_DJF[,1:floor(length(lat_model)/2),], c(1,2), mean, na.rm=T)
mean_pr_summer_model[,  (floor(length(lat_model)/2)+1):length(lat_model) ] <- apply(pr_JJA[,  (floor(length(lat_model)/2)+1):length(lat_model)  ,], c(1,2), mean, na.rm=T)


#######################################
print("Plotting model mean precipitation")
png(paste(WK_DIR,"/model/mean_pr_summer_model.png",sep=""), width=700)
print("plotting model")
lowlat_model <- min(which(lat_model > -60))
highlat_model <- min(which(lat_model > 80))
pr_plot_model <- mean_pr_summer_model
pr_plot_model[which(pr_plot_model > 15)] <- 15
image.plot(lon_model - 180, lat_model[lowlat_model:highlat_model], (pr_plot_model*mask_model)[ c( (length(lon_model)/2+1):length(lon_model), 1:(length(lon_model)/2)),lowlat_model:highlat_model], zlim=c(0,15),  breaks=seq(0,15, by=1), col=matlab.like(15), xlab="", ylab="", main="Mean Pr(mm/d), summer, model years, Model")
map(add=T)  ; abline(h=0, lwd=.2)
dev.off()
#######################################

## Now getting GLEAM
load(paste(OBS_DATA, "/mean_precip_summer_GLEAM_1980_2014.RData", sep=""))
load(paste(OBS_DATA, "/lon_GLEAM_P.RData", sep=""))
load(paste(OBS_DATA, "/lat_GLEAM_P.RData", sep=""))
print("Regridding GLEAM Precip")
mean_precip_summer_GLEAM_corrected <- mean_precip_summer_GLEAM
mean_precip_summer_GLEAM_corrected[which(is.na( mean_precip_summer_GLEAM== T))] <- 0
mean_precip_summer_GLEAM_modelres <- bicubic.grid(lon_GLEAM_P, lat_GLEAM_P, mean_precip_summer_GLEAM_corrected[,], xlim=range(lon_GLEAM_P), ylim=range(lat_GLEAM_P), dx=(lon_model[3]-lon_model[2]),  dy=(lat_model[3]-lat_model[2]) )$z / 30

print("Plotting GLEAM Pr")

png(paste(WK_DIR,"/obs/mean_precip_summer_summer_GLEAM.png",sep=""), width=700)
mean_precip_summer_GLEAM_modelres[which(mean_precip_summer_GLEAM_modelres > 15)] <- 15
image.plot(lon_model - 180, lat_model[lowlat_model:highlat_model], mean_precip_summer_GLEAM_modelres[,lowlat_model:highlat_model]*mask_model[ c((length(lon_model)/2+1):length(lon_model), 1:(length(lon_model)/2)),lowlat_model:highlat_model], zlim=c(0,15), breaks=seq(0,15, by=1),  col=matlab.like(15), xlab="", ylab="", main="Mean Pr summer (mm/d), 1980-2014, GLEAM (regridded to model res.)")
map(add=T)  ; abline(h=0, lwd=.2)
dev.off()

#######################################
print("Plotting Pr diff, Model - GLEAM")
png(paste(WK_DIR,"/model/mean_precip_summer_summer_model_GLEAM_diff.png",sep=""), width=700)
diff <- (mean_pr_summer_model*mask_model)[ c( (length(lon_model)/2+1):length(lon_model), 1:(length(lon_model)/2)),lowlat_model:highlat_model] - mean_precip_summer_GLEAM_modelres[,lowlat_model:highlat_model]*mask_model[ c((length(lon_model)/2+1):length(lon_model), 1:(length(lon_model)/2)),lowlat_model:highlat_model]
diff[which(diff > 5)] <- 5; diff[which(diff <  -5)] <- -5;
image.plot(lon_model - 180, lat_model[lowlat_model:highlat_model],  diff , zlim=c(-5,5), breaks=seq(-5,5, by=0.5),  col=matlab.like(20), xlab="", ylab="", main="Mean Pr (mm/d), summer, Model - GLEAM (saturates at +/-5 mm/d)")
map(add=T)  ; abline(h=0, lwd=.2); rm(diff)
dev.off()


##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
## Correcting model coupling for precipitation biases according to relationship between mean summertime Pr and cor(SM,ET) from CMIP5 models
print("Correcting model coupling for precipitation biases")
print("loading the CMIP5, 2x2 data")

load(paste(OBS_DATA, "/lon.RData", sep=""))
load(paste(OBS_DATA, "/lat.RData", sep=""))
lon_2x2 <- lon; lat_2x2 <- lat
load(paste(OBS_DATA, "/mean_pr_summer_2x2_allmodels.RData", sep=""))
load(paste(OBS_DATA, "/corr_mrsos_evspsbl_summer_2x2_allmodels.RData", sep=""))
load(paste(OBS_DATA, "/list_models_mrsos_PCMDI.RData", sep=""))
load(paste(OBS_DATA, "/list_models_pr_long.RData", sep=""))
load(paste(OBS_DATA, "/mask_2x2_NAs.RData", sep=""))

###############################
#We have to regrid everything to 2 degrees:
print("regridding cor(SM,ET) from the model to 2x2")
mrsos_JJA[which(is.na(mrsos_JJA)==T)] <- 0 ; mrsos_DJF[which(is.na(mrsos_DJF)==T)] <- 0
mrsos_JJA_2x2 <- array(NA, dim=c(dim(mean_pr_summer_2x2_allmodels)[1:2], dim(mrsos_JJA)[3]))
mrsos_DJF_2x2 <- array(NA, dim=c(dim(mean_pr_summer_2x2_allmodels)[1:2], dim(mrsos_JJA)[3]))
evspsbl_JJA_2x2 <- array(NA, dim=c(dim(mean_pr_summer_2x2_allmodels)[1:2], dim(mrsos_JJA)[3]))
evspsbl_DJF_2x2 <- array(NA, dim=c(dim(mean_pr_summer_2x2_allmodels)[1:2], dim(mrsos_JJA)[3]))
print("regridding JJA SM and ET")
for (t in 1:(dim(mrsos_JJA)[3]) ){
mrsos_JJA_2x2[,,t] <- bicubic.grid(lon_model, lat_model, mrsos_JJA[,,t], xlim=c(0,360), ylim=c(-90,90), dx=2, dy=2 )$z
evspsbl_JJA_2x2[,,t] <- bicubic.grid(lon_model, lat_model, evspsbl_JJA[,,t],xlim=c(0,360), ylim=c(-90,90), dx=2, dy=2 )$z }
print("regridding DJF SM and ET")
for (t in 1:dim(mrsos_DJF)[3]){
mrsos_DJF_2x2[,,t] <- bicubic.grid(lon_model, lat_model, mrsos_DJF[,,t], xlim=c(0,360), ylim=c(-90,90), dx=2, dy=2 )$z
evspsbl_DJF_2x2[,,t] <- bicubic.grid(lon_model, lat_model, evspsbl_DJF[,,t],xlim=c(0,360), ylim=c(-90,90), dx=2, dy=2 )$z }

print("computing 2x2 correlation")
corr_mrsos_evspsbl_2x2 <- array(NA, dim=c(181,91))
for (i in 1:181){
for (j in 1:45) {
if (mrsos_DJF_2x2[i,j,1]!=0) {corr_mrsos_evspsbl_2x2[i,j] <- cor(mrsos_DJF_2x2[i,j,],evspsbl_DJF_2x2[i,j,], use="complete.obs")}}
for (j in 46:91 ) {
if (mrsos_JJA_2x2[i,j,1]!=0) {corr_mrsos_evspsbl_2x2[i,j] <- cor(mrsos_JJA_2x2[i,j,],evspsbl_JJA_2x2[i,j,], use="complete.obs")} }
}

##############
print("Regridding model P to 2x2")
mean_pr_summer_model_2x2 <- bicubic.grid(lon_model, lat_model, mean_pr_summer_model[,], xlim=c(0,360), ylim=c(-90,90),  dx=2, dy=2)$z 

#############
print("Regridding GLEAM coupling to 2x2")
corr_mrsos_evspsbl_GLEAM_corrected <- corr_smsurf_E_GLEAM
corr_mrsos_evspsbl_GLEAM_corrected[which(is.na(corr_smsurf_E_GLEAM)==T)] <- 0
corr_mrsos_evspsbl_GLEAM_2x2 <- bicubic.grid(lon_GLEAM, lat_GLEAM, corr_mrsos_evspsbl_GLEAM_corrected[,], xlim=c(-180,180), ylim=c(-90,90),  dx=2, dy=2)$z
corr_mrsos_evspsbl_GLEAM_2x2 <-corr_mrsos_evspsbl_GLEAM_2x2 [c(91:181,1:90),]

##############
print("Regridding GLEAM P to 2x2")
mean_precip_summer_GLEAM_2x2 <- bicubic.grid(lon_GLEAM_P, lat_GLEAM_P, mean_precip_summer_GLEAM_corrected[,], xlim=c(-180,180), ylim=c(-90,90),  dx=2, dy=2)$z / 30
mean_precip_summer_GLEAM_2x2 <- mean_precip_summer_GLEAM_2x2[c(91:181,1:90),]


############## CORRECTION for Pr DIFFERENCE #############################
print(" CORRECTING for Pr DIFFERENCE")
bob <- which(list_models_mrsos_PCMDI[-c(11:12)] %in% list_models_pr_long)
bill <- which(list_models_pr_long %in% list_models_mrsos_PCMDI[-c(11:12)])
print("veryfing CMIP5 models lists match")
list_models_mrsos_PCMDI[-c(11:12)][bob] == list_models_pr_long[bill]
corr_mrsos_evspsbl_2x2_corrP  <- array(NA, dim=dim(corr_mrsos_evspsbl_2x2))
for (i in 1:length(lon_2x2)){
for (j in 1:length(lat_2x2)){
if ((is.na(corr_mrsos_evspsbl_summer_2x2_allmodels[i,j,])==FALSE)) {
regression <- lm( corr_mrsos_evspsbl_summer_2x2_allmodels[i,j,-c(11:12)][bob] ~ mean_pr_summer_2x2_allmodels[i,j,bill])
estimate <- as.vector(regression$coeff[2])*(mean_precip_summer_GLEAM_2x2[i,j] - mean_pr_summer_model_2x2[i,j]) + corr_mrsos_evspsbl_2x2[i,j]
if ((is.na(estimate)==F) &&  (estimate > 1) ) {estimate <- 1}
if ((is.na(estimate)==F) && (estimate < -1) ) {estimate <- -1}
corr_mrsos_evspsbl_2x2_corrP[i,j] <- estimate
rm(regression);rm(estimate)}}}

#i=16; j=71; print(lon[i]); print(lat[j])
#i=121; j=66; print(lon[i]); print(lat[j])
#x11()
#regression <- lm( corr_mrsos_evspsbl_summer_2x2_allmodels[i,j,-c(11:12)][bob] ~ mean_pr_summer_2x2_allmodels[i,j,bill])
#plot(mean_pr_summer_2x2_allmodels[i,j,bill],  corr_mrsos_evspsbl_summer_2x2_allmodels[i,j,-c(11:12)][bob], xlim=c(0, 15), ylim=c(-1,1.5))
#abline(regression$coeff[1],regression$coeff[2], col="red"); 
#abline(v=mean_precip_summer_GLEAM_2x2[i,j], col="blue")
#abline(v=mean_pr_summer_model_2x2[i,j], col="black", lty=2)
#points(mean_pr_summer_model_2x2[i,j],  corr_mrsos_evspsbl_2x2[i,j], pch=19)
#points(mean_precip_summer_GLEAM_2x2[i,j], regression$coeff[1] + regression$coeff[2]*mean_precip_summer_GLEAM_2x2[i,j]  , pch=19, col="blue")
#points(mean_precip_summer_GLEAM_2x2[i,j], corr_mrsos_evspsbl_GLEAM_2x2[i,j]  , pch=17, col="blue")
#points(mean_precip_summer_GLEAM_2x2[i,j],  corr_mrsos_evspsbl_2x2_corrP[i,j], pch=19)

col_custom =  colorRampPalette(c("darkblue","blue","cyan","white","orange","red","darkred"))
#x11(); image.plot(mean_pr_summer_model_2x2*mask_2x2_NAs, zlim=c(0,15), breaks=seq(0,15, by=1),  col=matlab.like(15))
#x11(); image.plot(mean_precip_summer_GLEAM_2x2*mask_2x2_NAs, zlim=c(0,15), breaks=seq(0,15, by=1),  col=matlab.like(15))
#x11(); image.plot((mean_pr_summer_model_2x2*mask_2x2_NAs - mean_precip_summer_GLEAM_2x2*mask_2x2_NAs)[c(91:181,1:90),], main="Precip, Model-Obs", zlim=c(-5,5), col=col_custom(20))

##########################################
print("Plotting model coupling corrected for P, on 2x2")
png(paste(WK_DIR,"/model/corr_mrsos_evspsbl_summer_model_2x2_corrP.png",sep=""), width=700)
print("plotting model")
lowlat_2x2 <- min(which(lat_2x2 > -60))
highlat_2x2 <- min(which(lat_2x2 > 80))
image.plot(lon_2x2 - 180, lat_2x2[lowlat_2x2:highlat_2x2], (corr_mrsos_evspsbl_2x2_corrP*mask_2x2_NAs)[ c( (length(lon_2x2)/2+1):length(lon_2x2), 1:(length(lon_2x2)/2)),lowlat_2x2:highlat_2x2], zlim=c(-1,1),  breaks=seq(-1,1, by=0.1), col=matlab.like(20), xlab="", ylab="", main="cor(SM,ET), summer, model years, Model, corrected for P bias vs GLEAM, 2x2")
map(add=T)  ; abline(h=0, lwd=.2)
dev.off()

#x11(); image.plot(  (corr_mrsos_evspsbl_2x2_corrP*mask_2x2_NAs - corr_mrsos_evspsbl_2x2*mask_2x2_NAs )[ c( (length(lon_2x2)/2+1):length(lon_2x2), 1:(length(lon_2x2)/2)),lowlat_2x2:highlat_2x2], main="Cor(SM,ET), Model_corrP - Model", zlim=c(-1,1), col=col_custom(20))


#x11(); image.plot(corr_mrsos_evspsbl_GLEAM_2x2, zlim=c(-1,1))
#x11(); image.plot(corr_mrsos_evspsbl_2x2, zlim=c(-1,1))
#x11(); image.plot(  (corr_mrsos_evspsbl_2x2*mask_2x2_NAs - corr_mrsos_evspsbl_GLEAM_2x2 )[ c( (length(lon_2x2)/2+1):length(lon_2x2), 1:(length(lon_2x2)/2)),], main="Cor(SM,ET), Model - Obs", zlim=c(-2,2), col=col_custom(20))

##########################################
print("Plotting GLEAM coupling on 2x2")
png(paste(WK_DIR,"/obs/corr_mrsos_evspsbl_summer_GLEAM_2x2.png",sep=""), width=700)
print("plotting model")
lowlat_2x2 <- min(which(lat_2x2 > -60))
highlat_2x2 <- min(which(lat_2x2 > 80))
image.plot(lon_2x2 - 180, lat_2x2[lowlat_2x2:highlat_2x2], (corr_mrsos_evspsbl_GLEAM_2x2*mask_2x2_NAs)[ c( (length(lon_2x2)/2+1):length(lon_2x2), 1:(length(lon_2x2)/2)),lowlat_2x2:highlat_2x2], zlim=c(-1,1),  breaks=seq(-1,1, by=0.1), col=matlab.like(20), xlab="", ylab="", main="cor(SM,ET), summer, 1980-2014, GLEAM, 2x2")
map(add=T)  ; abline(h=0, lwd=.2)
dev.off()


##########################################
print("Plotting model - GLEAM coupling on 2x2")
png(paste(WK_DIR,"/model/corr_mrsos_evspsbl_summer_model_GLEAM_diff_2x2.png",sep=""), width=700)
print("plotting model")
lowlat_2x2 <- min(which(lat_2x2 > -60))
highlat_2x2 <- min(which(lat_2x2 > 80))
diff <-  (corr_mrsos_evspsbl_2x2_corrP*mask_2x2_NAs - corr_mrsos_evspsbl_GLEAM_2x2*mask_2x2_NAs)[ c( (length(lon_2x2)/2+1):length(lon_2x2), 1:(length(lon_2x2)/2)),lowlat_2x2:highlat_2x2]
image.plot(lon_2x2 - 180, lat_2x2[lowlat_2x2:highlat_2x2], diff, zlim=c(-2,2),  breaks=seq(-2,2, by=0.1), col=matlab.like(40), xlab="", ylab="", main="cor(SM,ET), summer, Model - GLEAM (2x2)")
map(add=T)  ; abline(h=0, lwd=.2); rm(diff)
dev.off()




############################################################
print("Normal End of SM_ET_coupling.R")
############################################################
