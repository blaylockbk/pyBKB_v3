## Brian Blaylock
## March 21, 2019

'''
Workflow for putting GLM on HRRR grid and evaluating the contingency table.

    1) Get GLM Events for the previous hour of the time of interest.
    2) Get HRRR Lightning (LTNG) data and lat/lon grid for the DATETIME.
    3) Filter Events to HRRR Domain.
    4) Map the GLM events onto the HRRR grid.
    5) Apply a spatial filter to bloat the number of HRRR grid points that
       witness each GLM event.
    6) Compute the contingency table.
'''

from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import scipy.ndimage as ndimage
import os
import multiprocessing

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')

from BB_HRRR.HRRR_Pando import get_hrrr_all_valid, \
                               get_hrrr_latlon,\
                               get_hrrr_variable
from BB_GOES.get_GLM import get_GLM_file_nearesttime,\
                            accumulate_GLM_FAST,\
                            bin_GLM_on_HRRR_grid
from BB_maps.my_basemap import draw_HRRR_map,\
                               draw_centermap
from BB_HRRR.HRRR_paths import get_domains
from BB_wx_calcs.binary_events import *



## Create HRRR map object with Basemap
print('Create HRRR map.')
m = draw_HRRR_map(resolution='c')
Hlat, Hlon = get_hrrr_latlon(DICT=False)

# Get all HRRR forecast lead times
fxx = range(1,19)
print('Forecasts', list(fxx))

## Generate Domain Paths and Domain Masks
print('Generate domains and masks.')

domains = get_domains(add_states=['UT', 'CO', 'TX', 'FL'], HRRR_specific=True)
#domains = get_domains(add_states=['CO', 'TX', 'FL'], HRRR_specific=False)
print(domains.keys())


def get_GLM_HRRR_contingency_stats(validDATE, fxx=range(1,19)):
    '''
    Inputs:
        validDATE - A datetime that represents the end of the hour.
        fxx       - List of forecasts. Deafult starts at 0 because 
                    the F00 LTNG forecast doesn't have any output.
    
    Return:
        (A, B, C, D) - A list of values for contingency table of binary events.
        (Observed_Binary, Forecast_binary) - The binary grids for the HRRR and
            GLM data.
        (num_GLM_events, num_files, expected_files) - Number of GLM events
            recorded during the period, number of GLM files, number of expected
            GLM files for the period.
    '''

    ##=============================================================================
    ## 1) Get GLM Events for the previous hour.
    print('(1/7) Get GLM Events. %s' % validDATE)
    files = get_GLM_file_nearesttime(validDATE-timedelta(minutes=30), window=30, verbose=False)
    E = accumulate_GLM_FAST(files, data_type='event', verbose=False)
    
    print('\nGot %s of %s expected files.' % (files['Number'], files['Number Expected']))
    if E == None:
        return None
    print('Total Events: {:,}'.format(len(E['longitude'])))

    ##=============================================================================
    ## 2) Get HRRR Lightning data and lat/lon grid.
    print('(2/7) Get HRRR Data.')
    HH = get_hrrr_all_valid(validDATE, 'LTNG:entire', fxx=fxx)

    ##=============================================================================
    ## 3) Filter Events to HRRR domain and 4) Map GLM points HRRR grid
    print('(3/7) Filter GLM.')
    print('(4/7) Put GLM on HRRR grid.')
    hist, filtered = bin_GLM_on_HRRR_grid(E, Hlat, Hlon, m)
    print('In-HRRR Events: {:,}'.format(np.sum(filtered)))

    # Before we bloat the Events grid, lets get a count of the total events
    # inside each domain.
    return_this= {'Number Events': {}}
    for DOMAIN in domains:
        # Get hist for the masked domains
        hist_domain = np.ma.array(hist, mask=domains[DOMAIN]['mask'])
        num_events = int(np.sum(hist_domain.filled(0)))
        return_this['Number Events'][DOMAIN] = num_events
        print('{:>15,} events in {:}'.format(num_events, DOMAIN))

    #=============================================================================
    ## 5) Apply a spatial filter to bloat (enlarge or upscale) the number of HRRR
    #     grid points that witness each GLM event.
    # The GLM instrument has a resolution of only ~14 km. That is much more coarse
    # than the 3 km HRRR grid we just mapped the GLM data onto. If you plotted the
    # results of histogram, you would see the data is polkadoted like a speckled
    # sussex chicken. We now apply a spatial filter that will fill in the gaps.
    print('(5/7) Bloat GLM data with spatial filter.')
    custom_filter = np.array([[0,1,1,1,0],
                              [1,1,1,1,1],
                              [1,1,1,1,1],
                              [1,1,1,1,1],
                              [0,1,1,1,0]])
    bloat_glm = ndimage.generic_filter(hist, np.max, footprint=custom_filter)

    ##=============================================================================
    ## 6) Compute the GLM/HRRR contingency table for every requested forecast hour.
    # Two binary fields:
    #  1) HRRR yes/no lightning: Based on a threshold of >= 0.04 flashes/km2/5min.
    #     Since each grid box is 9 km2, this value is 0.36 flashes/gridbox/5min.
    #     If the maximum lightning was sustained for the entire hour, we would
    #     expect a maximum of about 4-5 flashes in that gridbox. This threshold was
    #     used because it got rid of the "popcorn" thunderstorms.
    #  2) GLM yes/no event: Must have more than one event in the grid box.

    print('(6/7) Generate binary grids.')
    Observed_binary = bloat_glm > 1     # More than 1 GLM event in a grid box.
    Forecast_binary = HH.data >= 0.04   # Greater than 0.04 flashes/km2/5min.

    ## Return some data
    return_this['table'] = {}
    return_this['Observed Binary'] = Observed_binary
    return_this['Forecast Binary'] = Forecast_binary
    return_this['Number GLM Files'] = files['Number']
    return_this['Number Expected Files'] = files['Number Expected']
    return_this['DATETIME'] = validDATE

    print('(7/7) Compute contingency table for each subdomain.')
    # For each subdomains...
    for DOMAIN in domains.keys():
        print('    Stats for %s' % DOMAIN)
        # masked binaries
        if DOMAIN != 'HRRR':
            O_m = np.ma.array(Observed_binary, mask=domains[DOMAIN]['mask'])
            F_m = np.ma.array([np.ma.array(F, mask=domains[DOMAIN]['mask']) for F in Forecast_binary])
        else:
            O_m = Observed_binary
            F_m = np.array([F for F in Forecast_binary])
        #
        # Compute contingency table for domain-masked observations and each forecast.
        tables = np.array([contingency_table(F_m_i, O_m, print_table=False) for F_m_i in F_m])
        A, B, C, D = [tables[:,n] for n in range(0,4)]
        #
        return_this['table'][DOMAIN] = (A, B, C, D)
    print('(FIN)')
    return return_this


