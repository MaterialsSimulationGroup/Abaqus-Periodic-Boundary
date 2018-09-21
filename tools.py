import matplotlib
import matplotlib.pyplot as plt
import numpy as np

def SimplePlot(x,y,plotControl,picName):
    #how many datasets
    iSet=len(x)
    # Note that using plt.subplots below is equivalent to using
    # fig = plt.figure() and then ax = fig.add_subplot(111)
    fig, ax = plt.subplots()
    for i in range(iSet):
        a=plotControl[i][1]
        ax.plot(x[i], y[i], plotControl[i][1],)
        ax.plot(x[i], y[i], plotControl[i][1]+'^',label=plotControl[i][0])

    #ax.set_yscale('log')
    ax.set(xlabel=plotControl[i][2], ylabel=plotControl[i][3],title=plotControl[i][4])
    ax.grid()
    ax.legend(loc='bottom right',shadow=False, fontsize='x-large')

    fig.savefig(picName+".png")
    plt.show()
    return 0


def ComputeGradient(x,y):
    #Computes Gradient with forward difference method
    #initialize gradient list
    gradxy = [[] * 1 for i in range(5)]

    for iSolder in range(len(x)):
        for iTime in range(len(x[0])):
            try:
                gradxy[iSolder].append((y[iSolder][iTime+1]-y[iSolder][iTime-1])/(x[iSolder][iTime+1]-x[iSolder][iTime-1]))
            except:
                gradxy[iSolder].append(0.)

    return gradxy

