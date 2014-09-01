#Definition of inputs and outputs
#==================================
##Download from FTP=name
##Tools=group
##ParameterString|host|FTP server address|
##ParameterString|username|Username|
##ParameterString|password|Password|
##ParameterString|remoteDir|Remote Directory|
##ParameterFile|localDir|Local Directory|True|False
##*ParameterExtent|newExtent|Extent to subset after downloading|0,1,0,1|
##ParameterString|timestamp|Download files modified since (date in YYYYMMDDhhmmss format)|
##ParameterBoolean|overwrite|Overwrite existing files|True
 
#Algorithm body
#==================================
import ftplib
import os
import re
import socket
from osgeo import gdal
from gdalconst import *
from processing.core.ProcessingLog import ProcessingLog

regex='\d{14}'
SUBSET = 1
DONOTSUBSET = 2
FTPRECONNECT = -1

tmpFileList = list();

def downloadFile(filename, f, loglines):
    
    # check if the file already exists and if we want to overwrite
    localFile = localDir + os.sep + filename
    if os.path.isfile(localFile) and not overwrite:
        return DONOTSUBSET
    
    # check that the file not a directory
    try:
        f.nlst('"'+filename + os.sep+'"')
    except Exception:
        pass
    else:
        return DONOTSUBSET
    
    # check if timestamp is given and if the remote file has a later date then timestamp
    if timestamp.strip():
        cmd = 'MDTM %s' % filename
        try:
            timeStr = f.sendcmd(cmd)
        except ftplib.all_errors:
            progress.setText('ERROR: cannot obtain timestamp for file %s' % filename)
            loglines.append('ERROR: cannot obtain timestamp for file %s' % filename)
            return FTPRECONNECT
        try:
            match = re.search(regex, timeStr)
            if match:
                if len(timestamp) > len(match.group(0)):
                    progress.setText('ERROR: invalid user specified timestamp')
                    loglines.append('ERROR: invalid user specified timestamp')
                    return DONOTSUBSET
                else:
                    timeRemote = int(match.group(0)[0:len(timestamp)])
                    timeLocal = int(timestamp)
        except ValueError:
            progress.setText('ERROR: invalid user specified or remote timestamp for %s' % filename)
            loglines.append('ERROR: invalid user specified or remote timestamp for %s' % filename)
            return DONOTSUBSET
        if timeRemote < timeLocal:
            return DONOTSUBSET
        
    # download the file
    try:
        progress.setText('Downloading file %s ...' %filename)
        f.retrbinary('RETR %s' % filename, open(localFile, 'wb').write)
    except ftplib.all_errors:
        progress.setText('ERROR: cannot read file "%s"' % filename)
        loglines.append('ERROR: cannot read file "%s"' % filename)
        return FTPRECONNECT
    else:
        progress.setText('Downloaded "%s" to %s' % (filename, localDir))
        loglines.append('Downloaded "%s" to %s' % (filename, localDir))
    
    return SUBSET


def subsetToExtent(filename):
    # if no extent is specified do not subset
    if newExtent == "0,1,0,1":
        return
    
    # otherwise get the subset extent coordinates
    extents = newExtent.split(",")
    try:
        [nxmin, nxmax, nymin, nymax] = [float(i) for i in extents]
    except ValueError:
        progress.setText('Invalid subset extent !')
        return    
    
    # rename the downloaded file to a temp filename
    tmpFilename = localDir + os.sep + "tmp_" + filename
    localFilename = localDir + os.sep + filename
    try:
        if os.path.exists(tmpFilename):
            os.remove(tmpFilename)
        os.rename(localFilename,tmpFilename)
    except:
        None
    
    # It would be easier to get the raster extents using QgsRasterLayer and not GDAL but
    # there is a bug in QgsRasterLayer that crashes QGIS "randomly" when opening a layer.
    # Maybe it's fixed in QGIS 2.0
    #layer = QGisLayers.getObjectFromUri(tmpFilename)
    #xmin = max(xmin, layer.extent().xMinimum())
    #xmax = min(xmax, layer.extent().xMaximum())
    #ymin = max(ymin, layer.extent().yMinimum())
    #ymax = min(ymax, layer.extent().yMaximum())
    
    # get the minimum extent of the subset extent and the file extent  
    try:
        inlayer = gdal.Open(tmpFilename, GA_ReadOnly)   
    except:
        progress.setText('Cannot get layer info ! Not subsetting.')
        return
            
    if not inlayer:
        progress.setText('Cannot get layer info !! Not subsetting.')
        return
            
        
    # get the raster extent coordinates using GDAL
    geoinformation = inlayer.GetGeoTransform(can_return_null = True)

    if geoinformation:
        cols = inlayer.RasterXSize
        rows = inlayer.RasterYSize
        tlX = geoinformation[0] # top left X
        tlY = geoinformation[3] # top left Y
        brX = geoinformation[0] + geoinformation[1] * cols + geoinformation[2] * rows # bottom right X
        brY = geoinformation[3] + geoinformation[4] * cols + geoinformation[5] * rows # bottom right Y

        xmin = min(tlX, brX)
        xmax = max(tlX, brX)
        ymin = min(tlY, brY)
        ymax = max(tlY, brY)
    else:
        progress.setText('Cannot get layer info !!! Not subsetting.')
        inlayer = None
        return  
    inlayer = None
    
    xmin = max(nxmin, xmin)
    xmax = min(nxmax, xmax)
    ymin = max(nymin, ymin)
    ymax = min(nymax, ymax)
        
    # call gdal_translate to perform the subsetting
    progress.setText('Subsetting')
    subsetExtent = str(xmin)+","+str(xmax)+","+str(ymin)+","+str(ymax)
    param = {'INPUT':tmpFilename, 'OUTSIZE':100, 'OUTSIZE_PERC':True, 'NO_DATA':"none", 'EXPAND':0, 'SRS':'', 'PROJWIN':subsetExtent, 'EXTRA':'-co "COMPRESS=LZW"', 'SDS':False, 'OUTPUT':localFilename}
    if not processing.runalg("gdalogr:translate",param):
        progress.setText('Problems with subsetting "%s"' % filename)
        loglines.append('Problems with subsetting "%s"' % filename)      
    for filename in tmpFileList:
        try:
            os.remove(filename)
            tmpFileList.remove(filename)
        except:
            None;
    tmpFileList.append(tmpFilename)
    progress.setText('Subsetting finished!')  
            
            
