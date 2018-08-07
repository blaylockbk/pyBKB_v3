# Brian Blaylock
# July 25, 2018

"""
Calculate the empirical cumulative distribution (percentiles)
for a set of HRRR grids.

For every hour of the year, calculate +/-15 day (31 total days) mean and
percentiles for the CONUS from the Pando HRRR archive. New file is created for
each hour saved as a HDF5 file.

Built to run on the Open Science Grid
"""

import os
import numpy as np
from datetime import datetime, timedelta
import h5py

import sys
sys.path.append('../../../pyBKB_v3')
from BB_HRRR.HRRR_Pando import get_hrrr_variable
from BB_wx_calcs.wind import wind_uv_to_spd

def get_HRRR_value(validDATE):
    """
    Get HRRR data. Retrun the value, not the latitude and longitude.
    """
    runDATE = validDATE - timedelta(hours=fxx)
    
    if variable[:2] == 'UV':
        # Then we want to calculate the wind speed from U and V components.
        wind_lev = variable.split(':')[-1] # This is the level of interest        
        Hu = get_hrrr_variable(runDATE, 'UGRD:'+wind_lev,
                               fxx=fxx, model='hrrr', field='sfc',
                               value_only=True, verbose=False)
        Hv = get_hrrr_variable(runDATE, 'VGRD:'+wind_lev,
                               fxx=fxx, model='hrrr', field='sfc',
                               value_only=True, verbose=False)
        
        if np.shape(Hu['value']) == () or np.shape(Hv['value']) == ():
            print("!! WARNING !! COULD NOT GET %s %s f%02d" % (variable, runDATE, fxx))
            return None
        else:
            spd = wind_uv_to_spd(Hu['value'], Hv['value'])
            return spd
    
    else:
        H = get_hrrr_variable(runDATE, variable,
                              fxx=fxx, model='hrrr', field='sfc',
                              value_only=True, verbose=False)

        if np.shape(H['value']) == ():
            # If the data is a nan, then return None. This will be important for filtering.
            print("!! WARNING !! COULD NOT GET %s %s f%02d" % (variable, runDATE, fxx))
            return None
        else:
            return H['value']


def stats_save(H, centerDATE, validDATES, SAVEDIR='.'):
    """
    Calculate the statistics for a set of HRRR grids and save them to an HDF5 
    file.

    Input:
        H           - Three dimensional array of the HRRR grids
        centerDATE  - Datetime object, assuming a leapyear 2016, of the
                      center date of intereste in the validDATES list
        validDATES  - List of datetimes the data represents
    """
    # Remove empty arrays that may exist. None arrays exist if the HRRR file
    # could not be downloaded from Pando.
    print("    Date Range", validDATES[0], validDATES[-1])
    print("    Removing empty arrays...", end='')
    count_none = np.sum(1 for x in H if x is None)
    H = list(filter(lambda x: x is not None, H))
    print('done!')
    print("    Counted %s None values" % count_none)
    percentage_retrieved = 100*len(H)/float(len(validDATES))
    print("    Retrieved %s/%s expected samples for calculations --- %.2f%% \n" % (len(H), len(validDATES), percentage_retrieved))
    H = np.array(H)

    # Exit if job didn't download enough.
    if percentage_retrieved < 90:
        print('!!! The results array collected less than 90% of the expected samples')
        print('!!! Exit with exit code 74')
        sys.exit(os.EX_IOERR)
   
    # Calculate Statistics. Round to only two decimals to save storage.
    
    # Percentiles
    timer = datetime.now()
    print("    Calculate percentiles...", end='')
    perH = np.percentile(H, percentiles, axis=0)
    perH = np.round(perH, 2)
    print('done!')

    # Mean
    print("    Calculate mean...", end='')
    sumH = np.sum(H, axis=0)
    count = len(H)
    meanH = sumH/count
    meanH = np.round(meanH, 2)
    print('done!')

    stats_timer = datetime.now() - timer
    print("    Statistics Timer: %s" % stats_timer)


    # Save directory
    if not os.path.exists(SAVEDIR):
        os.makedirs(SAVEDIR)
        print('created directory: %s' % SAVEDIR)
    
    # Create HDF5 file of the data
    print("")
    print("    Saving the HDF5 file...", end='')
    timer = datetime.now()
    FILENAME = '%s/OSG_HRRR_%s_m%02d_d%02d_h%02d_f%02d.h5' % (SAVEDIR, var_str, centerDATE.month, centerDATE.day, centerDATE.hour, fxx)
    f = h5py.File(FILENAME, 'w')
    h5_per = f.create_dataset('percentiles', data=np.array(percentiles), compression="gzip", compression_opts=9)
    h5_count = f.create_dataset('samples', data=count)
    h5_expected = f.create_dataset('expected samples', data=len(validDATES))
    h5_cores = f.create_dataset('cores', data=use_cpu)
    h5_timer = f.create_dataset('download timer', data=str(download_timer))
    h5_timer = f.create_dataset('statistics timer', data=str(stats_timer))
    h5_mean = f.create_dataset('mean', data=meanH, compression="gzip", compression_opts=9)
    for i in range(len(percentiles)):
        f.create_dataset('p%02d' % (percentiles[i]), data=perH[i], compression="gzip", compression_opts=9)
    h5_begD = f.create_dataset('Beginning Date', data=str(validDATES[0]))
    h5_endD = f.create_dataset('Ending Date', data=str(validDATES[-1]))
    f.close()
    print('done!')
    print('    FILE:', FILENAME)
    hdf5_timer = datetime.now() - timer
    print("    HDF5 Timer: %s" % hdf5_timer)


