# Brian Blaylock
# September 7, 2018

"""
Match data collected from the GOES-16 Geostationary Lightning Mapper (GLM) with
the Advanced Baseline Imager (ABI) data collection windows.

New GLM files are created every 20 seconds
New ABI files are created every 5 minutes (however, the scan is about 2.5 mins)
Thus, we expect 15 GLM data files for the 5 minute window.

This function gets the GLM files that have ending dates between the ABI scan 
start and five minutes after the scan start. In other words, I want to collect
all the lightning observations during the ABI 5 minute interval.

Approximate Timeline of 5 minutes of ABI and GLM data collection:
    ABI scan    |----------------|_____________|
    GLM scan    |-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.|

    Where:
        - (dash) is 10 seconds of data collection
        _ (underscore) is 10 seconds of no data collection
        . (period) is the interval that the GLM writes a file

Functions:
    get_GLM_files_for_range() - Get GLM file names for a date range
    get_GLM_files_for_ABI()   - Get GLM file names for an ABI image
    accumulate_GLM()          - Return list of point data for a list of files
"""

import os 
import numpy as np 
from datetime import datetime, timedelta
from netCDF4 import Dataset

import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3/')
sys.path.append('B:\pyBKB_v3')


def get_GLM_files_for_range(sDATE, eDATE):
    """
    Get all the GLM 'flashes' data file names that occurred within a range of
    DATES

    Input:
        sDATE - the begining date you want GLM data for
        eDATE - the ending date you want GLM data for (exclusive)
    """
    # GOES16 ABI and GLM data is stored on horel-group7 and on Pando
    HG7 = '/uufs/chpc.utah.edu/common/home/horel-group7/Pando/GOES16/GLM-L2-LCFA/'

    # List range of dates by hour. Each hour is a directory we need to grab files from.
    hours = int((eDATE-sDATE).seconds/60/60 + (eDATE-sDATE).days*24 + 1)
    DATES = [sDATE+timedelta(hours=h) for h in range(hours)]

    GLM = []
    for i in DATES:
        DIR = '%s/%s/' % (HG7, i.strftime('%Y%m%d/%H'))
        try:
            for f in os.listdir(DIR):
                GLM.append(DIR+f)
        except:
            print('Missing: %s' % DIR)
            pass

    GLM_FILES = list(filter(lambda x: datetime.strptime(x.split('_')[4], 'e%Y%j%H%M%S%f') < eDATE
                            and  datetime.strptime(x.split('_')[4], 'e%Y%j%H%M%S%f') >= sDATE, GLM))

    return_this = {'Files': GLM_FILES,
                   'Range': [sDATE, eDATE]                  
                  }
    
    return return_this


def get_GLM_files_for_ABI(FILE, next_minutes=5):
    """
    Get all the GLM 'flashes' data file names that occurred within a range of
    DATES

    Input:
        FILE         - The file name of an ABI image
        next_minutes - Time time duration to collect GLM file names. Default is
                       5 minutes which is the timedelta between ABI scans.
    """
    # GOES16 ABI and GLM data is stored on horel-group7 and on Pando
    HG7 = '/uufs/chpc.utah.edu/common/home/horel-group7/Pando/GOES16/GLM-L2-LCFA/'

    # List range of dates by hour. Each hour is a directory we need to grab files from.
    # Get info from the file name
    FILE_SPLIT = FILE.split('_')
    sDATE = datetime.strptime(FILE_SPLIT[3], 's%Y%j%H%M%S%f')
    eDATE = sDATE + timedelta(minutes=next_minutes)

    hours = int((eDATE-sDATE).seconds/60/60 + (eDATE-sDATE).days*24 + 1)
    DATES = [sDATE+timedelta(hours=h) for h in range(hours)]

    GLM = []
    for i in DATES:
        DIR = '%s/%s/' % (HG7, i.strftime('%Y%m%d/%H'))
        try:
            for f in os.listdir(DIR):
                GLM.append(DIR+f)
        except:
            print('Missing: %s' % DIR)
            pass

    GLM_FILES = list(filter(lambda x: datetime.strptime(x.split('_')[4], 'e%Y%j%H%M%S%f') < eDATE
                            and  datetime.strptime(x.split('_')[4], 'e%Y%j%H%M%S%f') >= sDATE, GLM))

    return_this = {'Files': GLM_FILES,
                   'Range': [sDATE, eDATE]                  
                  }
    
    return return_this


