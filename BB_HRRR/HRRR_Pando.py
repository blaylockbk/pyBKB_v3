# Brian Blaylock
# July 3, 2018

"""
Get data from a HRRR grib2 file on the MesoWest HRRR Pando Archive
Requires cURL, wgrib2, and pygrib

Contents:
    get_hrrr_variable()            - Returns dict of single HRRR variable.
    get_hrrr_latlon()              - Return a dict of the CONUS HRRR grid lat/lon.
    get_hrrr_all_valid()           - Return a 3D array of all forecasts at a valid datetime.

    pluck_hrrr_point()             - Returns valid time and plucked value from lat/lon
    hrrr_subset                    - Returns a subset of the model domain
    hrrr_area_stats                - Returns statistics for the subset

    pluck_point_MultiPro()         - Feeds variables from multiprocessing for timeseries
    pluck_LocDic_MultiPro()        - Feeds variables from multiprocessing for timeseries for a Location Dictionary

    point_hrrr_time_series()       - Returns HRRR time series at a single point in the domain.
    LocDic_hrrr_time_series()      - Returns dictionary of the HRRR timeseries at multiple points.
    point_hrrr_pollywog()          - Returns HRRR pollywog at a single point in the domain.
    LocDic_hrrr_pollywog()         - Returns dictionary of the HRRR pollywog at multiple points

    LocDic_hrrr_hovmoller          - A hovmoller array to show all forecasts at each valid time.

    The difference between a time series and a pollywog is that:
        - a time series is for the all analyses (f00) or all forecast hours (fxx) for multiple runs
        - a pollywog is a time series for the full forecast cycle of a single run, i.e. f00-f18

A Special Note on U and V wind components:
    You can set the variable to be 'UVGRD:[level]' and the get_hrrr_variable
    function will convert the U and V winds from grid-relative to
    earth-relative, and will compute the wind speed. These are stored in the 
    keys 'UGRD', 'VGRD', and 'SPEED'. The other functions will return these 
    three values in a np.array() in the order (U, V, SPEED). If you do not 
    want to convert the winds to earth-relative, you can keep them in
    grid-relative by requesting the 'UGRD:[level]' and 'VGRD:[level]' independently.

# (Remove the temporary file)
#    ?? Is it possible to push the data straight from curl to ??
#    ?? pygrib, without writing/removing a temp file? and     ??
#    ?? would that speed up this process?                     ??
"""

import os
import pygrib
from datetime import datetime, timedelta
import requests
import ssl
import re
import numpy as np
import multiprocessing

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')
from BB_wx_calcs.wind import wind_uv_to_spd

###############################################################################
###############################################################################

