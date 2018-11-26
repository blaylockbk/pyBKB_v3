# Brian Blaylock
# November 26, 2018

"""
Make animated gifs out of images in a directory

os.system('convert *.png animated.gif')
"""

import os

HEAD = '/uufs/chpc.utah.edu/common/home/u0553130/public_html/PhD/HRRR_Spread/Hourly_May2018-Oct2018/'

DIRS = os.listdir(HEAD)

for v in DIRS:
    for d in ['CONUS', 'UTAH', 'WEST']:
        path = '%s/%s/%s' % (HEAD, v, d)
        try:
            os.system('convert -delay 25 %s/*.png %s/animated.gif' % (path, path))
            print('finished', path)
        except:
            print('failed', path)
            pass
