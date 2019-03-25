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
    filter_by_path()          - Filter GLM flashes by a path.
    filter_by_HRRR()          - Filter GLM flashes by HRRR domain.
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
        DATE   - Datetime object for the date you want to find the nearest GLM
                 file available.
        window - Number of minutes +/- the requested nearest DATE.
                 Default is 0 and only returns the nearest file.
    
    Return:
        A list of file paths+names of GLM files.
    """
    # Number of expected files 
    expected = window*3*2
    
    # List available files for the requested datetime and include files for
    # +/- 1 hour
    HG7 = '/uufs/chpc.utah.edu/common/home/horel-group7/Pando/GOES16/GLM-L2-LCFA/'
    ls1 = HG7+'%s/' % (DATE-timedelta(hours=1)).strftime('%Y%m%d/%H')
    ls2 = HG7+'%s/' % DATE.strftime('%Y%m%d/%H')
    ls3 = HG7+'%s/' % (DATE+timedelta(hours=1)).strftime('%Y%m%d/%H')

    if verbose:
        print("Looking in these file paths for the nearest datetime")
        print('  ', ls1)
        print('  ', ls2)
        print('  ', ls3)
        print('---------------------------------------------------')

    # List the files in those directory, if the directory exists.
    if os.path.exists(ls1):
        files1 = list(map(lambda x: HG7+(datetime.strptime(x.split('_')[3], 's%Y%j%H%M%S%f')).strftime('%Y%m%d/%H/')+x, os.listdir(ls1)))
        # Remove GOES-17 files if there are any
        files1 = list(filter(lambda x: '_G16_' in x, files1))
    else:
        files1 = []
        print('**************************************************************')
        print('!!!WARNING!!! Missing GLM directory', ls1)
        print('**************************************************************')
    if os.path.exists(ls2):
        files2 = list(map(lambda x: HG7+(datetime.strptime(x.split('_')[3], 's%Y%j%H%M%S%f')).strftime('%Y%m%d/%H/')+x, os.listdir(ls2)))
        # Remove GOES-17 files if there are any
        files2 = list(filter(lambda x: '_G16_' in x, files2))
    else:
        files2 = []
        print('**************************************************************')
        print('!!!WARNING!!! Missing GLM directory', ls2)
        print('**************************************************************')
    if os.path.exists(ls3):
        files3 = list(map(lambda x: HG7+(datetime.strptime(x.split('_')[3], 's%Y%j%H%M%S%f')).strftime('%Y%m%d/%H/')+x, os.listdir(ls3)))
        # Remove GOES-17 files if there are any
        files3 = list(filter(lambda x: '_G16_' in x, files3))
    else:
        files3 = []
        print('**************************************************************')
        print('!!!WARNING!!! Missing GLM directory', ls3)
        print('**************************************************************')
    

    all_files = np.array(files1+files2+files3)
    all_files = np.sort(all_files) # Sort files by name

    if len(all_files) == 0:
        print('There are no GLM files within three hours of Date requested')
        if window==0:
            return None
        else:
            return {'Files': [],
                    'Number': 0,
                    'Number Expected': expected,
                    'Range': [np.nan, np.nan]}                

    # Get start datetime of all files
    files_datetime = list(map(lambda x: datetime.strptime(x.split('_')[3], 's%Y%j%H%M%S%f'), all_files))
    files_datetime = np.array(files_datetime)

    # Find the file nearest the requested DATE
    nearest_datetime_idx = np.argmin(np.abs(files_datetime - DATE))
    nearest_datetime = datetime.strptime(all_files[nearest_datetime_idx].split('_')[3], 's%Y%j%H%M%S%f')

    if verbose:
        print('    Date Requested:', DATE)
        print('  Nearest GLM file:', nearest_datetime)

    # Return the list of files
    if window==0:
        if verbose:
            print('Return 1 file nearest to %s because window is set to 0' % nearest_datetime)
        return all_files[nearest_datetime_idx]
    else:
        '''
        GLM outputs files are every 20 seconds. We expect 3 files per minute.
        If window is 5 minutes, we expect to retrieve data from 31 files
           3*5 files before DATE, file nearest DATE, 3*5 files after DATE
        '''
        
        # DATETIME of plus and minus window
        minus_window_datetime = DATE - timedelta(minutes=window)
        plus_window_datetime = DATE + timedelta(minutes=window)
        
        dates_in_window = np.logical_and(files_datetime>=minus_window_datetime, 
                                         files_datetime<plus_window_datetime)

        if np.sum(dates_in_window)==0:
            print('************************************************************')
            print('!! WARNING !! There are no GLM files for the period requested!')
            print('************************************************************')
            return {'Files': [],
                    'Number': 0,
                    'Number Expected': expected,
                    'Range': [np.nan, np.nan]}

        # Get index of plus and minus window datetime
        #minus_window_datetime_idx = np.argmin(np.abs(files_datetime-minus_window_datetime))
        #plus_window_datetime_idx = np.argmin(np.abs(files_datetime-plus_window_datetime))

        # Retrieve files for the requested window
        #a = slice(minus_window_datetime_idx, plus_window_datetime_idx)
        #sDATE = datetime.strptime(all_files[a][0].split('_')[3], 's%Y%j%H%M%S%f')
        #eDATE = datetime.strptime(all_files[a][-1].split('_')[4], 'e%Y%j%H%M%S%f')
        a = all_files[dates_in_window]
        sDATE = datetime.strptime(a[0].split('_')[3], 's%Y%j%H%M%S%f')
        eDATE = datetime.strptime(a[-1].split('_')[4], 'e%Y%j%H%M%S%f')
        if verbose:
            print('---------------------------------------------------')
            print(' Window == +/- %s Minutes' % (window))
            print(' Window DATES == ', minus_window_datetime, plus_window_datetime)
            print('    first observation: %s' % (sDATE))
            print('     last observation: %s' % (eDATE))
            print('  Returning data from %s GLM files (expected %s)' % (len(a), expected))
            print('---------------------------------------------------')
            if len(a)/expected < .5:
                print('************************************************************')
                print('!! WARNING !! Less than 50% of the expected GLM files available for the period')
                print('************************************************************')
        return {'Files': a,
                'Number': len(a),
                'Number Expected': expected,
                'Range': [sDATE, eDATE] 
               }



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
    energy = G.variables[data_type+'_energy'].data
    if data_type == 'event':
        area = np.nan
    else:
        area = G.variables[data_type+'_area'].data
    G.close()
    if complete%5 == 0:
        sys.stdout.write('\r-->> Accumulate GLM FAST MP: %.1f%%' % complete)
    return [lats, lons, area, energy]


def accumulate_GLM_FAST(GLM, data_type='flash', verbose=True):
    """
    A multiprocessing (fast) version of accumulate_GLM
        GLM       - a list of file paths
        data_type - 'flash', 'group', or 'event'
    """    

    # If GLM is not a dictionary with a key 'Files', then package it as a dict
    if type(GLM) is not dict:
        GLM = {'Files':GLM}
        # Find the earliest and latest file start date if they are not provided
        FILE_DATES = [datetime.strptime(i.split('_')[3], 's%Y%j%H%M%S%f') for i in GLM['Files']]
        GLM['Range'] = [min(FILE_DATES), max(FILE_DATES)]

    if len(GLM['Files'])==0:
        print('************************************************************')
        print('!! WARNING !! There are no GLM files!')
        print('************************************************************')
        return None
    
    inputs = [[i/len(GLM['Files'])*100, data_type, f] for i, f in enumerate(GLM['Files'])]

    cpus = np.minimum(len(GLM['Files']), 10)
    P = multiprocessing.Pool(cpus)
    results = P.map(accumulate_GLM_FAST_MP, inputs)
    P.close()

    lats = [i[0] for i in results]
    lons = [i[1] for i in results]
    area = [i[2] for i in results]
    energy = [i[3] for i in results]
    
    lats = list(itertools.chain(*lats))
    lons = list(itertools.chain(*lons))
    energy = list(itertools.chain(*energy))
    if data_type == 'event':
        area = None
    else:
        area = list(itertools.chain(*area))

    return {'latitude': np.array(lats),
            'longitude': np.array(lons),
            'area': np.array(area),
            'energy': np.array(energy),
            'DATETIME': GLM['Range']}

def accumulate_GLM(GLM, data_type='flash', verbose=True, in_HRRR_domain=False):
    """
    Accumulate all the GLM 'flash' data that occurred within the 5-minute
    scan window for an ABI file and return the latitude, longitude, and energy
    of all the flashes.

    Input:
        GLM       - A list of GLM file paths and names returned by 
                    get_GLM_files_for_range() or get_GLM_files_for_ABI().
        data_type - Data to retrieve. Default is 'flash' data. Other options 
                    are 'event' and 'group' which have messed up latitude and
                    longitude, so don't use them unless you figure them out.
    
    Output:
        A dictionary containing the latitudes, longitudes, and energy of each
        flash (or event or group).
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
    area = np.array([])

    # Read the data
    for i, FILE in enumerate(GLM['Files']):
        G = xarray.open_dataset(FILE)
        lats = np.append(lats, G.variables[data_type+'_lat'].data)
        lons = np.append(lons, G.variables[data_type+'_lon'].data)
        energy = np.append(energy, G.variables[data_type+'_energy'].data)
        area = np.append(energy, G.variables[data_type+'_area'].data)
        G.close()
        if verbose:
            DATE = datetime.strptime(FILE.split('_')[3], 's%Y%j%H%M%S%f')
            sys.stdout.write('\r%.1f%% Complete (%s of %s) : %s' % (i/len(GLM['Files'])*100, i, len(GLM['Files']), DATE))

    # Filter results if not in HRRR domain
    if in_HRRR_domain:
        # HRRR max/min latitude and longitude were determined previously
        # 21.138, 52.61565, -134.09613, -60.91784
        
        # Filter for locations within the HRRR domain
        index_bound_lat = np.logical_and(lats > 21.138, lats < 52.61565)
        index_bound_lon = np.logical_and(lons > -134.09613, lons < -60.91784)
        bound = np.logical_and(index_bound_lat, index_bound_lon)

        lats = lats[bound]
        lons = lons[bound]
        energy = energy[bound]
        area = area[bound]

    return {'latitude': lats,
            'longitude': lons,
            'energy': energy,
            'area': area,
            'DATETIME': GLM['Range']}