def get_hrrr_variable(DATE, variable,
                      fxx=0,
                      model='hrrr',
                      field='sfc',
                      removeFile=True,
                      value_only=False,
                      verbose=True,
                      outDIR='./'):
    """
    Uses cURL to grab the requested variable from a HRRR grib2 file in the
    HRRR archive. Uses the the requested variable string to search the .idx
    file and determine the byte range. When the byte range of a variable is
    known, cURL is capable of downloading a single variable from a larger GRIB2
    file. This function packages the data in a dictionary.

    Input:
        DATE       - The datetime(year, month, day, hour) for the HRRR file you
                     want. This is the same as the model run time, in UTC.
        variable   - A string describing the variable you are looking for in the
                     GRIB2 file. Refer to the .idx files. For example:
                        https://pando-rgw01.chpc.utah.edu/hrrr/sfc/20180101/hrrr.t00z.wrfsfcf00.grib2.idx
                     You want to put the variable short name and the level
                     information. For example, for 2m temperature:
                        variable='TMP:2 m above ground'
        fxx        - The forecast hour you desire. Default is the analysis hour,
                     or f00.
        model      - The model you want. Options include ['hrrr', 'hrrrX', 'hrrrak']
        field      - The file output type. Options include ['sfc', 'prs']
        removeFile - True: remove the GRIB2 file after it is downloaded
                     False: do not remove the GRIB2 file after it is downloaded
        value_only - True: only return the values, not the lat/lon.
                        Returns output in 0.2 seconds
                     False: returns value and lat/lon, grib message, analysis and valid datetime.
                        Returns output in 0.75-1 seconds
        verbose    - Prints some diagnostics
        outDIR     - Specify where the downloaded data should be downloaded.
                     Default is the current directory. 

    Tips:
        1. The DATE you request represents the model run time. If you want to
           retrieve the file based on the model's valid time, you need to
           offset the DATE with the forecast lead time. For example:
                VALID_DATE = datetime(year, month, day, hour)   # We want the model data valid at this time
                fxx = 15                                        # Forecast lead time
                RUN_DATE = VALID_DATE-timedelta(hours=fxx)      # The model run datetime that produced the data
                get_hrrr_variable(RUN_DATE, 'TMP:2 m', fxx=fxx) # The returned data will be a forecast for the requested valid time and lead time
        
        2. You can request both U and V components at a level by using
                variable='UVGRD:10 m'
            This special request will return the U and V component winds
            converted from grid-relative to earth-relative, as well as the 
            calculated wind speed.
            Note: You can still get the grid-relative winds by requesting both
                  'UGRD:10 m' and 'VGRD:10 m' individually.
    """

    ## --- Catch Errors -------------------------------------------------------
    # Check that you requested the right model name and field name
    if model not in ['hrrr', 'hrrrX', 'hrrrak']:
        raise ValueError("Requested model must be 'hrrr', 'hrrrX', or 'hrrrak'")
    if field not in ['prs', 'sfc']:
        raise ValueError("Requested field must be 'prs' or 'sfc'. We do not store other fields in the archive")
    
    # Check that you requested the right forecasts available for the model
    if model == 'hrrr' and fxx not in range(19):
        raise ValueError("HRRR: fxx must be between 0 and 18\nYou requested f%02d" % fxx)
    elif model == 'hrrrX' and fxx != 0:
        raise ValueError("HRRRx: fxx must be 0. We do not store other forecasts in the archive.\nYou requested f%02d" % fxx)
    elif model == 'hrrrak' and fxx not in range(37):
        raise ValueError("HRRRak: fxx must be between 0 and 37\nYou requested f%02d" % fxx)
    
    # Check that the requested hour exists for the model
    if model == 'hrrrak' and DATE.hour not in range(0,24,3):
        raise ValueError("HRRRak: DATE.hour must be 0, 3, 6, 9, 12, 15, 18, or 21\nYou requested %s" % DATE.hour)

    if verbose:
        # Check that the request datetime has happened
        if DATE > datetime.utcnow():
            print("Warning: The datetime you requested hasn't happened yet\nDATE: %s F%02d\n UTC: %s" % (DATE, fxx, datetime.utcnow()))
    ## ---(Catch Errors)-------------------------------------------------------


    ## --- Set Temporary File Name --------------------------------------------
    # Temporary file name has to be unique, or else when we use multiprocessing
    # we might accidentally delete files before we are done with them.
    outfile = '%stemp_%s_%s_f%02d_%s.grib2' % (outDIR, model, DATE.strftime('%Y%m%d%H'), fxx, variable[:3].replace(":", ''))

    if verbose is True:
        print("")
        print(' >> Dowloading tempfile: %s' % outfile)


    ## --- Requested Variable -------------------------------------------------
    # A special variable request is 'UVGRD:[level]' which will get both the U
    # and V wind components converted to earth-relative direction in a single
    # download. Since UGRD always proceeds VGRD, we will set the get_variable
    # as UGRD. Else, set get_variable as variable.
    if variable.split(':')[0] == 'UVGRD':
        # We need both U and V to convert winds from grid-relative to earth-relative
        get_variable = 'UGRD:' + variable.split(':')[1]
    else:
        get_variable = variable


    ## --- Set Data Source ----------------------------------------------------
    """
    Dear User,
      HRRR files are only downloaded and added to Pando every 3 hours.
      That means if you are requesting data for today that hasn't been copied
      to Pando yet, you will need to get it from the NOMADS website instead.
      But good news! It's an easy fix. All we need to do is redirect you to the
      NOMADS server. I'll check that the date you are requesting is not for
      today's date. If it is, then I'll send you to NOMADS. Deal? :)
                                                  -Sincerely, Brian
    """
    
    # If the datetime requested is less than six hours ago, then the file is 
    # most likely on Pando. Else, download from NOMADS. 
    #if DATE+timedelta(hours=fxx) < datetime.utcnow()-timedelta(hours=6):
    if DATE < datetime.utcnow()-timedelta(hours=12):
        # Get HRRR from Pando
        if verbose:
            print("Oh, good, you requested a date that should be on Pando.")
        grib2file = 'https://pando-rgw01.chpc.utah.edu/%s/%s/%s/%s.t%02dz.wrf%sf%02d.grib2' \
                    % (model, field,  DATE.strftime('%Y%m%d'), model, DATE.hour, field, fxx)
        fileidx = grib2file+'.idx'
    else:
        # Get operational HRRR from NOMADS
        if model == 'hrrr':
            if verbose:
                print("/n---------------------------------------------------------------------------")
                print("!! Hey! You are requesting a date that is not on the Pando archive yet.  !!")
                print("!! That's ok, I'll redirect you to the NOMADS server. :)                 !!")
                print("---------------------------------------------------------------------------\n")
            #grib2file = 'http://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.%s/%s.t%02dz.wrf%sf%02d.grib2' \
            #            % (DATE.strftime('%Y%m%d'), model, DATE.hour, field, fxx)
            grib2file = 'http://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.%s/conus/hrrr.t%02dz.wrf%sf%02d.grib2' \
                        % (DATE.strftime('%Y%m%d'), DATE.hour, field, fxx)
            fileidx = grib2file+'.idx'
        elif model == 'hrrrX':
            print("\n-------------------------------------------------------------------------")
            print("!! Sorry, I haven't download that Experimental HRRR run from ESRL yet  !!")
            print("!! Try again in a few hours.                                           !!")
            print("-------------------------------------------------------------------------\n")
            return None
        elif model == 'hrrrak':
            if verbose:
                print("/n---------------------------------------------------------------------------")
                print("!! Hey! You are requesting a date that is not on the Pando archive yet.  !!")
                print("!! That's ok, I'll redirect you to the PARALLEL NOMADS server. :)        !!")
                print("---------------------------------------------------------------------------\n")
            grib2file = 'http://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.%s/alaska/hrrr.t%02dz.wrf%sf%02d.ak.grib2' \
                        % (DATE.strftime('%Y%m%d'), DATE.hour, field, fxx)
            fileidx = grib2file+'.idx'

    if verbose:
        print('GRIB2 File: %s' % grib2file)
        print(' .idx File: %s' % fileidx)


    ## --- Download Requested Variable ----------------------------------------
    try:
        lines = requests.get(fileidx).text.split('\n')

        ## 1) Find the byte range for the requested variable. First find where
        #     in the .idx file the variable is located. We need the byte number
        #     The variable begins on. Keep a count (gcnt) of the line number so
        #     we can also get the beginning byte of the next variable. This is 
        #     our byte range.
        gcnt = 0
        for g in lines:
            expr = re.compile(get_variable)
            if expr.search(g):
                if verbose is True:
                    print(' >> Matched a variable: ', g)
                parts = g.split(':')
                rangestart = parts[1]
                if variable.split(':')[0] == 'UVGRD':
                    parts = lines[gcnt+2].split(':')      # Grab range between U and V variables
                else:
                    parts = lines[gcnt+1].split(':')      # Grab range for requested variable only
                rangeend = int(parts[1])-1
                if verbose is True:
                    print(' >> Byte Range:', rangestart, rangeend)
                byte_range = str(rangestart) + '-' + str(rangeend)
            gcnt += 1
        ## 2) When the byte range is discovered, use cURL to download the file.
        os.system('curl -s -o %s --range %s %s' % (outfile, byte_range, grib2file))
        
        
        ## --- Convert winds to earth-relative --------------------------------
        # If the requested variable is 'UVGRD:[level]', then we have to change
        # the wind direction from grid-relative to earth-relative.
        # You can still get the grid-relative winds by requesting 'UGRD:[level]'
        # and # 'VGRD:[level] independently.
        # !!! See more information on why/how to do this here:
        # https://github.com/blaylockbk/pyBKB_v2/blob/master/demos/HRRR_earthRelative_vs_gridRelative_winds.ipynb
        if variable.split(':')[0] == 'UVGRD':
            if verbose:
                print(' >> Converting winds to earth-relative')
            wgrib2 = '/uufs/chpc.utah.edu/sys/installdir/wgrib2/2.0.2/wgrib2/wgrib2'
            if model == 'hrrrak':
                regrid = 'nps:225.000000:60.000000 185.117126:1299:3000.000000 41.612949:919:3000.000000'
            if model == 'hrrr' or model == 'hrrrX':
                regrid = 'lambert:262.500000:38.500000:38.500000:38.500000 237.280472:1799:3000.000000 21.138123:1059:3000.000000'
            os.system('%s %s -new_grid_winds earth -new_grid %s %s.earth' % (wgrib2, outfile, regrid, outfile))
            os.system('rm -f %s' % outfile) # remove the original file
            outfile = outfile+'.earth'      # assign the `outfile`` as the regridded file
        

        ## 3) Get data from the file, using pygrib and return what we want to use
        grbs = pygrib.open(outfile)
        if verbose:
            print('  Run Date: %s F%02d' % (grbs[1].analDate.strftime('%Y-%m-%d %H:%M UTC'), fxx))
            print('Valid Date: %s' % grbs[1].validDate.strftime('%Y-%m-%d %H:%M UTC'))

        # Note: Returning only the variable value is a bit faster than returning 
        #       the variable value with the lat/lon and other details. You can
        #       specify this when you call the function.
        if value_only:
            if variable.split(':')[0] == 'UVGRD':
                return_this = {'UGRD': grbs[1].values,
                                'VGRD': grbs[2].values,
                                'SPEED': wind_uv_to_spd(grbs[1].values, grbs[2].values)}
            else:
                value = grbs[1].values
                if variable=='REFC:entire':
                    value = np.ma.array(value, mask=value==-10)
                elif variable=='LTNG:entire':
                    value = np.ma.array(value, mask=value==0)
                return_this = {'value': value}
            if removeFile:
                os.system('rm -f %s' % (outfile))
            return return_this
        else:
            if variable.split(':')[0] == 'UVGRD':
                value1, lat, lon = grbs[1].data()
                if model == 'hrrrak':
                    lon[lon>0] -= 360
                return_this = {'UGRD': value1,
                               'VGRD': grbs[2].values,
                               'SPEED': wind_uv_to_spd(value1, grbs[2].values),
                               'lat': lat,
                               'lon': lon,
                               'fxx': fxx,
                               'valid': grbs[1].validDate,
                               'anlys': grbs[1].analDate,
                               'msg': [str(grbs[1]), str(grbs[2])],
                               'name': [grbs[1].name, grbs[2].name],
                               'units': [grbs[1].units, grbs[2].units],
                               'level': [grbs[1].level, grbs[2].level],
                               'URL': grib2file}
            else:
                value, lat, lon = grbs[1].data()
                if variable=='REFC:entire':
                    value = np.ma.array(value, mask=value==-10)
                elif variable=='LTNG:entire':
                    value = np.ma.array(value, mask=value==0)
                if model == 'hrrrak':
                    lon[lon>0] -= 360
                return_this = {'value': value,
                               'lat': lat,
                               'lon': lon,
                               'fxx': fxx,
                               'valid': grbs[1].validDate,
                               'anlys': grbs[1].analDate,
                               'msg': str(grbs[1]),
                               'name': grbs[1].name,
                               'units': grbs[1].units,
                               'level': grbs[1].level,
                               'URL': grib2file}                
            if removeFile:
                os.system('rm -f %s' % (outfile))

            return return_this
            

    except:
        if verbose:
            print(" _______________________________________________________________")
            print(" !!   Run Date Requested :", DATE, "F%02d" % fxx )
            print(" !! Valid Date Requested :", DATE+timedelta(hours=fxx))
            print(" !!     Current UTC time :", datetime.utcnow())
            print(" !! ------------------------------------------------------------")
            print(" !! ERROR downloading GRIB2:", grib2file)
            print(" !! Is the variable right?", variable)
            print(" !! Does the .idx file exist?", fileidx)
            print(" ---------------------------------------------------------------")
        return {'value' : np.nan,
                'lat' : np.nan,
                'lon' : np.nan,
                'valid' : np.nan,
                'anlys' : np.nan,
                'msg' : np.nan,
                'URL': grib2file}


