# Brian Blaylock
# October 31, 2018                                             Happy Halloween!

"""
Make GOES-16 RGB Composite Images from the Advanced Baseline Imager (ABI).
Uses the level 2 multiband formatted file (ABI-L2-MCMIPC; 2 km resolution).

Quick Guide Recipes: http://rammb.cira.colostate.edu/training/visit/quick_guides/

Contents:
    contrast_correction()       - Adjust the RGB contrast for a pseudo-rayleigh
                                  scattering correction.
    files_on_pando()            - For a given Date, list the available files.
    file_nearest()              - Return path and name of file nearest a datetime.
    get_GOES_dates()            - For ABI file opened with xarray, return the
                                  scan's start, end, and midpoint datetimes.
    get_GOES_latlon()           - Return the latitude/longitude values for the
                                  grid. Also return satellite's height and longitude.
    make_colorTuple()           - Convert a 3D RGB array into a list of color
                                  tuples suitable for plotting with pcolormesh.
    
    get_GOES_TrueColor()        - RGB Product: True Color
    get_GOES_FireTemperature()  - RGB Product: Fire Temperature
    get_GOES_DayConvection()    - RGB Product: Day Convection
    get_GOES_AirMass()          - RGB Product: Air Mass
"""

import numpy as np 
from datetime import datetime, timedelta
from pyproj import Proj
import subprocess
import xarray
import matplotlib.pyplot as pyplot
import metpy

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')
sys.path.append('B:\pyBKB_v3')


def contrast_correction(color, contrast):
    """
    Modify the contrast of an RGB (a poor-man's Rayleigh correction)
    See: #www.dfstudios.co.uk/articles/programming/image-programming-algorithms/image-processing-algorithms-part-5-contrast-adjustment/

    Input:
        color    - An RGB array or value between 0 and 1.
        contrast - Contrast level
    Output:
        COLOR    - Contrast adjusted RGB value or values
    """
    F = (259*(contrast + 255))/(255.*259-contrast)
    COLOR = F*(color-.5)+.5
    COLOR = np.minimum(COLOR, 1)
    COLOR = np.maximum(COLOR, 0)
    return COLOR


def files_on_pando(DATE):
    """
    Returns a list of ABI file on Pando for the DATE requested.
    """
    # List files in Pando bucket
    PATH_Pando = 'GOES16/ABI-L2-MCMIPC/%s/' % (DATE.strftime('%Y%m%d'))
    ls = ' ls horelS3:%s | cut -c 11-' % (PATH_Pando)
    rclone_out = subprocess.check_output('rclone ' + ls, shell=True)
    flist = rclone_out.decode().split('\n')
    flist = np.array([l for l in flist if '.nc' in l]) # only include .nc files
    flist = np.array(['%s%s' % (PATH_Pando, l) for l in flist])
    flist.sort()
    return np.array(flist)


def get_files_for_range(sDATE, eDATE, satellite=16, dataset='ABI', verbose=False):
    """
    Get all ABI or GLM files for a daterange.

    Input:
        sDATE     - The begining date
        eDATE     - The ending date (inclusive)
        satellite - The number of the GOES satellite. 16, or 17.
    """
    assert satellite in [16, 17], ('satellite must be either 16 or 17')
    assert dataset in ['ABI', 'GLM'], ('dataset must be either "ABI" or "GLM"')

    if dataset == 'ABI':
        Data = 'ABI-L2-MCMIPC'
    elif dataset == 'GLM':
        Data = 'GLM-L2-LCFA'

    # GOES16 ABI and GLM data is stored on horel-group7 and on Pando
    HG7 = '/uufs/chpc.utah.edu/common/home/horel-group7/Pando/GOES%s/%s/' % (satellite, Data)

    # Directories are sorted by hour. Get all possible direcotires within the
    # requested range of dates.
    dt = eDATE-sDATE
    hours = dt.days*24 + int((dt).seconds/3600)
    look_here_DATES = [sDATE+timedelta(hours=h) for h in range(hours+1)]

    # Store the files from each directory
    files = []
    for DATE in look_here_DATES:
        # Directory path for this date...
        DIR = HG7+'%s/' % DATE.strftime('%Y%m%d/%H')
        if verbose:
            print("Looking here: %s" % DIR)
        # Store the files (full path) from those directories, if it exists
        if os.path.exists(DIR):
            files += list(map(lambda x: DIR+x, os.listdir(DIR)))

    # Sometime a file might be in the wrong directory. This was the case when GLM on GOES-17
    # was being tested. We want to remove these, so save this variable for later.
    files = list(filter(lambda x: '_G%02d_' % satellite in x, files))

    # Convert to numpy array for indexing
    files = np.array(files)

    # Filter the files based on the requested range. File start scan should
    # be after sDATE and file end scan should be before eDATE.
    # First, we need arrays of the datetimes of each file.
    sSCANS = np.array([datetime.strptime(x.split('_')[3], 's%Y%j%H%M%S%f') for x in files])
    eSCANS = np.array([datetime.strptime(x.split('_')[4], 'e%Y%j%H%M%S%f') for x in files])

    # Determine index of files within the bounds. 
    within_bounds = np.logical_and(sSCANS>=sDATE, eSCANS<=eDATE)
    files = files[within_bounds]

    return files


