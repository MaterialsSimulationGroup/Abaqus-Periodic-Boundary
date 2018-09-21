# Abaqus-Periodic-Boundary
Description:
The file can be used in conjuction to provide Stress-Strain plots from uniaxial tension on an repetitive volume element (RVE) with periodic boundary conditions. 

File structure:

1) CallAbq.py:   
              Generates Paramters in Paramters.p
              Calls PeriodicModel.py in abaqus
              Reads Results.p
              Plots model results (Stress-Time and Stress-Strain Plot)
              
2) PeriodicModel.py:
              Creates cubic volume element
              applies material properties
              generates load steps
              applies periodic boundary conditions
              applies uniaxial strain
              performs postprocessing
              writes results into Results_Export.p
               
3) Tools.py:
            contains the plot function
