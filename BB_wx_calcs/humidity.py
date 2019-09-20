import numpy as np

# --- Humidity ---------------------------------------------------------------

def dwptRH_to_Temp(dwpt, RH):
    """
    Convert a dew point temerature and relative humidity to an air temperature.
    Equation from:
    http://andrew.rsmas.miami.edu/bmcnoldy/humidity_conversions.pdf

    Input:
        dwpt - Dew point temperature in Celsius
        RH - relative humidity in %
    Output:
        Temp - Temperature in Celsius
    """
    a = 17.625
    b = 243.04
    Temp = b * (a*dwpt/(b+dwpt)-np.log(RH/100.)) / (a+np.log(RH/100.)-(a*dwpt/(b+dwpt)))
    return Temp


def Tempdwpt_to_RH(Temp, dwpt):
    """
    Convert a temperature and dew point temperature to relative humidity.
    Equation from:
    http://andrew.rsmas.miami.edu/bmcnoldy/humidity_conversions.pdf

    Input:
        Temp - Temperature in Celsius
        dwpt - Dew point temperature in Celsius

    Output:
        RH - relative humidity in % 
    """
    a = 17.625
    b = 243.04
    RH = 100*(np.exp((a*dwpt/(b+dwpt)))/np.exp((a*Temp/(b+Temp))))
    return RH


def TempRH_to_dwpt(Temp, RH):
    """
    Convert a temperature and relative humidity to a dew point temperature.
    Equation from:
    http://andrew.rsmas.miami.edu/bmcnoldy/humidity_conversions.pdf

    Input:
        Temp - Air temperature in Celsius
        RH - relative humidity in %
    Output:
        dwpt - Dew point temperature in Celsius
    """
    # Check if the Temp coming in is in celsius and if RH is between 0-100%
    passed = False
    test_temp = Temp < 65

    if np.sum(test_temp) == np.size(Temp):
        passed = True
        test_rh = np.logical_and(RH <= 100, RH >= 0)
        if np.sum(test_rh) == np.size(RH):
            passed = True
        else:
            print("faied relative humidity check")
    else:
        print("faild temperature check")

    if passed is True:
        a = 17.625
        b = 243.04
        dwpt = b * (np.log(RH/100.) + (a*Temp/(b+Temp))) / (a-np.log(RH/100.)-((a*Temp)/(b+Temp)))
        return dwpt

    else:
        print("TempRH_to_dwpt input requires a valid temperature and humidity.")
        return "Input needs a valid temperature (C) and humidity (%)."

def TempRH_to_dwpt_2(Temp, RH):
    """
    Alternative solution to convert Temp and RH to DWPT.
    Difference between this and previous solution gets large when dwpt is < -50
    Convert a temperature and relative humidity to a dew point temperature.
    Equation from:
    http://www.ajdesigner.com/phphumidity/dewpoint_equation_dewpoint_temperature.php

    Input:
        Temp - Air temperature in Celsius
        RH - relative humidity in %
    Output:
        dwpt - Dew point temperature in Celsius
    """
    p1 = (RH/100.)**(1/8.)
    p2 = 112 + 0.9*Temp
    p3 = 0.1*Temp
    p4 = 112

    Td = p1*p2+p3-p4

    return Td

def PresTempSpecHumid_to_RH(pres, temp, specific_humidity):
    """
    Convert specific humidity to relative humidity
    Source:
        https://earthscience.stackexchange.com/questions/2360/how-do-i-convert-specific-humidity-to-relative-humidity

    pres - pressure in hPa
    temp - temerature in C
    specific_humidity in kg/kg
    """
    RH = 0.263*pres*100*specific_humidity*(np.exp((17.67*(temp+273.15-273.15))/(temp+273.15-29.65)))**-1
    return RH