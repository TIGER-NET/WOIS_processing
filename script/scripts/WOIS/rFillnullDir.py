#Definition of inputs and outputs
#==================================
##Timeseries=group
##r.fillnulls for directory=name
##ParameterRaster|inputFileDir|An image in the input directory|False
##ParameterSelection|method|Method|bilinear;bicubic;rst|2
##ParameterNumber|tension|Spline tension parameter|None|None|40.0
##ParameterNumber|smooth|Spline smoothing parameter|None|None|0.1
##ParameterFile|outputDir|Output directory|True|
##ParameterExtent|extent|Region extent|
##ParameterNumber|cellSize|Region cellsize (leave 0 for default)|0.0|None|0.0

 
#Algorithm body
#==================================

import os
import glob
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException

oldDir = os.getcwd()

progress.setText("Looking for input files.")
# find all the images in the input directory
os.chdir(os.path.dirname(inputFileDir))
fileName, fileExtension = os.path.splitext(inputFileDir)
matchingFiles =  glob.glob("*"+fileExtension)
matchingFiles.sort()

os.chdir(oldDir)

# run grass:r.fillnulls for each image
progress.setText("Starting r.fillnulls executions")
iteration = 1.0
for image in matchingFiles:
    progress.setPercentage(int(iteration/float(len(matchingFiles))*100))
    progress.setText("Processing image: "+os.path.basename(image))
    params={'input':os.path.dirname(inputFileDir)+os.sep+image, 'method':method, 'tension':tension, 'smooth':smooth, 'GRASS_REGION_CELLSIZE_PARAMETER':cellSize, \
            'GRASS_REGION_PARAMETER':extent, 'output':outputDir+os.sep+os.path.basename(image)}
    if processing.runalg("grass:r.fillnulls", params):
        iteration +=1
    else:
        raise GeoAlgorithmExecutionException("Unable to execute script \"r.fillnulls for directory\". Check Processing log for details.")
progress.setText("Finished!")