###############################################################################
###############################################################################


def get_hrrr_latlon(DICT=True):
    """
    Get the HRRR latitude and longitude grid, a file stored locally
    """
    import xarray
    data = '/uufs/chpc.utah.edu/common/home/horel-group7/Pando/hrrr/HRRR_latlon.h5'
    x = xarray.open_dataset(data)
    lat = x.latitude.data
    lon = x.longitude.data
    
    if DICT:
        return {'lat': lat,
                'lon': lon}
    else:
        return lat, lon


###############################################################################
###############################################################################

def get_hrrr_all_valid_MP(inputs):
    """
    Return a forecast for a valid time.
    Input: (validDATE, VAR, fxx, verbose)
    """
    validDATE, VAR, fxx, verbose = inputs
    return get_hrrr_variable(validDATE-timedelta(hours=fxx), VAR, fxx=fxx, value_only=True, verbose=verbose)['value']


def get_hrrr_all_valid(validDATE, variable, fxx=range(19), verbose=False):
    """
    Return a 3D array with all forecasts for a single valid time.
    This is about seven times faster than using a simple list comprehension.

    Input:
        validDATE - datetime for the valid date of interest
        variable  - HRRR variable string (e.g. 'TMP:2 m')
        fxx       - forecast hours you want to retrieve. Default 0-18.
    
    Return:
        3D array of the forecasts for the requested valid time. The first
        dimension matches the leadtime of each fxx.
    """
    inputs = [[validDATE, variable, f, verbose] for f in fxx]
    
    # Don't use more cores than needed, and don't use all available cores
    cores = np.minimum(len(range(19)), multiprocessing.cpu_count()-1)
    with multiprocessing.Pool(19) as p:
        HH = p.map(get_hrrr_all_valid_MP, inputs)
        p.close()
        p.join()
    
    # If the returned value is nan, then make an array full of nans
    for i, hh in enumerate(HH):
        if np.shape(hh) == ():
            HH[i] = np.ones([1059, 1799])*np.nan

    if type(HH[0]) == np.ma.core.MaskedArray:
        return np.ma.array(HH)
    else:
        return np.array(HH)



