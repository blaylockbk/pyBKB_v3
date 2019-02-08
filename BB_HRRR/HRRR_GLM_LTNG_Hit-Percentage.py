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

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3/')
from BB_HRRR.HRRR_Pando import get_hrrr_latlon, get_hrrr_all_valid, get_hrrr_variable
from BB_maps.my_basemap import draw_HRRR_map, draw_CONUS_cyl_map
from BB_GOES.get_GLM import get_GLM_file_nearesttime, accumulate_GLM_FAST

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

# Draw cylindrical projection HRRR map. We need to use a cylindrical projection
# because the plt.contour method will output the collection vertices in 
# latitude/longitude coordinates. If we used the lambert projection, then the
# contour vertices would be in strange map units.
print('Drawing Maps...')
mc = draw_CONUS_cyl_map()

# Draw the regular HRRR basemap for plotting purposes
m = draw_HRRR_map()
print('               ...Done\n\n')

# =============================================================================
# =============================================================================


def points_inside_contours_MP(inputs):
    """
    Input: [paths_glm, unique COLLECTION, level]
    
    Return: A dictionary of the boolean arrays for each paths_glm domain.
    """
    paths_glm, COLLECTION, level = inputs

    in_LTNG = {}

    for i in paths_glm.keys():
        # Initialize an array to store when points are inside a collection
        # that is the same length as the number of GLM flashes in the domain.
        inside = np.zeros_like(paths_glm[i]['latitude'])
        
        # Combine the lat/lon points into a tuple pair
        latlon_pair = [(paths_glm[i]['longitude'][j], paths_glm[i]['latitude'][j]) for j in range(len(inside))]
        
        # Each collection may have many paths--a path for each contour area.
        # We need to loop through each area and find out which points
        # lie inside the area. Those points that inside the path area (True),
        # Then we add those to the inside array.
        num = len(COLLECTION.collections[level].get_paths())
        for j, V in enumerate(COLLECTION.collections[level].get_paths()):
            is_inside = V.contains_points(latlon_pair)
            inside += is_inside
            sys.stdout.write('\r-->>  %s: %.1f%% Complete (%s of %s contour areas)' % (i, (j+1)/num*100, (j+1), num))
        
        # Convert the inside array from a count to a boolean. This boolean
        # matches the lat/lon points in the same order.
        # Add this information to the paths_glm file as a new key 'in_LTNG'
        # meaning the GLM point is inside the HRRR's LTNG field.
        in_LTNG[i] = np.array(inside, dtype=bool)
        
    return in_LTNG
    
    
def points_inside_contours(paths_glm, COLLECTIONS, level=0,):
    """
    Determine which points are inside a set of collections.
    Use a differenet CPU for each item in COLLECTIONS (i.e. there is a
    collection for each forecast lead time; f00-f18)

    Input:
        paths_glm   - Dictionary where each keys is a domain of interest.
                      Each domain is also a dictionary that contains the
                      latitude and longitude of GLM flash inside that domain.
        COLLECTIONS - List of contour collections; matplotlib.contour.QuadContourSet
                      from plt.contour() 
        level       - Contour level index. Usually set to 0 for first contour
                      level.

    Return:
        paths_glm   - Same as input, except with booleans for GLM points that
                      were inside the HRRR 
    """
    ## GLM Path Dictionary, Contour Collection, Lead Time, Contour Level Index
    # Length of inputs should equal the number of contour collections which 
    # should be the number of forecast lead times, i.e. len(fxx).
    timer = datetime.now()
    inputs = [[paths_glm, COL, level] for i, COL in enumerate(COLLECTIONS)]
    
    cores = np.minimum(multiprocessing.cpu_count(), len(inputs))
    with multiprocessing.Pool(cores) as p:
        
        in_LTNG_dicts = np.array(p.map(points_inside_contours_MP, inputs))
        p.close()
        p.join()
    print('\nTimer -- points_inside_contours(): ', datetime.now()-timer)
    
    ## Need to unpack the returned dictionaries.
    # in_LTNG_dicts should be as long as there are forecasts lead time; len(fxx)
    # Unpack the boolean for each forecast hour and put into the paths_glm dictionary.
    # For each forecast lead line, in_LTNG_Fxx, 'GLM' is the boolean of flashes
    # and 'hit rate' is the number of GLM flashes that occurred inside a HRRR
    # contour for that forecasted time.
    for i in range(len(in_LTNG_dicts)):
        for d in in_LTNG_dicts[i].keys():
            flash_boolean = in_LTNG_dicts[i][d]
            paths_glm[d]['in_LTNG_F%02d' % i] = {'boolean':flash_boolean,
                                                 'hit rate': sum(flash_boolean)/len(flash_boolean)}   
    
    return paths_glm


