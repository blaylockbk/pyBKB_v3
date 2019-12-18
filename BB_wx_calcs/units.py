## Brian Blaylock
## April 9, 2019

# --- Temperature -------------------------------------------------------------
def K_to_C(K):
    """Convert Kelvin to Celsius"""
    return K - 273.15

def K_to_F(K):
    """convert Kelvin to Fahrenheit"""
    return (K-273.15)*9/5.+32

def C_to_K(T_C):
    """Converts celsius to Kelvin"""
    return T_C + 273.15

def C_to_F(C):
    """Converts Celsius to Fahrenheit"""
    return C*9/5.+32

def F_to_C(F):
    """Convert Fahrenheit to Celsius"""
    return (F-32) * 5/9


# --- Wind --------------------------------------------------------------------
def mps_to_MPH(mps):
    """Convert m/s to MPH"""
    return mps * 2.2369


# --- Precipitation -----------------------------------------------------------
def mm_to_inches(mm):
    """Convert mm to inches"""
    return mm * 0.0394