#XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
#Author: Georg Siroky
#Institution: Materials Center Leoben
#Description:   callAbq defines a Parameterset for PeriodicModel.py and calls PeriodicModel.py in abaqus.
#               The results are loaded after the jobs has finished and two plot are generated
#XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
import os
import pickle
import numpy as np
import sys

ToolsDir="C:/Users/yourDir"
InputDir="C:/Users/yourDir"
WorkDir="C:/Users/yourDir"

#import Abaqus Toolbox
sys.path.append(ToolsDir)
from tools import*

#XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
#Write Paramter File
os.chdir(WorkDir)
#Parameters for evaluation of model
Parameters=[['CubeSize', 1.]]
pickle.dump(Parameters, open("Parameters.p", "wb"))
#XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

#XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
#Define abaqus executable
executable= 'abq2017'
#Directory of input file
os.chdir(InputDir)
inputfile='PeriodicModel.py'
jobname='RVE'
#Execute python script in abaqus
call = executable + ' cae noGUI=' + inputfile + ' > ' + jobname + '.out 2>&1'
os.system(call)
#XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

#XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
#Open Data and Plot Results
os.chdir(WorkDir)
#Open Results file
resultsName='Results.p'
DataExport=pickle.load(open(resultsName, "rb"))
#XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
#XXXXXXXXXXXXXXXXXXXXXXXXx  Plot Stress over Time  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
#Define Plot Discription 
plotControl=[["Visco tdisp=1s",'g','Time [s]','Stress [MPa]', 'Creep Response']]

nSets=len(DataExport)
ii=0
name=jobname+'Creep'
x=[[] for i in xrange(nSets)]
y=[[] for i in xrange(nSets)]
#Open export data file of multiple evaluations
for iData in DataExport:
    #read time steps
    for tstep in iData:
        x[ii].append(tstep[1])
        y[ii].append(tstep[2])
    ii+=1
#create plot
plot=SimplePlot(x,y,plotControl,name)
#XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
#XXXXXXXXXXXXXXXXXXXXXXXXx  Plot Stress over Strain  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
#Define Plot Discription 
plotControl=[["Visco tdisp=1s",'g','Strain [%]','Stress [MPa]', 'Creep Response']]

nSets=len(DataExport)
ii=0
name=jobname+'StressStrain'
x=[[] for i in xrange(nSets)]
y=[[] for i in xrange(nSets)]
#Open export data file of multiple evaluations
for iData in DataExport:
    #read time steps
    for tstep in iData:
        x[ii].append(tstep[3]*100)
        y[ii].append(tstep[2])
    ii+=1
#create plot
plot2=SimplePlot(x,y,plotControl,name)
