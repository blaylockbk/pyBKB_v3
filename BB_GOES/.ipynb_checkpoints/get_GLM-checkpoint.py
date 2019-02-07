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
import xarray
import multiprocessing
import itertools

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3/')
sys.path.append('B:\pyBKB_v3')

def get_GLM_file_nearesttime(DATE, window=0, verbose=True):
    """
    Get the file path+name for the GLM file nearest to a specified date. Will
    return a list of nearby files according to the window argument.
    The request DATE is the *start date* of the GLM observation time and 
    represents observed events/groups/flashes begining at DATE and ending at
    DATE+20 seconds.

    Input:
        DATE   - datetime object for the date you want to find the nearest GLM
                 file available.
        window - number of files before and after the nearest date requested to
                 return. Default is 0, which will only return the nearest file.
                 If set to 6, then will return 13 total files--6 before the
                 requested DATE (two minutes before DATE), the file nearest to
                 the requested DATE, and 6 after the DATE (two minutes after
                 DATE).
    
    Return:
        A list of file paths+names of GLM files.
    """
    # List available files for the requested datetime and include files for
    # +/- 1 hour
    HG7 = '/uufs/chpc.utah.edu/common/home/horel-group7/Pando/GOES16/GLM-L2-LCFA/'
    ls1 = HG7+'%s/' % (DATE-timedelta(hours=1)).strftime('%Y%m%d/%H')
    ls2 = HG7+'%s/' % DATE.strftime('%Y%m%d/%H')
    ls3 = HG7+'%s/' % (DATE+timedelta(hours=1)).strftime('%Y%m%d/%H')

    if verbose:
        print("Looking in these file paths for th nearest datetime")
        print(ls1)
        print(ls2)
        print(ls3)

    # List the files in those directory
    files1 = list(map(lambda x: HG7+(datetime.strptime(x.split('_')[3], 's%Y%j%H%M%S%f')).strftime('%Y%m%d/%H/')+x, os.listdir(ls1)))
    files2 = list(map(lambda x: HG7+(datetime.strptime(x.split('_')[3], 's%Y%j%H%M%S%f')).strftime('%Y%m%d/%H/')+x, os.listdir(ls2)))
    files3 = list(map(lambda x: HG7+(datetime.strptime(x.split('_')[3], 's%Y%j%H%M%S%f')).strftime('%Y%m%d/%H/')+x, os.listdir(ls3)))
    all_files = files1+files2+files3

    # Find the file nearest the requested DATE
    nearest_datetime_idx = np.argmin(list(map(lambda x: np.abs(datetime.strptime(x.split('_')[3], 's%Y%j%H%M%S%f')-DATE), all_files)))
    nearest_datetime = datetime.strptime(all_files[nearest_datetime_idx].split('_')[3], 's%Y%j%H%M%S%f')

    if verbose:
        print('       requested:', DATE)
        print('nearest GLM file:', nearest_datetime)
        print('        GLM file:', all_files[nearest_datetime_idx])

    # Return the list
    if window==0:
        if verbose:
            print('1 file for nearst time becuase window set to 0')
        return all_files[nearest_datetime_idx]
    else:
        # Retrieve files for the requested window
        a = slice(nearest_datetime_idx-window, nearest_datetime_idx+window+1)
        if verbose:
            print('window = %s files (+/- %s minutes)' % (window, window/3))
            print('returning %s files' % len(all_files[a]))
        return all_files[a]




def get_GLM_files_for_range(sDATE, eDATE, HOURS=range(24)):
    """
    Get all the GLM 'flashes' data file names that occurred within a range of
    DATES

    Input:
        sDATE - the begining date you want GLM data for
        eDATE - the ending date you want GLM data for (exclusive)
        HOURS - Separate retreval by hour
    """
    # GOES16 ABI and GLM data is stored on horel-group7 and on Pando
    HG7 = '/uufs/chpc.utah.edu/common/home/horel-group7/Pando/GOES16/GLM-L2-LCFA/'

    # List range of dates by hour. Each hour is a directory we need to grab files from.
    ## Old method: All possible files from all hours
    #hours = int((eDATE-sDATE).seconds/60/60 + (eDATE-sDATE).days*24 + 1)
    #DATES = [sDATE+timedelta(hours=h) for h in range(hours)]
    ## New method: All possible files from hours requested
    days = (eDATE-sDATE).days
    DAYS = [sDATE + timedelta(days=d) for d in range(days)]
    DATES = [datetime(d.year, d.month, d.day, h) for d in DAYS for h in HOURS]

    PATHS = ['%s/%s/' % (HG7, i.strftime('%Y%m%d/%H')) for i in DATES]

    GLM = []
    for i in PATHS:
        try:
            for f in os.listdir(i):
                GLM.append(i+f)
        except:
            print('Missing: %s' % i)
            pass

    # Filter out the ones not within the requested sDATE and eDATE
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


def accumulate_GLM_FAST_MP(inputs):
    """input - the full path to a GLM directory"""
    complete, data_type, FILE = inputs
    G = xarray.open_dataset(FILE)
    lats = G.variables[data_type+'_lat'].data
    lons = G.variables[data_type+'_lon'].data
    G.close()
    if complete%5 == 0:
        print('%.1f%%' % complete)
    return [lats, lons]


def accumulate_GLM_FAST(GLM, data_type='flash', verbose=True):
    """A mutliprocessing (fast) version of accumulate_GLM"""
    # If GLM is not a dictionary with a key 'Files', then package it as a dict
    if type(GLM) is not dict:
        GLM = {'Files':GLM}
        # Find the earliest and latest file start date if they are not provided
        FILE_DATES = [datetime.strptime(i.split('_')[3], 's%Y%j%H%M%S%f') for i in GLM['Files']]
        GLM['Range'] = [min(FILE_DATES), max(FILE_DATES)]

    inputs = [[i/len(GLM['Files'])*100, data_type, f] for i, f in enumerate(GLM['Files'])]

    cpus = np.minimum(len(GLM['Files']), 10)
    P = multiprocessing.Pool(cpus)
    results = P.map(accumulate_GLM_FAST_MP, inputs)
    P.close()

    lats = [i[0] for i in results]
    lons = [i[1] for i in results]
    lats = list(itertools.chain(*lats))
    lons = list(itertools.chain(*lons))

    return {'latitude': np.array(lats),
            'longitude': np.array(lons),
            'DATETIME': GLM['Range']}

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
        G = xarray.open_dataset(FILE)
        lats = np.append(lats, G.variables[data_type+'_lat'].data)
        lons = np.append(lons, G.variables[data_type+'_lon'].data)
        energy = np.append(energy, G.variables[data_type+'_energy'].data)
        num_per_20_seconds = np.append(num_per_20_seconds, len(G.variables[data_type+'_lat'].data))
        G.close()
        if verbose:
            DATE = datetime.strptime(FILE.split('_')[3], 's%Y%j%H%M%S%f')
            sys.stdout.write('\r%.1f%% Complete (%s of %s) : %s' % (i/len(GLM['Files'])*100, i, len(GLM['Files']), DATE))

    return {'latitude': lats,
            'longitude': lons,
            'energy': energy,
            'number of values each 20 seconds': num_per_20_seconds,
            'DATETIME': GLM['Range']}


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    from mpl_toolkits.basemap import Basemap
    
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
