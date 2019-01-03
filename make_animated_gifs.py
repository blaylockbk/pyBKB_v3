# Brian Blaylock
# November 26, 2018

"""
Make animated gifs out of images in a directory

os.system('convert *.png animated.gif')
"""

import os



# HRRR Spread
#HEAD = '/uufs/chpc.utah.edu/common/home/u0553130/public_html/PhD/HRRR_Spread/Hourly_Nov2017-Apr2018/'
HEAD = '/uufs/chpc.utah.edu/common/home/u0553130/public_html/PhD/HRRR_Spread/Hourly_May2018-Oct2018/'
DIRS = os.listdir(HEAD)
#for v in DIRS:
for v in ['UVGRD']:
    for d in ['CONUS', 'UTAH', 'WEST']:
    #for d in ['HRRR_and_GLM']:
        path = '%s/%s/%s' % (HEAD, v, d)
        try:
            os.system('convert -delay 25 %s/*.png %s/animated.gif' % (path, path))
            print('finished', path)
        except:
            print('failed', path)
            pass


'''
# GLM Hourly
HEAD = '/uufs/chpc.utah.edu/common/home/u0553130/public_html/PhD/GOES16_GLM/Hourly_May2018-Oct2018/'
DIRS = os.listdir(HEAD)
for d in ['CONUS', 'UTAH', 'WEST', 'GLM']:
    path = '%s/%s' % (HEAD, d)
    try:
        os.system('convert -delay 25 %s/*.png %s/animated.gif' % (path, path))
        print('finished', path)
    except:
        print('failed', path)
        pass
'''