def plot_hit_rate_and_false_alarm_ratio(A, B, C, D, fxx):
    """plot hit rate and false alarm ratio for all forecast hours"""
    plt.plot(fxx, hit_rate(A, B, C, D), label='Hit Rate')
    plt.plot(fxx, false_alarm_ratio(A, B, C, D), label='False Alarm Ratio')
    plt.legend()
    plt.grid()
    plt.title(validDATE)
    plt.xticks(fxx)
    plt.show()


def plot_map(O_binary, F_binary):
    '''
    O_binary - observed binary grid
    F_binary - forecast binary grid
    '''
    fig, (ax1, ax2) = plt.subplots(1,2, figsize=(15,5))
    #
    plt.sca(ax1)
    m.pcolormesh(Hlon, Hlat, O_binary, latlon=True)
    m.drawcoastlines()
    m.drawstates()
    m.drawcountries()
    plt.title('GLM Events (bloated)')
    #
    plt.sca(ax2)
    m.pcolormesh(Hlon, Hlat, F_binary, latlon=True)
    m.drawcoastlines()
    m.drawstates()
    m.drawcountries()
    plt.title('HRRR LTNG > 0.04')
    plt.suptitle(validDATE, fontweight='semibold')
    plt.subplots_adjust(wspace=.01, hspace=.01)
    plt.show()


def write_table_to_file(contingency_dict, DATE, write_domains, SAVEDIR = './HRRR_GLM_contingency_table/'):
    """
    Inputs:
        contingency_dict - the dictionary returned from
                           get_GLM_HRRR_contingency_stats()
        DATE             -
        write_domains    - list of which domains to write data to file.
                           (prevents double-recording if the domain already 
                            has this line)
    """
    for DOMAIN in domains:
        if DOMAIN in write_domains:
            # Directories for each Domain
            DOM_DIR = "%s/%s/" % (SAVEDIR, DOMAIN)
            if not os.path.exists(DOM_DIR):
                os.makedirs(DOM_DIR)
            
            SAVEFILE = "%s/%s_%s.csv" % (DOM_DIR, DOMAIN, DATE.strftime('%Y_m%m_h%H')) 
            
            # Initiate new file with header if the day of the month is 1.
            if DATE.day == 1:
                A_str = ','.join(['F%02d_A' % i for i in fxx])
                B_str = ','.join(['F%02d_B' % i for i in fxx])
                C_str = ','.join(['F%02d_C' % i for i in fxx])
                D_str = ','.join(['F%02d_D' % i for i in fxx])
                HEADER = 'DATE,GLM Event COUNT,NUM FILES,EXPECTED FILES,' + A_str + ',' + B_str + ',' + C_str + ',' + D_str
                with open(SAVEFILE, "w") as f:
                    f.write('%s\n' % HEADER)

            if contingency_dict is None:
                A_str = ','.join(np.array(np.ones_like(fxx)*np.nan, dtype=str))
                B_str = ','.join(np.array(np.ones_like(fxx)*np.nan, dtype=str))
                C_str = ','.join(np.array(np.ones_like(fxx)*np.nan, dtype=str))
                D_str = ','.join(np.array(np.ones_like(fxx)*np.nan, dtype=str))
                line = "%s,%s,%s,%s,%s,%s,%s,%s" % (DATE, 
                                                    np.nan,
                                                    0,   # None returned because GLM files was zero
                                                    180, # We expected 180 GLM files
                                                    A_str, B_str, C_str, D_str)
            else:
                A, B, C, D =  contingency_dict['table'][DOMAIN]
                A_str = ','.join(np.array(A, dtype=str))
                B_str = ','.join(np.array(B, dtype=str))
                C_str = ','.join(np.array(C, dtype=str))
                D_str = ','.join(np.array(D, dtype=str))
                line = "%s,%s,%s,%s,%s,%s,%s,%s" % (DATE, 
                                                    contingency_dict['Number Events'][DOMAIN],
                                                    contingency_dict['Number GLM Files'],
                                                    contingency_dict['Number Expected Files'],
                                                    A_str, B_str, C_str, D_str)
            with open(SAVEFILE, "a") as f:
                f.write('%s\n' % line)
            print('Wrote to', SAVEFILE)

