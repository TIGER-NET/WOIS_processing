#Definition of inputs and outputs
#==================================
##Timeseries=group
##Build Virtual Raster - directory=name
##ParameterRaster|inFile|Image located in input directory |False
##ParameterSelection|resolution|Resolution|average;highest;lowest
##ParameterBoolean|separate|Layer stack|True
##ParameterBoolean|proj_difference|Allow projection difference|False
##OutputRaster|outputFile|Output file|False
 
#Algorithm body
#==================================

import os

# Get file extension from the example file and the directory
rasterExt = os.path.splitext(inFile)[1]
dataDir = os.path.dirname(inFile)

# Get all the files in the same directory with the same extension
fileList = list()
for path, subdirs, files in os.walk(dataDir):
    for name in files:
        progress.setText(name)
        if name.endswith(rasterExt):
            progress.setText("File found")
            fileList.append(os.path.join(path,name)) 
fileList.sort()

# convert the file list to string
fileListStr = ""
for fileName in fileList:
    fileListStr = fileListStr + fileName + ";"
 
# rename the output to end with .vrt so that QGIS can open the file automaticall
if not (os.path.splitext(outputFile)[1]) == '.vrt':
    outputFile = os.path.splitext(outputFile)[0]+'.vrt'

# call gdalbuildvrt
processing.runalg("gdalogr:buildvirtualraster", {'INPUT': fileListStr, 'SEPARATE':True, 'OUTPUT':outputFile}) 