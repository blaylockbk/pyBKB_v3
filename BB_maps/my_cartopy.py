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

load_states
load_counties
"""

import platform
import cartopy.crs as ccrs # Cartopy Coordinate Reference System
import cartopy.feature as cfeature
from cartopy.io.shapereader import Reader

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

