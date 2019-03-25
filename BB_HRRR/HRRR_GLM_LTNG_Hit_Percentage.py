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


def points_inside_contours_MP(inputs):
    """
    Each processor works on a single forecast lead time and does the following:
        1) Number of GLM flashes that occur inside a HRRR LTNG forecast.
        2) Total area of HRRR LTNG forecasted area.
        3) Area of LTNG forecasted area with at least one GLM flash.

    Input: [GLM_HRRR_dict, this_fxx, level]
    
    Return: Dictionary of the HRRR/GLM statistics for this processor's FXX.
        'flash inside'    - A boolean of GLM flashes that exist inside HRRR
                            forecasted LTNG contours
        'area total'      - Total area, in km^2, of HRRR forecasted LTNG area.
        'area with flash' - HRRR forecasted LTNG area that had a flash.
    """
    GLM_HRRR_dict, this_fxx, level = inputs
    this_fxx_idx = this_fxx[0]
    this_fxx_value = this_fxx[1]
    #
    fxx_stats = {}
    #
    for i in GLM_HRRR_dict.keys():
        # Get the CONTOUR for this domain and forecast lead time.
        CONTOUR = GLM_HRRR_dict[i]['CONTOURS'][this_fxx_idx]
        
        
        # Total Number of GLM Flashes
        num_flashes = len(GLM_HRRR_dict[i]['latitude'])

        # Initialize a dictionary to store statistics for this forecast grid.
        #     flashes inside  : An array indicating which GLM flashes occur 
        #                       inside a HRRR forecasted area. Initialized as zeros
        #                       with length of number of GLM flashes.
        #     area total      : Total area of HRRR forecasted LTNG (accumulates over loop)
        #     area with flash : Total area of HRRR LTNG contours that contain a GLM flash.
        #                       (accumulates over loop).    
        fxx_stats[i] = {'flash inside': np.zeros(num_flashes),
                        'area total': 0,
                        'area with flash': 0}
        #
        if num_flashes == 0:
            # If there are no GLM flashes inside the Path domain, then return
            # None to indicate that there were no flashes. We use this later to
            # indicate a hit-rate of np.nan.
            fxx_stats[i]['flash inside'] = None
            # Return the total contoured LTNG area.
            for j, V in enumerate(CONTOUR.collections[level].get_paths()):
                obj = {'type':'Polygon','coordinates':[[tuple(i) for i in V.vertices]]}
                json_area = geojson_area(obj)/1e6 # Units: square kilometers
                # Add area to area_total and area_w_flash
                fxx_stats[i]['area total'] += json_area
        #
        else:
            # Combine the GLM lat/lon points into a tuple pair
            latlon_pair = list(zip(GLM_HRRR_dict[i]['longitude'], GLM_HRRR_dict[i]['latitude']))
            #
            # Each collection may have many paths--a path for each contour area.
            # We need to loop through each area and find out which GLM flashes
            # lie inside the area.
            # If a flash is inside the contour area, then add the area of that
            # contour to 'area with flash'.
            
            # Number of individual contours. V is the contour.
            num = len(CONTOUR.collections[level].get_paths())
            for j, V in enumerate(CONTOUR.collections[level].get_paths()):
                # 1) Determine which flashes are inside each contour
                is_inside = V.contains_points(latlon_pair)
                fxx_stats[i]['flash inside'] += is_inside
                #
                # 2) Was there any flash in this contoured area?
                any_flash = np.sum(is_inside) > 0
                #
                # 3) Compute area of the contour
                obj = {'type':'Polygon','coordinates':[[tuple(i) for i in V.vertices]]}
                json_area = geojson_area(obj)/1e6 # Units: square kilometers
                #
                # Add the contour area to 'area total'
                fxx_stats[i]['area total'] += json_area
                # Add the contour area to 'area with flash' if there was a flash in it
                if any_flash:
                    fxx_stats[i]['area with flash'] += json_area
                #
                sys.stdout.write('\r-->>  %s (F%02d): %.1f%% Complete (%s of %s contour areas)' % (i, this_fxx_value, (j+1)/num*100, (j+1), num))
                #
            # Convert the 'flash inside' array from a count to a boolean.
            # This boolean matches the lat/lon points in the same order.
            fxx_stats[i]['flash inside'] = np.array(fxx_stats[i]['flash inside'], dtype=bool)
            #
    return fxx_stats


