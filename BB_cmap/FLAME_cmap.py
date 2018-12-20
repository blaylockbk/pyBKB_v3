# Brian Blaylock
# December 19, 2018

import numpy as np
import matplotlib.colors as colors

"""
Standardized colormaps from National Weather Service

Source: Joseph Moore joseph.moore@noaa.gov
Document: OneDrive/02_Horel_Group/NWS Standard Color Curve Summary.pdf

Returns three items: 1) The color map 2) the minimum value 3) the maximum value
"""

def cm_ros():
    """
    Rate of spread (in chains/hour):    vmax=150, vmin=0
    """
    # The range of bins
    a = [0, 2, 5, 20, 50, 150, 151]

    # Bins normalized between 0 and 1
    norm = [(float(i)-min(a))/(max(a)-min(a)) for i in a]

    # Color tuple for every bin
    C = np.array([[215,215,215],
                  [0,194,26],
                  [0,107,194],
                  [242,255,66],
                  [201,119,4],
                  [173,0,0],
                  [0,0,0]])/255.

    # Create a tuple for every color indicating the normalized position on the colormap and the assigned color.
    COLORS = []
    for i, n in enumerate(norm):
        COLORS.append((n, C[i]))

    cmap = colors.LinearSegmentedColormap.from_list("Fire Rate of Spread", COLORS)

    return {'cmap':cmap,
            'vmin': 0,
            'vmax': 150,
            'units': 'chains/hour',
            'name': 'Fire Rate of Spread'}