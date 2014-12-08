#Definition of inputs and outputs
#==================================
##Timeseries=group
##GRASS r.series for whole directory=name
##ParameterRaster|dataDir|An image file located in the data directory|False
##ParameterString|filenameFormat|Input images filename, with date string replaced by Y,M and D (e.g. NDVI_YYYYMMDD_africa.tif)|
##ParameterFile|outputDir|Output directory|True
##ParameterString|outputFileFormat|Output images filename, with YMD where the date string is supposed to be (eg. NDVI_YMD_alaska.tif)|
##ParameterSelection|groupBy|Aggregation condition|year-month;year-month-day;year;month;day;decadal;format
##ParameterBoolean|propagateNulls|Propagate NULLs|True
##ParameterSelection|operation|Aggregate operation|average;count;median;mode;minimum;min_raster;maximum;max_raster;stddev;range;sum;variance;diversity;slope;offset;detcoeff;quart1;quart3;perc90;skewness;kurtosis                                                   
##*ParameterString|range|Ignore values outside this range (lo,hi)|-10000000000,10000000000
##ParameterExtent|extent|Region extent|
##ParameterNumber|cellSize|Region cellsize (leave 0 for default)|0.0|None|0.0
 
#Algorithm body
#==================================

import os
import glob
import re
import datetime
from PyQt4.QtGui import *
from processing.core.ProcessingLog import ProcessingLog
from processing.algs.grass.GrassUtils import GrassUtils
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException


def convertDatetoDoy(dateString, lengthYearString, lengthMonthString, lengthDayString):
    try:
        year = int(dateString[0:lengthYearString])
    except:
        year = 1
    try:
        month = int(dateString[lengthYearString:lengthYearString + lengthMonthString])
    except:
        month = 1
    try:
        day = int(dateString[lengthYearString + lengthMonthString:lengthYearString + lengthMonthString + lengthDayString])
    except:
        day = 1
    
    # If day string has a length of 3 it means that it already represents a doy    
    if lengthDayString == 3:
        doy = day
    # Otherwise calculate doy
    else:
        doy = datetime.datetime(year = year, month = month, day = day) - datetime.datetime(year = year, month = 1, day = 1)
        doy = doy.days + 1
    
    yearDoyStr = "%04d%03d" % (year, doy)
    return yearDoyStr       

def getFiles(dataDir, filenameFormat, outputFileFormat, groupFiles, outputFiles, groupBy):

    # year-month
    if groupBy == 0:
        regex = '(Y{2,4}M{2})D{0,3}'
    # year-month-day
    elif groupBy == 1:
        regex = '(Y{2,4}M{2}D{2,3})'
    # year
    elif groupBy == 2:
        regex = '(Y{2,4})M{0,2}D{0,3}'
    # month
    elif groupBy == 3:
        regex = 'Y{0,4}(M{2})D{0,3}'
    # day
    elif groupBy == 4:
        regex = 'Y{0,4}M{0,2}(D{2,3})'
    # decadal
    elif groupBy == 5:
        regex = '((Y{0,4})(M{0,2})(D{2,3}))'
    # whole directory
    elif groupBy == 6:
        fileName, fileExtension = os.path.splitext(filenameFormat)
        regex = '('+fileName+')'+fileExtension
    else:
        return
    
    # first find where the date string is located in the filename and construct a 
    # regex to match it
    match = re.search(regex, filenameFormat)
    if not match:
        progress.setText("No match for date string in filename format!")
        loglines.append("No match for date string in filename format!")
        return
    startDateString = match.start(1)
    lengthDateString = match.end(1)-match.start(1)
    # if grouping by format the regex has to be different to when grouping by date
    if groupBy == 6:
        dateRegex = fileExtension+"$"
    else:
        dateRegex = "(?<=^.{"+str(startDateString)+"})\d{"+str(lengthDateString)+"}" 
    # then replace it with * to find all the files that match the filename format
    matchingFormat = re.sub(regex, "*", filenameFormat)
    
    # For decadal grouping need to save the length of year, month and day strings
    # to be able to convert the date to doy later on
    if groupBy == 5:
        lengthYearString = len(match.group(2))
        lengthMonthString = len(match.group(3))
        lengthDayString = len(match.group(4))
    
    # find all the matching files in the data dir
    os.chdir(dataDir)
    matchingFiles =  sorted(glob.glob(matchingFormat))
    
    # now group them according to the date
    for filename in matchingFiles:
        match = re.search(dateRegex,filename)
        if not match:
            continue
        # If aggregation is by decade and the datestring doesn't specify DOY then DOY must be
        # calculated so that the images can be grouped by year and last two digits of DOY
        if groupBy == 5:
            date = convertDatetoDoy(match.group(), lengthYearString, lengthMonthString, lengthDayString)
            # need to subtract 1 and add 10 since decade 1 has days 1-10, decade 2 has days 11-20, etc. 
            date = str(int(date)-1+10)[:-1]
        else:
            date = match.group()
        if date in groupFiles:
            groupFiles[date] += ";"+dataDir+os.sep+filename
        else:
            groupFiles[date] = dataDir+os.sep+filename             
    # create an output filename for date
    for date in groupFiles:
        outputFile = re.sub('YMD', str(date), outputFileFormat)
        outputFile = re.sub("\..{2,4}$", ".tif", outputFile) # make sure it's a tiff
        outputFiles[date] = outputFile
        

groupFiles = dict()
outputFiles = dict()

loglines = []
loglines.append('GRASS r.series for whole directory script console output')
loglines.append('')

oldDir = os.getcwd()

progress.setText("Looking for matching files.")
getFiles(os.path.dirname(dataDir), filenameFormat, outputFileFormat, groupFiles, outputFiles, groupBy)

os.chdir(oldDir)

if len(groupFiles) == 0 or len(outputFiles) == 0:
    progress.setText("No matching files found! r.series will not be executed.")
    loglines.append("No matching files found! r.series will not be executed.")
else:
    # run r.series for each group of files
    GrassUtils.startGrassSession()
    progress.setText("Starting GRASS r.series executions")
    loglines.append("Starting GRASS r.series executions")
    iteration = 1.0
    for date in sorted(groupFiles.iterkeys()):
        progress.setPercentage(int(iteration/float(len(groupFiles))*100))
        progress.setText("Processing date string: "+date)
        loglines.append("Processing date string: "+date)
        params={'input':groupFiles[date], '-n':propagateNulls, 'method':operation, \
                'range':range, 'GRASS_REGION_CELLSIZE_PARAMETER':cellSize, 'GRASS_REGION_PARAMETER':extent, 'output':outputDir+os.sep+outputFiles[date]}
        if processing.runalg("grass:r.series",params):
            iteration +=1
        else:
            GrassUtils.endGrassSession()
            raise GeoAlgorithmExecutionException("Unable to execute script \"GRASS r.series for whole directory\". Check SEXTANTE log for details.")
    progress.setText("Finished!")
    loglines.append("Finished!")
    GrassUtils.endGrassSession()
    
ProcessingLog.addToLog(ProcessingLog.LOG_INFO, loglines)