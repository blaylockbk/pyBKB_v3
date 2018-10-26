# Brian Blaylock
# September 21, 2018

"""
Stitch together two images side by side

os.system('convert img1.png img2.png +append new.png')
"""

import os

HEAD = '/uufs/chpc.utah.edu/common/home/u0553130/public_html/PhD/HRRR_RMSE/'

for v in ['TMP:2 m', 'DPT:2 m', 'CAPE:surface', 'HGT:500 mb', 'WIND:10 m', 'UGRD:10 m', 'VGRD:10 m', 'REFC:entire', 'LTNG:entire']:
    for h in range(24):
        DIR = v.split(':')[0]
        NAM = v.replace(':', '-').replace(' ', '-')
        if v == 'HGT:500 mb':
            DIR = 'HGT500'

        img1 = HEAD+'RMSD_v2/%s/CONUS_HRRR_RMSD-%s_hours-%02d.png' % (DIR, NAM, h)
        img2 = HEAD+'RMSD_v3/%s/CONUS_HRRR_RMSD-%s_hours-%02d.png' % (DIR, NAM, h)
        new  = HEAD+'RMSD_v2v3/%s/%02d.png' % (DIR, h)
        try:
            os.system('convert %s %s +append %s' % (img1, img2, new))
        except:
            pass
