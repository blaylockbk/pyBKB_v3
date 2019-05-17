# Brian Blaylock
# July 3, 2018                       # 155 years since the battle at Gettysburg

"""
Return Basemaps for domains I regularly use.

Can define the resolution of the map with resolution argument:
    'c' - crude
    'l' - low
    'i' - intermediate
    'h' - high
    'f' - full

Note: Basemap is no longer supported. I Should lean more towards Cartopy, but 
Basemap is so handy!
"""

from mpl_toolkits.basemap import Basemap
import numpy as np
import os

## Abbreviated State Names
all_states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', \
              'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', \
              'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', \
              'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', \
              'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']


def draw_centermap(center, size=(3,3), resolution='i', area_thresh=2000):
    """
    Draw a square map given a center.
    input:
        center - A tuple for latitude and longitude, i.e. (42, -110.5)
                 A MesoWest Station ID, i.e. 'KSLC'
                 A state name, i.e. 'Utah'
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

    return Basemap(projection='cyl', resolution=resolution, area_thresh=area_thresh,
                   llcrnrlon=lon-size[1], llcrnrlat=lat-size[0],
                   urcrnrlon=lon+size[1], urcrnrlat=lat+size[0])

def draw_CONUS_cyl_map(resolution='i', area_thresh=2000):
    """
    Draw the United States in cylindrical coordinates.
    """
    bot_left_lat  = 22
    bot_left_lon  = -127
    top_right_lat = 53
    top_right_lon = -65
    #
    return Basemap(projection='cyl', resolution=resolution, area_thresh=area_thresh,
                   llcrnrlon=bot_left_lon, llcrnrlat=bot_left_lat,
                   urcrnrlon=top_right_lon, urcrnrlat=top_right_lat)


def draw_HRRR_map(resolution='i', area_thresh=2000):
    """
    Draw the Continental United States HRRR Domain with lambert conformal
    projection.
    Map specifications are from the HRRR's namelist.wps file:
    https://rapidrefresh.noaa.gov/hrrr/HRRR/static/HRRRv1/namelist.wps
    """
    FILE = '/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3/BB_maps/saved_map_objects/HRRR_lcc_%s_%s.npy' % (resolution, area_thresh)
    if os.path.exists(FILE):
        m = np.load(FILE).item()
        print('loaded %s map from file' % FILE)
    else:
        m = Basemap(projection='lcc', resolution=resolution, area_thresh=area_thresh,
                    width=1800*3000, height=1060*3000,
                    lat_1=38.5, lat_2=38.5,
                    lat_0=38.5, lon_0=-97.5)
        # Save the map object for later use
        np.save(FILE, m)
        print('saved %s map to file' % FILE)
    ## Store map object in location dictionary
    return m


def draw_ALASKA_map(resolution='i', area_thresh=3000):
    """
    Draw a map of Alaska
    """
    bot_left_lat  = 40
    bot_left_lon  = -205
    top_right_lat = 80
    top_right_lon = -115
    return Basemap(projection='cyl', resolution=resolution, area_thresh=area_thresh,
                   llcrnrlon=bot_left_lon, llcrnrlat=bot_left_lat,
                   urcrnrlon=top_right_lon, urcrnrlat=top_right_lat)


def draw_GOES_East_geo(resolution='i', area_thresh=3000):
    """
    Draw GOES-16 East geostationary projection
    # See this: https://github.com/blaylockbk/pyBKB_v3/issues/1
    """
    print('WARNING: you will get better lines if you plot with Cartopy.'
          'See this: https://github.com/blaylockbk/pyBKB_v3/issues/1')
    return Basemap(projection='geos', lon_0=-75.0,
                   resolution=resolution, area_thresh=area_thresh,
                   llcrnrx=-3626269.5, llcrnry=1584175.9,
                   urcrnrx=1381770.0, urcrnry=4588198.0)

def draw_GLM_map(resolution='i', area_thresh=3000):
    return Basemap(resolution=resolution, area_thresh=area_thresh,
                   llcrnrlon=-134, llcrnrlat=-57,
                   urcrnrlon=-14, urcrnrlat=57)