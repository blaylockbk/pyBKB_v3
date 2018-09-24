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

Note: Basemap is no longer supported
"""

from mpl_toolkits.basemap import Basemap

def draw_centermap(lat, lon, size=(3,3), resolution='i', area_thresh=2000):
    """
    Draw a square map given a center latitude and longitude.
    input:
        lat  - The center latitude
        lon  - The center longitude
        size - A tuple for the distance between the center location and how far
               left/right/up/down you want the map to display
    """
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
    return Basemap(projection='lcc', resolution=resolution, area_thresh=area_thresh,
                   width=1800*3000, height=1060*3000,
                   lat_1=38.5, lat_2=38.5,
                   lat_0=38.5, lon_0=-97.5)


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
    """
    return Basemap(projection='geos', lon_0='-75.0',
                   resolution=resolution, area_thresh=area_thresh,
                   llcrnrx=-3626269.5, llcrnry=1584175.9,
                   urcrnrx=1381770.0, urcrnry=4588198.0)

def draw_GLM_map(resolution='i', area_thresh=3000):
    return Basemap(resolution=resolution, area_thresh=area_thresh,
                   llcrnrlon=-134, llcrnrlat=-57,
                   urcrnrlon=-14, urcrnrlat=57)