def GLM_xarray_concatenate(FILES, data_type='flash', verbose=True):
    """
    ** This function isn't as fast as accumulate_GLM, but it returns the output
    ** in xarray format.

    Return GLM data from multiple files as a concatenated xarray dataframe.
    I wonder what the limit of number of open files is? Depends on available 
    memory.

    Input:
        FILES     - A list of file paths and names for each GLM file
        data_type - 'flash', 'group', or 'event' 
    """
    # Open all the files for the ABI scan and store in a dictionary
    for i, f in enumerate(FILES):
        with xarray.open_dataset(f) as G:
            if i == 0:
                lon = G.flash_lon
                lat = G.flash_lat
                energy = G.flash_energy
                area = G.flash_area
            else:
                lon = xarray.concat([lon, G.flash_lon], dim='number_of_flashes')
                lat = xarray.concat([lat, G.flash_lat], dim='number_of_flashes')
                energy = xarray.concat([energy, G.flash_energy], dim='number_of_flashes')
                area = xarray.concat([area, G.flash_area], dim='number_of_flashes')
            
            if verbose:
                num = len(FILES)
                sys.stdout.write('\r%.1f%% Complete (%s of %s)' % (i/num*100, i, num))
    # Other Variables:
    #flash_id = xarray.concat([dd[i].flash_id for i in dd.keys()], dim='number_of_flashes')
    #flash_quality_flag = xarray.concat([dd[i].flash_quality_flag for i in dd.keys()], dim='number_of_flashes')
    #flash_time_offset_of_first_event = xarray.concat([dd[i].flash_time_offset_of_first_event for i in dd.keys()], dim='number_of_flashes')
    #flash_time_offset_of_last_event = xarray.concat([dd[i].flash_time_offset_of_last_event for i in dd.keys()], dim='number_of_flashes')
    #group_parent_flash_id = xarray.concat([dd[i].group_parent_flash_id for i in dd.keys()], dim='number_of_groups')

    # Return the values
    return {'longitude': lon,
            'latitude': lat,
            'area': area,
            'energy': energy
            }

