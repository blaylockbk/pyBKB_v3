## Brian Blaylock
## March 29, 2019

"""
Generate frames to animate GOES-16/GOES-17 images with GLM

1. True Color + Night IR (option to include Fire temperature)
2. Add GLM16 flashes (option to include GLM17 in different color)
"""

import numpy as np 
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt 

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')
sys.path.append('B:\pyBKB_v3)

from BB_maps.my_basemap import draw_centermap
from BB_GOES.get_ABI import 


if __name__ == '__main__':

sDATE = datetime()