def file_nearest(DATE):
    """
    Return the file name and path nearest the requested date.
    """
    flist = files_on_pando(DATE)
    date_diff = [*map(lambda x: abs(datetime.strptime(x.split('_')[3], 's%Y%j%H%M%S%f')-DATE), flist)]
    return '/uufs/chpc.utah.edu/common/home/horel-group7/Pando/%s' % (flist[np.argmin(date_diff)])


def get_GOES_dates(C, verbose=True):
    """
    Return the ABI scan's start, end, and midpoint datetime from an opened file.
    
    Input:
        C - an ABI file opened with xarray
    """
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
    
    return {'sDATE': scan_start,
            'eDATE': scan_end,
            'DATE' : scan_mid}

def get_GOES_latlon(C, verbose=True):
    """
    Performs cartographic transformation of the geostationary dataset with pyproj.
    This transformation returns a lat/lon array for each GOES-16 gridpoint.

    Input:
        C - An ABI file opened with xarray.
    """
    # Satellite height
    sat_h = C['goes_imager_projection'].perspective_point_height

    # Satellite longitude
    sat_lon = C['goes_imager_projection'].longitude_of_projection_origin

    # Satellite sweep
    sat_sweep = C['goes_imager_projection'].sweep_angle_axis

    # The projection x and y coordinates equals the scanning angle (in radians)
    # multiplied by the satellite height. See details here:
    #   https://proj4.org/operations/projections/geos.html?highlight=geostationary
    x = C['x'][:] * sat_h
    y = C['y'][:] * sat_h

    # Create a pyproj geostationary map object
    p = Proj(proj='geos', h=sat_h, lon_0=sat_lon, sweep=sat_sweep)

    # Perform cartographic transformation. That is, convert image projection
    # coordinates (x and y) to latitude and longitude values.
    XX, YY = np.meshgrid(x, y)
    lons, lats = p(XX, YY, inverse=True)
    
    # Assign the pixels showing empty space as a single point in the Gulf of Alaska
    R = C['CMI_C02'].data # load a visible channel to get NAN values
    lats[np.isnan(R)] = 57
    lons[np.isnan(R)] = -152

    return {'lat': lats,
            'lon': lons,
            'Satellite Height': sat_h,
            'Satellite Longitude': sat_lon}


def make_colorTuple(RGB, verbose=True):
    """
    Convert an 3D RGB array into an color tuple list suitable for plotting with
    pcolormesh.
    Input:
        RGB - a three dimensional array of RGB values from np.dstack([R, G, B])
    """
    # Don't use the last column of the RGB array or else the image will be scrambled!
    # This is the strange nature of pcolormesh.
    rgb = RGB[:,:-1,:]

    # Flatten the array, because that's what pcolormesh wants.
    colorTuple = rgb.reshape((rgb.shape[0] * rgb.shape[1]), 3)

    # Adding an alpha channel will plot faster, according to Stack Overflow. Not sure why.
    colorTuple = np.insert(colorTuple, 3, 1.0, axis=1)

    if verbose:
        print("\n******************************************")
        print(" How to use color tuple with pcolormesh:")
        print(" >>> TC = get_GOES_TrueColor(FILE)")
        print(" >>> newmap = plt.pcolormesh(TC['lon'], TC['lat'], np.zeros_like(TC['lon']), color=TC['TrueColor Tuple'], linewidth=0)")
        print(" >>> newmap.set_array(None)")
        print("******************************************\n")

    return colorTuple


