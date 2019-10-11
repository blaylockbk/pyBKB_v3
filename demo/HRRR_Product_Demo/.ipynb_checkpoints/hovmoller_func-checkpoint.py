## Brian Blaylock
## October 10, 2019

"""
Make a HRRR hovmoller for a point. These are the
behind-the-scenes functions for hovmoller.ipynb
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from matplotlib.dates import DateFormatter, HourLocator

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')
from BB_HRRR.HRRR_Pando import LocDic_hrrr_hovmoller
from BB_cmap.NWS_standard_cmap import cm_wind, cm_temp, cm_dpt, cm_rh, cm_precip
from BB_cmap.reflectivity_cmap import reflect_ncdc
from BB_MesoWest.get_MesoWest import get_mesowest_stninfo



def get_spex():
    '''
    Create specifications (spex) dictionary for each variable plot.
    Returns the dicionary. 
    '''
    spex = {'10 m MAX Wind Speed':{'HRRR var':'WIND:10 m',
                                   'MW var':'wind_speed',
                                   'units': cm_wind()['units'],
                                   'cmap':cm_wind()['cmap'],
                                   'save':'WIND',
                                   'contour':range(5, 50, 5),
                                   'vmax':cm_wind()['vmax'],
                                   'vmin':cm_wind()['vmin']},
            'Simulated Reflectivity':{'HRRR var':'REFC:entire atmosphere',
                                      'MW var':'reflectivity',
                                      'units': reflect_ncdc()['units'],
                                      'cmap':reflect_ncdc()['cmap'],
                                      'save':'REF',
                                      'contour':range(20, 100, 20),
                                      'vmax':reflect_ncdc()['vmax'],
                                      'vmin':reflect_ncdc()['vmin']},
            '2 m Temperature':{'HRRR var':'TMP:2 m',
                               'MW var':'air_temp',
                               'units': cm_temp()['units'],
                               'cmap':cm_temp()['cmap'],
                               'save':'TMP',
                               'contour':range(-20, 50, 5),
                               'vmax':cm_temp()['vmax'],
                               'vmin':cm_temp()['vmin']},
            '2 m Dew Point':{'HRRR var':'DPT:2 m',
                               'MW var':'dew_point_temperature',
                               'units': cm_dpt()['units'],
                               'cmap':cm_dpt()['cmap'],
                               'save':'DPT',
                               'contour':range(-20, 50, 5),
                               'vmax':cm_dpt()['vmax'],
                               'vmin':cm_dpt()['vmin']},
            '2 m Relative Humidity':{'HRRR var':'RH:2 m',
                                     'MW var':'relative_humidity',
                                     'units':cm_rh()['units'],
                                     'cmap':cm_rh()['cmap'],
                                     'save':'RH',
                                     'contour':range(100,121,10),
                                     'vmax':cm_rh()['vmax'],
                                     'vmin':cm_rh()['vmin']},
            '1 h Accumulated Precipitation':{'HRRR var':'APCP:surface',
                                             'MW var':'accumulated_precip',
                                             'units': cm_precip()['units'],
                                             'cmap':cm_precip()['cmap'],
                                             'save':'PCP',
                                             'contour':range(50,101,5),
                                             'vmax':cm_precip()['vmax'],
                                             'vmin':cm_precip()['vmin']},
            'Total Accumulated Precipitation':{'HRRR var':'APCP:surface:0',
                                               'MW var':'accumulated_precip',
                                               'units': cm_precip()['units'],
                                               'cmap':cm_precip()['cmap'],
                                               'save':'APCP',
                                               'contour':range(50,101,5),
                                               'vmax':cm_precip()['vmax'],
                                             'vmin':cm_precip()['vmin']},
            'Solar Radiation':{'HRRR var':'DSWRF:surface',
                               'MW var':'solar_radiation',
                               'units': r'W m$\mathregular{^{-2}}$',
                               'cmap':'magma',
                               'save':'SOL',
                               'contour':range(300, 1000, 100)},
           }
    return spex


def print_options():
    """
    Print the variables and number index in the dictionary.
    The variable number is used to define which variable 
    the user wants to plot.
    """
    print('Set the variable number from this list')
    print('--------------------------------------')
    for i, s in enumerate(get_spex()):
        print('%s: %s' % (i, s))
    print('--------------------------------------')
        

def plot_hov(sDATE, eDATE, variable_number, stations, save=True):
    """
    Plots a hovmoller diagram from HRRR values at a point for all 
    forecasts and the specified dates.
    
    Input:
        sDATE           - start datetime
        eDATE           - end datetime
        variable_number - variable number from the spex dictionary
        stations        - a list of mesowest station ids
        save            - True: saves the image
                          False: don't save the images
    Output: 
        hovmoller       - a dicionary of the hovmoller data
    """
    # get the specifications dictionary
    spex = get_spex()
    
    # get the stations location dictionary (from MesoWest function)
    locations = get_mesowest_stninfo(stations)
    
    # based on the user input variable_number, which variable are we getting?
    variable = list(spex.keys())[variable_number]
       
    print('Requested %s' % variable)
    print('---------------------------------------')
    
    # retrieve the hovmoller dictionary
    hovmoller = LocDic_hrrr_hovmoller(sDATE, eDATE, locations, spex[variable]['HRRR var'])
    
    # For relavant variables, convert units from Kelvin to Celsius
    if variable == '2 m Temperature' or variable == '2 m Dew Point':
        for stn in stations:
            hovmoller[stn] = hovmoller[stn]-273.15
            
    # Make a new figure for each station requested
    for i, stn in enumerate(stations):
        fig = plt.figure(i, figsize=[13, 6])
        ax1 = plt.subplot(111)

        plt.title('%s %s' % (stn, variable), fontweight='bold')
        plt.title(sDATE.strftime('%Y-%m-%d %H:%M'), loc='left')
        plt.title(eDATE.strftime('%Y-%m-%d %H:%M'), loc='right')

        # HRRR Hovmoller
        hv = ax1.pcolormesh(hovmoller['valid_1d+'], hovmoller['fxx_1d+'], hovmoller[stn],
                            cmap=spex[variable]['cmap'],
                            vmax=spex[variable]['vmax'],
                            vmin=spex[variable]['vmin'])
        cb = plt.colorbar(hv, pad=.01, shrink=0.8, label='%s (%s)' % (variable, spex[variable]['units']))
        
        ax1.set_xlim(hovmoller['valid_1d+'][0], hovmoller['valid_1d+'][-1])
        ax1.set_ylim(0, 19)
        ax1.set_yticks(range(0, 19, 3))
        ax1.axes.xaxis.set_ticklabels([])
        ax1.set_ylabel('HRRR Forecast Hour')
        
        ax1.grid(linewidth=0.25)
               
        # Format date axis
        ax1.xaxis.set_major_locator(HourLocator(byhour=range(0,24,3)))
        dateFmt = DateFormatter('%b %d\n%H:%M')
        ax1.xaxis.set_major_formatter(dateFmt)
        
        if save: plt.savefig('%s_%s_%s_%s' % (stn, spex[variable]['save'], \
                                              sDATE.strftime('%Y%m%d-%H%M'), \
                                              eDATE.strftime('%Y%m%d-%H%M')), bbox_inches='tight')


if __name__ == '__main__':
    ## Recent Date range
    UTC_now = datetime.utcnow()
    sDATE = datetime(UTC_now.year, UTC_now.month, UTC_now.day, UTC_now.hour)-timedelta(hours=6)
    eDATE = datetime(UTC_now.year, UTC_now.month, UTC_now.day, UTC_now.hour)+timedelta(hours=18)

    ## Custom Date range
    #sDATE = datetime(2019, 6, 1, 0)
    #eDATE = datetime(2019, 6, 2, 0)
    
    print_options()
    
    print('Which variable do you want to plot?')
    var_number = int(input('Choose a number from the above list: '))
    
    stations = ['WBB', 'KMRY']
    plot_hov(sDATE, eDATE, var_number, stations)




