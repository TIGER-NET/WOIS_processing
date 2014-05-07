#Definition of inputs and outputs
#==================================
##Timeseries=group
##GRASS r.univar for timeseries=name
##ParameterFile|map|Name of input raster map(s)|False|False
##ParameterRaster|zones|Raster map used for zoning, must be of type CELL|True
##*ParameterBoolean|e|Calculate extended statistics|False
##*ParameterNumber|percentile|Percentile to calculate (requires extended statistics flag)|0.0|100.0|90
##OutputFile|output|Name for output text file

#Algorithm body
#==================================

import os
from qgis.core import *
from sextante.core.QGisLayers import QGisLayers
from sextante.grass.GrassUtils import GrassUtils
from sextante.core.SextanteUtils import SextanteUtils
from sextante.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException


def setMinExtent(layer, zones):
    xMinimum = max(layer.extent().xMinimum(), zones.extent().xMinimum())
    xMaximum = min(layer.extent().xMaximum(), zones.extent().xMaximum())
    yMinimum = max(layer.extent().yMinimum(), zones.extent().yMinimum())
    yMaximum = min(layer.extent().yMaximum(), zones.extent().yMaximum())
    return str(xMinimum)+","+str(xMaximum)+","+str(yMinimum)+","+str(yMaximum)

layers = map.split(";")
if not (layers == None or len(layers) == 0):
    GrassUtils.startGrassSession()
    iteration = 1.0
        
    # set up the actual and temporary outputs
    outputFile = open(output, 'w')
    outputFile.close()
    tempOutput = SextanteUtils.tempFolder() + os.sep + "rUnivarScriptOut.txt"
    if os.path.exists(tempOutput):
        os.remove(tempOutput)
    
    # get the zones cover raster layer
    zonesLayer = QGisLayers.getObjectFromUri(zones)
    
    # run r.univar individually for each input raster        
    for layername in layers:
        layer = QGisLayers.getObjectFromUri(layername)
        if isinstance(layer, QgsRasterLayer):
            if zonesLayer:
                extent = setMinExtent(layer, zonesLayer)
            else:
                extent = setMinExtent(layer, layer)
            progress.setPercentage(int(iteration / float(len(layers)) * 100))
            progress.setText("Processing image: " + layername)
            params = {'map': layername, 'zones': zones, '-e': e, '-g': False, '-t': True, 'percentile': percentile, 'GRASS_REGION_PARAMETER': extent, 'output': tempOutput}
            if sextante.runalg("grass:r.univar", params) and os.path.exists(tempOutput):
                # copy the output from the temporary to actual output file
                with open(tempOutput) as inputFile, open(output, "a") as outputFile:
                    outputFile.write(layername + "\n")
                    outputFile.write(inputFile.read())
                iteration += 1
            else:
                GrassUtils.endGrassSession()
                raise GeoAlgorithmExecutionException("Unable to execute script \"GRASS r.univar for timeseries\". Check SEXTANTE log for details.")
                
    progress.setText("Finished!")
    GrassUtils.endGrassSession()
