##Product generation=group
##Backscatter Normalization=name
##sigma0=raster
##ParameterNumber|Sigma0_Nodata_value|sigma0 nodata|None|None|0.0
##local_incidence_angle=raster
##ParameterNumber|Lia_Nodata_value|lia nodata|None|None|0.0
##ParameterNumber|ria|reference inclidence angle|None|None|50
####parameter_database=folder
##output_raster=output raster


import os
import numpy as np
import sys
from osgeo import osr
import glob
import datetime

if not os.path.dirname(scriptDescriptionFile) in sys.path:
    sys.path.append(os.path.join(os.path.dirname(scriptDescriptionFile), "ancillary"))

import gdalport
from Equi7Grid import Equi7Grid

def get_slope(sigma0, p_db, temp_slope, compress=True):
    
    # get needed information from dataset
    temp_ds = gdalport.open_image(sigma0)
    extent = temp_ds.get_extent()
    project = temp_ds.projection()
    geot = temp_ds.geotransform()
    
    # create grid system
    grid = Equi7Grid()
    area = [(extent[0], extent[1]), (extent[2], extent[1]),
                    (extent[2], extent[3]), (extent[0], extent[3])]
    
    
    # get the resolution of reprojected sigma0
    sigma_sr = osr.SpatialReference()
    sigma_sr.ImportFromWkt(project)
    para_sr = osr.SpatialReference()
    para_sr.ImportFromWkt(grid.get_projection("AF"))
    tx = osr.CoordinateTransformation(sigma_sr, para_sr)
    x1, _, _ = tx.TransformPoint(geot[0], geot[3])
    x2, _, _ = tx.TransformPoint(geot[0]+geot[1], geot[3])
    res_in_meter = np.abs(x2-x1)
    
    # close dataset
    temp_ds = None
    
    # search subfolder for different resolutions   
    found_tiles = None
    subfolders = [ x for x in os.listdir(p_db) if os.path.isdir(os.path.join(p_db, x)) and x.startswith("AF")]
    # sort the subfolder in a certain order
    best_subfolder_index = np.argmin([np.fabs(res_in_meter-int(x[2:])) for x in subfolders])
    subfolders[0: best_subfolder_index+1] = subfolders[best_subfolder_index::-1]
    
    for subfolder in subfolders:
    # file tiles
        res = int(subfolder[2:])
        tiles = grid.search_tiles(area, project, res=res)
        exist_status = [os.path.exists(os.path.join(p_db, subfolder, tile)) for tile in tiles]
        if all(exist_status):
            corr_tiles = [glob.glob(os.path.join(p_db, subfolder, tile, "*SLOPE*_{}.tif".format(tile))) for tile in tiles]
            if all(corr_tiles):
                found_tiles = [tiles[0] for tiles in corr_tiles]
                break

    if found_tiles is None:
        progress.setText("Error: slope parameters are not available in the current parameter database!")
        return False
    
    options = {}
    #if compress:
    #    options["co"] = "COMPRESS=LZW"
    options["srcnodata"] = -9999
    options["dstnodata"] = -9999
    ret, info = gdalport.call_gdalwarp(found_tiles, temp_slope, t_srs=project,
                           te=" ".join(map(str, extent)), tr="{} {}".format(geot[1], geot[5]),
                           of="GTiff", r="bilinear", **options)
    if not ret:
        progress.setText("ERROR: \n" + info)
    return ret


def main():
    # parameters
    if ria>80 or ria<10:
        progress.setText("Error: Reference incidence angle cannot greater than 80 or less than 10!")
        return
    output_dir = os.path.dirname(output_raster)
    parameter_path = os.path.join(parameter_database, "EQUI7", "params_sgrt")
    if not os.path.exists(parameter_path):
        progress.setText("Error: cannot find valid parameters in the parameter database!")
        return
    if not os.path.exists(sigma0):
        progress.setText("Error: sigma0 image does not exist!")
        return
    if not os.path.exists(local_incidence_angle):
        progress.setText("Error: local incidence angle image does not exist!")
        return
    
    temp_slope_path = os.path.join(output_dir, "__temp_slope_{}.tif".format(datetime.datetime.now().strftime("%Y%m%d%H%M%S")))
    if not get_slope(sigma0, parameter_path, temp_slope_path):
        return

    # sigma
    sigma0_ds = gdalport.open_image(sigma0)
    sigma0_arr = sigma0_ds.read_band(1)
    lia = gdalport.open_image(local_incidence_angle).read_band(1)
    slope = gdalport.open_image(temp_slope_path).read_band(1)

    # mask the invalid region
    #idx = (sigma0_arr != Sigma0_Nodata_value) & (lia != Lia_Nodata_value) & (slope!=-9999)
    idx = (np.abs(sigma0_arr - Sigma0_Nodata_value) > 0.000001) & (np.abs(lia - Lia_Nodata_value) > 0.000001) & (slope!=-9999)
    normalization = np.empty_like(sigma0_arr)
    normalization[:] = -9999 #Sigma0_Nodata_value
    normalization[idx] = sigma0_arr[idx] - slope[idx] * (lia[idx] - ria)

    # ouput
    gdalport.write_image(normalization, output_raster, nodata=[-9999], geotransform=sigma0_ds.geotransform(),
                        projection=sigma0_ds.projection(), option=["COMPRESS=LZW"])
    sigma0_ds = None
    os.remove(temp_slope_path)
    progress.setText("Done!")


# main entry
main()