def get_HRRR_LTNG_hit_rate(DATE, fxx=range(19)):
    '''
    Return the HRRR's hit rate for lightning forecasts from the GLM flash data.

    Input:
        DATE - the valid time requested
        fxx  - a list of the forecast hour lead times. Default is f00-f18.

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
    
    if glm is None:
        print('!!! Warning !!! DATE %s had no lightning data' % DATE)
        # Return: hit_rate, number of flashes, number of files, numb of expected files
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
    print("Observations in each region:")
    for i in filtered_glm.keys():
        num = len(filtered_glm[i]['latitude'])
        print("    %s\t:\t%s" % (i, '{:,}'.format(num)))
    print("----------------------------------------------")

    ## Create Contour Collections Objects -------------------------------------
    #--------------------------------------------------------------------------
    # We can matplotlib.pyplot.contour() to generate Paths for each contour
    # area for every forecast lead time requested. These paths are used to
    # determine if a GLM flash occurred within the HRRR forecasted lightning
    # threat area.
    # NOTE: We must generate the collections with a cylindrical map projection,
    #       else contour returns funny map coordinates for the vertices of the
    #       path.
    # NOTE: Use H.data to access the unmasked array for correct contouring.
    # NOTE: Set levels=[0] to draw contours where lightning threat >0.
    
    CONTOURS = []
    for i, H in enumerate(HH):
        c = mc.contour(Hlon, Hlat, H.data, latlon=True, levels=[0])
        CONTOURS.append(c)
    plt.close()

    ## Determine which GLM flashes occurred in a HRRR contour -----------------
    #--------------------------------------------------------------------------
    # Uses the function points_inside_contours(), which relies on
    # multiprocessing, to return a list of points that are inside or outside
    # the contours. There is an array for each forecast lead time, fxx.
    timer = datetime.now()
    glm_hit_rate = points_inside_contours(filtered_glm, CONTOURS)
    print('\n!!! Timer: count GLM flashes inside HRRR contours:', datetime.now()-timer)

    return glm_hit_rate, (files['Number'], files['Number Expected'])
    

if __name__ == '__main__':
    timerStart = datetime.now()
    
    '''
    ## Date representing the valid time of interest
    sDATE = datetime(2018, 7, 1, 0)
    eDATE = datetime(2018, 8, 1, 0)
    days = (eDATE-sDATE).days
    DATES = [sDATE+timedelta(days=d) for d in range(days)]

    output = np.array(list(map(get_HRRR_LTNG_hit_rate, DATES)))

    a = np.array([i[0] for i in output])
    flash_counts = [i[1] for i in output]
    num_files = [i[2] for i in output]
    num_files_expected = [i[3] for i in output]

    # Set first column (F00) as nan, because there are never lightning 
    # forecasts for that column.
    a[:,0] = np.nan

    plt.figure(1)
    z = np.nanpercentile(a, [0, 25, 50, 75, 100], axis=0)
    plt.fill_between(range(19), z[0], z[-1], color=[.9,.9,.9])
    plt.fill_between(range(19), z[1], z[-2], color=[.7,.7,.7])
    plt.plot(range(19), z[2], linewidth=5, color='k')

    plt.plot(range(19), np.transpose(a))
    plt.plot(range(19), np.nanmean(a, axis=0), linewidth=1, color='w')

    plt.xticks(range(19))
    plt.grid()


    plt.figure(2, figsize=[5,5])
    plt.boxplot(flash_counts)
    plt.title('samples: %s' % len(flash_counts))
    
    
    plt.show()
    '''
    # =========================================================================
    
    ## Single Date and Figure
    #DATE = datetime(2018, 5, 14, 22) # Mallard Fire
    #DATE = datetime(2018, 7, 5, 23) # Lake Christine
    DATE = datetime(2018, 7, 17, 6) # July Storm
    #DATE = datetime(2018, 7, 27, 0) # Missing GLM data

    a, files_expected = get_HRRR_LTNG_hit_rate(DATE)

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
    
    # =========================================================================

    '''
    # Write output to a file
    fxx_strs = ','.join(['F%02d' % i for i in range(19)])
    header = 'DATE,GLM_FLASH_COUNT,FILES,EXPECTED,'+fxx_strs

    # Loop over many dates and write output to a file
    sDATE = datetime(2018, 8, 1, 1)
    eDATE = datetime(2018, 9, 1, 1)
    #hours = int((eDATE-sDATE).days*24+((eDATE-sDATE).seconds/3600))
    #DATES = [sDATE+timedelta(hours=h) for h in range(hours)]
    days = int((eDATE-sDATE).days)
    DATES = [sDATE+timedelta(days=d) for d in range(days)]

    # Open File and write a header
    with open("GLM_in_HRRR_%s.csv" % sDATE.strftime('%b-%Y_h%H'), "w") as f:
        f.write('%s\n' % header)

    for DATE in DATES:
        percentage, flash_count, num_files, num_files_expected = get_HRRR_LTNG_hit_rate(DATE)
        percentage = np.array(percentage.round(5), dtype=str)
        fxx_str = ','.join(percentage)
        textOutput = '%s,%s,%s,%s,%s' % (DATE, flash_count, num_files, num_files_expected, fxx_str)
        # write line to output file
        with open("GLM_in_HRRR_%s.csv" % sDATE.strftime('%b-%Y_h%H'), "a") as f:
            f.write(textOutput)
            f.write("\n")
    '''
    # =========================================================================
    """
    months = [5, 6, 7, 8, 9, 10]
    hours = range(15, 24)

    #months = [10]
    #hours = [3]

    for h in hours:
        for m in months:
            print('\n\n\n')
            print('=========================================================')
            print('=========================================================')
            print('WORKING ON MONTH %s and HOUR %s' % (m, h))
            print('=========================================================')
            print('=========================================================')

            # Write output to a file
            fxx_strs = ','.join(['F%02d' % i for i in range(19)])
            header = 'DATE,GLM_FLASH_COUNT,FILES,EXPECTED,'+fxx_strs

            # Loop over many dates and write output to a file
            sDATE = datetime(2018, m, 1, h)
            eDATE = datetime(2018, m+1, 1, h)
            #hours = int((eDATE-sDATE).days*24+((eDATE-sDATE).seconds/3600))
            #DATES = [sDATE+timedelta(hours=h) for h in range(hours)]
            days = int((eDATE-sDATE).days)
            DATES = [sDATE+timedelta(days=d) for d in range(days)]

            # Open File and write a header
            with open("GLM_in_HRRR_%s.csv" % sDATE.strftime('%b-%Y_h%H'), "w") as f:
                f.write('%s\n' % header)

            for DATE in DATES:
                percentage, flash_count, num_files, num_files_expected = get_HRRR_LTNG_hit_rate(DATE)
                percentage = np.array(percentage.round(5), dtype=str)
                fxx_str = ','.join(percentage)
                textOutput = '%s,%s,%s,%s,%s' % (DATE, flash_count, num_files, num_files_expected, fxx_str)
                # write line to output file
                with open("GLM_in_HRRR_%s.csv" % sDATE.strftime('%b-%Y_h%H'), "a") as f:
                    f.write(textOutput)
                    f.write("\n")

            print('Total Timer:', datetime.now()-timerStart)
    """

    months = [5, 6, 7, 8, 9, 10]
    hours = range(15, 24)

    for h in hours:
        for m in months:
            # Loop over many dates and write output to a file
            sDATE = datetime(2018, m, 1, h)
            eDATE = datetime(2018, m+1, 1, h)
            days = int((eDATE-sDATE).days)
            DATES = [sDATE+timedelta(days=d) for d in range(days)]

            for DATE in DATES:
                a, files_expected = get_HRRR_LTNG_hit_rate(DATE)
            
                if DATE == sDATE:
                    # Make New file and create header
                    print('make file and add header for each Domain')

                # For each domain, 
                    # Write
                    # date, total flashes, num files, expected files, hit rate f00, hit rate f01, f02, f03, ..., f18
            


