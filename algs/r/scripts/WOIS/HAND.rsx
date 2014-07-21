##[DEM analysis]=group
##DEM = raster
##Flow_direction = raster
##Drainage_network = raster
##HAND_raster = output raster
DEM <- raster(DEM,1)
Flow_direction <- raster(Flow_direction,1)
Drainage_network <- raster(Drainage_network,1)
dll.path <- file.path(.Library[1],"resample",.Platform$r_arch,paste("sartools",.Platform$dynlib.ext,sep=""))
dyn.load(dll.path)
source(file.path(.Library[1],"resample/HAND.R"))
e <- extent(max(xmin(DEM),xmin(Flow_direction),xmin(Drainage_network)),
min(xmax(DEM),xmax(Flow_direction),xmax(Drainage_network)),
max(ymin(DEM),ymin(Flow_direction),ymin(Drainage_network)),
min(ymax(DEM),ymax(Flow_direction),ymax(Drainage_network)))
DEM <- crop(DEM,e)
Flow_direction <- crop(Flow_direction,e)
Drainage_network <- crop(Drainage_network,e)
projection(Flow_direction) <- projection(DEM)
projection(Drainage_network) <- projection(DEM)
# set tolerance for check of common extent higher
# this is necessary because GRASS writes a different nominal resolution into its output files
rasterOptions(tolerance = 0.5)
HAND_raster <- HAND(DEM, Flow_direction, Drainage_network, flowdir.type="GRASS")
