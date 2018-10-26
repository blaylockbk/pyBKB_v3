# Brian Blaylock
# July 27, 2018

"""
HRRR Neighborhood Ensemble Probability

Using the computationally efficient approach, eq. (4) and (5) in Schwartz
and Sobash, 2017.

Schwartz, C.S. and R.A. Sobash, 2017: Generating Probabilistic Forecasts from
    Convection-Allowing Ensembles Using Neighborhood Approaches: A Review and
    Recommendations. Mon. Wea. Rev., 145, 3397–3418,
    https://doi.org/10.1175/MWR-D-16-0400.1 
"""

import numpy as np
from datetime import datetime, timedelta
import scipy.ndimage as ndimage
import matplotlib.pyplot as plt
import multiprocessing

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')
sys.path.append('B:\\pyBKB_v2')
from BB_HRRR.HRRR_Pando import get_hrrr_variable, get_hrrr_latlon
from BB_maps.my_basemap import draw_HRRR_map, draw_centermap
from BB_cmap.NCAR_ensemble_cmap import cm_prob

import matplotlib as mpl
mpl.rcParams['figure.figsize'] = [12, 10]
mpl.rcParams['savefig.bbox'] = 'tight'
mpl.rcParams['savefig.dpi'] = 100     # For web
mpl.rcParams['figure.titleweight'] = 'bold'
mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 10
mpl.rcParams['axes.labelsize'] = 8
mpl.rcParams['axes.titlesize'] = 12
mpl.rcParams['figure.subplot.hspace'] = 0.01

def radial_footprint(radius):
    y,x = np.ogrid[-radius: radius+1, -radius: radius+1]
    footprint = x**2+y**2 <= radius**2
    footprint = 1*footprint.astype(float)
    return footprint

def neighborhood_mean(values):
    return np.mean(values)

def member_multipro(inputs):
    """Multiprocessing Inputs for member"""
    validDATE = inputs[0]
    f = inputs[1]
    threshold = inputs[2]
    variable = inputs[3]
    threshold = inputs[4]
    #
    runDATE = validDATE - timedelta(hours=f)
    H = get_hrrr_variable(runDATE, variable, fxx=f)
    return H['value'] >= threshold


def NEP(validDATE, threshold=35, variable='REFC:entire', radius=9, fxx=range(2,5), hours_span=0):
    '''
    Compute the Neighborhood Ensemble Probability

    Input:
        DATE      - Datetime object representing the valid date.
        threshold - The threshold value for which you wish to compute probability.
        variable  - Variable string from the HRRR .idx file 
        radius    - The number of grid points the radial spatial filter uses
        fxx       - A list of forecast hours (between 0 and 18) to use in the probability.
        hour_span - Number hours +/- the valid hour to consider as members.
                    Default 0 will only use the validDATE. If you set to 1, then
                    will use additional model runs valid for +/- 1 hour the
                    validDATE
    '''
    # Generate a list of datetimes based on the validDATE and the hours_span
    sDATE = validDATE - timedelta(hours=hours_span)
    eDATE = validDATE + timedelta(hours=hours_span)
    DATES = [sDATE + timedelta(hours=h) for h in range(int((eDATE-sDATE).seconds/60/60)+1)]

    print()
    print('### Neighborhood Ensemble Probability###')
    print('     Valid Dates:\t%s' % DATES)
    print('        Variable:\t%s' % variable)
    print(' Threshold value:\t%s' % threshold)
    print('   Radial filter:\t %s grid points (%s km)' % (radius, (3*radius)))
    print('  Forecast hours:\t%s' % (['f%02d' % f for f in fxx]))
            
    
    ## First, compute the ensemble probability (EP) for each grid point.
    # Retrieve all the HRRR grids as each member.
    inputs_list = [[d, f, threshold, variable, threshold] for d in DATES for f in fxx]
    # Multiprocessing :)
    cpus = np.minimum(multiprocessing.cpu_count(), len(inputs_list))
    p = multiprocessing.Pool(cpus)
    members = np.array(p.map(member_multipro, inputs_list))
    p.close()

    # Average of all grid points, ensemble probability (EP)
    EP = np.mean(members, axis=0)

    ## Second, average EP neighborhood at each point.
    NEP = ndimage.generic_filter(EP, neighborhood_mean, footprint=radial_footprint(radius))

    print("\n###########################################################")
    print("  Neighborhood Ensemble Probability:")
    print("    Percentage of grid points within the radius %s km (%s grid points)" % (radius*3, radius))
    print("    where %s >= %s" % (variable, threshold))
    print("###########################################################\n")

    ## 3) Return some values
    # Load the latitude and longitude.
    return_this = get_hrrr_latlon()

    # Return the array with zero probability masked
    masked = NEP
    masked = np.ma.array(masked)
    masked[masked == 0] = np.ma.masked

    # also return the masked probabilities
    return_this['prob'] = masked
    return_this['members'] = len(members)
    
    return return_this

