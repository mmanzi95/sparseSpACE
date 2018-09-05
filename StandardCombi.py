import numpy as np
import combiScheme
import Grid
import math
import logging
import combiScheme

#This class implements the standard combination technique
class StandardCombi(object):
    #initialization
    #a = lower bound of integral; b = upper bound of integral
    #grid = specified grid (e.g. Trapezoidal);
    def __init__(self,a,b,grid=TrapezoidalGrid()):
        self.log=logging.getLogger(__name__)
        self.dim = len(a)
        self.a = a
        self.b = b
        self.grid = grid
        assert(len(a) == len(b))

    #standard combination scheme for quadrature
    #lmin = minimum level; lmax = target level
    #f = function to integrate; dim=dimension of problem
    def performCombi(self,minv,maxv,f,dim):
        start = self.a
        end = self.b
        #compute minimum and target level vector
        lmin = [minv for i in range(dim)]
        lmax = [maxv for i in range(dim)]
        combiintegral= 0
        self.scheme = getCombiScheme(lmin[0],lmax[0],dim)
        for ss in self.scheme:
            integral=self.grid.integrate(f,ss[0],start,end) * ss[1]
            combiintegral += integral
        realIntegral = f.getAnalyticSolutionIntegral(self.a,self.b)
        print("CombiSolution",combiintegral)
        print("Analytic Solution", realIntegral)
        print("Difference", abs(combiintegral - realIntegral))
        return self.scheme, abs(combiintegral - realIntegral), combiintegral

    #calculate the number of points for a standard combination scheme
    def getTotalNumPoints(self,distinctFunctionEvals = False):
        numPoints = 0
        for ss in self.scheme:
            if distinctFunctionEvals:
                factor = int(ss[1])
            else:
                factor = 1
            self.grid.setCurrentArea(self.a,self.b,ss[0])
            numPoints += np.prod(np.array(self.grid.levelToNumPoints(ss[0]))) * factor
            #print nx*ny
        return numPoints