#==============================================================================
#==============================================================================
#==============================================================================

def filter_by_path(glm):
    
    """
    Inputs:
        glm    - the object returned by accumulate_GLM
    """
    from matplotlib.path import Path
    from BB_HRRR.HRRR_Pando import get_hrrr_latlon
    
    # Get HRRR latitude and longitude grids
    Hlat, Hlon = get_hrrr_latlon(DICT=False)

    # =============================================================================
    print('Make domain paths...')
    ## Create Path boundaries of HRRR domain and subdomains of interest:
    # HRRR: All points counter-clockwise around the model domain.
    # West, Central, East: A 16 degree wide and 26 degree tall boundary region.
    PATH_points = {
        'HRRR':
            {'lon': np.concatenate([Hlon[0], Hlon[:,-1], Hlon[-1][::-1], Hlon[:,0][::-1]]),
            'lat': np.concatenate([Hlat[0], Hlat[:,-1], Hlat[-1][::-1], Hlat[:,0][::-1]])},
        'West':{
            'lon':[-120, -104, -104, -120, -120],
            'lat':[24.4, 24.4, 50.2, 50.2, 24.2]},
        'Central':{
            'lon':[-104, -88, -88, -104, -104],
            'lat':[24.4, 24.4, 50.2, 50.2, 24.2]},
        'East':{
            'lon':[-88, -72, -72, -88, -88],
            'lat':[24.4, 24.4, 50.2, 50.2, 24.2]},
        'Utah':{
            'lon':[-114.041664, -111.047526, -111.045645,  -109.051460, -109.048632, -114.051534, -114.041664],
            'lat':[41.993580, 42.002846, 40.998538, 40.998403, 36.998310, 37.000574, 41.993580]}
    }
    ## Combine lat/lon as vertice pair as a tuple. i.e. (lon, lat).
    PATH_verts = {}
    for i in PATH_points.keys():
        PATH_verts[i] = np.array([(PATH_points[i]['lon'][j], PATH_points[i]['lat'][j]) for j in range(len(PATH_points[i]['lon']))])

    ## Generate Path objects from the vertices.
    PATHS = {}
    for i in PATH_verts.keys():
        PATHS[i] = Path(PATH_verts[i])

    ## Filter GLM observation within the HRRR domain. -------------------------
    #--------------------------------------------------------------------------
    # The GLM observes flashes for the disk in its field of view. We only want
    # the flashes within the HRRR domain. This is tricky. We can't just use
    # lat/lon bounds, because the projection of the HRRR model *bends* the
    # lat/lon and we would overshoot corners. 
    # Instead, we will use the Paths created at the begining of the script and
    # determine which GLM points are inside each Path.Patch.
    
    # Total number of GLM observations
    print("Total GLM observations:", len(glm['latitude']))
    
    # Generate a lat/lon tuple for each point
    print('generate lat/lon pair...')
    GLM_latlon_pair = list(zip(glm['longitude'], glm['latitude']))
    print('...done')

    # Return a None if the legnth of GLM_latlon_pairs is zero, because there
    # are no flashes.    
    if len(GLM_latlon_pair) == 0:
        print('!!! Warning !!! DATE %s had no lightning data' % DATE)
        # Return: hit_rate, number of flashes, number of files, numb of expected files
        return None

    ## Determine which GLM observation points, from a lat/lon tuple, are in
    # each boundary Path.
    # !! Refer to the Paths generated at the begining of the script!!
    
    # Using each Path in PATHS, determine which GLM points fall inside the Path
    print('Find which points are inside path')
    print('')
    inside_path = {}
    for i in PATHS.keys(): 
        inside_path[i] = PATHS[i].contains_points(GLM_latlon_pair)
    print('...done!')

    ## Filter the GLM data keys by the bounding Path (points inside Path):
    filtered_glm = {'DATETIME':glm['DATETIME']}
    for i in inside_path.keys():
        if np.size(glm['area']) == 1:
            filtered_glm[i] = {
                'latitude': glm['latitude'][inside_path[i]],
                'longitude': glm['longitude'][inside_path[i]],
                'energy': glm['energy'][inside_path[i]],
                'area': None
            }
        else:
            filtered_glm[i] = {
                'latitude': glm['latitude'][inside_path[i]],
                'longitude': glm['longitude'][inside_path[i]],
                'energy': glm['energy'][inside_path[i]],
                'area': glm['area'][inside_path[i]]
            }
    return filtered_glm


