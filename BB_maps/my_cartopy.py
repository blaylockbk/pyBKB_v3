# Brian Blaylock
# June 29, 2018

"""
Custom map set-up for Cartopy

Notes: There are issues with plotting boundaries
- The standard COASTLINE and STATES makes a funny cut out of the Columbia River
- County boundaries are not included in cartopy. The Census Bureau shapefile is
  high enough resolution that it doesn't match up with COASTLINES and STATES.
- The Great Salt Lake boundary is wrong. It looked better in Basemap.

proj_HRRR
proj_GOES16

extent_centermap()
add_NEXRAD()

arcgisimage()

load_states
load_counties
"""

import numpy as np

import platform

import cartopy.crs as ccrs                # Cartopy Coordinate Reference System
import cartopy.feature as cfeature
from cartopy.io.shapereader import Reader
import cartopy.io.img_tiles as cimgt      # For reading tiles form web services


## Abbreviated State Names
all_states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', \
              'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', \
              'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', \
              'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', \
              'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

# Plate Carree coordinate system for Latitude/Longitude values. I use this so
# so just import it, i.e. `from BB_maps.my_cartopy import pc`
pc = ccrs.PlateCarree()


def extent_HRRR(ax):
    """
    This is a manual hack because I can't figure out how cartopy's set_extent
    function works!!! 😢
    """
    
    ax1.set_extent([-124.1, -71.1, 24.2, 50.5], crs=pc)
    


def extend_Utah(ax):
    ax.set_extent([-114.75, 108.25, 36, 43], crs=pc)


def proj_HRRR():
    """The High-Resolution Rapid Refresh model projection"""
    lccProjParams_HRRR = {'central_latitude'   : -38.5,        # same as lat_0
                          'central_longitude'  : -97.5,        # same as lon_0
                          'standard_parallels' : (38.5, 38.5)} # same as (lat_1, lat_2)
    return ccrs.LambertConformal(**lccProjParams_HRRR)

def proj_GOES16():
    geostationaryProjParams_GOES16 = {'central_longitude' : -75.0,
                                      'satellite_height' : 35786023.0,
                                      'sweep_axis' : 'x'}
    return ccrs.Geostationary(**geostationaryProjParams_GOES16)

## === Set extent =============================================================
## ============================================================================
def extent_centermap(ax, center, size=(3,3)):
    """
    Set extent as a square map over a center location
    input:
        center - A tuple for latitude and longitude, i.e. (42, -110.5)
                 or A MesoWest Station ID, i.e. 'KSLC'
                 or A state name, i.e. 'Utah'
        size   - A tuple for the distance between the center location and how
                 far left/right/up/down you want the map to display
    """

    if type(center) == tuple:
        lat, lon = center
    else:
        # Read in list of states
        states = np.genfromtxt('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3/BB_maps/data/states_latlon.csv', names=True, delimiter=',', dtype=None, encoding='UTF-8')
        if center.upper() in np.char.upper(states['State']):
            state_idx = np.argwhere(states['State'] == center)[0][0]
            STATE, lat, lon = states[state_idx]
        else:
            # Maybe it is a MesoWest station ID
            from BB_MesoWest.get_MesoWest import get_mesowest_stninfo
            a = get_mesowest_stninfo(center)
            if a != 'ERROR':
                lat, lon = a[center]['latitude'], a[center]['longitude']
            else:
                print('I am sorry. I do not under stand your request')
                print('Input must be a (lat,lon) tuple, a state like "Utah", or a MesoWest ID')

    ax.set_extent([lon-size[1], lon+size[1], lat-size[0], lat+size[0]])


## === Add CONUS NEXRAD .png from Iowa State ==================================
## ============================================================================

def add_NEXRAD(ax, DATE='mostRecent', version='n0q'):
    """
    Add NEXRAD mosaic composite reflectivity .png image to a cartopy axis. 
    Data is from Iowa Environmental Mesonet:
        
        https://mesonet.agron.iastate.edu/docs/nexrad_composites/

    Input:
        ax      - the figure axis
        DATE    - the datetime (UTC) you wish to retrieve. Default is the most
                  recent image.
        version - 'n0r' Base reflectivity at 5 dbz resolution (depreciated??)
                  'n0q' Base reflectivity at 0.5 dbz resolution 
    """
    assert version in ['n0q', 'n0r'], "version argument must be 'n0q' or 'n0r'."

    if DATE == 'mostRecent':
        ax.add_wms(wms='https://mesonet.agron.iastate.edu/cgi-bin/wms/nexrad/%s-t.cgi?' % version,
                   layers='nexrad-%s-wmst' % version)
    else:
        strDATE = DATE.strftime('%Y-%m-%dT%H:%M:%SZ')
        ax.add_wms(wms='https://mesonet.agron.iastate.edu/cgi-bin/wms/nexrad/%s-t.cgi?' % version,
                   layers='nexrad-%s-wmst' % version,
                   wms_kwargs={'time':strDATE})

## === arcgisimage ============================================================
## ============================================================================
def arcgisimage(ax, service="World_Shaded_Relief", zoom=1):
    """
    Duplicate the functionality of Basemap `arcgisimage()` function.
    
    My favorite background is the "World_Shaded_Relief"
    """
    url = 'https://server.arcgisonline.com/ArcGIS/rest/services/' \
          '%s/MapServer/tile/{z}/{y}/{x}.jpg' % service
    
    image = cimgt.GoogleTiles(url=url)
    ax.add_image(image, zoom)


##=============================================================================
##=============================================================================

def load_states(projection, resolution='500k'):
    """
    State Shapefiles from the Census Bureau (2017)
    https://www.census.gov/geo/maps-data/data/cbf/cbf_state.html

    projection - The cartopy map projection
    resolution - '500k' is the highest resolution (default)
                 '5m'
                 '20m' is the lowest resolution
    """
    if platform.system() == 'Linux':
        source = '/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3/BB_maps/shapefiles/cb_2017_us_state_%s/cb_2017_us_state_%s.shp' % (resolution, resolution)
    else:
        source = 'C:\\Users\\blaylockbk\\OneDrive\\Documents\\pyBKB_v3\\BB_maps\\shapefiles\\cb_2017_us_state_%s\\cb_2017_us_state_%s.shp' % (resolution, resolution)
    return cfeature.ShapelyFeature(Reader(source).geometries(),
                                   projection, facecolor='none')


def load_counties(projection, resolution='500k'):
    """
    County Shapefiles from the Census Bureau (2017)
    https://www.census.gov/geo/maps-data/data/cbf/cbf_state.html

    projection - The cartopy map projection
    resolution - '500k' is the highest resolution (default)
                 '5m'
                 '20m' is the lowest resolution
    """
    if platform.system() == 'Linux':
        source = '/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3/BB_maps/shapefiles/cb_2017_us_county_%s/cb_2017_us_county_%s.shp' % (resolution, resolution)
    else:
        source = 'C:\\Users\\blaylockbk\\OneDrive\\Documents\\pyBKB_v3\\BB_maps\\shapefiles\\cb_2017_us_county_%s\\cb_2017_us_county_%s.shp' % (resolution, resolution)
    return cfeature.ShapelyFeature(Reader(source).geometries(),
                                   projection, facecolor='none')

