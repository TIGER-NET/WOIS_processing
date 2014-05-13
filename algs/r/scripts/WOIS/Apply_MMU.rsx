##[Classification]=group
##Layer = raster
##Nodata_value = number 255
##MMU = number 3
##Output_raster = output raster
tryCatch(find.package("igraph"), error=function(e) install.packages("igraph", lib=file.path(Sys.getenv("USERPROFILE"),".qgis/sextante/rlibs")))
Layer <- raster(Layer,1)
NAvalue(Layer) <- Nodata_value
tmp1 <- clump(Layer)
pxarea <- freq(tmp1)
Output_raster = Layer
Output_raster[tmp1 %in% pxarea[pxarea[,2] <= MMU,1]] <- 0
