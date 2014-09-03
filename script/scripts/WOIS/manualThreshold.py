##Flood mapping=group
##Manual Threshold=name
##input_raster=raster
##ParameterNumber|Nodata_value|NoData Value|None|None|0.0
##ParameterBoolean|Lower_than|Lower than|True
##ParameterNumber|threshold|Threshold|None|None|-14.0
##classified_raster=output raster


from osgeo import gdal
from osgeo import gdalconst
from processing.tools import dataobjects

gdal.AllRegister()
progress.setText("processing image...")

raster = gdal.Open(input_raster)
rasterBand = raster.GetRasterBand(1)
try:
    data = rasterBand.ReadAsArray()
except:
    raise GeoAlgorithmExecutionException('Error reading raster data. File might be too big.')
nodata_idx = data==Nodata_value
bool_raster = data<threshold if Lower_than else data>threshold
byte_raster = bool_raster.astype("uint8")
byte_raster[nodata_idx] = 255

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
out_ds = driver.Create(classified_raster, rasterXSize, rasterYSize, 1, gdalconst.GDT_Byte)
if out_ds is None:
    raise IOError("cannot create file of {}".format(filename))
if not geotransform is None:
    out_ds.SetGeoTransform(geotransform)
if not projection is None:
    out_ds.SetProjection(projection)
out_ds.GetRasterBand(1).WriteArray(byte_raster, 0, 0)
out_ds=None

progress.setText("Finished!")