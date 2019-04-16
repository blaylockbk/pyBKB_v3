## Brian Blaylock
## April 16, 2019              "Kinda cloudy. We've been getting lots of rain."

"""
Get GOES GLM or ABI data from Horel-Group7

NOTE: For reference, we expect 180 GLM files per hour (file every 20 seconds)
      and 12 ABI files per hour (CONUS file every 5 minutes with ~2.5 minutes 
      for each scan cycle).
      Thus, we expect 15 GLM data files for a 5 minute ABI window.

Approximate Timeline of 5 minutes of ABI and GLM data collection:
    ABI scan    (start)[----------------|_____________](end)
    GLM scan    (start)[-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.](end)

    Where:
        - (dash) is 10 seconds of data collection
        _ (underscore) is 10 seconds of no data collection
        . (period) is an additional 10 second interval of GLM data collection.

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


def get_GOES_nearesttime(DATE, product='ABI', satellite=16, window=0, verbose=True):
    """
    Get the full file path and name for the file nearest to the specified DATE.

    Input:
        DATE      - Datetime object for the date you want to find the nearest
                    file available.
        product   - 'ABI' for Advanced Baseline Imager, or
                    'GLM' for Geostationary Lightning Mapper
        satellite - 16 or 17, denotes GOES-16 or GOES-17. Default is 16.
        window    - Number of minutes +/- the requested nearest DATE.
                    Default is 0 and only returns the nearest file.
                    If window is 30, will get the 30 minutes before and after
                    the DATE and gives an hours worth of data.
    """
    print('Requested %s\tsatellite: GOES-%s\tProduct: %s' % (DATE, satellite, product))

    assert satellite in [16, 17], ('satellite must be 16 or 17')
    assert product in ['ABI', 'GLM'], ('product must be "ABI" or "GLM"')

    if satellite == 16:
        if product == 'ABI':
            assert DATE >= datetime(2017, 7, 11), ('GOES-16 ABI available after 11 July 2017.')
        if product == 'GLM':
            assert DATE >= datetime(2018, 5, 1), ('GOES-16 GLM available after 1 May 2018.')
    elif satellite == 17:
        if product == 'ABI':
            assert DATE >= datetime(2019, 1, 1), ('GOES-17 ABI available after 1 January 2019.')
        if product == 'GLM':
            assert DATE >= datetime(2019, 2, 7), ('GOES-17 GLM available after 7 February 2019.')

    # Full name of the product
    if product == 'ABI':
        PRODUCT= 'ABI-L2-MCMIPC'
    elif product == 'GLM':
        PRODUCT= 'GLM-L2-LCFA'
    
    # List all files for directory of interest and previous and next hour
    # (just in case the closest time is in one of those). If we are requesting
    # a single nearest time, or a window of files less than one hour, then we 
    # look in the requested DATE directory and previous and next hour. If
    # window > 60 minutes, then we need to look in additional directories.
    # For example, if window is 200 minutes, then we need to check +/-
    # 3 hours
    hours_window_adjust = int(np.maximum(1, np.ceil(window/60)))
    sDATE = DATE-timedelta(hours=hours_window_adjust)
    eDATE = DATE+timedelta(hours=hours_window_adjust)
    
    # Files are organized by hour. Get all hours 
    dt = eDATE-sDATE
    hours = dt.days*24 + int((dt).seconds/3600)
    look_here_DATES = [sDATE+timedelta(hours=h) for h in range(hours+1)]

    # Directory all data is stored on horel-group7
    HG7 = '/uufs/chpc.utah.edu/common/home/horel-group7/Pando/GOES%s/%s/' % (satellite,PRODUCT)

    files = []
    for D in look_here_DATES:
        # I apologize, but I am downloadling GOES-16 ABI data differently than
        # everything else (GOES-16 is not kept in hour direcotires).
        if satellite == 16 and product == 'ABI':
            DIR = HG7+'%s/' % D.strftime('%Y%m%d')
        else:
            DIR = HG7+'%s/' % D.strftime('%Y%m%d/%H')
        if verbose:
            print("Looking here: %s" % DIR)
        # List the files in those directories, if the directory exists.
        if os.path.exists(DIR):
            files += list(map(lambda x: DIR+x, os.listdir(DIR)))
        else:
            print('**************************************************************')
            print('!!!WARNING!!! Missing %s directory: %s', (product, DIR))
            print('**************************************************************')

    # Sometime a file might be in the wrong directory (this was the case when
    # GOES-17 was being tested). We only want files for the requested satelite.
    files = list(filter(lambda x: '_G%02d_' % satellite in x, files))
    
    # Filter for NetCDF type file (remove .png images, if any)
    files = list(filter(lambda x: x[-3:] == '.nc', files))

    # Convert to numpy array, only get unique items (in case there are 
    # duplicates), and sort by name.
    files = np.array(files)
    files = np.unique(files)
    files = np.sort(files)
    
    # Convert the files start scan and end scan to datetime object.
    sSCANS = np.array([datetime.strptime(x.split('_')[3], 's%Y%j%H%M%S%f') for x in files])
    eSCANS = np.array([datetime.strptime(x.split('_')[4], 'e%Y%j%H%M%S%f') for x in files])
    
    if window == 0:
        # We only expect 1 file to be closest to the date requested.
        expected = 1
        # Nearest file is the closest eSCAN datetime to the requested DATE
        nearest_file_idx = np.argmin(np.abs(eSCANS-DATE))
        nearest_file = files[nearest_file_idx]
        if verbose:
            print('Nearest File:', nearest_file)
            print('File DATETIME:', eSCANS[nearest_file_idx])
        return nearest_file
    else:
        # GLM outputs files are every 20 seconds, thus, we expect 3 files per
        # minute. If window is +/-5 minutes, then we expect to retrieve data
        # from 30 files, i.e. 5*2 minutes * 3 files per minute == 30 files.
        expected = window*2*3
        # If window != 0, then get a range of files.
        # Filter the files based on the requested range. File start scan should be 
        # after sDATE and file end scan should be before eDATE.
        sWINDOW = DATE - timedelta(minutes=window)
        eWINDOW = DATE + timedelta(minutes=window)
        within_bounds = np.logical_and(sSCANS>=sWINDOW, eSCANS<=eWINDOW)
        window_files = files[within_bounds]

        len_files = len(window_files)
        if len_files == 0:
            print('************************************************************')
            print('!! WARNING !! There are no %s files for the period requested!' % product)
            print('************************************************************')
            return {'Files': [],
                    'Number': 0,
                    'Number Expected': expected,
                    'Range': [np.nan, np.nan]}
        else:
            if verbose:
                print('---------------------------------------------------')
                print(' Window == +/- %s Minutes' % (window))
                print('    first observation: %s' % (sWINDOW))
                print('     last observation: %s' % (eWINDOW))
                print('  Returning data from %s GLM files (expected %s)' % (len_files, expected))
                print('---------------------------------------------------')
                if len_files/expected < .5:
                    print('************************************************************')
                    print('!! WARNING !! Less than 50% of the expected GLM files available for the period')
                    print('************************************************************')
        return {'Files': window_files,
                'Number': len_files,
                'Number Expected': expected,
                'Range': [sWINDOW, eWINDOW]}
