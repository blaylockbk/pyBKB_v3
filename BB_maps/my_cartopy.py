# Brian Blaylock
# June 29, 2018

"""
Custom map set-up for Cartopy

Some notes: There are issues with plotting boundaries
- The standard COASTLINE and STATES makes a funny cut out of the Columiba River
- County boundaries are not included in cartopy. The Census Bureau shapefile is
  high enough resolution that it doesn't match up with COASTLINES and STATES.
- The Great Salt Lake boundary is wrong. It looked better in Basemap.
"""

import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.io.shapereader import Reader

def load_states(projection, resolution='500k'):
    """
    State Shapefiles from the Census Bureao (2017)
    https://www.census.gov/geo/maps-data/data/cbf/cbf_state.html

    projection - The cartopy map projection
    resolution - '500k' is the highest resolution (default)
                 '5m'
                 '20m' is the lowest resolution
    """
    source = 'C:\\Users\\blaylockbk\\OneDrive\\Documents\\pyBKB_v3\\BB_maps\\shapefiles\\cb_2017_us_state_%s\\cb_2017_us_state_%s.shp' % (resolution, resolution)
    return cfeature.ShapelyFeature(Reader(source).geometries(),
                                   projection, facecolor='none')


def load_counties(projection, resolution='500k'):
    """
    County Shapefiles from the Census Bureao (2017)
    https://www.census.gov/geo/maps-data/data/cbf/cbf_state.html

    projection - The cartopy map projection
    resolution - '500k' is the highest resolution (default)
                 '5m'
                 '20m' is the lowest resolution
    """
    source = 'C:\\Users\\blaylockbk\\OneDrive\\Documents\\pyBKB_v3\\BB_maps\\shapefiles\\cb_2017_us_county_%s\\cb_2017_us_county_%s.shp' % (resolution, resolution)
    return cfeature.ShapelyFeature(Reader(source).geometries(),
                                   projection, facecolor='none')