def filter_by_HRRR(lats, lons, Hlat, Hlon, m=False):
    """
    Take a set of points and return a boolean of which points are inside
    the HRRR domain. Typically used to filter GLM flashes, groups, or events
    that are inside the HRRR domain.
    NOTE: Converting the lat/lon points to the HRRR's lambert-conformal 
          map coordinates is incredibly faster than looping though each point
          with the `contains_points` path method to check if it exists.
          This faster method is possible because the HRRR grid is regular and 
          in a box. If the path is irregular, we would have to use the
          `contains_points` method.

    Input:
        lats - a vector of latitudes
        lons - a vector of longitudes
        Hlat - HRRR gridded latitudes from `get_hrrr_latlon(DICT=False)`
        Hlon - HRRR gridded longitudes from `get_hrrr_latlon(DICT=False)`
        m    - the HRRR domain basemap object from `draw_HRRR_map()`
    """  
    # Convert HRRR lat/lon points to map coordinates
    X, Y = m(Hlon, Hlat)

    # Convert input points to map coordinates
    glm_X, glm_Y = m(lons, lats)

    # Determine which are inside 
    filtered = np.logical_and.reduce((glm_X > X.min(), glm_X < X.max(),
                                      glm_Y > Y.min(), glm_Y < Y.max()))
    return filtered