def ftpConnect(loglines):
    progress.setText('Connecting to FTP!') 
    loglines.append('Connecting to FTP!')
    try:
        f = ftplib.FTP(host, timeout = 10)
    except (socket.error, socket.gaierror), e:
        progress.setText('ERROR: cannot reach "%s"' % host)
        loglines.append('ERROR: cannot reach "%s"' % host)
        return None
    progress.setText('Connected to host "%s"' % host)
    loglines.append('Connected to host "%s"' % host)
    
    try:
        f.login(username, password)
    except ftplib.error_perm:
        progress.setText('ERROR: cannot login with provided username and password')
        loglines.append('ERROR: cannot login with provided username and password')
        f.close()
        return None
    progress.setText('Logged in as %s' % username)
    loglines.append('Logged in as %s' % username)
    
    try:
        f.cwd(remoteDir)
    except ftplib.error_perm:
        progress.setText('ERROR: cannot CD to "%s"' % remoteDir)
        loglines.append('ERROR: cannot CD to "%s"' % remoteDir)
        f.close()
        return None
    progress.setText('Changed to "%s" folder' % remoteDir)
    loglines.append('Changed to "%s" folder' % remoteDir)
    
    return f
            
def ftpDownload(loglines):
    
    f = ftpConnect(loglines)
    if not f:
        return

    try:
        files = f.nlst()
    except ftplib.error_perm:
        try:
            f.set_pasv(False)
            files = f.nlst()
        except:
            progress.setText('ERROR: can not retrieve file listing from FTP server.')
            loglines.append('ERROR: can not retrieve file listing from FTP server.')
            f.close()
            return
    
    for filename in files:
        for count in range(1,3): 
            if f:
                res = downloadFile(filename, f, loglines)
            else:
                res = FTPRECONNECT
            if res == FTPRECONNECT:
                try:
                    f.close()
                except:
                    None
                f = ftpConnect(loglines)
            else:
                break
        if count == 3:
            progress.setText('ERROR: can not establish connection with the server!')
            loglines.append('ERROR: can not establish connection with the server!') 
        if res == SUBSET:
            subsetToExtent(filename) 
                
    
    progress.setText('Finished!')
    loglines.append('Finished!')
    f.close()
    
    for tmpFile in tmpFileList:
        try:
            os.remove(tmpFile)
        except:
            progress.setText('WARNING: can not delete temporary file "%s"' %tmpFile)
            loglines.append('WARNING: can not delete temporary file "%s"' %tmpFile)
    return




loglines = []
loglines.append('Download from FTP script console output')
loglines.append('')

# create the local directory if it doesn't exist
if not os.path.isdir(localDir):
    try:
        os.makedirs(localDir)
        progress.setText('Created local directory %s' % localDir)
        loglines.append('Created local directory %s' % localDir)
    except:
        progress.setText('Can not create local directory %s' % localDir)
        loglines.append('Can not create local directory %s' % localDir)
    
if os.path.isdir(localDir):
    ftpDownload(loglines)
    
ProcessingLog.addToLog(ProcessingLog.LOG_INFO, loglines)
