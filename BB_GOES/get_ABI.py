# Brian Blaylock
# September 14, 2018

"""
Make GOES-16 Composite Images from the Advanced Baseline Imager
"""

import numpy as np 
from datetime import datetime, timedelta
from pyproj import Proj
import subprocess
import xarray
import matplotlib.pyplot as pyplot

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')
sys.path.append('B:\pyBKB_v3')

def contrast_correction(color, contrast):
    """
    Modify the contrast of an RGB
    See: #www.dfstudios.co.uk/articles/programming/image-programming-algorithms/image-processing-algorithms-part-5-contrast-adjustment/

    Input:
        C - contrast level
    """
    F = (259*(contrast + 255))/(255.*259-contrast)
    COLOR = F*(color-.5)+.5
    COLOR = np.minimum(COLOR, 1)
    COLOR = np.maximum(COLOR, 0)
    return COLOR


def files_on_pando(DATE):
    """
    Get a list of file in Pando on the DATE requested
    """
    # List files in Pando bucket
    PATH_Pando = 'GOES16/ABI-L2-MCMIPC/%s/' % (DATE.strftime('%Y%m%d'))
    ls = ' ls horelS3:%s | cut -c 11-' % (PATH_Pando)
    rclone_out = subprocess.check_output('rclone ' + ls, shell=True)
    flist = rclone_out.decode().split('\n')
    flist = np.array([l for l in flist if '.nc' in l]) # only include .nc files
    flist.sort()
    return np.array(flist)


def file_nearest(DATE):
    """
    Return the file name nearest the requested date
    """
    flist = files_on_pando(DATE)
    date_diff = [*map(lambda x: abs(datetime.strptime(x.split('_')[3], 's%Y%j%H%M%S%f')-DATE), flist)]
    return '/uufs/chpc.utah.edu/common/home/horel-group7/Pando/GOES16/ABI-L2-MCMIPC/%s/%s' % (DATE.strftime('%Y%m%d'), flist[np.argmin(date_diff)])


def get_GOES_truecolor(FILE, only_RGB=False, night_IR=True, contrast_adjust=True, verbose=True):
    """
    Uses Channel 1, 2, 3 to create a "True Color" Image.
    """
    try:
        C = xarray.open_dataset(FILE)
        if verbose:
            print("Fetching:", FILE)
    except:
        print("Can't open file:", FILE)
        return None

    # Scan's start time, converted to datetime object
    scan_start = datetime.strptime(C.time_coverage_start, '%Y-%m-%dT%H:%M:%S.%fZ')

    # Scan's end time, converted to datetime object
    scan_end = datetime.strptime(C.time_coverage_end, '%Y-%m-%dT%H:%M:%S.%fZ')

    # File creation time, convert to datetime object
    file_created = datetime.strptime(C.date_created, '%Y-%m-%dT%H:%M:%S.%fZ')

    # The 't' variable is the scan's midpoint time
    # I'm not a fan of numpy datetime, so I convert it to a regular datetime object
    midpoint = str(C['t'].data)[:-8]
    scan_mid = datetime.strptime(midpoint, '%Y-%m-%dT%H:%M:%S.%f')

    if verbose:
        print('Scan Start    : %s' % scan_start)
        print('Scan midpoint : %s' % scan_mid)
        print('Scan End      : %s' % scan_end)
        print('File Created  : %s' % file_created)
        print('Scan Duration : %.2f minutes' % ((scan_end-scan_start).seconds/60))
        
    # Load the three channels into appropriate R, G, and B variables
    R = C['CMI_C02'].data
    G = C['CMI_C03'].data
    B = C['CMI_C01'].data
        
    # RGB values must be between 0 and 1.
    R = np.maximum(R, 0)
    G = np.maximum(G, 0)
    B = np.maximum(B, 0)

    R = np.minimum(R, 1)
    G = np.minimum(G, 1)
    B = np.minimum(B, 1)

    # Apply a gamma correction to the image
    gamma = 0.4
    R = np.power(R, gamma)
    G = np.power(G, gamma)
    B = np.power(B, gamma)
    if verbose:
        print('    Gamma correction, gamma=', gamma)

    # Calculate the "True" Green
    G_true = 0.48358168 * R + 0.45706946 * B + 0.06038137 * G
    G_true = np.maximum(G_true, 0)
    G_true = np.minimum(G_true, 1)

    # The RGB array for the true color image
    RGB = np.dstack([R, G_true, B])

    if contrast_adjust:
        # Amount of contrast
        contrast_amount = 105
        # Apply contrast correction
        RGB = contrast_correction(RGB, contrast_amount)
        if verbose:
            print('    Contrast correction, contrast=', contrast_amount)

    if night_IR:
        cleanIR = C['CMI_C13'].data

        # Apply range limits for clean IR channel
        cleanIR = np.maximum(cleanIR, 90)
        cleanIR = np.minimum(cleanIR, 313)

        # Normalize the channel between a range
        cleanIR = (cleanIR-90)/(313-90)

        # Invert colors so that cold clouds are white
        cleanIR = 1 - cleanIR

        # Lessen the brightness of the coldest clouds so they don't appear so bright when we overlay it on the true color image
        cleanIR = cleanIR/1.4

        RGB = np.dstack([np.maximum(R, cleanIR), np.maximum(G_true, cleanIR), np.maximum(B, cleanIR)])


    # Satellite height
    sat_h = C['goes_imager_projection'].perspective_point_height

    # Satellite longitude
    sat_lon = C['goes_imager_projection'].longitude_of_projection_origin

    # Satellite sweep
    sat_sweep = C['goes_imager_projection'].sweep_angle_axis

    # The projection x and y coordinates equals the scanning angle (in radians) multiplied by the satellite height
    # See details here: https://proj4.org/operations/projections/geos.html?highlight=geostationary
    x = C['x'][:] * sat_h
    y = C['y'][:] * sat_h

    # Create a pyproj geostationary map object
    p = Proj(proj='geos', h=sat_h, lon_0=sat_lon, sweep=sat_sweep)

    # Perform cartographic transformation. That is, convert image projection coordinates (x and y)
    # to latitude and longitude values.
    XX, YY = np.meshgrid(x, y)
    lons, lats = p(XX, YY, inverse=True)
    
    # Assign the pixels showing space as a single point in the Gulf of Alaska
    lats[np.isnan(R)] = 57
    lons[np.isnan(R)] = -152

    # Create a color tuple for pcolormesh

    # Don't use the last column of the RGB array or else the image will be scrambled!
    # This is the strange nature of pcolormesh.
    rgb = RGB[:,:-1,:]

    # Flatten the array, becuase that's what pcolormesh wants.
    colorTuple = rgb.reshape((rgb.shape[0] * rgb.shape[1]), 3)

    # Adding an alpha channel will plot faster, according to Stack Overflow. Not sure why.
    colorTuple = np.insert(colorTuple, 3, 1.0, axis=1)

    return {'TrueColor': RGB,
            'file': FILE,
            'lat': lats,
            'lon': lons,
            'sDATE': scan_start,
            'eDATE': scan_end,
            'DATE' : scan_mid,
            'Satellite Height': sat_h,
            'lon_0': sat_lon,
            'X': x,
            'Y': y,
            'rgb_tuple': colorTuple}
