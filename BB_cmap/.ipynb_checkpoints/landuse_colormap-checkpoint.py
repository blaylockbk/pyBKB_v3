# Brian Blaylock
# July 3, 2018

"""
Custom terrain and landuse colormaps

Four Different Land Use Categories:
   - LU_MODIS20
   - LU_MODIS21     includes lake category
   - LU_USGS
   - LU_NLCD

# !!!MUST SET VMAX AND VMIN LIKE THIS TO SCALE COLOR RANGE CORRECTLY!!!
cm, labels = LU_MODIS21()
plt.pcolormesh(LU_INDEX, cmap=cm, vmin=1, vmax=len(labels) + 1)
"""

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np

# ! represents categories not included in the HRRR model
def LU_MODIS21():
    C = np.array([[0, .4, 0],           # 1 Evergreen Needleleaf Forest
                  [0, .4, .2],          # ! 2 Evergreen Broadleaf Forest
                  [.2, .8, .2],         # 3 Deciduous Needleleaf Forest
                  [.2, .8, .4],         # 4 Deciduous Broadleaf Forest
                  [.2, .6, .2],         # 5 Mixed Forests
                  [.3, .7, 0],          # 6 Closed Shrublands
                  [.82, .41, .12],      # 7 Open Shurblands
                  [.74, .71, .41],      # 8 Woody Savannas
                  [1, .84, .0],         # 9 Savannas
                  [0, 1, 0],            # 10 Grasslands
                  [0, 1, 1],            # ! 11 Permanant Wetlands
                  [1, 1, 0],            # 12 Croplands
                  [1, 0, 0],            # 13 Urban and Built-up
                  [.7, .9, .3],         # ! 14 Cropland/Natural Vegetation Mosaic
                  [1, 1, 1],            # ! 15 Snow and Ice
                  [.914, .914, .7],     # 16 Barren or Sparsely Vegetated
                  [.5, .7, 1],          # 17 Water (like oceans)
                  [1, 0, .74],          # 18 Wooded Tundra
                  [.97, .5, .31],       # ! 19 Mixed Tundra
                  [.91, .59, .48],      # ! 20 Barren Tundra
                  [0, 0, .88]           # ! 21 Lake
                 ])

    cm = ListedColormap(C)

    labels = ['Evergreen Needleleaf Forest',
              'Evergreen Broadleaf Forest',
              'Deciduous Needleleaf Forest',
              'Deciduous Broadleaf Forest',
              'Mixed Forests',
              'Closed Shrublands',
              'Open Shrublands',
              'Woody Savannas',
              'Savannas',
              'Grasslands',
              'Permanent Wetlands',
              'Croplands',
              'Urban and Built-Up',
              'Cropland/Natural Vegetation Mosaic',
              'Snow and Ice',
              'Barren or Sparsely Vegetated',
              'Water',
              'Wooded Tundra',
              'Mixed Tundra',
              'Barren Tundra',
              'Lake']

    return {'cmap':cm,
            'labels': labels,
            'vmin': 1,
            'vmax': len(labels) + 1}


def LU_MODIS20():
    C = np.array([[0, .4, 0],       # 1 Evergreen Needleleaf Forest
                  [0, .4, .2],      # ! 2 Evergreen Broadleaf Forest
                  [.2, .8, .2],     # 3 Deciduous Needleleaf Forest
                  [.2, .8, .4],     # 4 Deciduous Broadleaf Forest
                  [.2, .6, .2],     # 5 Mixed Forests
                  [.3, .7, 0],      # 6 Closed Shrublands
                  [.82, .41, .12],  # 7 Open Shurblands
                  [.74, .71, .41],  # 8 Woody Savannas
                  [1, .84, .0],     # 9 Savannas
                  [0, 1, 0],        # 10 Grasslands
                  [0, 1, 1],        # ! 11 Permanant Wetlands
                  [1, 1, 0],        # 12 Croplands
                  [1, 0, 0],        # 13 Urban and Built-up
                  [.7, .9, .3],     # ! 14 Cropland/Natual Vegation Mosaic
                  [1, 1, 1],        # ! 15 Snow and Ice
                  [.914, .914, .7], # 16 Barren or Sparsely Vegetated
                  [0, 0, .88],      # 17 Water
                  [.86, .08, .23],  # 18 Wooded Tundra
                  [.97, .5, .31],   # ! 19 Mixed Tundra
                  [.91, .59, .48]   # ! 20 Barren Tundra
                 ])

    cm = ListedColormap(C)

    labels = ['Evergreen Needleleaf Forest',
              'Evergreen Broadleaf Forest',
              'Deciduous Needleleaf Forest',
              'Deciduous Broadleaf Forest',
              'Mixed Forests',
              'Closed Shrublands',
              'Open Shrublands',
              'Woody Savannas',
              'Savannas',
              'Grasslands',
              'Permanent Wetlands',
              'Croplands',
              'Urban and Built-Up',
              'Cropland/Natural Vegetation Mosaic',
              'Snow and Ice',
              'Barren or Sparsely Vegetated',
              'Water',
              'Wooded Tundra',
              'Mixed Tundra',
              'Barren Tundra']

    return {'cmap':cm,
            'labels': labels,
            'vmin': 1,
            'vmax': len(labels) + 1}


