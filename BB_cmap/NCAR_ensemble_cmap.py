# Brian Blaylock
# July 30, 2018

import numpy as np
import matplotlib.colors as colors

"""
Standardized colormaps from NCAR Ensemble

Source: https://ensemble.ucar.edu/index.php

Returns three items: 1) The color map 2) the minimum value 3) the maximum value
"""


def cm_prob():
    """
    Probability:    vmax=1, vmin=.1

    """
    # The range of probability bins
    a = np.arange(0.1, 1, 0.1)

    # Bins normalized between 0 and 1
    norm = [(float(i) - min(a)) / (max(a) - min(a)) for i in a]

    # Color tuple for every bin
    C = (
        np.array(
            [
                [215, 227, 238],
                [181, 202, 255],
                [143, 179, 255],
                [127, 151, 255],
                [171, 207, 99],
                [232, 245, 158],
                [255, 250, 20],
                [255, 209, 33],
                [255, 163, 10],
                [255, 76, 0],
            ]
        )
        / 255.0
    )

    # Create a tuple for every color indicating the normalized position on the colormap and the assigned color.
    COLORS = []
    for i, n in enumerate(norm):
        COLORS.append((n, C[i]))

    cmap = colors.LinearSegmentedColormap.from_list("Temperature", COLORS)

    return {"cmap": cmap, "vmin": 0.1, "vmax": 1, "units": "probability"}
