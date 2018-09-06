# Brian Blaylock
# May 2, 2018

import numpy as np
import matplotlib.colors as colors

"""
Colormap for Utah Division of Air Quality

Returns three items: 1) The color map 2) the minimum value 3) the maximum value
"""


def cm_airquality(pollutant='PM25'):
    """
    Range of values:
        Celsius: -18 to 27 C
        (Fahrenheit: 0 to 80 F)

    Input:
        pollutant: PM25 or O3
    """
    # The PM 2.5 Colorscale
    if pollutant == 'PM25':
        a = np.array([0, 12, 35.5, 55.5, 150.5, 250]) # micrograms/m3
        vmin = 0
        vmax = 250
        units = r'$\mu$g m$\mathregular{^{-3}}$'
    elif pollutant == 'O3':
        a = np.array([0, 55, 71, 86, 106, 201]) # parts per billion
        vmin = 0
        vmax = 201
        units = 'ppb'

    # Normalize the bin between 0 and 1 (uneven bins are important here)
    norm = [(float(i)-min(a))/(max(a)-min(a)) for i in a]

    # Color tuple for every bin
    C = np.array([[0, 228, 0],
                [255,255,0],
                [255,126,0],
                [255,0,0],
                [153,0,76],
                [126,0,35]])

    # Create a tuple for every color indicating the normalized position on the colormap and the assigned color.
    COLORS = []
    for i, n in enumerate(norm):
        COLORS.append((n, np.array(C[i])/255.))

    # Create the colormap
    cmap = colors.LinearSegmentedColormap.from_list("dewpoint", COLORS)

    return {'cmap':cmap,
            'vmin': vmin,
            'vmax': vmax,
            'units': units}