###############################################################################
###############################################################################


def pluck_hrrr_point(H, lat=40.771, lon=-111.965, verbose=True, XY_only=False):
    """
    Pluck the value from the nearest lat/lon location in the HRRR grid.
    
    Input:
        H       - A dictionary as returned from get_hrrr_variable()
                  NOTE: Requires the lat and lon keys in the dictionary.
        lat     - The desired latitude location you want. Default is KSLC
        lon     - The desired longitude location you want. Default is KSLC
        XY_only - False: return the valid date and the value at the point
                  True:  return the x and y value for the point
    Return:
        if H variable is UVGRD:
            [valid time, U value, V value, Speed value]
        else:
            [valid time, variable value from plucked location]        
    """
    try:
        # 1) Compute the absolute difference between the grid lat/lon and the point
        abslat = np.abs(H['lat']-lat)
        abslon = np.abs(H['lon']-lon)

        # 2) Element-wise maxima. (Plot this with pcolormesh to see what I've done.)
        c = np.maximum(abslon, abslat)

        # 3) The index of the minimum maxima (which is the nearest lat/lon)
        x, y = np.where(c == np.min(c))
        x = x[0]
        y = y[0]
        if verbose:
                print(" >> Requested Center lat: %s\t lon: %s" % (lat, lon))
                print(" >>     Plucked HRRR lat: %s\t lon: %s" % (H['lat'][x, y], H['lon'][x, y]))
                print(" >>     Plucked from   x: %s\t   y: %s" % (x, y))
        if XY_only:
            return [x, y]
        
        # 4) Value of the variable at that location
        if 'UGRD' in H:
            U_plucked = H['UGRD'][x, y]
            V_plucked = H['VGRD'][x, y]
            S_plucked = H['SPEED'][x, y]
            if verbose:
                print(" >> Plucked value (U, V, Speed): %s, %s, %s" % (U_plucked,V_plucked,S_plucked))

            return [H['valid'], U_plucked, V_plucked, S_plucked]

        else:
            plucked = H['value'][x, y]
            if verbose:
                print(" >> Plucked value: %s" % (plucked))

            # 5) Return the valid time and the plucked value
            return [H['valid'], plucked]

    except:
        if 'UGRD' in H:
            message = H['msg'][0]+'\n'+H['msg'][1]
        else:
            message = H['msg']
        print("\n------------------------------------!")
        print(" !> ERROR in pluck_hrrr_point():\n%s \nLat:%s Lon:%s" % (message, lat, lon))
        print("------------------------------------!\n")
        return [np.nan, np.nan]


def hrrr_subset(H, half_box=9, lat=40.771, lon=-111.965, thin=1, verbose=True):
    """
    Trim the HRRR data to a box around a center point.
    Very handy when you need to plot wind barbs for a smaller domain.

    Input:
        H        - A dictionary as returned from get_hrrr_variable()
        half_box - The number of gridpoints equal to half the length of the box
                   surrounding the center point.
        lat      - The center latitude
        lon      - The center longitude
        thin     - Thin out the values (set to 2 for every other value)
    Return:
        A dictionary of the values and lat/lon grids for the subset.
        If H variable is UVGRD, then output separate key for U, V, and SPEED.
    """
    x, y = pluck_hrrr_point(H, lat=lat, lon=lon, verbose=verbose, XY_only=True)

    if 'UGRD' in H:
        subset = {'lat': H['lat'][x-half_box:x+half_box, y-half_box:y+half_box][::thin,::thin],
                  'lon': H['lon'][x-half_box:x+half_box, y-half_box:y+half_box][::thin,::thin],
                  'UGRD': H['UGRD'][x-half_box:x+half_box, y-half_box:y+half_box][::thin,::thin],
                  'VGRD': H['VGRD'][x-half_box:x+half_box, y-half_box:y+half_box][::thin,::thin],
                  'SPEED': H['SPEED'][x-half_box:x+half_box, y-half_box:y+half_box][::thin,::thin],                
                  'x': x,
                  'y': y}
    else:
        subset = {'lat': H['lat'][x-half_box:x+half_box, y-half_box:y+half_box][::thin,::thin],
                  'lon': H['lon'][x-half_box:x+half_box, y-half_box:y+half_box][::thin,::thin],
                  'value': H['value'][x-half_box:x+half_box, y-half_box:y+half_box][::thin,::thin],
                  'x': x,
                  'y': y}
    if verbose:
        print(' >> Size of subset: %s x %s grid points' % np.shape(subset['lat']))

    return subset


