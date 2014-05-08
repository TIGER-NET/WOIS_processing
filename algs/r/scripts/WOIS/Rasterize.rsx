##[Conversion]=group
##Vector_layer=vector
##Resolution=number 0.1
##Function=string
##Field=field Vector_layer
##Output_raster=output raster
library(sartools)
grid <- get.ASARgrid("GeoLatLon_2.4arcsec")
grid <- crop(grid, Vector_layer)
fac <- round(Resolution / xres(grid))
grid <- aggregate(grid, fac)
Output_raster <- rasterize(Vector_layer, grid, field=Field, fun=Function)
