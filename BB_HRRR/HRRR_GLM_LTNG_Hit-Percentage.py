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
from datetime import datetime, timedelta
import multiprocessing

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3/')
from BB_HRRR.HRRR_Pando import get_hrrr_latlon, get_hrrr_all_valid
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
lat, lon = get_hrrr_latlon(DICT=False)

# Draw cylindrical projection HRRR map. We need to use a cylindrical projection
# because the plt.contour method will output the collection vertices in 
# latitude/longitude coordinates. If we used the lambert projection, then the
# contour vertices would be in strange map units.
mc = draw_CONUS_cyl_map()

# Draw the regular HRRR basemap for plotting purposes
m = draw_HRRR_map()

def points_inside_contours_MP(inputs):
    """
    Input: [lat, lon, COLLECTIONS, level]
        lat        - list of GLM observed latitudes
        lon        - list of GLM observed longitudes
        COLLECTION - a matplotlib.contour.QuadContourSet object from plt.contour()
        level      - contour level. Usually set to 0 for first contour level.
    """
    lat, lon, COLLECTION, level = inputs
    
    # Initialize an array to store when points are instide a collection
    inside = np.zeros_like(lat)
    
    # Combine the lat/lon points into a tuple pair
    latlon_pair = [(lon[i], lat[i]) for i in range(len(lat))]
    
    # Each collection may have many paths--a path for each contour area.
    # We need to loop through each area and find out which points
    # lie inside the area. Those points that inside the path area (True),
    # Then we add those to the inside array.
    num = len(COLLECTION.collections[level].get_paths())
    for i, V in enumerate(COLLECTION.collections[level].get_paths()):
        is_inside = V.contains_points(latlon_pair)
        inside += is_inside
        sys.stdout.write('\r%.1f%% Complete (%s of %s)' % ((i+1)/num*100, (i+1), num))
    
    # Convert the inside array to a boolean. This boolean
    # matches the lat/lon points in the same order.
    return np.array(inside, dtype=bool)
    
    
def points_inside_contours(lat, lon, COLLECTIONS, level=0):
    """
    lat         - list of latitudes
    lon         - list of longitudes
    COLLECTIONS - list of contour collections; matplotlib.contour.QuadContourSet 
    level       - contour level index, usually zero.
    """
    # GLM Latitude, GLM Longitude, Contour Collection, Contour Level Index
    timer = datetime.now()
    inputs = [[lat, lon, C, 0] for i, C in enumerate(COLLECTIONS)]
    cores = np.minimum(multiprocessing.cpu_count(), len(inputs))
    with multiprocessing.Pool(cores) as p:
        a = np.array(p.map(points_inside_contours_MP, inputs))
        p.close()
        p.join()
    print('\n', datetime.now()-timer)
    return a


def get_HRRR_LTNG_hit_rate(DATE, fxx=range(19)):
    '''
    Return the HRRR's hit rate for lightning forecasts from the GLM flash data.

    Input:
        DATE - the valid time requested
        fxx  - a list of the forecast hour lead times. Default is f00-f18.
    '''

    ## Get GLM data
    # Since the HRRR lightning product is for the previous hour, we need to 
    # get the GLM flashes that occurred during that hour. This function will
    # grab the GLM file nearest the (DATE - 30 minutes) and all files +/- 30
    # minutes, i.e. all GLM files for the hour before the DATE.
    # If there isn't any GLM files for the hour period, then return nans.
    timer=datetime.now()
    files = get_GLM_file_nearesttime(DATE-timedelta(minutes=30), window=30, verbose=True)
    g = accumulate_GLM_FAST(files)
    print('\n GLM Download Timer:', datetime.now()-timer)
    
    if g is None:
        print('!!! Warning !!! DATE %s had no lightning data' % DATE)
        hit_rate = np.ones_like(fxx)*np.nan
        # Return: hit_rate, number of flashes, number of files, numb of expected files
        return hit_rate, 0, len(files['Files']), files['Number Expected']
    

    ## Get HRRR data
    timer=datetime.now()
    # HRRR Lightning Threat Forecasts (Analysis field is empty for lightning
    # threat). Units: maximum flashes per km2 per 5min for previous hour.
    # Remember: HH is a masked array for LTNG and REFC.
    HH = get_hrrr_all_valid(DATE, 'LTNG:entire', fxx=fxx)
    print('\n HRRR Download Timer:', datetime.now()-timer)   


    ## Filter GLM observation within the HRRR domain.
    # The GLM observes flashes for the disk in its field of view. We only want
    # the flashes within the HRRR domain.
    print("Total GLM observations:", len(g['latitude']))
    # Bounds of HRRR domain:
    bound_lat = np.logical_and(g['latitude']>lat.min(), g['latitude']<lat.max())
    bound_lon = np.logical_and(g['longitude']>lon.min(), g['longitude']<lon.max())
    bound = np.logical_and(bound_lat, bound_lon)
    # Apply bounding box to GLM data
    g['latitude'] = g['latitude'][bound]
    g['longitude'] = g['longitude'][bound]
    g['energy'] = g['energy'][bound]
    g['area'] = g['area'][bound]
    print("Observations in HRRR domain:", len(g['latitude']))

    ## Create Contour Collections Objects
    # We can matplotlib.pyplot.contour() to generate Paths for each contour
    # area for every forecast lead time requested. These paths are used to
    # determine if a GLM flash occurred within the HRRR forecasted lightning
    # threat area.
    # NOTE: We must generate the collections with a cylindrical map projection,
    #       else contour returns funny map coordinates for the vertices of the
    #       path.
    # NOTE: Use H.data to access the unmasked array for correct contouring.
    # NOTE: Set levels=[0] to make contour around areas where lightning threat
    #       > 0.
    CONTOURS = []
    for i, H in enumerate(HH):
        c = mc.contour(lon, lat, H.data, latlon=True, levels=[0])
        CONTOURS.append(c)
    plt.close()

    ## Determine which GLM flashes occurred in a HRRR contour
    # Uses the function points_inside_contours(), which relies on
    # multiprocessing, to return a list of points that are inside or outside
    # the contours. There is an array for each forecast lead time, fxx.
    timer = datetime.now()
    inside = points_inside_contours(g['latitude'], g['longitude'], CONTOURS)
    print('\n!!! Timer: count GLM flashes inside HRRR contours:', datetime.now()-timer)

    ## Compute percentage of GLM flashes inside HRRR forecast for each fxx.
    hit_rate = np.array([sum(i)/len(i) for ii, i in enumerate(inside)])

    # Return: hit_rate, number of flashes, number of files, number of expected files
    return hit_rate, len(g['latitude']), len(files['Files']), files['Number Expected']


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
    '''
    # Single Date
    DATE = datetime(2018, 7, 27, 0, 30)
    a = get_HRRR_LTNG_hit_rate(DATE)
    '''
    

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
    months = [5, 6, 7, 8, 9, 10]
    hours = range(3, 24)

    months = [10]
    hours = [3]

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

    


    