def write_to_files_MP(inputs):
    year, month, hour = inputs

    sDATE = datetime(year, month, 1, hour)
    if month==12:
        eDATE = datetime(year+1, 1, 1, hour)
    else:
        eDATE = datetime(year, month+1, 1, hour)
        
    #days = int((eDATE-sDATE).days)
    #DATES = [sDATE+timedelta(days=d) for d in range(days)]
    #
    print('\n')
    print('=========================================================')
    print('=========================================================')
    print('       WORKING ON MONTH %s and HOUR %s' % (month, hour))
    print('=========================================================')
    print('=========================================================')
    #
    ### Check if the file we are working on exists
    #
    SAVEDIR = './HRRR_GLM_contingency_table/'

    DOMAINS = ['Utah', 'Colorado', 'Texas', 'Florida', 'HRRR', 'West', 'Central', 'East']
    FILES = ["%s/%s/%s_%s.csv" % (SAVEDIR, D, D, sDATE.strftime('%Y_m%m_h%H')) for D in DOMAINS]
    EXISTS = [os.path.exists(i) for i in FILES]

    Next_DATE = []
    for (F, E) in zip(FILES, EXISTS):
        if E:
            last = np.genfromtxt(F, delimiter=',', names=True, encoding='UTF-8', dtype=None)['DATE'][-1]
            Next_DATE.append(datetime.strptime(last, '%Y-%m-%d %H:%M:%S')+timedelta(days=1))
        else:
            Next_DATE.append(sDATE)

    # Does the last date equal to the last day of the month of interest?
    have_all_dates = np.array(Next_DATE) == eDATE

    DOM_DATES = []
    for i in Next_DATE:
        next_sDATE = i
        days = int((eDATE-next_sDATE).days)
        DATES = [next_sDATE+timedelta(days=d) for d in range(days)]
        DOM_DATES.append(DATES)

    days = int((eDATE-sDATE).days)
    DATES = [sDATE+timedelta(days=d) for d in range(days)]

    for DATE in DATES:
        print(DATE)
        write_domains = []
        for (DOM, DOM_DD) in zip(DOMAINS,DOM_DATES):
            # Do we need this date?
            if DATE in DOM_DD:
                write_domains.append(DOM)
            #print('%s, %s' % (DOM, DD in DOM_DD))
        if len(write_domains) != 0:
            print(write_domains)
            contingency_dict = get_GLM_HRRR_contingency_stats(DATE)
            write_table_to_file(contingency_dict, DATE, write_domains)
            print()

    return 'Finished %s' % len(DATES)    
        

###############################################################################

if __name__ == '__main__':


    ## Specify the valid Datetime of interest
    #DATE = datetime(2018, 5, 14, 22) # Mallard Fire
    #DATE = datetime(2018, 7, 5, 23) # Lake Christine
    #DATE = datetime(2018, 7, 17, 6) # July Storm
    #DATE = datetime(2018, 7, 27, 0) # Missing GLM data


    ## Each file will be all days for the hour of that month
    year = 2018
    #months = range(5,12)
    #hours = range(24)


    import socket
    host = socket.gethostname().split('.')[0]
    if host == 'wx2':
        months = [9]
        hours = range(24)
    elif host == 'wx3':
        months = [12]
        hours = range(24)
    elif host == 'wx4':
        months = [11]
        hours = range(24)
    elif host == 'meso3':
        months = [10]
        hours = range(24)
    elif host == 'meso4':
        months = [5]
        hours = range(24)
    
    print('\n     =======================================')
    print('        HOST: %s, MONTHS: %s HOURS: %s' % (host, months, hours))
    print('     =======================================\n')


    inputs = [(year, month, hour) for month in months for hour in hours]
    #inputs += [(year, month, hour) for month in range(7,11) for hour in range(24)]

    this = list(map(write_to_files_MP, inputs))