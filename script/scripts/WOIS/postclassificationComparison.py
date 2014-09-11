#Definition of inputs and outputs
#==================================
##Post-classification comparison=name
##Timeseries=group
##ParameterRaster|classification|Select classification of "initial state" |False
##ParameterRaster|reference|Select classification of "final state"|False
##ParameterBoolean|w|Wide report (132 columns)|False
##ParameterExtent|extent|Region extent|
##OutputFile|output|Name for output file containing the change detection matrix

#Algorithm body
#==================================

import os
from processing.tools.system import tempFolder
from processing.core.ProcessingLog import ProcessingLog

loglines = []
loglines.append('Post-classification comparison script console output')
loglines.append('')

# set up the actual and temporary outputs
outputFile = open(output, 'w')
outputFile.close()
tempOutput = tempFolder() + os.sep + "postclassificationComparisionScript.txt"
if os.path.exists(tempOutput):
    os.remove(tempOutput)

if processing.runalg("grass:r.kappa",classification,reference,'CHANGE DETECTION MATRIX',True,w,extent,tempOutput):
    with open(tempOutput) as inputFile, open(output, "a") as outputFile:
        lines = inputFile.readlines()
        writeLines = False
        for line in lines:
            if line.startswith('Cats') or line.startswith('cat#'):
                break
            if writeLines:
                outputFile.write(line)
            elif line.startswith('Error Matrix'):
                writeLines = True
                outputFile.write('Change detection matrix\n')
    progress.setText('Saved change detection matrix to file %s' % output)
    loglines.append('Saved change detection matrix to file %s' % output)
    ProcessingLog.addToLog(ProcessingLog.LOG_INFO, loglines)
else:
    progress.setText('ERROR running r.kappa. Check log for details.')
    loglines.append('ERROR running r.kappa. Check log for details.')
    ProcessingLog.addToLog(ProcessingLog.LOG_INFO, loglines)