#Definition of inputs and outputs
#==================================
##Normalise image=name
##Image processing=group
##ParameterRaster|input|Input image|False
##OutputRaster|output|Name for output raster map
 
#Algorithm body
#==================================
from processing.tools.system import tempFolder
import os
from processing.tools import dataobjects
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException

# temporary file to hold the raster statistics

statsFileName = tempFolder() + os.sep + "rNormaliseRasterOut.txt"
if os.path.exists(statsFileName):
    os.remove(statsFileName)
  
layer = dataobjects.getObjectFromUri(input)
extent = str(layer.extent().xMinimum())+","+str(layer.extent().xMaximum())+","+str(layer.extent().yMinimum())+","+str(layer.extent().yMaximum())

# can't use OTB second order statistics as it include no-value value in the stats
# get the mean and std dev of the input raster
progress.setText("Calculating image statistics...")
params = {'map': input, 'zones': None, '-e': False, '-g': False, '-t': False, 'percentile': 90, 'GRASS_REGION_PARAMETER': extent, 'output': statsFileName}
if not(processing.runalg("grass:r.univar", params) and os.path.exists(statsFileName)):
    raise GeoAlgorithmExecutionException("Unable to execute script \"Normalise image\". Can not compute image statistics. Check SEXTANTE log for details.")

# open the stats file and read out the mean and standard deviation
KEYWORDS = ['mean', 'deviation']
mean = 0
stddev = 1
statsFile = open(statsFileName, "r").readlines()
for line in statsFile:
    words = line.split()
    for word in words:
        if word == "mean:":
            mean = words[words.index(word)+1]
        if word == "deviation:":
            stddev = words[words.index(word)+1]

# now use OTB band math to normalise
progress.setText("Normalising...")
expression = "(im1b1-"+str(mean)+")/"+str(stddev)
params = {'-il':input, '-ram':512, '-exp':expression,'-out':output}
if not(processing.runalg("otb:bandmath", params) and os.path.exists(output)):
    raise GeoAlgorithmExecutionException("Unable to execute script \"Normalise image\". Can not perform band math normalisation. Check SEXTANTE log for details.")
progress.setText("Finished!")