##[Conversion]=group
##Input_layer = vector
##Input_raster = raster
tryCatch(find.package("maptools"), error=function(e) install.packages("maptools", lib=file.path(.Library[1])))
tryCatch(find.package("rgeos"), error=function(e) install.packages("rgeos", lib=file.path(.Library[1])))
library(maptools)
library(rgeos)
outputfile <- filename(Input_raster)
extension(outputfile) <- "kml"
p <- Input_layer[Input_layer$value > 0,]
p2 <- gUnaryUnion(p, id=p@data[,"value"])
kmlPolygon(p2@polygons[[1]], kmlfile=outputfile, name=names(Input_raster), col="#006699")
