# Brian Blaylock
# July 3, 2018

import numpy as np

# --- Wind ---------------------------------------------------------------
def wind_spddir_to_uv(wspd, wdir):
    """
    calculated the u and v wind components from wind speed and direction
    Input:
        wspd: wind speed
        wdir: wind direction
    Output:
        u: u wind component
        v: v wind component
    """

    rad = 4.0 * np.arctan(1) / 180.
    u = -wspd * np.sin(rad * wdir)
    v = -wspd * np.cos(rad * wdir)

    return u, v


def wind_uv_to_dir(U, V):
    """
    Calculates the wind direction from the u and v component of wind.
    Takes into account the wind direction coordinates is different than the
    trig unit circle coordinate. If the wind direction is 360 then returns zero
    (by % 360)
    Inputs:
      U = west / east direction(wind from the west is positive, from the east is negative)
      V = south / noth direction(wind from the south is positive, from the north is negative)
    """
    WDIR = (270 - np.rad2deg(np.arctan2(V, U))) % 360
    return WDIR


def wind_uv_to_spd(U, V):
    """
    Calculates the wind speed from the u and v wind components
    Inputs:
      U = west / east direction(wind from the west is positive, from the east is negative)
      V = south / noth direction(wind from the south is positive, from the north is negative)
    """
    try:
        WSPD = np.sqrt(np.square(U) + np.square(V))
    except:
        # why didn't numpy work???
        WSPD = (U*U + V*V)**(.5)
    return WSPD


# Below is used for calculing the angle between two wind vectors
def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    return vector / np.linalg.norm(vector)


def angle_between(v1, v2):
    """
    Calcualates the angle between two wind vecotrs. Utilizes the cos equation:
                cos(theta) = (u dot v) / (magnitude(u) dot magnitude(v))

    Input:
        v1 = vector 1. A numpy array, list, or tuple with
             u in the first index and v in the second
        v2 = vector 2. A numpy array, list, or tuple with
             u in the first index and v in the second
    Output:
    Returns the angle in radians between vectors 'v1' and 'v2': :

            >> > angle_between((1, 0, 0), (0, 1, 0))
            1.5707963267948966
            >> > angle_between((1, 0, 0), (1, 0, 0))
            0.0
            >> > angle_between((1, 0, 0), (-1, 0, 0))
            3.141592653589793
    """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    angle = np.arccos(np.dot(v1_u, v2_u))
    if np.isnan(angle):
        if (v1_u == v2_u).all():
            return np.rad2deg(0.0)
        else:
            return np.rad2deg(np.pi)
    return np.rad2deg(angle)



#--- Example -----------------------------------------------------------------#
if __name__ == "__main__":
    u = np.array([1, 5, -9])
    v = np.array([-1, -2, 5])

    vector1 = [u[0], v[0]]
    vector2 = [u[1], v[1]]
    vector3 = [u[2], v[2]]

    print("U component: ", u)
    print("V component: ", v)
    print("Wind Directions: ", wind_uv_to_dir(u, v))
    print("Wind Speeds: ", wind_uv_to_spd(u, v))
    print("")
    print("Angle between vector 1 and 2: ", angle_between(vector1, vector2))
    print("Angle between vector 2 and 3: ", angle_between(vector2, vector3))

    print("")
    print(alt_to_pres(850, 1288))
    