#XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
#Author: Georg Siroky
#Institution: Materials Center Leoben
#Description: 	Generates a cube with periodic boundary conditions. Applying uniaxial strain to it.
#				Postprocessing: Evaluates strain and stress over all elements. Exports to "Data Export"
#XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *
import mesh
import os
import numpy as np
import time
import platform
import pickle

#Identify System
System=platform.system()
#Initialize ---------------------------------------------------------------------
startTime=time.time()
if System == 'Linux':
	os.chdir(r"/home/yourDir")
elif System == 'Windows':
	WorkDir="C:/Users/yourDir"
	os.chdir(WorkDir)

#import Parameters
Parameters=pickle.load(open("Parameters.p","rb"))
DataExport=[]

for iParameters in Parameters:
	
	file=open("Test_results.txt","w")
	file.write("\n")
	file.close()
	####################################################################################################################
	##Initialising
	#CubeSize
	a = iParameters[1]
	#Elements per Edge
	n =8
	#Selection Box Size
	dist = a*1.0e-003
	#Temperature
	T0=(20+273.)

	jobName='RVE'
	CreepType='None'
	Element=C3D8R

	timeApplyDisp=2
	timeRelaxation=2

	SubmitJob=True
	WriteInput=True
	Postprocessing=True
	####################################################################################################################

	#Create Cube
	mdb.close()
	myModel = mdb.Model(name='one')
	del mdb.models['Model-1']
	mdb.models['one'].ConstrainedSketch(name='__profile__', sheetSize=
		200.0)
	mdb.models['one'].sketches['__profile__'].rectangle(point1=(0.0, 0.0)
		, point2=(a,a))
	mdb.models['one'].Part(dimensionality=THREE_D, name='Mikromech_8mal8', type=
		DEFORMABLE_BODY)
	mdb.models['one'].parts['Mikromech_8mal8'].BaseSolidExtrude(depth=a, 
		sketch=mdb.models['one'].sketches['__profile__'])
	del mdb.models['one'].sketches['__profile__']


	#Materialdata
	mdb.models['one'].Material(name='Mat')
	mdb.models['one'].materials['Mat'].Elastic(table=((55000.0, 0.3), ))
	mdb.models['one'].materials['Mat'].Density(table=((7.8e-9, ), ))
	#mdb.models['one'].materials['Mat'].Plastic(table=((200.0, 0.0), (255.0, 0.0005),(260.,3)))
	if CreepType=='Power':
		mdb.models['one'].materials['Mat'].Plastic(table=((200.0, 0.0), (255.0, 0.0005),(260.,30)))	#250.0, 0.0), (260.0, 0.0005),(265.,3) #hardening=MULTILINEAR_KINEMATIC
		mdb.models['one'].materials['Mat'].Creep(law=TIME, table=((7.e-24, 7.5, -0.9),))	#8.9e-33, 18
	elif CreepType=='Sinh':
		mdb.models['one'].materials['Mat'].Plastic(hardening=MULTILINEAR_KINEMATIC,table=((200.0, 0.0), (255.0, 0.0005), (260., 30)))
		mdb.models['one'].materials['Mat'].Creep(law=HYPERBOLIC_SINE, table=((1.23e-5, 0.05, 6.0,45000,8.314),)) #A,alpha,n,Q,R,
		mdb.models['one'].setValues(absoluteZero=0.)
	elif CreepType=='Visco':
		mdb.models['one'].materials['Mat'].Plastic(hardening=COMBINED,table=((200.0, 0.0), (255.0, 0.0005), (260., 0.001)))
		mdb.models['one'].materials['Mat'].plastic.CyclicHardening(parameters=ON, table=((200.0, 10.0, 0.10),))
		mdb.models['one'].materials['Mat'].Viscous(law=TIME, table=((6.e-8,5.5,0 ,0.001), ))
	elif CreepType=='Visco1':
		mdb.models['one'].materials['Mat'].Plastic(hardening=MULTILINEAR_KINEMATIC,table=((200.0, 0.0), (255.0, 0.0005), (260., 30)))
		mdb.models['one'].materials['Mat'].Viscous(law=TIME, table=((6.e-8,5.5,0 ,0.001), ))
	else:
		print 'No Creep Law implemented'

	#Material			
	mdb.models['one'].HomogeneousSolidSection(material='Mat', name='Section-Mat', thickness=None)

	#Sections
	allcells = mdb.models['one'].parts['Mikromech_8mal8'].cells
	regionCells=(mdb.models['one'].parts['Mikromech_8mal8'].cells,)				

	mdb.models['one'].parts['Mikromech_8mal8'].SectionAssignment(offset=0.0, 
		offsetField='', offsetType=MIDDLE_SURFACE, region=regionCells, sectionName='Section-Mat', thicknessAssignment=FROM_SECTION)				

	##Meshing
	mdb.models['one'].parts['Mikromech_8mal8'].Set(cells=mdb.models['one'].parts['Mikromech_8mal8'].cells.getByBoundingBox(0.0,0.0,0.0,a,a,a), name ='Alles')
	#Global Seeds
	mdb.models['one'].parts['Mikromech_8mal8'].seedPart(deviationFactor=0.1, minSizeFactor=0.1, size=a/n)

	#Elementtype
	#Linear
	RegionRVE=mdb.models['one'].parts['Mikromech_8mal8'].Set(cells=allcells, name='Set-RVE')

	elemType = mesh.ElemType(elemCode=Element, elemLibrary=STANDARD)
	mdb.models['one'].parts['Mikromech_8mal8'].setElementType(regions=RegionRVE, elemTypes=(elemType,))
		
	#Mesh
	mdb.models['one'].parts['Mikromech_8mal8'].generateMesh()
	mdb.models['one'].rootAssembly.regenerate()

	#Assembly
	mdb.models['one'].rootAssembly.DatumCsysByDefault(CARTESIAN)
	mdb.models['one'].rootAssembly.Instance(dependent=ON,name='Mikromech_8mal8', part=mdb.models['one'].parts['Mikromech_8mal8'])

	mdb.models['one'].rootAssembly.allInstances['Mikromech_8mal8']

	#Define Temperature field
	AllCells = mdb.models['one'].rootAssembly.allInstances['Mikromech_8mal8'].cells.getByBoundingBox(xMin=0., yMin=0., zMin=0., xMax=a, yMax=a, zMax=a)
	TempRegion = mdb.models['one'].rootAssembly.Set(cells=AllCells, name='Set-Temp')
	mdb.models['one'].Temperature(name='Predefined Field-1', createStepName='Initial', region=TempRegion,distributionType=UNIFORM, crossSectionDistribution=CONSTANT_THROUGH_THICKNESS,magnitudes=(T0,))

	#Steps
	#Step Apply Tension
	mdb.models['one'].ViscoStep(name='ApplyTension', previous='Initial', timePeriod=timeApplyDisp, initialInc=0.00001,minInc=1e-20, maxInc=timeApplyDisp, cetol=0.1,amplitude=RAMP)
	mdb.models['one'].Temperature(name='Predefined Field-2', createStepName='ApplyTension', region=TempRegion, distributionType=UNIFORM, crossSectionDistribution=CONSTANT_THROUGH_THICKNESS,magnitudes=(T0,))

	mdb.models['one'].FieldOutputRequest(name='F-Output-ApplyDisp1',
		createStepName='ApplyTension', variables=('S', 'MISES', 'MISESMAX', 'TSHR',
		'CTSHR', 'ALPHA', 'TRIAX', 'VS', 'PS', 'CS11', 'ALPHAN', 'SSAVG', 
		'MISESONLY', 'PRESSONLY', 'E', 'VE', 'PE', 'VEEQ', 'PEEQ', 'PEEQT', 
		'PEEQMAX', 'PEMAG', 'PEQC', 'EE', 'IE', 'THE', 'NE', 'LE', 'ER', 'SE', 
		'SPE', 'SEPE', 'SEE', 'SEP', 'SALPHA', 'U', 'UT', 'UR', 'V', 'VT', 
		'VR', 'RBANG', 'RBROT', 'RF', 'RT', 'RM', 'CF', 'SF', 'TF', 'VF', 
		'ESF1', 'NFORC', 'NFORCSO', 'RBFOR', 'BF', 'CORIOMAG', 'ROTAMAG', 
		'CENTMAG', 'CENTRIFMAG', 'GRAV', 'P', 'HP', 'TRSHR', 'TRNOR'))

	#Referencepoints	REFS, REFD
	mdb.models['one'].rootAssembly.ReferencePoint(point=(0.0, 0.0, 0.0))
	mdb.models['one'].rootAssembly.features.changeKey(fromName='RP-1', 
		toName='REFD')
	mdb.models['one'].rootAssembly.ReferencePoint(point=(0.0, 0.0, 0.0))
	mdb.models['one'].rootAssembly.features.changeKey(fromName='RP-1', 
		toName='REFS')
	mdb.models['one'].rootAssembly.features['REFS'].suppress()
	mdb.models['one'].rootAssembly.Set(name='REFD', referencePoints=(
		mdb.models['one'].rootAssembly.referencePoints[5], ))
	mdb.models['one'].rootAssembly.features['REFS'].resume()
	mdb.models['one'].rootAssembly.features['REFD'].suppress()
	mdb.models['one'].rootAssembly.Set(name='REFS', referencePoints=(
		mdb.models['one'].rootAssembly.referencePoints[6], ))
	mdb.models['one'].rootAssembly.features['REFD'].resume()


	#####################################################################################################################################################################################
	##Create PBCs
	#####################################################################################################################################################################################
	#Faces
	#*************************************************************************************************************************************************************************************

	#Facesets, Equations: X X _
	k = 0
	FXX0 = []
	FXXL = []
	for y in range(int(n)-1):
		for x in range(int(n)-1):
			FXX0.append(mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox((x+1.0)*a/n-dist, (y+1.0)*a/n-dist, -dist, (x+1.0)*a/n+dist, (y+1.0)*a/n+dist, dist))
			FXXL.append(mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox((x+1.0)*a/n-dist, (y+1.0)*a/n-dist, a-dist, (x+1.0)*a/n+dist, (y+1.0)*a/n+dist, a+dist))
			mdb.models['one'].rootAssembly.Set(name='FXX0_'+str(k+1), nodes=FXX0[k])
			mdb.models['one'].rootAssembly.Set(name='FXXL_'+str(k+1), nodes=FXXL[k])
			#Equations
			mdb.models['one'].Equation(name='FXXL_XX0_1_' +str(k+1), terms=((1.0, 'FXXL_'+str(k+1), 1), (-1.0, 'FXX0_'+str(k+1), 1), (-1.0, 'REFS', 3)))
			mdb.models['one'].Equation(name='FXXL_XX0_2_' +str(k+1), terms=((1.0, 'FXXL_'+str(k+1), 2), (-1.0, 'FXX0_'+str(k+1), 2), (-1.0, 'REFS', 2)))
			mdb.models['one'].Equation(name='FXXL_XX0_3_' +str(k+1), terms=((1.0, 'FXXL_'+str(k+1), 3), (-1.0, 'FXX0_'+str(k+1), 3), (-1.0, 'REFD', 3)))
			k = k+1	

	#Facesets, Equations: X _ X
	k = 0
	FX0X = []
	FXLX = []
	for z in range(int(n)-1):
		for x in range(int(n)-1):
			FX0X.append(mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox((x+1.0)*a/n-dist, -dist, (z+1.0)*a/n-dist, (x+1.0)*a/n+dist, dist, (z+1.0)*a/n+dist))
			FXLX.append(mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox((x+1.0)*a/n-dist, a-dist, (z+1.0)*a/n-dist, (x+1.0)*a/n+dist, a+dist, (z+1.0)*a/n+dist))
			mdb.models['one'].rootAssembly.Set(name='FX0X_'+str(k+1), nodes=FX0X[k])
			mdb.models['one'].rootAssembly.Set(name='FXLX_'+str(k+1), nodes=FXLX[k])
			#Equations
			mdb.models['one'].Equation(name='FXLX_X0X_1_' +str(k+1), terms=((1.0, 'FXLX_'+str(k+1), 1), (-1.0, 'FX0X_'+str(k+1), 1), (-1.0, 'REFS', 1)))
			mdb.models['one'].Equation(name='FXLX_X0X_2_' +str(k+1), terms=((1.0, 'FXLX_'+str(k+1), 2), (-1.0, 'FX0X_'+str(k+1), 2), (-1.0, 'REFD', 2)))
			mdb.models['one'].Equation(name='FXLX_X0X_3_' +str(k+1), terms=((1.0, 'FXLX_'+str(k+1), 3), (-1.0, 'FX0X_'+str(k+1), 3), (-1.0, 'REFS', 2)))
			k = k+1	

	#Facesets, Equations: _ X X
	k = 0
	F0XX = []
	FLXX = []		
	for z in range(int(n)-1):
		for y in range(int(n)-1):
			F0XX.append(mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox(-dist, (y+1.0)*a/n-dist, (z+1.0)*a/n-dist, dist, (y+1.0)*a/n+dist, (z+1.0)*a/n+dist))
			FLXX.append(mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox(a-dist, (y+1.0)*a/n-dist, (z+1.0)*a/n-dist, a+dist, (y+1.0)*a/n+dist, (z+1.0)*a/n+dist))
			mdb.models['one'].rootAssembly.Set(name='F0XX_'+str(k+1), nodes=F0XX[k])
			mdb.models['one'].rootAssembly.Set(name='FLXX_'+str(k+1), nodes=FLXX[k])
			#Equations
			mdb.models['one'].Equation(name='FLXX_0XX_1_' +str(k+1), terms=((1.0, 'FLXX_'+str(k+1), 1), (-1.0, 'F0XX_'+str(k+1), 1), (-1.0, 'REFD', 1)))
			mdb.models['one'].Equation(name='FLXX_0XX_2_' +str(k+1), terms=((1.0, 'FLXX_'+str(k+1), 2), (-1.0, 'F0XX_'+str(k+1), 2), (-1.0, 'REFS', 1)))
			mdb.models['one'].Equation(name='FLXX_0XX_3_' +str(k+1), terms=((1.0, 'FLXX_'+str(k+1), 3), (-1.0, 'F0XX_'+str(k+1), 3), (-1.0, 'REFS', 3)))
			k = k+1
			
	###########################################################################################################################################################################################
	#Lines
	#**************************************************************************************************************************************************************************************

	#Edgesets: _ _ X
	k = 0
	E00X = []
	EL0X = []
	E0LX = []
	ELLX = []
	for z in range(int(n)-1):
		E00X.append(mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox(-dist, -dist, (z+1.0)*a/n-dist, dist, dist, (z+1.0)*a/n+dist))
		EL0X.append(mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox(a-dist, -dist, (z+1.0)*a/n-dist, a+dist, dist, (z+1.0)*a/n+dist))
		E0LX.append(mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox(-dist, a-dist, (z+1.0)*a/n-dist, dist, a+dist, (z+1.0)*a/n+dist))
		ELLX.append(mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox(a-dist, a-dist, (z+1.0)*a/n-dist, a+dist, a+dist, (z+1.0)*a/n+dist))
		mdb.models['one'].rootAssembly.Set(name='E00X_'+str(k+1), nodes=E00X[k])
		mdb.models['one'].rootAssembly.Set(name='EL0X_'+str(k+1), nodes=EL0X[k])
		mdb.models['one'].rootAssembly.Set(name='E0LX_'+str(k+1), nodes=E0LX[k])
		mdb.models['one'].rootAssembly.Set(name='ELLX_'+str(k+1), nodes=ELLX[k])
		k = k+1
		
	#Edgesets: _ X _
	k = 0
	E0X0 = []
	ELX0 = []
	E0XL = []
	ELXL = []	
	for y in range(int(n)-1):
		E0X0.append(mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox(-dist, (y+1.0)*a/n-dist, -dist, dist, (y+1.0)*a/n+dist, dist))
		ELX0.append(mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox(a-dist, (y+1.0)*a/n-dist, -dist, a+dist, (y+1.0)*a/n+dist, dist))
		E0XL.append(mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox(-dist, (y+1.0)*a/n-dist, a-dist, dist, (y+1.0)*a/n+dist, a+dist))
		ELXL.append(mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox(a-dist, (y+1.0)*a/n-dist, a-dist, a+dist, (y+1.0)*a/n+dist, a+dist))
		mdb.models['one'].rootAssembly.Set(name='E0X0_'+str(k+1), nodes=E0X0[k])
		mdb.models['one'].rootAssembly.Set(name='ELX0_'+str(k+1), nodes=ELX0[k])
		mdb.models['one'].rootAssembly.Set(name='E0XL_'+str(k+1), nodes=E0XL[k])
		mdb.models['one'].rootAssembly.Set(name='ELXL_'+str(k+1), nodes=ELXL[k])
		k = k+1
		
	#Edgesets: _ X _
	for k in range(len(E0X0)):
		mdb.models['one'].Equation(name='E0XL_0X0_1_'+str(k+1), terms=((1.0, 'E0XL_'+str(k+1), 1), (-1.0, 'E0X0_'+str(k+1), 1), (-1.0, 'REFS', 3)))
		mdb.models['one'].Equation(name='E0XL_0X0_2_'+str(k+1), terms=((1.0, 'E0XL_'+str(k+1), 2), (-1.0, 'E0X0_'+str(k+1), 2), (-1.0, 'REFS', 2)))
		mdb.models['one'].Equation(name='E0XL_0X0_3_'+str(k+1), terms=((1.0, 'E0XL_'+str(k+1), 3), (-1.0, 'E0X0_'+str(k+1), 3), (-1.0, 'REFD', 3)))
		
		mdb.models['one'].Equation(name='ELX0_0X0_1_'+str(k+1), terms=((1.0, 'ELX0_'+str(k+1), 1), (-1.0, 'E0X0_'+str(k+1), 1), (-1.0, 'REFD', 1)))
		mdb.models['one'].Equation(name='ELX0_0X0_2_'+str(k+1), terms=((1.0, 'ELX0_'+str(k+1), 2), (-1.0, 'E0X0_'+str(k+1), 2), (-1.0, 'REFS', 1)))
		mdb.models['one'].Equation(name='ELX0_0X0_3_'+str(k+1), terms=((1.0, 'ELX0_'+str(k+1), 3), (-1.0, 'E0X0_'+str(k+1), 3), (-1.0, 'REFS', 3)))
		
		mdb.models['one'].Equation(name='ELXL_0X0_1_'+str(k+1), terms=((1.0, 'ELXL_'+str(k+1), 1), (-1.0, 'E0X0_'+str(k+1), 1), (-1.0, 'REFD', 1), (-1.0, 'REFS', 3)))
		mdb.models['one'].Equation(name='ELXL_0X0_2_'+str(k+1), terms=((1.0, 'ELXL_'+str(k+1), 2), (-1.0, 'E0X0_'+str(k+1), 2), (-1.0, 'REFS', 1), (-1.0, 'REFS', 2)))
		mdb.models['one'].Equation(name='ELXL_0X0_3_'+str(k+1), terms=((1.0, 'ELXL_'+str(k+1), 3), (-1.0, 'E0X0_'+str(k+1), 3), (-1.0, 'REFD', 3), (-1.0, 'REFS', 3)))

	#Edgesets: _ _ X
	for k in range(len(E00X)):
		mdb.models['one'].Equation(name='EL0X_00X_1_'+str(k+1), terms=((1.0, 'EL0X_'+str(k+1), 1), (-1.0, 'E00X_'+str(k+1), 1), (-1.0, 'REFD', 1)))
		mdb.models['one'].Equation(name='EL0X_00X_2_'+str(k+1), terms=((1.0, 'EL0X_'+str(k+1), 2), (-1.0, 'E00X_'+str(k+1), 2), (-1.0, 'REFS', 1)))
		mdb.models['one'].Equation(name='EL0X_00X_3_'+str(k+1), terms=((1.0, 'EL0X_'+str(k+1), 3), (-1.0, 'E00X_'+str(k+1), 3), (-1.0, 'REFS', 3)))
		
		mdb.models['one'].Equation(name='E0LX_00X_1_'+str(k+1), terms=((1.0, 'E0LX_'+str(k+1), 1), (-1.0, 'E00X_'+str(k+1), 1), (-1.0, 'REFS', 1)))
		mdb.models['one'].Equation(name='E0LX_00X_2_'+str(k+1), terms=((1.0, 'E0LX_'+str(k+1), 2), (-1.0, 'E00X_'+str(k+1), 2), (-1.0, 'REFD', 2)))
		mdb.models['one'].Equation(name='E0LX_00X_3_'+str(k+1), terms=((1.0, 'E0LX_'+str(k+1), 3), (-1.0, 'E00X_'+str(k+1), 3), (-1.0, 'REFS', 2)))
		
		mdb.models['one'].Equation(name='ELLX_00X_1_'+str(k+1), terms=((1.0, 'ELLX_'+str(k+1), 1), (-1.0, 'E00X_'+str(k+1), 1), (-1.0, 'REFD', 1), (-1.0, 'REFS', 1)))
		mdb.models['one'].Equation(name='ELLX_00X_2_'+str(k+1), terms=((1.0, 'ELLX_'+str(k+1), 2), (-1.0, 'E00X_'+str(k+1), 2), (-1.0, 'REFS', 1), (-1.0, 'REFD', 2)))
		mdb.models['one'].Equation(name='ELLX_00X_3_'+str(k+1), terms=((1.0, 'ELLX_'+str(k+1), 3), (-1.0, 'E00X_'+str(k+1), 3), (-1.0, 'REFS', 3), (-1.0, 'REFS', 2)))
		
	#Edgesets + Equations: X _ _
	k = 0
	EX00 = []
	EXL0 = []
	EX0L = []
	EXLL = []
	for x in range(int(n)-1):
		EX00.append(mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox((x+1.0)*a/n-dist, -dist, -dist, (x+1.0)*a/n+dist, dist, dist))
		EXL0.append(mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox((x+1.0)*a/n-dist, a-dist, -dist, (x+1.0)*a/n+dist, a+dist, dist))
		EX0L.append(mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox((x+1.0)*a/n-dist, -dist, a-dist, (x+1.0)*a/n+dist, dist, a+dist))
		EXLL.append(mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox((x+1.0)*a/n-dist, a-dist, a-dist, (x+1.0)*a/n+dist, a+dist, a+dist))
		mdb.models['one'].rootAssembly.Set(name='EX00_'+str(k+1), nodes=EX00[k])
		mdb.models['one'].rootAssembly.Set(name='EXL0_'+str(k+1), nodes=EXL0[k])
		mdb.models['one'].rootAssembly.Set(name='EX0L_'+str(k+1), nodes=EX0L[k])
		mdb.models['one'].rootAssembly.Set(name='EXLL_'+str(k+1), nodes=EXLL[k])
		#Equations
		mdb.models['one'].Equation(name='EXL0_X00_1_' +str(k+1), terms=((1.0, 'EXL0_'+str(k+1), 1), (-1.0, 'EX00_'+str(k+1), 1), (-1.0, 'REFS', 1)))
		mdb.models['one'].Equation(name='EXL0_X00_2_' +str(k+1), terms=((1.0, 'EXL0_'+str(k+1), 2), (-1.0, 'EX00_'+str(k+1), 2), (-1.0, 'REFD', 2)))
		mdb.models['one'].Equation(name='EXL0_X00_3_' +str(k+1), terms=((1.0, 'EXL0_'+str(k+1), 3), (-1.0, 'EX00_'+str(k+1), 3), (-1.0, 'REFS', 2)))

		mdb.models['one'].Equation(name='EX0L_X00_1_' +str(k+1), terms=((1.0, 'EX0L_'+str(k+1), 1), (-1.0, 'EX00_'+str(k+1), 1), (-1.0, 'REFS', 3)))
		mdb.models['one'].Equation(name='EX0L_X00_2_' +str(k+1), terms=((1.0, 'EX0L_'+str(k+1), 2), (-1.0, 'EX00_'+str(k+1), 2), (-1.0, 'REFS', 2)))
		mdb.models['one'].Equation(name='EX0L_X00_3_' +str(k+1), terms=((1.0, 'EX0L_'+str(k+1), 3), (-1.0, 'EX00_'+str(k+1), 3), (-1.0, 'REFD', 3)))
			
		mdb.models['one'].Equation(name='EXLL_X00_1_'+str(k+1), terms=((1.0, 'EXLL_'+str(k+1), 1), (-1.0, 'EX00_'+str(k+1), 1), (-1.0, 'REFS', 1), (-1.0, 'REFS', 3)))
		mdb.models['one'].Equation(name='EXLL_X00_2_'+str(k+1), terms=((1.0, 'EXLL_'+str(k+1), 2), (-1.0, 'EX00_'+str(k+1), 2), (-1.0, 'REFD', 2), (-1.0, 'REFS', 2)))
		mdb.models['one'].Equation(name='EXLL_X00_3_'+str(k+1), terms=((1.0, 'EXLL_'+str(k+1), 3), (-1.0, 'EX00_'+str(k+1), 3), (-1.0, 'REFS', 2), (-1.0, 'REFD', 3)))
		k =k+1
		
	######################################################################################################################################################################################
	#Corners	
	#**************************************************************************************************************************************************************************************

	#Cornersets
	C000 = mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox(-dist, -dist, -dist, dist, dist, dist)
	CL00 = mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox(1.0-dist, -dist, -dist, 1.0+dist, dist, dist)
	C0L0 = mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox(-dist, 1.0-dist, -dist, dist, 1.0+dist, dist)
	C00L = mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox(-dist, -dist, 1.0-dist, dist, dist, 1.0+dist)
	CLL0 = mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox(1.0-dist, 1.0-dist, -dist, 1.0+dist, 1.0+dist, dist)
	CL0L = mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox(1.0-dist, -dist, 1.0-dist, 1.0+dist, dist, 1.0+dist)
	C0LL = mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox(-dist, 1.0-dist, 1.0-dist, dist, 1.0+dist, 1.0+dist)
	CLLL = mdb.models['one'].rootAssembly.instances['Mikromech_8mal8'].nodes.getByBoundingBox(1.0-dist, 1.0-dist, 1.0-dist, 1.0+dist, 1.0+dist, 1.0+dist)

	mdb.models['one'].rootAssembly.Set(name='C000', nodes=C000)
	mdb.models['one'].rootAssembly.Set(name='CL00', nodes=CL00)
	mdb.models['one'].rootAssembly.Set(name='C0L0', nodes=C0L0)
	mdb.models['one'].rootAssembly.Set(name='C00L', nodes=C00L)
	mdb.models['one'].rootAssembly.Set(name='CLL0', nodes=CLL0)
	mdb.models['one'].rootAssembly.Set(name='CL0L', nodes=CL0L)
	mdb.models['one'].rootAssembly.Set(name='C0LL', nodes=C0LL)
	mdb.models['one'].rootAssembly.Set(name='CLLL', nodes=CLLL)

	mdb.models['one'].Equation(name='CL00_1', terms=((1.0, 'CL00', 1), (-1.0, 'C000', 1), (-1.0, 'REFD', 1)))
	mdb.models['one'].Equation(name='CL00_2', terms=((1.0, 'CL00', 2), (-1.0, 'C000', 2), (-1.0, 'REFS', 1)))
	mdb.models['one'].Equation(name='CL00_3', terms=((1.0, 'CL00', 3), (-1.0, 'C000', 3), (-1.0, 'REFS', 3)))

	mdb.models['one'].Equation(name='C0L0_1', terms=((1.0, 'C0L0', 1), (-1.0, 'C000', 1), (-1.0, 'REFS', 1)))
	mdb.models['one'].Equation(name='C0L0_2', terms=((1.0, 'C0L0', 2), (-1.0, 'C000', 2), (-1.0, 'REFD', 2)))
	mdb.models['one'].Equation(name='C0L0_3', terms=((1.0, 'C0L0', 3), (-1.0, 'C000', 3), (-1.0, 'REFS', 2)))

	mdb.models['one'].Equation(name='C00L_1', terms=((1.0, 'C00L', 1), (-1.0, 'C000', 1), (-1.0, 'REFS', 3)))
	mdb.models['one'].Equation(name='C00L_2', terms=((1.0, 'C00L', 2), (-1.0, 'C000', 2), (-1.0, 'REFS', 2)))
	mdb.models['one'].Equation(name='C00L_3', terms=((1.0, 'C00L', 3), (-1.0, 'C000', 3), (-1.0, 'REFD', 3)))

	mdb.models['one'].Equation(name='CLL0_1', terms=((1.0, 'CLL0', 1), (-1.0, 'C000', 1), (-1.0, 'REFD', 1), (-1.0, 'REFS', 1)))
	mdb.models['one'].Equation(name='CLL0_2', terms=((1.0, 'CLL0', 2), (-1.0, 'C000', 2), (-1.0, 'REFS', 1), (-1.0, 'REFD', 2)))
	mdb.models['one'].Equation(name='CLL0_3', terms=((1.0, 'CLL0', 3), (-1.0, 'C000', 3), (-1.0, 'REFS', 3), (-1.0, 'REFS', 2)))

	mdb.models['one'].Equation(name='CL0L_1', terms=((1.0, 'CL0L', 1), (-1.0, 'C000', 1), (-1.0, 'REFD', 1), (-1.0, 'REFS', 3)))
	mdb.models['one'].Equation(name='CL0L_2', terms=((1.0, 'CL0L', 2), (-1.0, 'C000', 2), (-1.0, 'REFS', 1), (-1.0, 'REFS', 2)))
	mdb.models['one'].Equation(name='CL0L_3', terms=((1.0, 'CL0L', 3), (-1.0, 'C000', 3), (-1.0, 'REFS', 3), (-1.0, 'REFD', 3)))

	mdb.models['one'].Equation(name='C0LL_1', terms=((1.0, 'C0LL', 1), (-1.0, 'C000', 1), (-1.0, 'REFS', 1), (-1.0, 'REFS', 3)))
	mdb.models['one'].Equation(name='C0LL_2', terms=((1.0, 'C0LL', 2), (-1.0, 'C000', 2), (-1.0, 'REFD', 2), (-1.0, 'REFS', 2)))
	mdb.models['one'].Equation(name='C0LL_3', terms=((1.0, 'C0LL', 3), (-1.0, 'C000', 3), (-1.0, 'REFS', 2), (-1.0, 'REFD', 3)))

	mdb.models['one'].Equation(name='CLLL_1', terms=((1.0, 'CLLL', 1), (-1.0, 'C000', 1), (-1.0, 'REFD', 1), (-1.0, 'REFS', 1), (-1.0, 'REFS', 3)))
	mdb.models['one'].Equation(name='CLLL_2', terms=((1.0, 'CLLL', 2), (-1.0, 'C000', 2), (-1.0, 'REFS', 1), (-1.0, 'REFD', 2), (-1.0, 'REFS', 2)))
	mdb.models['one'].Equation(name='CLLL_3', terms=((1.0, 'CLLL', 3), (-1.0, 'C000', 3), (-1.0, 'REFS', 3), (-1.0, 'REFS', 2), (-1.0, 'REFD', 3)))

	#*************************************************************************************************************************************************************************************
	#Boundaries
	mdb.models['one'].DisplacementBC(amplitude=UNSET, createStepName=
		'Initial', distributionType=UNIFORM, fieldName='', fixed=OFF, localCsys=
		None, name='Fest', region=
		mdb.models['one'].rootAssembly.sets['C000'], u1=0.0, u2=0.0, u3=
		0.0, ur1=UNSET, ur2=UNSET, ur3=UNSET)

	mdb.models['one'].DisplacementBC(amplitude=UNSET, createStepName=
		'ApplyTension', distributionType=UNIFORM, fieldName='', fixed=OFF, localCsys=
		None, name='InitialDisp', region=
		mdb.models['one'].rootAssembly.sets['REFD'], u1=0.10, u2=UNSET,
		u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET)

	#**************************************************************************************************************************************************************************************
	#Create Job
	#**************************************************************************************************************************************************************************************
	if SubmitJob == True: 
		myJob=mdb.Job(name=jobName, model='one', description='')
		#mdb.jobs['AnandPBCTest'].writeInput(consistencyChecking=OFF)
		mdb.jobs[jobName].submit(consistencyChecking=OFF)
		mdb.jobs[jobName].waitForCompletion()
	if WriteInput == True:
		myJob=mdb.Job(name=jobName, model='one', description='')
		mdb.jobs[jobName].writeInput(consistencyChecking=OFF)


	#**************************************************************************************************************************************************************************************
	#Postprocessing
	#**************************************************************************************************************************************************************************************

	if Postprocessing == True:
		#Compute Stress Strain:
		if System == 'Linux':
			MicroODB=session.openOdb(name='/home/yourDir' +  jobName + '.odb')
		elif System == 'Windows':
			MicroODB=session.openOdb(name= jobName + '.odb')
			
		Micro_Assemb=MicroODB.rootAssembly
		Micro_Inst=Micro_Assemb.instances['MIKROMECH_8MAL8']

		#Define Steps for PostProcessing
		Step=['ApplyTension']
		#Initiate Data storage list
		Data=[]

		# get Max Load after Loadstep1
		elSet = Micro_Inst.elementSets['ALLES']

		#Go through all Steps
		for ii in Step:

			Frames=MicroODB.steps[ii].frames
			#Go through all Frames
			for iFrame in Frames:
				
				#Define subsets to evaluate Stress and Strain
				elSet=Micro_Inst.elementSets['ALLES']
				S_subset=iFrame.fieldOutputs['S'].getSubset(region=elSet,position=CENTROID)
				E_subset=iFrame.fieldOutputs['E'].getSubset(region=elSet,position=CENTROID)
				S_Val1=S_subset.values
				E_Val1=E_subset.values
				
				NumEl=len(S_Val1) 
				
				#Get Stress 
				S_Cum1=0.
				for v in S_Val1:
					S_Cum1+=v.data[0]
				
				#Get Strain
				E_Cum1=0.			
				for v in E_Val1:
					E_Cum1+=v.data[0]
				#accumulate absolute time

				if ii == 'ApplyTension':
					Data.append([iFrame.frameId, iFrame.frameValue, S_Cum1/NumEl, E_Cum1 / NumEl])
				elif ii == 'Relaxation1':
					Data.append([iFrame.frameId, iFrame.frameValue + timeApplyDisp ,S_Cum1/NumEl, E_Cum1/NumEl])
				elif ii == 'ApplyCompression':
					Data.append([iFrame.frameId, iFrame.frameValue + timeApplyDisp + timeRelaxation ,S_Cum1/NumEl, E_Cum1/NumEl])
				elif ii == 'Relaxation2':
					Data.append([iFrame.frameId, iFrame.frameValue + 2*timeApplyDisp + timeRelaxation ,S_Cum1/NumEl, E_Cum1/NumEl])
			
		#Export Results textfile (additional)
		file=open("Test_results.txt","w")
		file.write("Step: %s" % ii)
		file.write("-------------------------------------------------\n")
		file.write("Creep Model: %s \n" % CreepType)
		file.write("-------------------------------------------------\n")
		file.write("%s %s %s %s" %('StepID', 'FrameValue', 'Average_Stress_S11', 'Average_Strain_E11'))
		file.write("\n")
		for ii in Data:
			file.write("%s %s %s %s" %(ii[0],ii[1],ii[2], ii[3]))
			file.write("\n")
		
		file.close()
		#Append Data to DataExport for all Parametersets
		DataExport.append(Data)

#Export Data
ResultPickle='Results.p'
pickle.dump(DataExport, open(ResultPickle,'wb'))
print "Analysis Finished"

