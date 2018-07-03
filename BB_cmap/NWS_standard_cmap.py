# Brian Blaylock
# May 2, 2018

import numpy as np
import matplotlib.colors as colors

"""
Standardized colormaps from National Weather Service

Source: Joseph Moore joseph.moore@noaa.gov
Document: OneDrive/02_Horel_Group/NWS Standard Color Curve Summary.pdf

Returns three items: 1) The color map 2) the minimum value 3) the maximum value
"""

def cm_temp():
    """
    Celsius:    vmax=50, vmin=-50
    (Fahrenheit: vmax=120, vmin=-60)
    """
    # The range of temperature bins in Fahrenheit
    a = np.arange(-60,121,5)

    # Bins normalized between 0 and 1
    norm = [(float(i)-min(a))/(max(a)-min(a)) for i in a]

    # Color tuple for every bin
    C = np.array([[145,0,63],
                  [206,18,86],
                  [231,41,138],
                  [223,101,176],
                  [255,115,223],
                  [255,190,232],
                  [255,255,255],
                  [218,218,235],
                  [188,189,220],
                  [158,154,200],
                  [117,107,177],
                  [84,39,143],
                  [13,0,125],
                  [13,61,156],
                  [0,102,194],
                  [41,158,255], 
                  [74,199,255], 
                  [115,215,255], 
                  [173,255,255],
                  [48,207,194], 
                  [0,153,150], 
                  [18,87,87],
                  [6,109,44],
                  [49,163,84],
                  [116,196,118],
                  [161,217,155],
                  [211,255,190],  
                  [255,255,179], 
                  [255,237,160], 
                  [254,209,118], 
                  [254,174,42], 
                  [253,141,60], 
                  [252,78,42], 
                  [227,26,28], 
                  [177,0,38], 
                  [128,0,38], 
                  [89,0,66], 
                  [40,0,40]])/255.

    # Create a tuple for every color indicating the normalized position on the colormap and the assigned color.
    COLORS = []
    for i, n in enumerate(norm):
        COLORS.append((n, C[i]))

    cmap = colors.LinearSegmentedColormap.from_list("Temperature", COLORS)

    return {'cmap':cmap,
            'vmin': -50,
            'vmax': 50,
            'units': 'C'}

def cm_dpt():
    """
    Range of values:
        Celsius: -18 to 27 C
        (Fahrenheit: 0 to 80 F)
    """
    # The dew point temperature bins in Celsius (C)
    a = np.array([0,10,20,30,40,45,50,55,60,65,70,75,80])

    # Normalize the bin between 0 and 1 (uneven bins are important here)
    norm = [(float(i)-min(a))/(max(a)-min(a)) for i in a]

    # Color tuple for every bin
    C = np.array([[59,34,4],
                [84,48,5],
                [140,82,10],
                [191,129,45],
                [204,168,84],
                [223,194,125],
                [230,217,181],
                [211,235,231],
                [169,219,211],
                [114,184,173],
                [49,140,133],
                [1,102,95],
                [0,60,48],
                [0,41,33]])

    # Create a tuple for every color indicating the normalized position on the colormap and the assigned color.
    COLORS = []
    for i, n in enumerate(norm):
        COLORS.append((n, np.array(C[i])/255.))

    # Create the colormap
    cmap = colors.LinearSegmentedColormap.from_list("dewpoint", COLORS)

    return {'cmap':cmap,
            'vmin': -18,
            'vmax': 27,
            'units': 'C'}

def cm_rh():
    """
    Range of values:
        5 to 90 %
    """
    # The relative humidity bins in percent (%)
    a = [5,10,15,20,25,30,35,40,50,60,70,80,90]

    # Normalize the bin between 0 and 1 (uneven bins are important here)
    norm = [(float(i)-min(a))/(max(a)-min(a)) for i in a]

    # Color tuple for every bin
    C = np.array([[145,0,34],
                [166,17,34],
                [189,46,36],
                [212,78,51],
                [227,109,66],
                [250,143,67],
                [252,173,88],
                [254,216,132],
                [255,242,170],
                [230,244,157],
                [188,227,120],
                [113,181,92],
                [38,145,75],
                [0,87,46]])

    # Create a tuple for every color indicating the normalized position on the colormap and the assigned color.
    COLORS = []
    for i, n in enumerate(norm):
        COLORS.append((n, np.array(C[i])/255.))

    # Create the colormap
    cmap = colors.LinearSegmentedColormap.from_list("rh", COLORS)

    return {'cmap':cmap,
            'vmin': 5,
            'vmax': 90,
            'units': '%'}