if __name__ == '__main__':

    #validDATE = datetime(2018, 7, 17, 6) # Thunderstom Utah SL Counties
    validDATE = datetime(2018, 8, 1, 23) # Isolated Thunderstorms
    threshold =15
    radius = 9
    fxx = range(9, 19)
    variable = 'WIND:10 m'
    hours_span = 0

    if variable in ['UVGRD:10 m', 'WIND:10 m']:
        units = r'm s$\mathregular{^{-1}}$'
    elif variable == 'REFC:entire':
        units = 'dBZ'


    nep = NEP(validDATE, threshold=threshold, variable=variable, radius=radius, fxx=fxx, hours_span=hours_span)

    # Get the values at the valid time
    H = get_hrrr_variable(validDATE, variable, fxx=0)

    m = draw_centermap(40.77, -111.96, size=(2.5,3.5))

    plt.figure(figsize=[10,5])
    cm = cm_prob()
    m.pcolormesh(nep['lon'], nep['lat'], nep['prob'],
                    cmap=cm['cmap'],
                    vmax=cm['vmax'],
                    vmin=cm['vmin'],
                    latlon=True)
    cb = plt.colorbar(pad=.02, shrink=.8)

    m.contour(H['lon'], H['lat'], H['value']>=threshold,
            levels=[1],
            linewidths=.8,
            colors='crimson',
            latlon=True)

    m.drawcoastlines()
    m.drawcountries()
    m.drawstates()
    m.arcgisimage(service='World_Shaded_Relief', xpixels=1000, dpi=100)

    plt.title('HRRR NEP', loc='left', fontweight='semibold')
    plt.title('\nValid: %s' % validDATE.strftime('%Y %b %d %H:%M UTC'), loc='right')
    plt.xlabel('Probability %s > %s %s\nFxx: %s\nRadius: %s km' % (variable, threshold, units, ['F%02d' % f for f in fxx], radius*3))
    plt.show(block=False)


    m = draw_HRRR_map()
    plt.figure(figsize=[10,5])
    cm = cm_prob()
    m.pcolormesh(nep['lon'], nep['lat'], nep['prob'],
                    cmap=cm['cmap'],
                    vmax=cm['vmax'],
                    vmin=cm['vmin'],
                    latlon=True)
    cb = plt.colorbar(pad=.02, shrink=.8)

    m.contour(H['lon'], H['lat'], H['value']>=threshold,
            levels=[1],
            linewidths=.8,
            colors='crimson',
            latlon=True)

    m.drawcoastlines()
    m.drawcountries()
    m.drawstates()
    
    plt.title('HRRR NEP', loc='left', fontweight='semibold')
    plt.title('\nValid: %s' % validDATE.strftime('%Y %b %d %H:%M UTC'), loc='right')
    plt.xlabel('Neighborhood Probability %s > %s %s\nFxx: %s\nRadius: %s km' % (variable, threshold, units, ['F%02d' % f for f in fxx], radius*3))
    plt.show()