def hrrr_area_stats(H, half_box=5, lat=40.771, lon=-111.965, verbose=True):
    """
    Calculated statistics for a subset of the model domain.

    Input:
        H        - A dictionary returned from get_hrrr_variable()
        half_box - The number of grid boxes to +/- from the center lat/lon.
                   For the HRRR model, 5 represents a 30km x 30km box.
                   5 is the number of grids in each direction from the center
                   point, a 10 x 10 grid box, and multiplied by 3km for the
                   size of each grid box.
        lat      - The center latitude of the box. Default is KSLC
        lon      - The center longitude of the box. Default is KSLC
    
    Return:
        Dictionary of the stats around the point for the subset.
        If H variable is UVGRD, then returns a tuple for (U, V, SPEED)
    """
    
    if type(H['valid']) == datetime:    
    
        if verbose is True:
            print(" >> Half_box is set to %s. Your box will be %s-km2." % (half_box, half_box*2*3))
        
        box = hrrr_subset(H, half_box=half_box, lat=lat, lon=lon, verbose=verbose)

        if 'UGRD' in H:
            U_p = np.percentile(box['UGRD'], [1, 5, 10, 90, 95, 99])
            V_p = np.percentile(box['VGRD'], [1, 5, 10, 90, 95, 99])
            S_p = np.percentile(box['SPEED'], [1, 5, 10, 90, 95, 99])
            return_this = {'half box': half_box,
                           'requested center': (lat, lon),
                           'valid': H['valid'],
                           'box center value': (H['UGRD'][box['x'],box['y']], H['VGRD'][box['x'],box['y']], H['SPEED'][box['x'],box['y']]),
                           'min': (np.nanmin(box['UGRD']), np.nanmin(box['VGRD']), np.nanmin(box['SPEED'])), 
                           'p1': (U_p[0],V_p[0],S_p[0]),
                           'p5': (U_p[1],V_p[1],S_p[1]),
                           'p10': (U_p[2],V_p[2],S_p[2]),
                           'mean': (np.nanmean(box['UGRD']), np.nanmean(box['VGRD']), np.nanmean(box['SPEED'])), 
                           'p90': (U_p[3],V_p[3],S_p[3]),
                           'p95': (U_p[4],V_p[4],S_p[4]),
                           'p99': (U_p[5],V_p[5],S_p[5]),
                           'max': (np.nanmax(box['UGRD']), np.nanmax(box['VGRD']), np.nanmax(box['SPEED'])), 
                           'lat': box['lat'],
                           'lon': box['lon']
                           }
        else:
            p = np.percentile(box['value'], [1, 5, 10, 90, 95, 99])
            return_this = {'half box': half_box,
                           'requested center': [lat, lon],
                           'valid': H['valid'],
                           'box center value': H['value'][box['x'],box['y']],
                           'min': np.nanmin(box['value']),
                           'p1': p[0],
                           'p5': p[1],
                           'p10': p[2],
                           'mean': np.nanmean(box['value']),
                           'p90': p[3],
                           'p95': p[4],
                           'p99': p[5],
                           'max': np.nanmax(box['value']),
                           'lat': box['lat'],
                           'lon': box['lon']
                           }
        return return_this
    
    else:
        if verbose:
            print("\n------------------------------------!")
            print(" !> ERROR <! ERROR in hrrr_area_stats. Returning nan values.")
            print("------------------------------------!\n")
        return {'half box': half_box,
                'requested center': [lat, lon],
                'valid':np.nan,
                'box center value':np.nan,
                'min':np.nan,
                'p1':np.nan,
                'p5':np.nan,
                'p10':np.nan,
                'mean':np.nan,
                'p90':np.nan,
                'p95':np.nan,
                'p99':np.nan,
                'max':np.nan
               }


###############################################################################
### FUNCTIONS FOR MULTIPROCESSING #############################################

def pluck_point_MultiPro(multi_vars):
    """
    Use multiprocessing to pluck a single point from many HRRR grids
    """
    DATE = multi_vars[0]
    VAR = multi_vars[1]
    LAT = multi_vars[2]
    LON = multi_vars[3]
    FXX = multi_vars[4]
    MODEL = multi_vars[5]
    FIELD = multi_vars[6]
    VERBOSE = multi_vars[7]
    
    if VERBOSE == True:
        print('>>Pluck Points MultiPro: Working on', multi_vars)
    
    H = get_hrrr_variable(DATE, VAR, fxx=FXX, model=MODEL, field=FIELD, verbose=VERBOSE)
    return_this = pluck_hrrr_point(H, lat=LAT, lon=LON, verbose=VERBOSE)
    del H # does this help prevent multiprocessing from hanging??
    
    return return_this


def pluck_LocDic_MultiPro(multi_vars):
    """
    Use multiprocessing to pluck a point from many HRRR grids for all 
    locations in a location dictionary.
    """
    DATE = multi_vars[0]
    LOC_DIC = multi_vars[1]
    VAR = multi_vars[2]
    FXX = multi_vars[3]
    MODEL = multi_vars[4]
    FIELD = multi_vars[5]
    STATS = multi_vars[6]
    VERBOSE = multi_vars[7]
    
    if VERBOSE == True:
        print(' >> Pluck LocDic MultiPro: Working on', multi_vars)
        
    return_this = {'DATETIME':DATE}


    # Download the HRRR field once, and pluck values from it at all locations
    H = get_hrrr_variable(DATE, VAR, fxx=FXX, model=MODEL, field=FIELD, verbose=VERBOSE)
    
    if type(H['valid']) == datetime:
        for l in LOC_DIC.keys():
            if STATS != False:
                # Store all the area statistics
                return_this[l] = hrrr_area_stats(H, half_box=STATS, lat=LOC_DIC[l]['latitude'], lon=LOC_DIC[l]['longitude'], verbose=VERBOSE)
            else:
                # Only store the value, and not the date
                if 'UGRD' in H:
                    return_this[l] = pluck_hrrr_point(H, LOC_DIC[l]['latitude'], LOC_DIC[l]['longitude'], verbose=VERBOSE)[1:]       
                else:
                    return_this[l] = pluck_hrrr_point(H, LOC_DIC[l]['latitude'], LOC_DIC[l]['longitude'], verbose=VERBOSE)[1]       
        del H # does this help prevent multiprocessing from hanging??
        return return_this
    else:
        VALID_TIME = DATE+timedelta(hours=FXX)
        for l in LOC_DIC.keys():
            if STATS != False:
                return_this[l] = hrrr_area_stats(H, half_box=STATS, lat=LOC_DIC[l]['latitude'], lon=LOC_DIC[l]['longitude'], verbose=VERBOSE)
            else:
                if 'UVGRD' in VAR:
                    return_this[l] = [np.nan, np.nan, np.nan]
                else:
                    return_this[l] = np.nan
        return return_this


