# Brian Blaylock
# February 6, 2019      It snowed enough to close campus this morning.

"""
Count the number of GLM flashes inside a HRRR forecasted area of lightning
threat.

1) Get HRRR forecasts for a valid time.
2) Use matplotlib.pyplot.contour to draw patches of lightning threat
   greater than 0.
3) Get GLM flashes for the hour previous to the valid time.
4) Count the number of flashes that reside inside the contour.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
from datetime import datetime, timedelta
import multiprocessing
import os

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3/')
from BB_HRRR.HRRR_Pando import get_hrrr_latlon, get_hrrr_all_valid, get_hrrr_variable
from BB_maps.my_basemap import draw_HRRR_map, draw_CONUS_cyl_map
from BB_GOES.get_GLM import get_GLM_file_nearesttime, accumulate_GLM_FAST
from geojson_area.area import area as geojson_area

import matplotlib as mpl
mpl.rcParams['figure.figsize'] = [15,15]
mpl.rcParams['figure.titlesize'] = 15
mpl.rcParams['figure.titleweight'] = 'bold'
mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 10
mpl.rcParams['axes.labelsize'] = 12
mpl.rcParams['axes.titlesize'] = 15
mpl.rcParams['lines.linewidth'] = 1.8
mpl.rcParams['grid.linewidth'] = .25
mpl.rcParams['figure.subplot.wspace'] = 0.05
mpl.rcParams['figure.subplot.hspace'] = 0.05
mpl.rcParams['legend.fontsize'] = 10
mpl.rcParams['legend.framealpha'] = .75
mpl.rcParams['legend.loc'] = 'best'
mpl.rcParams['savefig.bbox'] = 'tight'
mpl.rcParams['savefig.dpi'] = 100

# Get HRRR latitude and longitude grids
Hlat, Hlon = get_hrrr_latlon(DICT=False)

# =============================================================================
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

print('                    ...Done')

# =============================================================================
# =============================================================================


def get_HRRR_LTNG_hit_rate(DATE, fxx=range(19), contour=0):
    '''
    Return the HRRR's hit rate for lightning forecasts from the GLM flash data.

    Input:
        DATE    - The valid time requested
        fxx     - A list of the forecast hour lead times. Default is f00-f18.
        contour - The plt.contour level interval. Default is 0 indicating
                  that we are looking for where LTNG > 0.

    Return:
        paths_glm - a dictionary of GLM flashes and if it is inside the
                    HRRR forecast
        files     - A tuple: (number of GLM files, number of expected GLM files)
    '''
    #
    ## Get GLM data------------------------------------------------------------
    #--------------------------------------------------------------------------
    # Since the HRRR lightning product is for the previous hour, we need to 
    # get the GLM flashes that occurred during that hour. This function will
    # grab the GLM file nearest the (DATE - 30 minutes) and all files +/- 30
    # minutes, i.e. all GLM files for the hour before the DATE.
    # If there isn't any GLM files for the hour period, then return nans.
    timer=datetime.now()
    files = get_GLM_file_nearesttime(DATE-timedelta(minutes=30), window=30, verbose=True)
    glm = accumulate_GLM_FAST(files)
    print('\n GLM Download Timer:', datetime.now()-timer)
    #
    # Return None if there are no GLM files retrieved. 
    if glm is None:
        print('!!! Warning !!! DATE %s had no lightning data' % DATE)
        # Return None and this indicates that there are no GLM flashes.
        return None, (files['Number'], files['Number Expected'])    
    #
    ## Get HRRR data-----------------------------------------------------------
    #--------------------------------------------------------------------------
    timer=datetime.now()
    # HRRR Lightning Threat Forecasts (Analysis field is empty for lightning
    # threat). Units: maximum flashes per km2 per 5min for previous hour.
    # Remember: HH is a masked array for LTNG and REFC.
    ###########HH = get_hrrr_all_valid(DATE, 'LTNG:entire', fxx=fxx)
    print('\n HRRR Download Timer:', datetime.now()-timer)   
    #
    #
    ## Filter GLM observation within the HRRR domain. -------------------------
    #--------------------------------------------------------------------------
    # The GLM observes flashes for the disk in its field of view. We only want
    # the flashes within the HRRR domain. This is tricky. We can't just use
    # lat/lon bounds, because the projection of the HRRR model *bends* the
    # lat/lon and we would overshoot corners. 
    # Instead, we will use the Paths created at the begining of the script and
    # determine which GLM points are inside each Path.Patch.
    #
    # Total number of GLM observations
    print("Total GLM observations:", len(glm['latitude']))
    #
    # Generate a lat/lon tuple for each point
    GLM_latlon_pair = [(glm['longitude'][i], glm['latitude'][i]) for i in range(len(glm['latitude']))]
    #
    # Return a None if the legnth of GLM_latlon_pairs is zero, because there
    # are no flashes.    
    if len(GLM_latlon_pair) == 0:
        print('!!! Warning !!! DATE %s had no lightning data' % DATE)
        # Return: hit_rate, number of flashes, number of files, numb of expected files
        return None, (files['Number'], files['Number Expected'])
    #
    ## Determine which GLM observation points, from a lat/lon tuple, are in
    # each boundary Path.
    # !! Refer to the Paths generated at the begining of the script!!
    #
    # Using each Path in PATHS, determine which GLM points fall inside the Path
    inside_path = {}
    for i in PATHS.keys(): 
        inside_path[i] = PATHS[i].contains_points(GLM_latlon_pair)
    #    
    ## Filter the GLM data keys by the bounding Path (points inside Path):
    filtered_glm = {}
    for i in inside_path.keys():
        filtered_glm[i] = {
            'latitude': glm['latitude'][inside_path[i]],
            'longitude': glm['longitude'][inside_path[i]],
            'energy': glm['energy'][inside_path[i]],
            'area': glm['area'][inside_path[i]]
        }
    #
    ## Print number of observations within each boundary Path.
    print("----------------------------------------------")
    print("GLM Observations in each region:")
    for i in filtered_glm.keys():
        num = len(filtered_glm[i]['latitude'])
        print("    %s\t:\t%s" % (i, '{:,}'.format(num)))
    print("----------------------------------------------")
    #
    #--------------------------------------------------------------------------
    ## Create Contour Collections Objects For Each Path -----------------------
    #--------------------------------------------------------------------------
    # We can matplotlib.pyplot.contour() to generate Paths for each contour
    # area for every forecast lead time requested. These paths are used to
    # determine if a GLM flash occurred within the HRRR forecasted lightning
    # threat area.
    # NOTE: Just make contours from un-projected grid (vertices are lat/lon).
    # NOTE: Use H.data to access the unmasked array for correct contouring.
    # NOTE: Set levels=[0] to draw contours where lightning threat >0.
    print("-->> Make Contours for each path...")
    # Add to the filtered_glm dictionary the contour objects for each path domain.
    # There will be one contour object for each requested forecast hour fxx.
    #
    '''
    for i in PATHS.keys():       
        filtered_glm[i]['CONTOURS'] = []
        if i == 'HRRR':
            # Generate contour for full grid if the path is the HRRR domain.
            for j, H in enumerate(HH):
                c = plt.contour(Hlon, Hlat, H.data, levels=[contour])
                filtered_glm[i]['CONTOURS'].append(c)
        else:
            # Need to mask data that is not within the specified domian.
            # Find model grid points that are not inside the ith domain path object.
            in_path = PATHS[i].contains_points(list(zip(Hlon.flatten(), Hlat.flatten())))
            not_in_path = np.invert(in_path)
            # Reshape points not_in_path boolean to array with shape of HRRR grid.
            not_in_path = not_in_path.reshape(np.shape(Hlat))
            for j, H in enumerate(HH):
                # Get a copy of the gridded forecast data and set all points
                # not in path to zero.
                if type(H) == np.ma.core.MaskedArray:
                    # LTNG is a returned as a masked array, but we need to make
                    # the contours from the raw data.
                    subDOMAIN = H.data.copy()
                else:
                    subDOMAIN = H.copy()
                subDOMAIN[not_in_path] = 0
                # Generate contour objects for each requested forecast hour based
                # on LTNG data inside the path.
                c = plt.contour(Hlon, Hlat, subDOMAIN, levels=[contour])
                filtered_glm[i]['CONTOURS'].append(c)
        plt.close()
        print('Created Contours for %s' % i)
    print('...done!\n')
    '''
    #
    #--------------------------------------------------------------------------
    ## Determine which GLM flashes occurred in a HRRR contour -----------------
    #--------------------------------------------------------------------------
    # Ok, the filtered_glm dictionary now includes, for each path domain, a 
    # list of forecast hours, FXX, and a list of contours for each fxx, CONTOURS.
    
    # Uses the function points_inside_contours(), which relies on
    # multiprocessing, to return a list of points that are inside or outside
    # the contours in each path domain. Each processor will work on a separate
    # forecast lead time, fxx.
    timer = datetime.now()
    #HRRR_GLM_info = points_inside_contours(filtered_glm, fxx)
    print('\n!!! Timer: count GLM flashes inside HRRR contours:', datetime.now()-timer)
    #
    return filtered_glm, (files['Number'], files['Number Expected'])


def write_table_to_file(a, files, expected, DATE, write_domains, SAVEDIR, DATE_fmt='%Y-%m-%d %H:%M:%S'):
    """
    """
    for DOMAIN in ['HRRR', 'West', 'Central', 'East', 'Utah']:
        if DOMAIN in write_domains:
            #
            SAVEFILE = SAVEDIR+"GLM_in_HRRR_%s_%s.csv" % (DOMAIN, DATE.strftime('%Y_m%m_h%H')) 
            #
            # Initiate new file with header if the day of the month is 1.
            if DATE.day == 1:
                HEADER = 'DATE,GLM FLASH COUNT,NUM FILES,EXPECTED FILES'
                with open(SAVEFILE, "w") as f:
                    f.write('%s\n' % HEADER)
            #
            if a is None:
                line = "%s,%s,%s,%s" % (DATE, 
                                        np.nan,        # because there are no flashes
                                        files,         # should be zero
                                        expected       # 180
                                       )
            else:
                line = "%s,%s,%s,%s" % (DATE, 
                                        len(a[DOMAIN]['latitude']),
                                        files,
                                        expected
                                        )
            print(line)
            with open(SAVEFILE, "a") as f:
                f.write('%s\n' % line)
            print('Wrote to', SAVEFILE)

def write_to_file(inputs):
    
    year, month, hour = inputs

    sDATE = datetime(year, month, 1, hour)
    if month==12:
        eDATE = datetime(year+1, 1, 1, hour)
    else:
        eDATE = datetime(year, month+1, 1, hour)

    # Maximum date available is "yesterday", and eDATE cannot exceed this date.
    # This should only be the case if you are running statistics for the
    # current month. (example: today is May 24th, so I can't run statistics
    # for May 24-31. Thus, eDATE should be May 23rd.)
    if eDATE > datetime.now():
        maximumDATE = datetime(year, eDATE.month-1, (datetime.utcnow()-timedelta(days=1)).day, hour)
        eDATE = np.minimum(eDATE, maximumDATE)

    #
    print('\n')
    print('=========================================================')
    print('=========================================================')
    print('       WORKING ON MONTH %s and HOUR %s' % (month, hour))
    print('           sDATE: %s' % sDATE.strftime('%H:%M UTC %d %b %Y'))
    print('           eDATE: %s' % eDATE.strftime('%H:%M UTC %d %b %Y'))
    print('=========================================================')
    print('=========================================================')

    #
    ### Check if the file we are working on exists
    #
    SAVEDIR = './HRRR_GLM_hit_rate_data/'
    DOMAINS = ['Utah', 'HRRR', 'West', 'Central', 'East']
    FILES = ["%s/GLM_in_HRRR_%s_%s.csv" % (SAVEDIR, D, sDATE.strftime('%Y_m%m_h%H')) for D in DOMAINS]
    EXISTS = [os.path.exists(i) for i in FILES]

    Next_DATE = []
    for (F, E) in zip(FILES, EXISTS):
        if E:
            list_DATES = np.genfromtxt(F, delimiter=',', names=True, encoding='UTF-8', dtype=None)['DATE']
            if np.shape(list_DATES) == ():
                # I suppose there is only one date in the list
                last = str(list_DATES)
            else:
                # Else, get the last date in the list
                last = list_DATES[-1]
            try:
                Next_DATE.append(datetime.strptime(last, '%Y-%m-%d %H:%M:%S')+timedelta(days=1))
                DATE_fmt = '%Y-%m-%d %H:%M:%S'
            except:
                Next_DATE.append(datetime.strptime(last, '%m/%d/%Y %H:%M')+timedelta(days=1))
                DATE_fmt = '%m/%d/%Y %H:%M'
        #
        else:
            Next_DATE.append(sDATE)
            DATE_fmt = '%Y-%m-%d %H:%M:%S'
    
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
            print('%s, %s\n' % (DOM, [DD for DD in DOM_DD]))
        if len(write_domains) != 0:
            print(write_domains)
            # Get GLM Flashes for each path and save to file
            a, (files, expected) = get_HRRR_LTNG_hit_rate(DATE)
            write_table_to_file(a, files, expected, DATE, write_domains, SAVEDIR, DATE_fmt='%Y-%m-%d %H:%M:%S')
            

    return 'Finished %s' % len(DATES)

if __name__ == '__main__':
    
    # =========================================================================
 
    if True:
        #months = [5, 6, 7, 8, 9, 10]

        year = 2019
        months = [9]
        #months = [datetime.utcnow().month]
        hours = range(24)

        
        import socket
        host = socket.gethostname().split('.')[0]
        '''
        if host == 'wx1':
            hours = [3, 4]
        elif host == 'wx2':
            hours = [7]
        elif host == 'wx3':
            months = [6]
            hours = [4]
        elif host == 'wx4':
            hours = [10, 11]
        elif host == 'meso3':
            hours = [23]
        elif host == 'meso4':
            hours = [11]
        '''
        print('\n     =======================================')
        print('        HOST: %s, HOURS: %s' % (host, hours))
        print('     =======================================\n')


        inputs = [(year, month, hour) for month in months for hour in hours]
        list(map(write_to_file, inputs))
