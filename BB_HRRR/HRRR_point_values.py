# Brian Blaylock
# December 13, 2018

"""
Grab data for specific points from HRRR grids based on a list of XY index 
value pairs.

These functions were originally created because we needed to pluck forecasted
gusts at the location of power transmission lines.
"""

import numpy as np
from datetime import datetime, timedelta
import xarray

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')
from BB_HRRR.HRRR_Pando import get_hrrr_latlon, get_hrrr_variable


def forecast_data(runDATE, XY_point_pairs, variable='GUST:surface', fxx=range(19)):
    '''
    Return a dictionary of forecasted values for a series of points
    
    Input:
        runDATE        - Python Datetime Object for the model run date interested in.
        XY_point_pairs - XY array coordinate pairs for the points you want. 
        variable       - HRRR variable name.
        fxx            - Forecasts to include in the output.
    '''
    ## First, get the latitude and longitude grid points that coorespond to the XY points
        
    # Load the HRRR latitude and longitude grid
    hLATLON = get_hrrr_latlon()
    
    # Get the latitude and longitude values for each XY point pair
    ulon = np.array([hLATLON['lon'][m, n] for m, n in XY_point_pairs])
    ulat = np.array([hLATLON['lat'][m, n] for m, n in XY_point_pairs])
    
    # We want to return these
    header = 'LATITUDE, LONGITUDE'
    return_this = {'lat':ulat,
                   'lon':ulon}
    
    ## Next, get the forecasts for each of the points
    for f in fxx:
        print('\rworking on f%02d' % f, end="")
        # Get the HRRR File
        H = get_hrrr_variable(runDATE, variable='GUST:surface', fxx=f, verbose=False)    
        
        # Get the points from the grid for the transmission lines
        vv = np.array([H['value'][m, n] for m, n in XY_point_pairs])
        
        # Add that to the array we want to return
        return_this['f%02d' % f] = vv

    print('\rDONE!')
    return return_this

def osg_data(runDATE, XY_point_pairs, variable='GUST:surface', fxx=range(19), percentile=95):
    '''
    Return a dictionary of HRRR climatology from OSG statistics for a series of points
    
    Input:
        runDATE        - Python Datetime Object for the model run date interested in
        XY_point_pairs - XY array coordinates for the points you want 
        variable       - HRRR variable name
        fxx            - Forecasts to include in the output
        percentile     - The percentile (from the file) you want to get
        outdir         - Path to write file
    '''
    ## First, get the latitude and longitude grid points that coorespond to the XY points
        
    # Load the HRRR latitude and longitude grid
    hLATLON = get_hrrr_latlon()
    
    # Get the latitude and longitude values for each XY point pair
    ulon = np.array([hLATLON['lon'][m, n] for m, n in XY_point_pairs])
    ulat = np.array([hLATLON['lat'][m, n] for m, n in XY_point_pairs])
    
    # We want to return these
    return_this = {'lat':ulat,
                   'lon':ulon,
                   'percentile':percentile}
    
    ## Next, get the forecasts for each of the points
    for f in fxx:
        print('\rworking on f%02d' % f, end="")
        # Get the HRRR File
        validDATE = runDATE + timedelta(hours=f)
        DATE = datetime(2016, validDATE.month, validDATE.day, validDATE.hour)
        var = variable.replace(':', '_').replace(' ', '_')
        DIR = '/uufs/chpc.utah.edu/common/home/horel-group8/blaylock/HRRR_OSG/hourly30/%s/' % var
        FILE = 'OSG_HRRR_%s_m%02d_d%02d_h%02d_f00.h5' % (var, DATE.month, DATE.day, DATE.hour)
        print(DIR+FILE)
        OSG = xarray.open_dataset(DIR+FILE)
        
        # Get the points from the grid for the transmission lines
        OSG_pth = np.array([OSG['p%02d' % percentile].data[m,n] for m, n in XY_point_pairs])
        
        # Add that to the array we want to return
        return_this['f%02d' % f] = OSG_pth
        
    print('\rDONE!')
    return return_this


if __name__=="__main__":

    import matplotlib.pyplot as plt
    from BB_cmap.NWS_standard_cmap import cm_wind

    fxx = 6
    variable = 'GUST:surface'
    percentile = 95

    # Get HRRR XY point pairs along transmission line
    point_pairs = np.load('../grid_resilience/data/HRRR_xy_points_for_powergrid.npy')

    # Get forecasted values at that those points
    runDATE = datetime(2018,11,8,6)
    forecasts = forecast_data(runDATE, point_pairs, variable=variable, 
                              fxx=[fxx])
    
    # Get OSG Climatology data for those same points
    osg_climo = osg_data(runDATE, point_pairs, variable=variable, 
                         fxx=[fxx], percentile=percentile)

    ## Make a figure
    fig, (ax1, ax2) = plt.subplots(1,2, figsize=[15,5])
    c = cm_wind()

    plt.sca(ax1)
    plt.scatter(forecasts['lon'], forecasts['lat'], c=forecasts['f%02d' % fxx],
                cmap=c['cmap'], vmax=c['vmax'], vmin=c['vmin'])
    plt.colorbar()
    plt.title("HRRR Gusts", loc='left', fontweight='semibold')
    plt.title('Run: %s F%02d' % (runDATE.strftime('%d-%b-%Y %H:%M'), fxx), loc='right')

    plt.sca(ax2)
    plt.scatter(osg_climo['lon'], osg_climo['lat'], c=osg_climo['f%02d' % fxx],
                vmin=0)
    plt.colorbar()
    plt.title("%sth Percentile" % percentile, loc='left', fontweight='semibold')
    plt.title('Valid %s' % (runDATE+timedelta(hours=fxx)).strftime('%d-%b %H:%M'), loc='right')

    plt.show()