def get_GOES_TrueColor(FILE, return_dates=True, return_latlon=True,
                             true_green=True,
                             night_IR=True,
                             contrast_adjust=True,
                             verbose=True):
    """
    Create a "True Color" RGB product.
    
    Follow recipe:
        http://cimss.ssec.wisc.edu/goes/OCLOFactSheetPDFs/ABIQuickGuide_CIMSSRGB_v2.pdf
        https://github.com/blaylockbk/pyBKB_v3/blob/master/BB_GOES/mapping_GOES16_TrueColor.ipynb
    """
    try:
        C = xarray.open_dataset(FILE)
        if verbose:
            print("Fetching:", FILE)
    except:
        print("Can't open file:", FILE)
        return None

    return_this = {'FILE': FILE,}

    # Get Date and geospatial info
    if return_dates:
        return_this.update(get_GOES_dates(C, verbose=verbose))
    if return_latlon:
        return_this.update(get_GOES_latlon(C, verbose=verbose))
        
    # Load the three channels into appropriate R, G, and B variables
    R = C['CMI_C02'].data
    G = C['CMI_C03'].data
    B = C['CMI_C01'].data
        
    # Apply range limits for each channel. RGB values must be between 0 and 1
    R = np.clip(R, 0, 1)
    G = np.clip(G, 0, 1)
    B = np.clip(B, 0, 1)
  
    # Apply a gamma correction to the image
    gamma = 2.2
    R = np.power(R, 1/gamma)
    G = np.power(G, 1/gamma)
    B = np.power(B, 1/gamma)
    
    if verbose:
        print('    Gamma correction, gamma=', gamma)

    if true_green:
        # Calculate the "True" Green
        G = 0.45 * R + 0.1 * G + 0.45 * B
        G = np.clip(G, 0, 1)
    
    RGB = np.dstack([R, G, B])

    if contrast_adjust:
        # Amount of contrast
        contrast_amount = 105
        # Apply contrast correction
        RGB = contrast_correction(RGB, contrast_amount)
        if verbose:
            print('    Contrast correction, contrast=', contrast_amount)

    if night_IR:
        cleanIR = C['CMI_C13'].data
        # Normalize the channel between a range. e.g. cleanIR = (cleanIR-minimum)/(maximum-minimum)
        cleanIR = (cleanIR-90)/(313-90)
        # Apply range limits for each channel. RGB values must be between 0 and 1
        cleanIR = np.clip(cleanIR, 0, 1)
        # Invert colors so that cold clouds are white
        cleanIR = 1 - cleanIR
        # Lessen the brightness of the coldest clouds so they don't appear so bright when we overlay it on the true color image
        cleanIR = cleanIR/1.4    
        RGB = np.dstack([np.maximum(R, cleanIR), np.maximum(G, cleanIR), np.maximum(B, cleanIR)])

    # Create a color tuple for pcolormesh
    return_this['TrueColor'] = RGB
    return_this['TrueColor Tuple'] = make_colorTuple(RGB, verbose=verbose)
    dat = C.metpy.parse_cf('CMI_C02')
    return_this['dat'] = dat
    return_this['crs'] = dat.metpy.cartopy_crs

    return return_this


