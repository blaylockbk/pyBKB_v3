# Brian Blaylock
# November 8, 2018

'''
Compute the model spread for a given variable. 

        Model Spread : The standard deviation between all solutions
Average Model Spread : The square root of the average variances.
'''

import numpy as np
from datetime import datetime, timedelta
import multiprocessing

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')
sys.path.append('B:\pyBKB_v3')
from BB_HRRR.HRRR_Pando import get_hrrr_variable, get_hrrr_latlon
from BB_wx_calcs.wind import wind_uv_to_spd

def spread(validDATE, variable, fxx=range(0,19), verbose=True):
    """
    Compute the HRRR model spread for a single analysis time.

    Input:
        validDATE - Datetime object of the analysis hour.
        variable  - HRRR GRIB2 variable string (i.e. 'TMP:2 m')
        fxx       - Range of hours to include in the 
    """
    timer=datetime.now()
    # List of runDates and forecast lead time that correspond to the validDATE.
    # First item is the runDATE, second item is the corresponding fxx
    run_fxx = [(validDATE - timedelta(hours=f), f) for f in fxx]

    # Download all forecasts for the validDATE from Pando
    H = np.array([get_hrrr_variable(z[0], variable, fxx=z[1],
                                    verbose=False, value_only=True)['value']
                  for z in run_fxx])

    spread = np.std(H, ddof=1, axis=0)
    if verbose:
        print('Timer for HRRR_Spread.spread():', datetime.now-timer)
    
    return spread

# =============================================================================
# =============================================================================

def get_HRRR_value(validDATE, variable, fxx):
    """
    Get HRRR data. Return just the value, not the latitude and longitude.
    If data is np.nan, then return None, i.e. the shape of the data is ().
    This makes it possible to filter out the None values later.
    """
    runDATE = validDATE - timedelta(hours=fxx)
    
    if variable.split(':')[0] == 'UVGRD':
        #print("getting U and V components")
        Hu = get_hrrr_variable(runDATE, 'UGRD', fxx=fxx, verbose=False)['value']
        Hv = get_hrrr_variable(runDATE, 'VGRD', fxx=fxx, verbose=False)['value']
        H =  wind_uv_to_spd(Hu, Hv)
        
    else:
        H = get_hrrr_variable(runDATE, variable, fxx=fxx, verbose=False)['value']
    
    if np.shape(H) == ():
        # Then the data is a nan. Return None so it can be filtered out.
        print("!! WARNING !! COULD NOT GET %s %s f%02d" % (variable, runDATE, fxx))
        return None
    else:
        return H


def mean_spread_MP(inputs):
    """
    Each processor works on a separate validDATE
    """
    i, D, variable, fxx, verbose = inputs

    if verbose:
        msg = 'Progress: %02d%% (%s of %s) complete ----> Downloading %s, %s\r' % ((i[0]+1)/i[1]*100, i[0]+1, i[1], D.strftime('%d %b %Y %H:%M UTC'), variable)
        sys.stdout.write(msg)
        sys.stdout.flush()
        print(msg)

    # Get all forecasts for the validDATE.
    HH = [get_HRRR_value(D, variable, f) for f in fxx]
    # Count None values and Filter out None values
    count_none = np.sum(1 for x in HH if x is None)
    HH = np.array(list(filter(lambda x: x is not None, HH)))
    if count_none > 0:
        print(" WARNING: %s had None values" % D)
        print("    Counted %s None values" % count_none)
        percentage_retrieved = 100*len(HH)/float(len(fxx))
        print("    Retrieved %s/%s expected samples for calculations --- %.2f%% \n" % (len(HH), len(fxx), percentage_retrieved))

    # Compute the variance from all forecasts
    var = np.var(HH, ddof=1, axis=0) # ddof=1 because we want the sample variance
    
    return var