###############################################################################
### Point and LocDic Functions ################################################

def point_hrrr_time_series(sDATE, eDATE,
                           variable='TMP:2 m',
                           lat=40.771, lon=-111.965,
                           fxx=0, model='hrrr', field='sfc',
                           verbose=True,
                           reduce_CPUs=2):
    """
    Produce a time series of HRRR data at a point for a specified variable
    at a lat/lon location. Use multiprocessing to speed this up :)
    
    Input:
        sDATE       - Valid time Start datetime
        eDATE       - Valid time End datetime
        variable    - The desired variable string from a line in the .idx file.
        lat         - Latitude of the point. Default is KSLC.
        lon         - Longitude of the point. Default is KSLC.
        fxx         - Forecast lead time for the time series, in hours.
                      Default is the model analysis, or F00. fxx=18 would make
                      a time series of all 18-hr forecasts.
        model       - Model type. Choose one: ['hrrr', 'hrrrX', 'hrrrAK']
        field       - Field type. Choose one: ['sfc', 'prs']
        reduce_CPUs - Limit multiprocessing CPUs. Default is to use all except 2.
    
    Return:
        A tuple of the valid datetime and the point value for each datetime.
    """

    ## 1) Create a range of dates and inputs for multiprocessing the
    #     get_hrrr_variable() and pluck_point_MultiPro(). Adjust the requested
    #     valid datetime to the model run datetime
    RUN_sDATE = sDATE - timedelta(hours=fxx)
    
    if model == 'hrrrak' and RUN_sDATE not in range(0,24,3):
        print(" >> HRRR Alaska not run for hour %s. Finding previous run." % RUN_sDATE.hour,)
        while RUN_sDATE.hour not in range(0,24,3):
            RUN_sDATE -= timedelta(hours=1)
        print(" Found hour %s." % RUN_sDATE)
    
    hours = int((eDATE-sDATE).days * 24 + (eDATE-sDATE).seconds / 3600)
    if model == 'hrrrak':
        RUN_DATES = np.array([RUN_sDATE + timedelta(hours=x) for x in range(0, hours, 3)])
        VALID_DATES = np.array([sDATE + timedelta(hours=x) for x in range(0, hours, 3)])
    else:
        RUN_DATES = np.array([RUN_sDATE + timedelta(hours=x) for x in range(0, hours)])
        VALID_DATES = np.array([sDATE + timedelta(hours=x) for x in range(0, hours)])
    multi_vars = [[d, variable, lat, lon, fxx, model, field, verbose] for d in RUN_DATES]

    ## 2) Use multiprocessing to get the plucked values from each map.
    cpu_count = multiprocessing.cpu_count() - reduce_CPUs
    p = multiprocessing.Pool(cpu_count)
    timer = datetime.now()
    ValidValue = np.array(p.map(pluck_point_MultiPro, multi_vars))
    p.close()
    print("Time Series F%02d: Finished with multiprocessing in %s on %s processors." % (fxx, datetime.now()-timer, cpu_count))

    if 'UVGRD' in variable:
        U = ValidValue[:, 1] # Second item is U component
        V = ValidValue[:, 2] # Third item is V component
        S = ValidValue[:, 3] # Fourth item is Wind Speed
        return [VALID_DATES, U, V, S]
    else:
        value = ValidValue[:, 1] # Second item is the value at that datetime
        return [VALID_DATES, value]


