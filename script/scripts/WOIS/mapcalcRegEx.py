#Definition of inputs and outputs
#==================================
##Timeseries=group
##OTB Band Math for temporal data=name
##ParameterRaster|dataDir1|im1 - An image located in the time-series 1 directory|False
##ParameterString|filenameFormat1|im1 filename, with date string replaced by Y,M and D (e.g. NDVI_YYYYMMDD_africa.tif)|
##ParameterRaster|dataDir2|im2 - An image located in the time-series 2 directory|True
##ParameterString|filenameFormat2|im2 filename, with date string replaced by Y,M and D (e.g. NDVI_YYYYMMDD_africa.tif)|
##ParameterRaster|dataDir3|im3 - An image located in the time-series 3 directory|True
##ParameterString|filenameFormat3|im3 filename, with date string replaced by Y,M and D (e.g. NDVI_YYYYMMDD_africa.tif)|
##ParameterFile|outputDir|Output directory|True
##ParameterString|outputFileFormat|Output images filename, with YMD where the date string is supposed to be (eg. NDVI_YMD_alaska.tif)|
##ParameterSelection|groupBy|Pair images by|year-month;year-month-day;year;month;day;decadal
##ParameterString|expression|Band math expression (eg. im1b1+im2b1)|
##ParameterNumber|ram|Available RAM (Mb)|None|None|128
 
#Algorithm body
#==================================

import os
import re
from processing.core.ProcessingLog import ProcessingLog
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException

class mapCalcRegExUtil():

    def __init__(self):
        None

    def getInputOutputFiles(self, dataDir, filenameFormat, dataDir2, filenameFormat2, dataDir3, filnameFormat3, outputFileFormat, inputFiles, outputFiles, groupBy):
        
        # Get a list of all files matching the filename format in the input directories
        fileList1 = list()
        fileList2 = list()
        fileList3 = list()
             
        # regular expression to match the "group-by" date string in the first filename format
        if dataDir:
            match1 = self.matchFiles(dataDir, filenameFormat, groupBy, fileList1)
            if match1:
                startDateString = match1.start(1)
                lengthDateString = match1.end(1)-match1.start(1)
                dateRegex1 = "(?<=^.{"+str(startDateString)+"})\d{"+str(lengthDateString)+"}" 
                fileList1.sort()
        
        # regular expression to match the "group-by" date in the second filename format
        if dataDir2:
            match2 = self.matchFiles(dataDir2, filenameFormat2, groupBy, fileList2) 
            if match2:
                startDateString = match2.start(1)
                lengthDateString = match2.end(1)-match2.start(1)
                dateRegex2 = "(?<=^.{"+str(startDateString)+"})\d{"+str(lengthDateString)+"}" 
                fileList2.sort()
        
        # regular expression to match the "group-by" date in the third filename format
        if dataDir3:
            match3 = self.matchFiles(dataDir3, filnameFormat3, groupBy, fileList3) 
            if match3:
                startDateString = match3.start(1)
                lengthDateString = match3.end(1)-match3.start(1)
                dateRegex3 = "(?<=^.{"+str(startDateString)+"})\d{"+str(lengthDateString)+"}" 
                fileList3.sort()
        
        # regular expression to match the full date in the first filename format
        # this will be the datestring of the output files
        startDateString = match1.start()
        lengthDateString = match1.end()-match1.start()
        fullDateRegex = "(?<=^.{"+str(startDateString)+"})\d{"+str(lengthDateString)+"}"         
        
        # now group the files from the three lists according to the "group-by" date
        for filename in fileList1:
            match = re.search(fullDateRegex,filename)
            if not match:
                continue
            fullDate = match.group()
            groupByDate1 = (re.search(dateRegex1,filename)).group()
            
            # if the other groups are empty, do one image bandmath
            if len(fileList2) == 0 and len(fileList3) == 0:
                inputFiles[fullDate] = dataDir+os.sep+filename 
                continue
            
            for filename2 in fileList2:
                match2 = re.search(dateRegex2, filename2)
                if not match2:
                    continue
                groupByDate2 = match2.group()
                if groupByDate2 == groupByDate1:
                    inputFiles[fullDate] = dataDir+os.sep+filename +";"+dataDir2+os.sep+filename2
                    break
            for filename3 in fileList3:
                match3 = re.search(dateRegex3, filename3)
                if not match3:
                    continue
                groupByDate3= match3.group()
                if groupByDate3 == groupByDate2 and groupByDate2 == groupByDate1:
                    inputFiles[fullDate] = inputFiles[fullDate] +";"+dataDir3+os.sep+filename3
                    break
                elif groupByDate3 == groupByDate1:
                    inputFiles[fullDate] = dataDir+os.sep+filename +";"+dataDir3+os.sep+filename3
                    break
                
        # create an output filename for date
        for date in inputFiles:
            outputFile = re.sub('YMD', str(date), outputFileFormat)
            outputFile = re.sub("\..{2,4}$", ".tif", outputFile) # make sure it's a tiff
            outputFiles[date] = outputFile

    
    def matchFiles(self, dataDir, filenameFormat, groupBy, matchingFiles):
        
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
            regex = 'Y{0,4}(M{2}D{1})D{0,2}'
        else:
            regex = '[YMD]{2,8}'
        
        # first find where the date string is located in the filename and construct a 
        # regex to match it
        match = re.search(regex, filenameFormat)
        if not match:
            ProcessingLog.addToLog(ProcessingLog.LOG_INFO, "No match for date string in filename format!")
            return None
        matchLength = match.end()-match.start()
        matchingFormat = re.sub(regex, "\d{"+str(matchLength)+"}", filenameFormat)
        matchingFormat += "$"
        
        # find all the matching files in the data dir
        os.chdir(dataDir)
        for filename in os.listdir("."):
            if re.search(matchingFormat, filename):
                matchingFiles.append(filename)
        return match


groupFiles = dict()
outputFiles = dict()

dataPath1 = None
dataPath2 = None
dataPath3 = None

oldDir = os.getcwd()

utils = mapCalcRegExUtil()
# pair the files from the two input dirs based on the group-by date
progress.setText("Looking for matching files.")
if dataDir1:
    dataPath1 = os.path.dirname(dataDir1)
if dataDir2:
    dataPath2 = os.path.dirname(dataDir2)
if dataDir3:
    dataPath3 = os.path.dirname(dataDir3)
utils.getInputOutputFiles(dataPath1, filenameFormat1, dataPath2, filenameFormat2, dataPath3, filenameFormat3, outputFileFormat, groupFiles, outputFiles, groupBy)
# run otb:bandmath for each pair of files
os.chdir(oldDir)
progress.setText("Starting OTB band math executions")
iteration = 1.0
for date in groupFiles:
    progress.setPercentage(int(iteration/float(len(groupFiles))*100))
    progress.setText("Processing date string: "+date)
    params = {'-il':groupFiles[date], '-ram':ram, '-exp':expression,'-out':outputDir+os.sep+outputFiles[date]}
    if processing.runalg("otb:bandmath", params):
        iteration +=1
    else:
        raise GeoAlgorithmExecutionException("Unable to execute script \"OTB Band Math for temporal data\". Check SEXTANTE log for details.")
progress.setText("Finished!")