def mean_spread(validDATES, variable='TMP:2 m', fxx=range(0,19), verbose=True, reduce_CPUs=3):
    """
    For a range of dates (or for an array of dates)

    Mean spread is the square root of the mean variance
---------------------------
    The average spread, otherwise known ad the average standard deviation,
    is correctly computed as the *square root of the average variance*.

    Sample Variance:
    sigma^2 = s^2 = 1/(n-1) SUM(x - mean(x)^2
    
    Standard Deviation
    sigma = s = sqrt(s^2)
    
    Average Model Spread
    mean(sigma) = sqrt(mean(s^2))

    Fortin, V., M. Abaza, F. Anctil, and R. Turcotte, 2014: Why Should 
         Ensemble Spread Match the RMSE of the Ensemble Mean?. J. 
         Hydrometeor., 15, 1708–1713, https://doi.org/10.1175/JHM-D-14-0008.1
         See equation (16)

    Input:
        validDATES    - A list of datetime objects representing the valid date
                        to consider for the mean calculation.
        variable      - A HRRR GRIB2 variable name code. Default is 2-m Temp.
        fxx           - Forecast hours to consider in the variance calculation
                        Default is all 0-18 hours.
    """
    
    args = [[(i, len(validDATES)), D, variable, fxx, verbose] for i, D in enumerate(validDATES)]
    cpus = multiprocessing.cpu_count() - reduce_CPUs
    P = multiprocessing.Pool(cpus)
    all_variances = P.map(mean_spread_MP, args)
    P.close()

    if verbose:
        print('\nFinished Loading HRRR Data.')

    # Mean spread is the square root of the mean variances
    if verbose:
        print('Computing mean spread...')
    mean_spread = np.sqrt(np.mean(all_variances, axis=0))
    if verbose:
        print('                     ...done')

    return mean_spread

# =============================================================================
# =============================================================================
# =============================================================================
# =============================================================================
"""
Mean Spread FOR THRESHOLD CONDITIONS
"""
def mean_spread_threshold_MP(inputs):
    """
    Each processor works on a separate validDATE
    """
    i, D, variable, fxx, condition, verbose = inputs

    if verbose:
        msg = 'Progress: %02d%% (%s of %s) complete ----> Downloading %s, %s\r' % ((i[0]+1)/i[1]*100, i[0]+1, i[1], D.strftime('%d %b %Y %H:%M UTC'), variable)
        sys.stdout.write(msg)
        sys.stdout.flush()
        print(msg)

    # Get all forecasts for the validDATE.
    HH = [get_HRRR_value(D, variable, f) for f in fxx]
    # Count None values and Filter out None values
    count_none = np.sum(1 for x in HH if x is None)
    HH = np.array(list(filter(lambda x: x is not None, HH)))
    if count_none > 0:
        print(" WARNING: %s had None values" % D)
        print("    Counted %s None values" % count_none)
        percentage_retrieved = 100*len(HH)/float(len(fxx))
        print("    Retrieved %s/%s expected samples for calculations --- %.2f%% \n" % (len(HH), len(fxx), percentage_retrieved))

    # Compute the variance from all forecasts
    var = np.var(HH, ddof=1, axis=0) # ddof=1 because we want the sample variance
    
    # Mask away values that don't meat the conditional statement.
    
    # We only want values if any of the forecast for that hour is .GT. a threshold.
    # Thus, find the max value of all forecasts, and mask all points that .LT. the threshold.
    if condition['condition'] == '>':
        masked_var_thresh = np.ma.array(var, mask=np.max(HH, axis=0) < condition['threshold'])
    elif condition['condition'] == '>=':
        masked_var_thresh = np.ma.array(var, mask=np.max(HH, axis=0) <= condition['threshold'])
    # Or, we only want values if any of the forecast for that hour is .LT. a threshold.
    # Thus, find the min value of all forecasts, and mask all points that are .GT. the threshold.
    elif condition['condition'] == '<':
        masked_var_thresh =np.ma.array(var, mask=np.min(HH, axis=0) > condition['threshold'])
    elif condition['condition'] == '<=':
        masked_var_thresh =np.ma.array(var, mask=np.min(HH, axis=0) >= condition['threshold'])

    return masked_var_thresh


def mean_spread_threshold(validDATES, variable='TMP:2 m', fxx=range(0,19),
                          verbose=True, reduce_CPUs=3,
                          condition = {'condition':'>=', 'threshold':10}):
    
    args = [[(i, len(validDATES)), D, variable, fxx, condition, verbose] for i, D in enumerate(validDATES)]
    cpus = multiprocessing.cpu_count() - reduce_CPUs
    P = multiprocessing.Pool(cpus)
    all_variances = np.ma.array(P.map(mean_spread_threshold_MP, args))
    P.close()

    if verbose:
        print('\nFinished Loading HRRR Data.')

    # Mean spread is the square root of the mean variances
    if verbose:
        print('Computing mean spread...')
    mean_spread = np.sqrt(np.ma.mean(all_variances, axis=0))    
    sample_count = np.ma.sum(all_variances > 0, axis=0)
    if verbose:
        print('                     ...done')

    return mean_spread, sample_count