def LocDic_hrrr_time_series(sDATE, eDATE, location_dic,
                            variable='TMP:2 m',
                            fxx=0, model='hrrr', field='sfc',
                            area_stats=False,
                            reduce_CPUs=2,
                            verbose=True):
    """
    Produce a time series of HRRR data for a specified variable at multiple
    lat/lon locations. Use multiprocessing to speed this up :)
    
    Input:
        sDATE        - Valid time Start datetime
        eDATE        - Valid time End datetime
        location_dic - A dictionary of a locations lat/lon in the form:
                       LocDoc = {'name':{'latitude':xxx, 'longitude':xxx}}
        variable     - The desired variable string from a line in the .idx file.
        fxx          - Forecast lead time for the time series, in hours.
                       Default is the model analysis, or F00. fxx=18 would make
                       a time series of all 18-hr forecasts.
        model        - Model type. Choose one: ['hrrr', 'hrrrX', 'hrrrAK']
        field        - Field type. Choose one: ['sfc', 'prs']
        area_stats   - False: Does not return area statistics. (default)
                       integer: Returns statistics around a point. The integer
                       set here represents the half_box around the location.
                       The number will be the number of grid points to +/- from
                       the location lat/lon point.
        reduce_CPUs  - Limit multiprocessing CPUs. Default is to use all except 2.
    
    Output:
        A dictionary for the valid time and a time series at each of the
        locations.
    """

    # 1) Create a range of dates
    RUN_sDATE = sDATE - timedelta(hours=fxx)
    
    if model == 'hrrrak' and RUN_sDATE not in range(0,24,3):
        print(" >> HRRR Alaska not run for hour %s. Finding previous run." % RUN_sDATE.hour,)
        while RUN_sDATE.hour not in range(0,24,3):
            RUN_sDATE -= timedelta(hours=1)
        print(" Found hour %s." % RUN_sDATE)
    
    hours = int((eDATE-sDATE).days * 24 + (eDATE-sDATE).seconds / 3600)
    if model == 'hrrrak':
        RUN_DATES = np.array([RUN_sDATE + timedelta(hours=x) for x in range(0, hours, 3)])
        VALID_DATES = np.array([sDATE + timedelta(hours=x) for x in range(0, hours, 3)])
    else:
        RUN_DATES = np.array([RUN_sDATE + timedelta(hours=x) for x in range(0, hours)])
        VALID_DATES = np.array([sDATE + timedelta(hours=x) for x in range(0, hours)])

    # 2) Initialize dictionary to store data for the valid dates. Each location
    #    name will also be a key.
    return_this = {'DATETIME':VALID_DATES}
    for l in location_dic:
        return_this[l] = np.array([])

    # 3) Create inputs list for multiprocessing used for get_hrrr_variable() and pluck_hrrr_point().
    multi_vars = [[d, location_dic, variable, fxx, model, field, area_stats, verbose] for d in RUN_DATES]

    # 4) Use multiprocessing to get the plucked values from each map.
    cpu_count = multiprocessing.cpu_count() - reduce_CPUs
    p = multiprocessing.Pool(cpu_count)
    timer = datetime.now()
    ValidValue = np.array(p.map(pluck_LocDic_MultiPro, multi_vars))
    p.close()
    print("LocDic Time Series F%02d: Finished multiprocessing in %s on %s processors" % (fxx, datetime.now()-timer, cpu_count))

    # REPACKAGE THE RETURNED VALUES FROM MULTIPROCESSING so that each key value
    # is the station name, and contains the time series for that station.
    for l in location_dic:
        num = range(len(ValidValue))
        if area_stats is False:
            return_this[l] = np.array([ValidValue[i][l] for i in num])
        else:
            try:
                return_this[l] = {'valid':np.array([ValidValue[i][l]['valid'] for i in num]),
                              'min':np.array([ValidValue[i][l]['min'] for i in num]),
                              'p1':np.array([ValidValue[i][l]['p1'] for i in num]),
                              'p5':np.array([ValidValue[i][l]['p5'] for i in num]),
                              'p10':np.array([ValidValue[i][l]['p10'] for i in num]),
                              'mean':np.array([ValidValue[i][l]['mean'] for i in num]),
                              'p90':np.array([ValidValue[i][l]['p90'] for i in num]),
                              'p95':np.array([ValidValue[i][l]['p95'] for i in num]),
                              'p99':np.array([ValidValue[i][l]['p99'] for i in num]),
                              'max':np.array([ValidValue[i][l]['max'] for i in num]),
                              'box center value':np.array([ValidValue[i][l]['box center value'] for i in num])
                             }
            except:
                return ValidValue
    return return_this


def point_hrrr_pollywog(DATE, variable,
                        lat=40.771, lon=-111.965,
                        forecasts=range(19),
                        model='hrrr', field='sfc',
                        reduce_CPUs=2,
                        verbose=True):
    """
    Returns a variable's value for each hour in a single HRRR model run
    initialized from a specific time at a specified lat/lon point in the domain.
    Use multiprocessing to speed this up :)

    John Horel named these pollywogs because when you plot the series of a 
    forecast variable with the analysis (F00) hour being a circle, the lines
    look like pollywogs.   O----

    input:
        DATE           - Datetime for the pollywog head or HRRR anlaysis (F00)
        variable       - The name of the variable in the HRRR .idx file
        lat            - Latitude of the point of interest. Default is KSLC.
        lon            - Longitude of the point of interest. Default is KSLC.
        forecasts      - A list of forecast hours you want.
        model          - Model type. Choose one: ['hrrr', 'hrrrX', 'hrrrAK']
        field          - Field type. Choose one: ['sfc', 'prs']
        reduce_CPUs    - Limit multiprocessing CPUs. Default is to use all except 2.

    output:
        Two vectors for the forecast data [valid date, pollywog vector]
    """

    # Use multiprocessing to pluck values at each forecast hour
    multi_vars = [[DATE, variable, lat, lon, f, model, field, verbose] for f in forecasts]

    cpu_count = multiprocessing.cpu_count() - reduce_CPUs
    p = multiprocessing.Pool(cpu_count)
    timer = datetime.now()
    ValidValue = np.array(p.map(pluck_point_MultiPro, multi_vars))
    p.close()
    print("Point Pollywog: Finished with multiprocessing in %s on %s processors." % (datetime.now()-timer, cpu_count))

    
    valid = ValidValue[:, 0] # First item is the valid datetime

    if 'UVGRD' in variable:
        U = ValidValue[:, 1] # Second item is U component
        V = ValidValue[:, 2] # Third item is V component
        S = ValidValue[:, 3] # Fourth item is Wind Speed
        return [valid, U, V, S]
    else:
        value = ValidValue[:, 1] # Second item is the value at that datetime
        return [valid, value]
    

