##Flood mapping=group
##Lin2dB=name
##input_raster=raster
##ParameterNumber|Nodata_value|NoData Value|None|None|0.0
##output_raster=output raster

from osgeo import gdal
from osgeo import gdalconst
import math
import numpy as np

gdal.AllRegister()
progress.setText("processing...")

raster = gdal.Open(input_raster)
rasterBand = raster.GetRasterBand(1)
try:
    data = rasterBand.ReadAsArray()
except:
    raise GeoAlgorithmExecutionException('Error reading raster data. File might be too big.')

raster_data = np.log10(np.ma.masked_values(data, Nodata_value))*10.

# write data
frmt = "GTiff"
driver = gdal.GetDriverByName(frmt)
bandCount = raster.RasterCount
rasterXSize = raster.RasterXSize
rasterYSize = raster.RasterYSize
geotransform = raster.GetGeoTransform()
projection = raster.GetProjectionRef()
if driver is None:
        raise IOError("cannot get driver of {}".format(frmt))
out_ds = driver.Create(output_raster, rasterXSize, rasterYSize, 1, gdalconst.GDT_Float32)
if out_ds is None:
    raise IOError("cannot create file of {}".format(filename))
if not geotransform is None:
    out_ds.SetGeoTransform(geotransform)
if not projection is None:
    out_ds.SetProjection(projection)
out_ds.GetRasterBand(1).WriteArray(raster_data, 0, 0)
out_ds=None

progress.setText("Finished!")