def bin_GLM_on_HRRR_grid(glm, Hlat, Hlon, m):
    """
    Return a grid of flash counts on the HRRR grid.

    This step requires us to put the GLM event data in the HRRR map coordinates
    because the HRRR lat/lon grid is irregularly spaced in lat/lon units. But,
    if we use the lambert-conformal map coordinates (the projection of the HRRR
    output), the grid spacing is equal. With the regular grid, in map
    coordinates, we can bin the GLM data as a 2D histogram.
    NOTE: We cannot do this with the lat/lon grid because `np.histogram2d` 
          requires 1D vectors in the x and y direction to specify the bins, and
          the lat/lon grid is not uniform. The map coordinates, however, are
          uniform (almost).

    Inputs: 
        glm  - dictionary returned from accumulate_glm().
        Hlat - HRRR latitude grid
        Hlon - HRRR longitude grid
        m    - basemap map object of HRRR grid returned by draw_HRRR_map
    
    Return:
        hist     - the 2D histogram binned on HRRR grid
        filtered - the boolean array of which of the points are inside the 
                   HRRR domain.
    """

    # Get the boolean of GLM points that are within the HRRR domain
    filtered = filter_by_HRRR(glm['latitude'], glm['longitude'], Hlat, Hlon, m)

    # Convert GLM points and HRRR latitude/longitude grid to the HRRR's
    # lambert-conformal map coordinates.
    glm_X, glm_Y = m(glm['longitude'][filtered], glm['latitude'][filtered])
    X, Y = m(Hlon, Hlat)

    # My working in the HRRR's map grid coordinates rather than latitude/longitude
    # coordinates, the grid spacing is approximately linear and we can generate
    # a 2D histogram with evenly spaced bins. Bin measurements are based on the
    # middle row and middle column of the HRRR grid. 
    mid_row_idx, mid_col_idx =  np.array(np.shape(Hlon))//2

    # Bins in the x and y directions are derived from the model's middle row.
    # To make the size of the 2D histogram to have the same number HRRR grid
    # points, we need one extra bin. Add an extra bin value at the end.
    xbins = X[mid_row_idx]
    xbins = np.append(xbins, xbins[-1]+np.mean(np.diff(xbins)))

    ybins = Y[:, mid_col_idx]
    ybins = np.append(ybins, ybins[-1]+np.mean(np.diff(ybins)))

    ## Generate the 2D histogram
    hist, xedges, yedges = np.histogram2d(glm_X, glm_Y, bins=(xbins, ybins))
    
    # The histogram needs to be transposed to be same as HRRR. Also, mask
    # the zero counts.
    hist = np.transpose(hist)
    hist = np.ma.array(hist, mask=hist==0)

    return (hist, filtered)



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