def points_inside_contours(GLM_HRRR_dict, fxx, level=0):
    """
    Determine which points are inside a set of collections.
    Use a different CPU for each item in COLLECTIONS (i.e. there is a
    collection for each forecast lead time; f00-f18)

    Input:
        GLM_HRRR_dict - Dictionary where each key is a domain path.
                        Each domain contains the following key:
                            latitude  - GLM flash latitude
                            longitude - GLM flash longitude
                            energy    - GLM flash energy
                            area      - GLM flash area
                            FXX       - Forecasts lead time (usually F00-F18)
                            CONTOURS  - List of HRRR LTNG forecast plt.contour
                                        objects for each lead time as a
                                        matplotlib.contour.QuadContourSet
        fxx           - List of forecast lead times.
        level         - Contour level index. Usually set to 0 for first contour
                        level. If contour object had multiple levels, you could
                        target those by adjusting this variable.

    Return:
        GLM_HRRR_dict - Same as input, except with the new 'HRRR LTNG' key
                        which contains the following for each fxx:
                            Flash Inside   - T/F flash inside HRRR contour.
                            Hit Rate       - Percentage of GLM flashes inside HRRR contour
                            False Alarm    - Percentage of HRRR contour area without a GLM flash
                            Total Area km2 - Total HRRR contour area
    """
    timer = datetime.now()
    # Each processor will work on a separate forecast lead time. Pass every 
    # processor the entire GLM_HRRR_dict, but tell it which forecast hour to 
    # work (this_fxx).
    
    # [GLM Path Dictionary, (idx, Forecast hour to work on), level]
    inputs = [[GLM_HRRR_dict, (i, this_fxx), level] for i, this_fxx in enumerate(fxx)]

    cores = np.minimum(multiprocessing.cpu_count(), len(inputs))
    with multiprocessing.Pool(cores) as p:
        FXX_stats_dicts = np.array(p.map(points_inside_contours_MP, inputs))
        p.close()
        p.join()
    print('\nTimer -- points_inside_contours(): ', datetime.now()-timer)
    
    ## Need to unpack the returned dictionaries.
    # FXX_stats_dicts should be as long as there are forecasts lead time.
    # Unpack the boolean for each forecast hour and put into GLM_HRRR_dict.

    ## Need to unpack the returned dictionaries.
    # in_LTNG_dicts should be as long as there are forecasts lead time; len(fxx) == len(in_LTNG_dicts)
    # Unpack the boolean for each forecast hour and put into the paths_glm dictionary.
    # For each forecast lead time, in_LTNG_Fxx:
    #   'Flash Inside'   - A boolean indicating which GLM flashes are inside the HRRR forecasted LTNG contours. 
    #   'Hit Rate'       - Percentage of GLM flashes that occurred inside a HRRR forecasted LTNG.
    #   'False Alarm'    - Percentage of HRRR forecasted LTNG contoured area that did not receive a GLM flash.
    #   'Total Area km2' - Total area of forecasted LTNG contours in the domain, in km^2.

    # Initialize storage array for each path domain
    for i in GLM_HRRR_dict.keys():
        GLM_HRRR_dict[i]['HRRR LTNG'] = {'Flash Inside': [],
                                         'Hit Rate': [],
                                         'False Alarm': [],
                                         'Total Area km2': []}
    #
    for i, this_dict in enumerate(FXX_stats_dicts):
        for d in this_dict.keys():
            flash_boolean = FXX_stats_dicts[i][d]['flash inside']
            area_total = FXX_stats_dicts[i][d]['area total']
            area_w_flash = FXX_stats_dicts[i][d]['area with flash']
            if area_total != 0:
                false_alarm = (area_total - area_w_flash)/area_total
            else:
                # If area_total == 0, then the area of the LTNG forecast area
                # is zero, and there were no false alarms.
                false_alarm = 0
            if flash_boolean is None:
                # If the returned boolean is None, then there were no GLM flashes for that domain
                # and the hit_rate can not be determined because the total forecastes flashes
                # is also zero.
                # e.g. Zero total flashes: (a) = 0 flashes inside contour,
                #                          (c) = 0 flashes outside contour,
                #                          Thus, a/(a+c) = 0/0 = undefined
                hit_rate = np.nan
            else:
                # Number of GLM flashes that were inside a HRRR forecasted LTNG contour/ total flashes
                # e.g. Ten total flashes: (a) = 8 flashes inside contour,
                #                         (c) = 2 flashes outside contour,
                #                         Thus, a/(a+c) = 8/10 = .8 = 80% hit rate.
                hit_rate = sum(flash_boolean)/len(flash_boolean)
            #
            # Package up the statistics nicely
            GLM_HRRR_dict[d]['HRRR LTNG']['Flash Inside'].append(flash_boolean)
            GLM_HRRR_dict[d]['HRRR LTNG']['Hit Rate'].append(hit_rate)
            GLM_HRRR_dict[d]['HRRR LTNG']['False Alarm'].append(false_alarm)
            GLM_HRRR_dict[d]['HRRR LTNG']['Total Area km2'].append(area_total)

    return GLM_HRRR_dict


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
    
    # Return None if there are no GLM files retrieved. 
    if glm is None:
        print('!!! Warning !!! DATE %s had no lightning data' % DATE)
        # Return None and this indicates that there are no GLM flashes.
        return None, (files['Number'], files['Number Expected'])    

    ## Get HRRR data-----------------------------------------------------------
    #--------------------------------------------------------------------------
    timer=datetime.now()
    # HRRR Lightning Threat Forecasts (Analysis field is empty for lightning
    # threat). Units: maximum flashes per km2 per 5min for previous hour.
    # Remember: HH is a masked array for LTNG and REFC.
    HH = get_hrrr_all_valid(DATE, 'LTNG:entire', fxx=fxx)
    print('\n HRRR Download Timer:', datetime.now()-timer)   


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
    GLM_latlon_pair = [(glm['longitude'][i], glm['latitude'][i]) for i in range(len(glm['latitude']))]
    
    # Return a None if the legnth of GLM_latlon_pairs is zero, because there
    # are no flashes.    
    if len(GLM_latlon_pair) == 0:
        print('!!! Warning !!! DATE %s had no lightning data' % DATE)
        # Return: hit_rate, number of flashes, number of files, numb of expected files
        return None, (files['Number'], files['Number Expected'])

    ## Determine which GLM observation points, from a lat/lon tuple, are in
    # each boundary Path.
    # !! Refer to the Paths generated at the begining of the script!!
    
    # Using each Path in PATHS, determine which GLM points fall inside the Path
    inside_path = {}
    for i in PATHS.keys(): 
        inside_path[i] = PATHS[i].contains_points(GLM_latlon_pair)
        
    ## Filter the GLM data keys by the bounding Path (points inside Path):
    filtered_glm = {}
    for i in inside_path.keys():
        filtered_glm[i] = {
            'latitude': glm['latitude'][inside_path[i]],
            'longitude': glm['longitude'][inside_path[i]],
            'energy': glm['energy'][inside_path[i]],
            'area': glm['area'][inside_path[i]]
        }
    
    ## Print number of observations within each boundary Path.
    print("----------------------------------------------")
    print("GLM Observations in each region:")
    for i in filtered_glm.keys():
        num = len(filtered_glm[i]['latitude'])
        print("    %s\t:\t%s" % (i, '{:,}'.format(num)))
    print("----------------------------------------------")

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
    HRRR_GLM_info = points_inside_contours(filtered_glm, fxx)
    print('\n!!! Timer: count GLM flashes inside HRRR contours:', datetime.now()-timer)

    return HRRR_GLM_info, (files['Number'], files['Number Expected'])
    

