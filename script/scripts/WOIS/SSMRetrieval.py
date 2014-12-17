##Product generation=group
##Soil Moisture Retrieval=name
##ParameterSelection|Sensor|Sensor type|ASAR;Sentinel-1
##sigma0=raster
##ParameterNumber|Sigma0_Nodata_value|sigma0 nodata|None|None|0.0
##local_incidence_angle=raster
##ParameterNumber|Lia_Nodata_value|lia nodata|None|None|0.0
##parameter_database=folder
##output_raster=output raster


import os
import sys
import shutil
import numpy as np
import glob
import datetime

if not os.path.dirname(scriptDescriptionFile) in sys.path:
    sys.path.append(os.path.join(os.path.dirname(scriptDescriptionFile), "ancillary"))
import gdalport
import Equi7Grid


def get_parameter(sigma0, p_db, param_name, outfilename, compress=True):
    
    # get needed information from dataset
    temp_ds = gdalport.open_image(sigma0)
    extent = temp_ds.get_extent()
    project = temp_ds.projection()
    geot = temp_ds.geotransform()
    
    # create grid system
    grid = Equi7Grid.Equi7Grid()
    area = [(extent[0], extent[1]), (extent[2], extent[1]),
                    (extent[2], extent[3]), (extent[0], extent[3])]
    # close dataset
    temp_ds = None
    
    # file tiles
    found_tiles = None  
    tiles = grid.search_tiles(area, project, res=500)
    exist_status = [os.path.exists(os.path.join(p_db, "AF500", tile)) for tile in tiles]
    if all(exist_status):
        param_tiles = [glob.glob(os.path.join(p_db, "AF500", tile, "*{}*_{}.tif".format(param_name, tile))) for tile in tiles]
        if all(param_tiles):
            found_tiles = [tiles[0] for tiles in param_tiles]

    if found_tiles is None:
        progress.setText("Error: {} parameters are not available in the current parameter database!".format(param_name))
        return False
    
    options = {}
    #if compress:
    #    options["co"] = "COMPRESS=LZW"
    options["srcnodata"] = -9999
    options["dstnodata"] = -9999
    ret,info = gdalport.call_gdalwarp(found_tiles, outfilename, t_srs=project,
                           te=" ".join(map(str, extent)), tr="{} {}".format(geot[1], geot[5]),
                           of="GTiff", r="bilinear", **options)
    if not ret:
        progress.setText("ERROR: \n" + info)
    return ret


def retrieve_surface_soil_moisture(sigma0_path, sigma0_nodata, lia_path, lia_nodata,
                          sensor, para_db_path, outfilename):
    ssm_res = 0.00416667
    default_nodata = -9999
    # make temp dir
    temp_dir = os.path.join(os.path.dirname(outfilename), "__temp_{}.tif".format(datetime.datetime.now().strftime("%Y%m%d%H%M%S")))
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)
    para_db_path = os.path.join(para_db_path, "EQUI7", "params_sgrt")
    # resample image to 500 Meter(0.00416667 degree)
    progress.setText("Resampling ... ")
    sigma0_ds = gdalport.open_image(sigma0_path)
    extent = sigma0_ds.get_extent()
    project = sigma0_ds.projection()
    options = {}
    options["co"] = "COMPRESS=LZW"
    options["srcnodata"] = sigma0_nodata
    options["dstnodata"] = sigma0_nodata
    temp_sigma0 = os.path.join(temp_dir, "__temp_{}".format(os.path.basename(sigma0_path)))
    gdalport.call_gdalwarp([sigma0_path], temp_sigma0, t_srs=project,
                           te=" ".join(map(str, extent)), tr="{} {}".format(ssm_res, -ssm_res),
                           of="GTiff", r="average", **options)
    temp_lia = os.path.join(temp_dir, "__temp_{}".format(os.path.basename(lia_path)))
    options["srcnodata"] = lia_nodata
    options["dstnodata"] = lia_nodata
    gdalport.call_gdalwarp([lia_path], temp_lia, t_srs=project,
                           te=" ".join(map(str, extent)), tr="{} {}".format(ssm_res, -ssm_res),
                           of="GTiff", r="average", **options)
    
    # print info
    progress.setText("Retrieving SSM ... ")
    # get the parameters
    dry_path = os.path.join(temp_dir, "__temp_dry_{}".format(os.path.basename(sigma0_path)))
    if not get_parameter(temp_sigma0, para_db_path, "DRY30", dry_path, compress=True):
        return
    wet_path = os.path.join(temp_dir, "__temp_wet_{}".format(os.path.basename(sigma0_path)))
    if not get_parameter(temp_sigma0, para_db_path, "WET30", wet_path, compress=True):
        return
    slope_path = os.path.join(temp_dir, "__temp_slope_{}".format(os.path.basename(sigma0_path)))
    if not get_parameter(temp_sigma0, para_db_path, "SLOPE", slope_path, compress=True):
        return
    
    # soil moisture retrieval
    sigma0 = gdalport.open_image(temp_sigma0).read_band(1)
    plia = gdalport.open_image(temp_lia).read_band(1)
    slope = gdalport.open_image(slope_path).read_band(1)
    dry = gdalport.open_image(dry_path).read_band(1)
    wet = gdalport.open_image(wet_path).read_band(1)
    
    idx = (np.abs(sigma0 - sigma0_nodata) > 0.000001) & (np.abs(plia - lia_nodata) > 0.000001) \
        & (slope != default_nodata) & (dry != default_nodata) & (wet != default_nodata)
    if sensor == "ASAR":
        sigma0[idx] = sigma0[idx] - slope[idx] * (plia[idx] - 30)
    else:
        dry[idx] = dry[idx] + slope[idx] * (plia[idx] - 30)
        wet[idx] = wet[idx] + slope[idx] * (plia[idx] - 30)
    
    ssm = np.empty_like(sigma0)
    ssm[:] = -9999
    ssm[idx] = (sigma0[idx] - dry[idx]) / (wet[idx] - dry[idx])
    #mask
    mask1_path = os.path.join(temp_dir, "__temp_mask1_{}".format(os.path.basename(sigma0_path)))
    if get_parameter(temp_sigma0, para_db_path, "MASK1", mask1_path, compress=True):
        mask = gdalport.open_image(mask1_path).read_band(1)
        mask_idx = mask!=0
        ssm[mask_idx] = default_nodata
    # ouput the ssm
    geot = sigma0_ds.geotransform()
    new_geot = [geot[0],ssm_res, 0, geot[3], 0, -ssm_res]
    gdalport.write_image(ssm, outfilename, geotransform=new_geot, nodata=[default_nodata],
                        projection=sigma0_ds.projection(), option=["COMPRESS=LZW"])
    # progress.setText("Done!")
    sigma0_ds = None
    shutil.rmtree(temp_dir)

def start_algorithm():
    # parameters validation
    if not os.path.isdir(parameter_database):
        progress.setText("Error: parameter database does not exist.")
        return
    para_db_path = os.path.join(parameter_database, "EQUI7", "params_sgrt")
    if not os.path.isdir(para_db_path):
        progress.setText("Error: cannot find valid parameters in the parameter database!")
        return
    
    if not os.path.exists(sigma0):
        progress.setText("Error: sigma0 image does not exist!")
        return
    if not os.path.exists(local_incidence_angle):
        progress.setText("Error: local incidence angle image does not exist!")
        return

    # start processing
    retrieve_surface_soil_moisture(sigma0, Sigma0_Nodata_value, local_incidence_angle, Lia_Nodata_value, Sensor, parameter_database, output_raster)
    progress.setText("Done!")

   
# start process
start_algorithm()