def LocDic_hrrr_pollywog(DATE, variable, location_dic,
                         forecasts=range(19),
                         model='hrrr', field='sfc',
                         area_stats=False,
                         reduce_CPUs=2,
                         verbose=True):
    """
    Returns a variable's value for each hour in a single HRRR model run
    initialized from a specific time at a specified lat/lon point in the
    domain for multiple locations.

    Input:
        DATE           - Datetime for the pollywog head or HRRR anlaysis (F00)
        variable       - The name of the variable in the HRRR .idx file
        location_dic   - A dictionary of a locations lat/lon in the form:
                         LocDoc = {'name':{'latitude':xxx, 'longitude':xxx}}
        forecasts      - A list of forecast hours you want.
        model          - Model type. Choose one: ['hrrr', 'hrrrX', 'hrrrAK']
        field          - Field type. Choose one: ['sfc', 'prs']
        area_stats     - False: Does not return area statistics. (default)
                         integer: Returns statistics around a point. The integer
                         set here represents the half_box around the location.
                         The number will be the number of grid points to +/- from
                         the location lat/lon point.
        reduce_CPUs    - Limit multiprocessing CPUs. Default is to use all except 2.

    Output:
        A dictionary for the valid time and pollywog at each of the locations.
    """
  
    # 1) Create a vector of Valid Dates
    VALID_DATES = np.array([DATE + timedelta(hours=x) for x in forecasts])

    # 2) Initialize dictionary to store data for the valid dates. Each location
    #    name will also be a key.
    return_this = {'DATETIME':VALID_DATES}
    for l in location_dic:
        return_this[l] = np.array([])

    # 3) Use multiprocessing to get the plucked values from each forecast.
    multi_vars = [[DATE, location_dic, variable, f, model, field, area_stats, verbose] for f in forecasts]

    cpu_count = multiprocessing.cpu_count() - reduce_CPUs
    p = multiprocessing.Pool(cpu_count)
    timer = datetime.now()
    ValidValue = np.array(p.map(pluck_LocDic_MultiPro, multi_vars))
    p.close()
    print("LocDic Pollywog: Finished multiprocessing in %s on %s processors" % (datetime.now()-timer, cpu_count))

    # REPACKAGE THE RETURNED VALUES FROM MULTIPROCESSING so that each key value
    # is the station name, and contains the time series for that station.
    for l in location_dic:
        num = range(len(ValidValue))
        if area_stats is False:
            return_this[l] = np.array([ValidValue[i][l] for i in num])
        else:
            return_this[l] = {'valid':np.array([ValidValue[i][l]['valid'] for i in num]),
                              'min':np.array([ValidValue[i][l]['min'] for i in num]),
                              'p1':np.array([ValidValue[i][l]['p1'] for i in num]),
                              'p5':np.array([ValidValue[i][l]['p5'] for i in num]),
                              'p10':np.array([ValidValue[i][l]['p10'] for i in num]),
                              'mean':np.array([ValidValue[i][l]['mean'] for i in num]),
                              'p90':np.array([ValidValue[i][l]['p90'] for i in num]),
                              'p95':np.array([ValidValue[i][l]['p95'] for i in num]),
                              'p99':np.array([ValidValue[i][l]['p99'] for i in num]),
                              'max':np.array([ValidValue[i][l]['max'] for i in num]),
                              'box center value':np.array([ValidValue[i][l]['box center value'] for i in num])
                             }
    return return_this


def LocDic_hrrr_hovmoller(sDATE, eDATE, location_dic,
                          variable='TMP:2 m',
                          forecasts=range(19),
                          area_stats=False,
                          reduce_CPUs=2,
                          verbose=True):
    """
    A "HRRR Hovmoller" is an array of all model forecasts for each valid time.
    I plot the HRRR forecast hour on the y-axis increasing from f00-f18, then 
    I plot the valid time on the x-axis across the bottom. This type of graph
    shows how the forecasts change over time.

    sDATE          - Valid time Start datetime
    eDATE          - Valid time End datetime
    variable       - The name of the variable in the HRRR .idx file
    location_dic   - A dictionary of a locations lat/lon in the form:
                     LocDoc = {'name':{'latitude':xxx, 'longitude':xxx}}
    forecasts      - A list of forecast hours you want.
    area_stats     - False: Does not return area statistics. (default)
                     integer: Returns statistics around a point. The integer
                     set here represents the half_box around the location.
                     The number will be the number of grid points to +/- from
                     the location lat/lon point.
    reduce_CPUs    - Limit multiprocessing CPUs. Default is to use all except 2.

    Output:
        Returns a 2D array
    """

    data = {}
    for f in forecasts:
        data[f] = LocDic_hrrr_time_series(sDATE, eDATE, location_dic,
                                          variable=variable,
                                          fxx=f,
                                          verbose=False,
                                          field='sfc',
                                          area_stats=area_stats,
                                          reduce_CPUs=reduce_CPUs)

    # Number of observations (hours in the time series)
    num = len(data[0]['DATETIME'])
    dates = data[0]['DATETIME']

    # Organize into Hovmoller array
    # matplotlib.pyplot.confourf requires a 2d array of the dates/fxx to plot
    # matplotlib.pyplot.pcolormesh requers a 1d array of the dates/fxx with size +1 for the limits
    #                              (otherwise it'll cut off the last row and column)
    hovmoller = {'fxx_2d':np.array([np.ones(num)*i for i in forecasts]),
                 'valid_2d':np.array([data[0]['DATETIME'] for i in forecasts]),
                 'fxx_1d+':list(forecasts)+[forecasts[-1]+1],
                 'valid_1d+':np.append(dates, dates[-1]+timedelta(hours=1))}

    if area_stats is False:
        # Returns a dictionary like hovmoller['WBB'] = 2D array
        for l in location_dic:
            hovmoller[l] = np.array([data[i][l] for i in forecasts])

    else:
        # NEED To repackage the statistical data with an extra layer
        # i.e. >> hovmoller[station id][area statistic]
        # i.e. >> hovmoller['WBB']['max'] = 2D array
        for l in location_dic:
            hovmoller[l] = {}
            for s in data[0][l]:
                hovmoller[l][s] = np.array([data[i][l][s] for i in forecasts])

    return hovmoller


###############################################################################
###############################################################################
###############################################################################

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from mpl_toolkits.basemap import Basemap

    m = Basemap(lon_0=-100)
    m.drawcoastlines()

    AK = get_hrrr_variable(datetime(2018, 2, 24, 15), 'TMP:2 m', fxx=0, model='hrrrak')
    H = get_hrrr_variable(datetime(2018, 2, 24, 15), 'TMP:2 m', fxx=0, model='hrrr')

    m.pcolormesh(AK['lon'], AK['lat'], AK['value'], latlon=True, vmax=310, vmin=210)
    m.pcolormesh(H['lon'], H['lat'], H['value'], latlon=True, vmax=310, vmin=210)
    plt.colorbar()
    plt.show()