def get_GOES_FireTemperature(FILE, return_dates=True, return_latlon=True, verbose=True):
    """
    Create a "Fire Temperature" RGB product.
    
    Follow recipe:
        http://rammb.cira.colostate.edu/training/visit/quick_guides/Fire_Temperature_RGB.pdf
        https://github.com/blaylockbk/pyBKB_v3/blob/master/BB_GOES/mapping_GOES16_FireTemperature.ipynb
    """
    try:
        C = xarray.open_dataset(FILE)
        if verbose:
            print("Fetching:", FILE)
    except:
        print("Can't open file:", FILE)
        return None

    return_this = {'FILE': FILE,}

    # Get Date and geospatial info
    if return_dates:
        return_this.update(get_GOES_dates(C, verbose=verbose))
    if return_latlon:
        return_this.update(get_GOES_latlon(C, verbose=verbose))

    # Load the three channels into appropriate R, G, and B variables
    R = C['CMI_C07'].data
    G = C['CMI_C06'].data
    B = C['CMI_C05'].data
   
    # Normalize each channel by the appropriate range of values  e.g. R = (R-minimum)/(maximum-minimum)
    R = (R-273)/(333-273)
    G = (G-0)/(1-0)
    B = (B-0)/(0.75-0)

    # Apply range limits for each channel. RGB values must be between 0 and 1
    R = np.clip(R, 0, 1)
    G = np.clip(G, 0, 1)
    B = np.clip(B, 0, 1)
  
    # Apply the gamma correction to Red channel.
    #   corrected_value = value^(1/gamma)
    gamma = 0.4
    R = np.power(R, 1/gamma)
    
    # The final RGB array :)
    RGB = np.dstack([R, G, B])

    # Create a color tuple for pcolormesh
    return_this['FireTemperature'] = RGB
    return_this['FireTemperature Tuple'] = make_colorTuple(RGB, verbose=verbose)

    return return_this


def get_GOES_DayConvection(FILE, return_dates=True, return_latlon=True, verbose=True):
    """
    Create a "Day Convection" RGB product.
    
    Follow recipe:
        http://rammb.cira.colostate.edu/training/visit/quick_guides/QuickGuide_GOESR_DayConvectionRGB_final.pdf
        https://github.com/blaylockbk/pyBKB_v3/blob/master/BB_GOES/mapping_GOES16_DayConvection.ipynb
    """
    try:
        C = xarray.open_dataset(FILE)
        if verbose:
            print("Fetching:", FILE)
    except:
        print("Can't open file:", FILE)
        return None

    return_this = {'FILE': FILE,}

    # Get Date and geospatial info
    if return_dates:
        return_this.update(get_GOES_dates(C, verbose=verbose))
    if return_latlon:
        return_this.update(get_GOES_latlon(C, verbose=verbose))

    # Load the three channels into appropriate R, G, and B variables
    R = C['CMI_C08'].data - C['CMI_C10'].data
    G = C['CMI_C07'].data - C['CMI_C13'].data
    B = C['CMI_C05'].data - C['CMI_C02'].data
   
    # Normalize each channel by the appropriate range of values. e.g. R = (R-minimum)/(maximum-minimum)
    R = (R--35)/(5--35)
    G = (G--5)/(60--5)
    B = (B--0.75)/(0.25--0.75)

    # Apply range limits for each channel. RGB values must be between 0 and 1
    R = np.clip(R, 0, 1)
    G = np.clip(G, 0, 1)
    B = np.clip(B, 0, 1)

    # The final RGB array :)
    RGB = np.dstack([R, G, B])

    # Create a color tuple for pcolormesh
    return_this['DayConvection'] = RGB
    return_this['DayConvection Tuple'] = make_colorTuple(RGB, verbose=verbose)

    return return_this


