##[Classification]=group
##Layer = raster
##Nodata_value = number 0
##Lower_than = boolean True
##Threshold = number -14
##Classified_raster = output raster
Layer <- raster(Layer,1)
NAvalue(Layer) <- Nodata_value
if (Lower_than) {
	Classified_raster <- Layer < Threshold
} else {
	Classified_raster <- Layer > Threshold
}
