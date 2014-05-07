##[Classification]=group
##Input_folder = folder
##Input_file_mask = string *_gr_geo_fld_manual.tif
##AOI = vector
##HAND_image = raster|R.raster
##HAND_threshold = number 11
##Flood_count = output raster
##Flood_count_as_percent_of_acquisitions = output raster
#library(sartools)
library(rgdal)
Input_folder = normalizePath(Input_folder)
dll.path <- file.path(Sys.getenv("USERPROFILE"),".qgis/sextante/rlibs/resample",.Platform$r_arch,paste("sartools",.Platform$dynlib.ext,sep=""))
dyn.load(dll.path)
source(file.path(Sys.getenv("USERPROFILE"),".qgis/sextante/rlibs/resample/resamplef.R"))
classified.imgs <- Sys.glob(file.path(Input_folder, Input_file_mask))
if (length(classified.imgs) == 0) stop("No images could be found")
#AOI <- readOGR("r:/Projects_work/TIGERNET/data/Demonstration cases/2012-09-14 Elisabeth NBI flood mapping for DC21",
#               "Lake_Tana_buffered_110km")
AOI <- spTransform(AOI, CRS("+init=epsg:4326"))
to <- raster(extent(-180,180,-90,90), nrows=150*1800, ncols=150*3600, crs=CRS("+init=epsg:4326"))
to <- crop(to, extent(AOI))
s <- list()
cat("Resampling to fixed grid...\n")
for (i in 1:length(classified.imgs)) {
	cat("File", i, "of", length(classified.imgs), "\n")
	r <- raster(classified.imgs[i])
	s[[i]] <- try(resamplef(r, to, "ngb", filename=rasterTmpFile()))
}
s <- stack(s)
rasterOptions(chunksize=1e6)
s.cnt <- calc(s, function(x,...) c(length(which(x == 1)), length(which(is.finite(x)))), filename=rasterTmpFile())
s.cnt <- stack(s.cnt, subset(s.cnt,1)/subset(s.cnt,2)*100)
floodmsk <- raster(HAND_image,1)
e <- extent(floodmsk)
floodmsk <- resamplef(floodmsk, s.cnt, "bilinear")
floodmsk <- floodmsk < HAND_threshold
s.cnt@layers[[1]][s.cnt@layers[[2]] == 0] <- NA
s.cnt@layers[[1]][floodmsk == 0] <- NA
s.cnt@layers[[3]][s.cnt@layers[[2]] == 0] <- NA
s.cnt@layers[[3]][floodmsk == 0] <- NA
s.cnt <- crop(s.cnt,e)
Flood_count = writeRaster(subset(s.cnt,1), rasterTmpFile(), datatype="INT2S")
Flood_count_as_percent_of_acquisitions= writeRaster(subset(s.cnt,3), rasterTmpFile(), datatype="FLT4S")