def accumulate_GLM(GLM, data_type='flash', verbose=True):
    """
    Accumulate all the GLM 'flash' data that occurred within the 5-minute
    scan window for an ABI file and return the latitude, longitude, and energy
    of all the flashes.

    Input:
        GLM       - A list of GLM files or the dictionary returned by 
                    get_GLM_files_for_range() or get_GLM_files_for_ABI().
        data_type - Data to retrieve. Default is 'flash' data. Other options 
                    are 'event' and 'group' which have messed up latitude and
                    longitude, so don't use them unless you figure them out.
    
    Output:
        A dictionary containing the latitudes, longitudes, and energy of each
        flash (or event or group). The num_per_20_seconds is a list of length
        of observations per file. If you need to, you can separate the data
        values by the data's 20-second intervals rather than the 5-minute lump.
    """
    # If GLM is not a dictionary with a key 'Files', then package it as a dict
    if type(GLM) is not dict:
        GLM = {'Files':GLM}
        # Find the earliest and latest file start date if they are not provided
        FILE_DATES = [datetime.strptime(i.split('_')[3], 's%Y%j%H%M%S%f') for i in GLM['Files']]
        GLM['Range'] = [min(FILE_DATES), max(FILE_DATES)]

    # Initialize arrays for latitude, longitude, and flash energy
    lats = np.array([])
    lons = np.array([])
    energy = np.array([])
    num_per_20_seconds = np.array([])

    # Read the data
    for i, FILE in enumerate(GLM['Files']):
        G = Dataset(FILE, 'r')
        lats = np.append(lats, G.variables[data_type+'_lat'][:])
        lons = np.append(lons, G.variables[data_type+'_lon'][:])
        energy = np.append(energy, G.variables[data_type+'_energy'][:])
        num_per_20_seconds = np.append(num_per_20_seconds, len(G.variables[data_type+'_lat'][:]))
        G.close()
        if verbose:
            DATE = datetime.strptime(FILE.split('_')[3], 's%Y%j%H%M%S%f')
            sys.stdout.write('%.1f%% Complete (%s of %s) : %s\r' % (i/len(GLM['Files'])*100, i, len(GLM['Files']), DATE))

    return {'latitude': lats,
            'longitude': lons,
            'energy': energy,
            'number of values each 20 seconds': num_per_20_seconds,
            'DATETIME': GLM['Range']}


if __name__ == '__main__':
    ## ABI File
    #ABI_FILE = 'OR_ABI-L2-MCMIPC-M3_G16_s20181280332199_e20181280334572_c20181280335091.nc'
    ABI = 'OR_ABI-L2-MCMIPC-M3_G16_s20181282357201_e20181282359574_c20181290000075.nc'

    ## Get Cooresponding GLM files
    GLM = accumulate_GLM(get_GLM_files_for_ABI(ABI))

    
    ## Make a new map object for the HRRR model domain map projection
    mH = Basemap(resolution='i', projection='lcc', area_thresh=5000, \
                width=1800*3000, height=1060*3000, \
                lat_1=38.5, lat_2=38.5, \
                lat_0=38.5, lon_0=-97.5)

    ## Plot each GLM file on the map
    plt.figure(figsize=[15, 10])

    print('Datetime Range:', GLM['DATETIME'])

    mH.scatter(GLM['longitude'], GLM['latitude'],
                marker='+',
                color='yellow',
                latlon=True)

    mH.drawmapboundary(fill_color='k')
    mH.drawcoastlines(color='w')
    mH.drawcountries(color='w')
    mH.drawstates(color='w')

    plt.title('GOES-16 GLM Flashes', fontweight='semibold', fontsize=15)
    plt.title('Start: %s\nEnd: %s' % (GLM['DATETIME'][0].strftime('%H:%M:%S UTC %d %B %Y'), GLM['DATETIME'][1].strftime('%H:%M:%S UTC %d %B %Y')), loc='right')    
    plt.show()
