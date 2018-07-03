# Brian Blaylock
# November 11, 2017
# NCAR Reflectivity Colormap

"""
I got this from somewhere
"""

from matplotlib.colors import LinearSegmentedColormap

def reflect_ncdc():
    reflect_ncdc_cdict = {'red':((0.0000, 0.000, 0.000),
                                 (0.0714, 0.000, 0.000),
                                 (0.1429, 0.000, 0.000),
                                 (0.2143, 0.000, 0.000),
                                 (0.2857, 0.000, 0.000),
                                 (0.3571, 0.000, 0.000),
                                 (0.4286, 1.000, 1.000),
                                 (0.5000, 0.906, 0.906),
                                 (0.5714, 1.000, 1.000),
                                 (0.6429, 1.000, 1.000),
                                 (0.7143, 0.839, 0.839),
                                 (0.7857, 0.753, 0.753),
                                 (0.8571, 1.000, 1.000),
                                 (0.9286, 0.600, 0.600),
                                 (1.000, 0.923, 0.923)),
                          'green':((0.0000, 0.925, 0.925),
                                   (0.0714, 0.627, 0.627),
                                   (0.1429, 0.000, 0.000),
                                   (0.2143, 1.000, 1.000),
                                   (0.2857, 0.784, 0.784),
                                   (0.3571, 0.565, 0.565),
                                   (0.4286, 1.000, 1.000),
                                   (0.5000, 0.753, 0.753),
                                   (0.5714, 0.565, 0.565),
                                   (0.6429, 0.000, 0.000),
                                   (0.7143, 0.000, 0.000),
                                   (0.7857, 0.000, 0.000),
                                   (0.8571, 0.000, 0.000),
                                   (0.9286, 0.333, 0.333),
                                   (1.000, 0.923, 0.923)),
                          'blue':((0.0000, 0.925, 0.925),
                                  (0.0714, 0.965, 0.965),
                                  (0.1429, 0.965, 0.965),
                                  (0.2143, 0.000, 0.000),
                                  (0.2857, 0.000, 0.000),
                                  (0.3571, 0.000, 0.000),
                                  (0.4286, 0.000, 0.000),
                                  (0.5000, 0.000, 0.000),
                                  (0.5714, 0.000, 0.000),
                                  (0.6429, 0.000, 0.000),
                                  (0.7143, 0.000, 0.000),
                                  (0.7857, 0.000, 0.000),
                                  (0.8571, 1.000, 1.000),
                                  (0.9286, 0.788, 0.788),
                                  (1.000, 0.923, 0.923))}
    reflect_ncdc_coltbl = LinearSegmentedColormap('REFLECT_NCDC_COLTBL', reflect_ncdc_cdict)
    
    return reflect_ncdc_coltbl

if __name__ == '__main__':
    
    cm_dBZ = reflect_ncdc()
    
    import sys
    sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')
    from BB_HRRR.HRRR_Pando import get_hrrr_variable
    from datetime import datetime
    import numpy as np
    import matplotlib.pyplot as plt

    H = get_hrrr_variable(datetime(2018, 6, 8, 1), 'REFC:entire')

    dBZ = H['value']
    dBZ = np.ma.array(dBZ)
    dBZ[dBZ == -10] = np.ma.masked

    plt.figure(1)
    plt.title('custom cmap reflect_ncdc()')
    plt.pcolormesh(dBZ, cmap=cm_dBZ)
    plt.colorbar()

    plt.figure(2)
    plt.title('gist_ncar')
    plt.pcolormesh(dBZ, cmap='gist_ncar')
    plt.colorbar()

    plt.show()