def cm_wind():
    """
    m/s: vmin=0, vmax=60
    (MPH: vmin=0, vmax=140)
    """
    # The wind speed bins in miles per hour (MPH)
    a = [0,5,10,15,20,25,30,35,40,45,50,60,70,80,100,120,140]

    # Normalize the bin between 0 and 1 (uneven bins are important here)
    norm = [(float(i)-min(a))/(max(a)-min(a)) for i in a]

    # Color tuple for every bin
    C = np.array([[16,63,120],
                [34,94,168],
                [29,145,192],
                [65,182,196],
                [127,205,187],
                [180,215,158],
                [223,255,158],
                [255,255,166],
                [255,232,115],
                [255,196,0],
                [255,170,0],
                [255,89,0],
                [255,0,0],
                [168,0,0],
                [110,0,0],
                [255,190,232],
                [255,115,223]])

    # Create a tuple for every color indicating the normalized position on the colormap and the assigned color.
    COLORS = []
    for i, n in enumerate(norm):
        COLORS.append((n, np.array(C[i])/255.))

    # Create the colormap
    cmap = colors.LinearSegmentedColormap.from_list("wind", COLORS)

    return {'cmap':cmap,
            'vmin': 0,
            'vmax': 60,
            'units': 'm/s'}

def cm_sky():
    """
    Range of Values:
        0 to 90 %
    """
    # The sky covered by clouds in percent (%)
    a = range(0,91,10)

    # Normalize the bin between 0 and 1 (uneven bins are important here)
    norm = [(float(i)-min(a))/(max(a)-min(a)) for i in a]

    # Color tuple for every bin
    C = np.array([[36, 160, 242],
                [78, 176, 242],
                [128, 183, 248],
                [160, 200, 255],
                [210, 225, 255],
                [225, 225, 225],
                [201, 201, 201],
                [165, 165, 165],
                [110, 110, 110],
                [80, 80, 80]])

    # Create a tuple for every color indicating the normalized position on the colormap and the assigned color.
    COLORS = []
    for i, n in enumerate(norm):
        COLORS.append((n, np.array(C[i])/255.))

    # Create the colormap
    cmap = colors.LinearSegmentedColormap.from_list("cloudcover", COLORS)

    return {'cmap':cmap,
            'vmin': 0,
            'vmax': 90,
            'units': '%'}


def cm_precip():
    """
    Range of values:
        metric: 0 to 762 millimeters
        (english: 0 to 30 inches)
    """
    # The amount of precipitation in inches
    a = [0,.01,.1,.25,.5,1,1.5,2,3,4,6,8,10,15,20,30]

    # Normalize the bin between 0 and 1 (uneven bins are important here)
    norm = [(float(i)-min(a))/(max(a)-min(a)) for i in a]

    # Color tuple for every bin
    C = np.array([[255,255,255],
                [199,233,192],
                [161,217,155],
                [116,196,118],
                [49,163,83],
                [0,109,44],
                [255,250,138],
                [255,204,79],
                [254,141,60],
                [252,78,42],
                [214,26,28],
                [173,0,38],
                [112,0,38],
                [59,0,48],
                [76,0,115],
                [255,219,255]])

    # Create a tuple for every color indicating the normalized position on the colormap and the assigned color.
    COLORS = []
    for i, n in enumerate(norm):
        COLORS.append((n, np.array(C[i])/255.))

    # Create the colormap
    cmap = colors.LinearSegmentedColormap.from_list("precipitation", COLORS)

    return {'cmap':cmap,
            'vmin': 0,
            'vmax': 762,
            'units': 'mm'}
    