def get_GOES_AirMass(FILE, return_dates=True, return_latlon=True, verbose=True):
    """
    Create an "Air Mass" RGB product.
    
    Follow recipe:
        http://rammb.cira.colostate.edu/training/visit/quick_guides/QuickGuide_GOESR_AirMassRGB_final.pdf
        https://github.com/blaylockbk/pyBKB_v3/blob/master/BB_GOES/mapping_GOES16_AirMass.ipynb
    """
    try:
        C = xarray.open_dataset(FILE)
        if verbose:
            print("Fetching:", FILE)
    except:
        print("Can't open file:", FILE)
        return None

    return_this = {'FILE': FILE,}

    # Get Date and geospatial info
    if return_dates:
        return_this.update(get_GOES_dates(C, verbose=verbose))
    if return_latlon:
        return_this.update(get_GOES_latlon(C, verbose=verbose))

    # Load the three channels into appropriate R, G, and B variables
    R = C['CMI_C08'].data - C['CMI_C10'].data
    G = C['CMI_C12'].data - C['CMI_C13'].data
    B = C['CMI_C08'].data-273.15 # remember to convert to Celsius
   
    # Normalize each channel by the appropriate range of values. e.g. R = (R-minimum)/(maximum-minimum)
    R = (R--26.2)/(0.6--26.2)
    G = (G--42.2)/(6.7--42.2)
    B = (B--64.65)/(-29.25--64.65)

    # Invert B
    B = 1-B

    # Apply range limits for each channel. RGB values must be between 0 and 1
    R = np.clip(R, 0, 1)
    G = np.clip(G, 0, 1)
    B = np.clip(B, 0, 1)

    # The final RGB array :)
    RGB = np.dstack([R, G, B])

    # Create a color tuple for pcolormesh
    return_this['AirMass'] = RGB
    return_this['AirMass Tuple'] = make_colorTuple(RGB, verbose=verbose)

    return return_this


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    print("test dataset")
    DIR = '/uufs/chpc.utah.edu/common/home/horel-group7/Pando/GOES16/ABI-L2-MCMIPC/20180914/'
    FILE = 'OR_ABI-L2-MCMIPC-M3_G16_s20182570022128_e20182570024501_c20182570025006.nc'

    ## RGB
    RGB_products = get_GOES_TrueColor(DIR+FILE)
    RGB_products.update(get_GOES_FireTemperature(DIR+FILE))
    RGB_products.update(get_GOES_DayConvection(DIR+FILE))
    RGB_products.update(get_GOES_AirMass(DIR+FILE))

    ## True Color
    plt.figure(1)
    plt.imshow(RGB_products['TrueColor'])
    
    plt.figure(2)
    # We need an array the shape of the data, so use R. The color of each pixel will be set by color=colorTuple.
    newmap = plt.pcolormesh(RGB_products['lon'], RGB_products['lat'], np.zeros_like(RGB_products['lon']), color=RGB_products['TrueColor Tuple'], linewidth=0)
    newmap.set_array(None) # Without this line the RGB colorTuple is ignored and only R is plotted.

    ## Fire Temperature RGB
    plt.figure(3)
    plt.imshow(RGB_products['FireTemperature'])
    
    plt.figure(4)
    newmap = plt.pcolormesh(RGB_products['lon'], RGB_products['lat'], np.zeros_like(RGB_products['lon']), color=RGB_products['FireTemperature Tuple'], linewidth=0)
    newmap.set_array(None)

    ## Day Convection RGB
    plt.figure(5)
    plt.imshow(RGB_products['DayConvection'])
    
    plt.figure(6)
    newmap = plt.pcolormesh(RGB_products['lon'], RGB_products['lat'], np.zeros_like(RGB_products['lon']), color=RGB_products['DayConvection Tuple'], linewidth=0)
    newmap.set_array(None)

    ## Air Mass RGB
    plt.figure(7)
    plt.imshow(RGB_products['AirMass'])
    
    plt.figure(8)
    newmap = plt.pcolormesh(RGB_products['lon'], RGB_products['lat'], np.zeros_like(RGB_products['lon']), color=RGB_products['AirMass Tuple'], linewidth=0)
    newmap.set_array(None)

    plt.show()

    # TrueColor with FireTemperature overlay
    plt.figure(9)
    TC_FT_composite = np.maximum(RGB_products['TrueColor'], RGB_products['FireTemperature'])
    plt.imshow(TC_FT_composite)
        
    plt.figure(10)
    TC_FT_composite = np.maximum(RGB_products['TrueColor Tuple'], RGB_products['FireTemperature Tuple'])
    newmap = plt.pcolormesh(RGB_products['lon'], RGB_products['lat'], np.zeros_like(RGB_products['lon']), color=TC_FT_composite, linewidth=0)
    newmap.set_array(None)
