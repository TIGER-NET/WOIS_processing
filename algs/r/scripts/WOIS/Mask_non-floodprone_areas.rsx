##[Classification]=group
##Input_HAND_raster = raster
##Input_thresholded_raster = raster
##HAND_threshold = number 10
##Output_flood_map = output raster
Input_HAND_raster <- raster(Input_HAND_raster,1)
Input_thresholded_raster <- raster(Input_thresholded_raster,1)
dll.path <- file.path(.Library[1],"resample",.Platform$r_arch,paste("sartools",.Platform$dynlib.ext,sep=""))
dyn.load(dll.path)
source(file.path(.Library[1],"resample/resamplef.R"))
fpmask <- resamplef(Input_HAND_raster, Input_thresholded_raster, "bilinear", datatype="INT2S")
fpmask <- fpmask <= HAND_threshold
fpmask[fpmask == 0] <- NA
Output_flood_map <- mask(Input_thresholded_raster, fpmask, datatype="INT2S")