# =============================================================================
# =============================================================================


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    from BB_datetimes.range import range_dates
    from BB_HRRR.HRRR_Pando import get_hrrr_latlon
    from BB_maps.my_basemap import draw_HRRR_map, draw_centermap

    latlon = get_hrrr_latlon()
    lat = latlon['lat']
    lon = latlon['lon']
    m = draw_HRRR_map()
    mW = draw_centermap(40, -115, (10,10))
    mU = draw_centermap(39.5, -111.6, (3.2,3.2))

    # Mean Spread for hour 1200 UTC for the range of dates
    hour = 12
    sDATE = datetime(2018, 5, 1, hour)
    eDATE = datetime(2018, 10, 1, hour)
    DATES = range_dates(sDATE, eDATE, DAYS=1)
    fxx = range(0,19)
    variable = 'TMP:2 m'

    AVG_SPREAD = mean_spread(DATES, variable=variable, fxx=fxx)

    plt.figure(1, figsize=(15,15))
    m.pcolormesh(lon, lat, AVG_SPREAD,
                cmap='magma',
                latlon=True,
                vmin=0)

    m.drawcoastlines(linewidth=.2, color='lightgrey')
    m.drawcountries(linewidth=.2, color='lightgrey')
    m.drawstates(linewidth=.2, color='lightgrey')

    plt.title('HRRR Model Spread %s' % variable, fontweight='bold', loc='left')
    plt.title('Start: %s\n End: %s' % (sDATE.strftime('%d %b %Y %H:%M UTC'),
                                            eDATE.strftime('%d %b %Y %H:%M UTC')), loc='right')
    plt.title('Hour: %s\nFXX: %s' % (hour, fxx))
    cb = plt.colorbar(orientation='horizontal', pad=.01, shrink=.8)
    cb.set_label('Mean Model Spread')
    #plt.savefig('./figs/hourly_SPREAD/CONUS_%s_h%02d' % (variable.replace(':', '-').replace(' ', '-'), hour))
    

    plt.figure(2, figsize=(9, 9))
    mW.pcolormesh(lon, lat, AVG_SPREAD,
                cmap='magma',
                latlon=True,
                vmin=0)

    mW.drawcoastlines(linewidth=.2, color='lightgrey')
    mW.drawcountries(linewidth=.2, color='lightgrey')
    mW.drawstates(linewidth=.2, color='lightgrey')

    plt.title('HRRR Model Spread %s' % variable, fontweight='bold', loc='left')
    plt.title('Start: %s\n End: %s' % (sDATE.strftime('%d %b %Y %H:%M UTC'),
                                            eDATE.strftime('%d %b %Y %H:%M UTC')), loc='right')
    plt.ylabel('Hour: %s\nFXX: %s' % (hour, fxx))
    cb = plt.colorbar(orientation='horizontal', pad=.01, shrink=.8)
    cb.set_label('Mean Model Spread')
    #plt.savefig('./figs/hourly_SPREAD/WEST_%s_h%02d' % (variable.replace(':', '-').replace(' ', '-'), hour))

    plt.figure(3, figsize=(9, 9))
    mU.pcolormesh(lon, lat, AVG_SPREAD,
                cmap='magma',
                latlon=True,
                vmin=0)

    mU.drawcoastlines(linewidth=.2, color='lightgrey')
    mU.drawcountries(linewidth=.2, color='lightgrey')
    mU.drawstates(linewidth=.2, color='lightgrey')

    plt.title('HRRR Model Spread %s' % variable, fontweight='bold', loc='left')
    plt.title('Start: %s\n End: %s' % (sDATE.strftime('%d %b %Y %H:%M UTC'),
                                            eDATE.strftime('%d %b %Y %H:%M UTC')), loc='right')
    plt.ylabel('Hour: %s\nFXX: %s' % (hour, fxx))
    cb = plt.colorbar(orientation='horizontal', pad=.01, shrink=.8)
    cb.set_label('Mean Model Spread')
    #plt.savefig('./figs/hourly_SPREAD/UTAH_%s_h%02d' % (variable.replace(':', '-').replace(' ', '-'), hour))
    
    plt.show()
    