# ==== Input Controls =========================================================

# Variable to work on. For wind speed calculations, use "UVGRD:10-m".
variable = sys.argv[1].replace('-', ' ')
#variable = 'UVGRD:10-m'.replace('-', ' ')
var_str = variable.replace(':', '-').replace(' ', '-')

# Date to work on. Input represents the valid date.
month = int(sys.argv[2])
day = int(sys.argv[3])
hour = int(sys.argv[4])
fxx = int(sys.argv[5])
#month = 7
#day = 15
#hour = 21
#fxx = 0

#SAVEDIR = '/uufs/chpc.utah.edu/common/home/horel-group8/blaylock/HRRR_OSG/hourly31_twoyears/%s' % var_str
SAVEDIR = './'

# Window: +/- days to include in the sample
window = int(sys.argv[6])
#window = 15

# Worker Jobs. The number of jobs each worker should do.
jobs_per_worker = int(sys.argv[7])
#jobs_per_worker = 1

# Archvie Data Range: The archive period of record to use, adjusted by window.
'''
The archive range is adjusted by the window so that you get consecutive years
at date range limits. This is a necessary adjustment for the first 15 days 
(or however long the window is) of the archive period, else the sample will
jump across three different years. For example, without the window
adjustment we get 62 samples that spans 3 different years:
    July 15-30, 2016 + June 30 - July 30, 2017 + June 30 - July 15, 2018
We don't want to span three different season (see how the sample is split
15 days in 2016 and 15 days in 2018). We only want to get two 
different season. With the adjustment we get 62 samples from 2 years:
    June 30 - July 30 2017 + June 30 - July 30 2017
'''
sDATE = datetime(2016, 7, 15) + timedelta(days=window+1)
eDATE = datetime(2018, 7, 15) + timedelta(days=window+1)

# List percentiles you want
percentiles = [0, 1, 2, 3, 4, 5, 10, 25, 33, 50, 66, 75, 90, 95, 96, 97, 98, 99, 100]

# Should I download using multiprocessing?
use_mp = True

# =============================================================================

# Create a list of validDATES for the window that are within the archive record.
years = range(sDATE.year, eDATE.year+1)
validDATES = []

for y in years:
    a = [datetime(y, month, day, hour) - timedelta(days=d) for d in range(window,-window-1,-1)
        if datetime(y, month, day, hour) - timedelta(days=d) >= sDATE
        if datetime(y, month, day, hour) - timedelta(days=d) < eDATE]
    validDATES += a

centerDATE = datetime(2016, month, day, hour)

print("\n", variable)
print('  Job 1: Working on %s' % (centerDATE.strftime('month: %m\t  day: %d\t hour: %H')))
print("  --- OSG Worker Requesting %s Samples ---" % len(validDATES))
print("")



if len(validDATES) != 0:
    # Download data for each validDATE
    if use_mp:
        try:
            import multiprocessing
            timer = datetime.now()
            cpu_count = multiprocessing.cpu_count()
            use_cpu = np.minimum(8, cpu_count) # don't save much download time when using more than 8 cores
            print("    Using %s CPUs" % use_cpu)
            p = multiprocessing.Pool(use_cpu)
            H = p.map(get_HRRR_value, validDATES)
            p.close()
            download_timer = datetime.now() - timer
            print("    Multiprocessing Download Timer:", download_timer)
        except:
            timer = datetime.now()
            print("    Multiprocessing Error. Running job in serial.")
            use_cpu = 1
            H = list(map(get_HRRR_value, validDATES))
            download_timer = datetime.now() - timer
            print("    Serial Download Timer:", download_timer)

    else:
        timer = datetime.now()
        use_cpu = 1
        print("    Using %s CPUs" % use_cpu)
        H = list(map(get_HRRR_value, validDATES))
        download_timer = datetime.now() - timer
        print("    Serial Download Timer: %s" % download_timer)

    # Compute statistics and save data 
    stats_save(H, centerDATE, validDATES, SAVEDIR=SAVEDIR)

    if jobs_per_worker > 1:
        job = 2
        while job <= jobs_per_worker:
            # The new centerDATE
            centerDATE += timedelta(days=1) # Center Date is +1 day
            print('\nJob %s: Working on %s' % (job, centerDATE.strftime('month: %m\t  day: %d\t hour: %H')))
            new_validDATES = []
            for y in years:
                a = [datetime(y, centerDATE.month, centerDATE.day, centerDATE.hour) - timedelta(days=d) for d in range(window,-window-1,-1)
                    if datetime(y, centerDATE.month, centerDATE.day, centerDATE.hour) - timedelta(days=d) >= sDATE
                    if datetime(y, centerDATE.month, centerDATE.day, centerDATE.hour) - timedelta(days=d) < eDATE]
                new_validDATES += a    
            
            # Which grids in H do we already have?
            grids_to_keep = [i in new_validDATES for i in validDATES]
            new_H = [h for i, h in enumerate(H) if grids_to_keep[i]]
            
            # Which grids to I need to get
            grids_to_get = [i for i in new_validDATES if i not in validDATES]
            print('    Need to download %s additional grids.' % len(grids_to_get))
            for dd in grids_to_get:
                new_H.append(get_HRRR_value(dd))

            # Run stats and save data
            stats_save(new_H, centerDATE, new_validDATES, SAVEDIR=SAVEDIR)
            job += 1


else:
    print('!!! There were no dates to retrieve. Exit with exit code 74')
    sys.exit(os.EX_IOERR)
