# Brian Blaylock
# November 8, 2018

'''
Compute the model spread for a given variable. 

        Model Spread : The standard deviation between all solutions
Average Model Spread : The square root of the average variances.

'''

import numpy as np
from datetime import datetime, timedelta

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')
sys.path.append('B:\pyBKB_v3')
from BB_HRRR.HRRR_Pando import get_hrrr_variable, get_hrrr_latlon

def spread(validDATE, variable, fxx=range(0,19), verbose=True):
    """
    Compute the HRRR model spread for a single analysis time.

    Input:
        validDATE - Datetime object of the analysis hour.
        variable  - HRRR GRIB2 variable string (i.e. 'TMP:2 m')
        fxx       - Range of hours to include in the 
    """
    # List of runDates and forecast lead time that correspond to the validDATE.
    # First item is the runDATE, second item is the corresponding fxx
    run_fxx = [(validDATE - timedelta(hours=f), f) for f in fxx]

    # Download all forecasts for the validDATE from Pando
    H = np.array([get_hrrr_variable(z[0], variable, fxx=z[1],
                                    verbose=False, value_only=True)['value']
                  for z in run_fxx])

    spread = np.std(H, axis=0)

    return spread

def mean_spread(sDATE, eDATE=None, variable='TMP:2 m', fxx=range(0,19), verbose=True):
    """
    for a range of dates (or for an array of dates)
    """