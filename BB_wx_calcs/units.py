## Brian Blaylock
## April 9, 2019

# --- Temperature -------------------------------------------------------------
def K_to_C(T_K):
    """
    Convert temperature in Kelvin and return temperature in Celsius
    Input:
        T_K - Temperature in Kelvin
    """
    return T_K - 273.15

def C_to_K(T_C):
    """
    Converts celsius to Kelvin
    input: 
         temperature in celsius
    return:
         temperature in Kelvin
    """
    return T_C + 273.15

def K_to_F(K):
    """
    convert Kelvin to Fahrenheit
    """
    return (K-273.15)*9/5.+32
    
def C_to_F(C):
    """
    converts Celsius to Fahrenheit
    """
    return C*9/5.+32

def K_to_C(K):
    """
    convert Kelvin to Celsius
    """
    return (K-273.15)

# --- Wind --------------------------------------------------------------------
def mps_to_MPH(mps):
    """
    Convert m/s to miles per hour, MPH
    """
    return mps * 2.2369

# --- Precipitation -----------------------------------------------------------
def mm_to_inches(mm):
    """
    Convert mm to inches
    """
    return mm * 0.0394