if __name__ == '__main__':
    
    DATE = datetime(2018, 5, 14, 22) # Mallard Fire
    #DATE = datetime(2018, 6, 13, 0) # Missing data
    
    a, (files, expected) = get_HRRR_LTNG_hit_rate(DATE)
    
   
    timerStart = datetime.now()
    
    # =========================================================================
    '''
    ## Single Date and Figure
    #DATE = datetime(2018, 5, 14, 22) # Mallard Fire
    #DATE = datetime(2018, 7, 5, 23) # Lake Christine
    DATE = datetime(2018, 7, 17, 6) # July Storm
    #DATE = datetime(2018, 7, 27, 0) # Missing GLM data

    a, (files, expected) = get_HRRR_LTNG_hit_rate(DATE)

    FXX = 1
    Hltng = get_hrrr_variable(DATE-timedelta(hours=FXX), 'LTNG:entire', fxx=FXX)

    plt.figure(figsize=[15,10])
    for i in ['HRRR', 'West', 'Central', 'East', 'Utah']:
        m.scatter(a[i]['longitude'], a[i]['latitude'],
                latlon=True, label='%s: %.1f%%' % (i, a[i]['in_LTNG_F%02d' % FXX]['hit rate']*100))

    m.scatter(a['HRRR']['longitude'][a['HRRR']['in_LTNG_F%02d' % FXX]['boolean']],
            a['HRRR']['latitude'][a['HRRR']['in_LTNG_F%02d' % FXX]['boolean']],
                latlon=True, s=1, color='k', label='inside HRRR LTNG')

    m.contour(Hlon, Hlat, Hltng['value'].data, levels=[0], colors='maroon', latlon=True, linewidths=.75)

    plt.legend()
    m.drawstates(); m.drawcoastlines(); m.drawcountries()
    m.drawmeridians(np.array([-104-16, -104, -104+16, -104+16+16]), labels=[1,1,0,1], fontsize=10, linewidth=2)
    m.drawparallels(np.array([24.4, 50.2]), labels=[1,1,1,1], fontsize=10, linewidth=2)
    plt.title('%s -- F%02d' % (DATE, FXX))
    #plt.savefig('HRRR_GLM_hit-rate_demo_%s' % DATE.strftime('%Y%m%d-%H%M))
    '''

    # =========================================================================
 
    if False:
        #months = [5, 6, 7, 8, 9, 10]

        year = 2018
        months = [12]
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


        SAVEDIR = './HRRR_GLM_hit_rate_data/'
        if not os.path.exists(SAVEDIR):
            os.makedirs(SAVEDIR)

        for h in hours:
            for m in months:
                print('\n')
                print('=========================================================')
                print('=========================================================')
                print('           WORKING ON MONTH %s and HOUR %s' % (m, h))
                print('=========================================================')
                print('=========================================================')

                # Loop over many dates and write output to a file (
                # new file each month.
                sDATE = datetime(year, m, 1, h)
                if m==12:
                    eDATE = datetime(year+1, 1, 1, h)
                else:
                    eDATE = datetime(year, m+1, 1, h)
                    
                days = int((eDATE-sDATE).days)
                DATES = [sDATE+timedelta(days=d) for d in range(days)]
                
                #
                for DATE in DATES:
                    if DATE == sDATE:
                        # Create Header and  initial new file for each domain
                        fxx_hit_head = ','.join(['F%02d_Hit_Rate' % i for i in range(19)])
                        fxx_false_head = ','.join(['F%02d_False_Alarm' % i for i in range(19)])
                        fxx_area_head = ','.join(['F%02d_Total_Area_km2' % i for i in range(19)])
                        HEADER = 'DATE,GLM FLASH COUNT,NUM FILES,EXPECTED FILES,'+fxx_hit_head+','+fxx_false_head+','+fxx_area_head
                        for d in PATH_points.keys():
                            SAVEFILE = SAVEDIR+"GLM_in_HRRR_%s_%s.csv" % (d, sDATE.strftime('%Y_m%m_h%H')) 
                            with open(SAVEFILE, "w") as f:
                                f.write('%s\n' % HEADER)

                    # Get Hit Rate Data for each domain Path
                    a, (files, expected) = get_HRRR_LTNG_hit_rate(DATE)
                    

                    for d in PATHS.keys():
                        # Write the following
                        # 1 date,
                        # 2 total flashes,
                        # 3 num files,
                        # 4 expected files,
                        # 5 hit rate f00, ..., f18
                        # 6 false alarm rate f00, ..., f18
                        # 7 total area f00, ..., f18
                        if a is None:
                            fxx_hits_str = ','.join(np.array(np.ones_like(range(19))*np.nan, dtype=str))
                            fxx_false_str = ','.join(np.array(np.ones_like(range(19))*np.nan, dtype=str))
                            fxx_area_str = ','.join(np.array(np.ones_like(range(19))*np.nan, dtype=str))
                            line = "%s,%s,%s,%s,%s,%s,%s" % (DATE, 
                                                             np.nan,        # because there are no flashes
                                                             files,         # should be zero
                                                             expected,      # 180
                                                             fxx_hits_str,  # nan, because no GLM data
                                                             fxx_false_str, # nan, because no GLM data
                                                             fxx_area_str)  # nan, to indicate there we no GLM data
                        else:
                            fxx_hits = np.round(a[d]['HRRR LTNG']['Hit Rate'], 4)
                            fxx_false = np.round(a[d]['HRRR LTNG']['False Alarm'], 4)
                            fxx_area = np.round(a[d]['HRRR LTNG']['Total Area km2'], 6)
                            fxx_hits_str = ','.join(np.array(fxx_hits, dtype=str))
                            fxx_false_str = ','.join(np.array(fxx_false, dtype=str))
                            fxx_area_str = ','.join(np.array(fxx_area, dtype=str))

                            line = "%s,%s,%s,%s,%s,%s,%s" % (DATE, 
                                                            len(a[d]['latitude']),
                                                            files,
                                                            expected,
                                                            fxx_hits_str,
                                                            fxx_false_str,
                                                            fxx_area_str)
                        SAVEFILE = SAVEDIR+"GLM_in_HRRR_%s_%s.csv" % (d, sDATE.strftime('%Y_m%m_h%H')) 
                        with open(SAVEFILE, "a") as f:
                            f.write('%s\n' % line)
                        print('Wrote to', SAVEFILE)


    """
    In output:
        - If "GLM FLASH COUNT" is nan, then there were either no GLM files obtained
        for that hour, or there were files, but no observed GLM flashes.
        - If "FXX" is nan, then there were no observed GLM flashes in that domain
    """