def LU_USGS24():

    C = np.array([[1, 0, 0],  # 1 Urban and Built-up Land
                  [1, 1, 0],  # ! 2 Dryland Cropland and Pasture
                  [1, 1, .2],  # 3 Irrigated Cropland and Pasture
                  [1, 1, .3],  # 4 Mixed Dryland/Irrigated Cropland and Pasture
                  [.7, .9, .3],  # 5 Cropland/Grassland Mosaic
                  [.7, .9, .3],  # 6 Cropland/Woodland Mosaic
                  [0, 1, 0],  # 7 Grassland
                  [.3, .7, 0],  # 8 Shrubland
                  [.82, .41, .12],  # 9 Mixed Shrubland/Grassland
                  [1, .84, .0],  # 10 Savanna
                  [.2, .8, .4],  # 11 Deciduous Broadleaf Forest
                  [.2, .8, .2],  # 12 Deciduous Needleleaf Forest
                  [0, .4, .2],  # 13 Evergreen Broadleaf Forest
                  [0, .4, 0],  # ! 14 Evergreen Needleleaf Forest
                  [.2, .6, .2],  # 15 Mixed Forests
                  [0, 0, .88],  # 16 Water Bodies
                  [0, 1, 1],  # ! 17 Herbaceous Wetlands
                  [.2, 1, 1],  # 18 Wooden Wetlands
                  [.914, .914, .7],  # 19 Barren or Sparsely Vegetated
                  [.86, .08, .23],  # 20 Herbaceous Tundraa
                  [.86, .08, .23],  # 21 Wooded Tundra
                  [.97, .5, .31],  # ! 22 Mixed Tundra
                  [.91, .59, .48],  # ! 23 Barren Tundra
                  [1, 1, 1]])  # ! 24 Snow and Ice

    cm = ListedColormap(C)

    labels = ['Urban and Built-up Land',
              'Dryland Cropland and Pasture',
              'Irrigated Cropland and Pasture',
              'Mixed Dryland/Irrigated Cropland and Pasture',
              'Cropland/Grassland Mosaic',
              'Cropland/Woodland Mosaic',
              'Grassland',
              'Shrubland',
              'Mixed Shrubland/Grassland',
              'Savanna',
              'Deciduous Broadleaf Forest',
              'Deciduous Needleleaf Forest',
              'Evergreen Broadleaf',
              'Evergreen Needleleaf',
              'Mixed Forest',
              'Water Bodies',
              'Herbaceous Wetland',
              'Wooden Wetland',
              'Barren or Sparsely Vegetated',
              'Herbaceous Tundra',
              'Wooded Tundra',
              'Mixed Tundra',
              'Bare Ground Tundra',
              'Snow or Ice']

    return {'cmap':cm,
            'labels': labels,
            'vmin': 1,
            'vmax': len(labels) + 1}


def LU_USGS_chris():
    # Provided by Chris Foster
    C = np.array([[0.0, 0.0, 1.0],
                  [0.0, 1.0, 1.0],
                  [0.4, 0.4, 0.4],
                  [0.0, 0.4, 0.2],
                  [0.2, 0.6, 0.2],
                  [0.3, 0.7, 0.0],
                  [0.8, 1.0, 0.2],
                  [0.0, 1.0, 0.0],
                  [0.8, 0.4, 0.2],
                  [0.6, 0.4, 0.0],
                  [1.0, 1.0, 1.0]])

    cm = ListedColormap(C)

    labels = ['Water',
              'Wetland',
              'Devloped Urban',
              'Evergreen Forest',
              'Deciduous Forest',
              'Irrigated Cropland and Pasture',
              'Cropland/Grassland Mosaic',
              'Grassland',
              'Shrubland',
              'Barren Land',
              'High Albedo Surface']

    return {'cmap':cm,
            'labels': labels,
            'vmin': 1,
            'vmax': len(labels) + 1}


def LU_NLCD_chris():
    # Provided by Chris Foster
    C = np.array([[0.0, 0.0, 1.0],
                  [0.0, 1.0, 1.0],
                  [0.3, 0.3, 0.3],
                  [0.4, 0.4, 0.4],
                  [0.5, 0.5, 0.5],
                  [0.6, 0.6, 0.6],
                  [0.0, 0.4, 0.2],
                  [0.2, 0.6, 0.2],
                  [0.3, 0.7, 0.0],
                  [0.8, 1.0, 0.2],
                  [0.0, 1.0, 0.0],
                  [0.8, 0.4, 0.2],
                  [0.6, 0.4, 0.0]])

    cm = ListedColormap(C)

    labels = ['Water',
              'Wetland',
              'Developed High Intensity',
              'Developed Medium Intensity',
              'Developed Low Intensity',
              'Developed Open Space',
              'Evergreen Forest',
              'Deciduous Forest',
              'Cultivated Crops',
              'Pasture/Hay',
              'Grassland',
              'Shrubland',
              'Barren Land']

    return {'cmap':cm,
            'labels': labels,
            'vmin': 1,
            'vmax': len(labels) + 1}

if __name__ == "__main__":

    # Grab colormap and labels
    C = LU_MODIS21()
    cm = C['cmap']
    labels = C['labels']
    vmax = C['vmax']
    vmin = C['vmin']

    # create some Land Use category field
    LU_INDEX = np.random.randint(0, vmax, (20, 20))

    plt.figure(1)
    plt.title('Land Use Categories')

    # !!!MUST SET VMAX AND VMIN LIKE THIS TO SCALE COLOR RANGE CORRECTLY!!!
    plt.pcolormesh(LU_INDEX, cmap=cm, vmin=vmin, vmax=vmax)
    cbar = plt.colorbar(shrink=.8)
    cbar.set_ticks(np.arange(0.5, len(labels) + 1))
    cbar.ax.set_yticklabels(labels)

    # cbar.ax.set_xticklabels(labels) #If using a horizontal colorbar
    # orientation
    cbar.ax.invert_yaxis()
    cbar.ax.tick_params(labelsize=8)
