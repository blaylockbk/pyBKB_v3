## Brian Blaylock
## August 8, 2019

"""
For a demo, look at the `make_RGB_Demo.ipynb` notebook in this directory.

`make_RGB.py` takes a GOES-East or GOES-West Multichannel data file
(with label ABI-L2-MCMIPC) and generates an RGB array for various GOES
products. These RGB recipes are from the GOES Quick Guides found here:
http://rammb.cira.colostate.edu/training/visit/quick_guides/

    - TrueColor
    - FireTemperature
    - AirMass
    - DayCloudPhase
    - DayConvection
    - DayCloudConvection
    - DayLandCloud
    - DayLandCloudFire
    - WaterVapor
    - DifferentialWaterVapor
    - DaySnowFog
    - NighttimeMicrophysics
    - Dust
    - SulfurDioxide
    - Ash
    - SplitWindowDifference
    - NightFogDifference

The returned RGB variable is a stacked np.array(). These can easily be viewed
with plt.imshow(RGB). 

The values must range between 0 and 1. Values are normalized between the
specified range: 
    NormalizedValue = (OriginalValue-LowerLimit)/(UpperLimit-LowerLimit)

If a gamma correction is required, it follows the pattern:
    R_corrected = R**(1/gamma)

The input for all is the variable C, which represents the file GOES file opened
with xarray:
    FILE = 'OR_ABI-L2-MCMIPC-M6_G17_s20192201631196_e20192201633575_c20192201634109.nc'
    C = xarray.open_dataset(FILE)

"""
import numpy as np
import matplotlib.pyplot as plt
import xarray


def load_RGB_channels(C, channels):
    """
    Return the R, G, and B arrays for the three channels requested. This
    function will convert the data any units in Kelvin to Celsius.

    Input:
        C        - The GOES multi-channel file opened with xarray.
        channels - A tuple of the channel number for each (R, G, B).
                   For example channel=(2, 3, 1) is for the true color RGB
    Return:
        Returns a list with three items--R, G, and B.
        Example: R, G, B = load_RGB_channels(C, (2,3,1))
    """
    # Units of each channel requested
    units = [C["CMI_C%02d" % c].units for c in channels]
    RGB = []
    for u, c in zip(units, channels):
        if u == "K":
            # Convert form Kelvin to Celsius
            RGB.append(C["CMI_C%02d" % c].data - 273.15)
        else:
            RGB.append(C["CMI_C%02d" % c].data)
    return RGB


def normalize(value, lower_limit, upper_limit, clip=True):
    """
    RGB values need to be between 0 and 1. This function normalizes the input
    value between a lower and upper limit. In other words, it converts your
    number to a value in the range between 0 and 1. Follows normalization
    formula explained here:
            https://stats.stackexchange.com/a/70807/220885
    NormalizedValue = (OriginalValue-LowerLimit)/(UpperLimit-LowerLimit)

    Input:
        value       - The original value. A single value, vector, or array.
        upper_limit - The upper limit.
        lower_limit - The lower limit.
        clip        - True: Clips values between 0 and 1 for RGB.
                    - False: Retain the numbers that extends outside 0-1.
    Output:
        Values normalized between the upper and lower limit.
    """
    norm = (value - lower_limit) / (upper_limit - lower_limit)
    if clip:
        norm = np.clip(norm, 0, 1)
    return norm


def TrueColor(C, pseudoGreen=True):
    """
    True Color RGB:
    http://cimss.ssec.wisc.edu/goes/OCLOFactSheetPDFs/ABIQuickGuide_CIMSSRGB_v2.pdf

    pseudoGreen - True: returns the calculated "True" green color
                False: returns the "veggie" channel
    """
    # Load the three channels into appropriate R, G, and B variables
    R, G, B = load_RGB_channels(C, (2, 3, 1))

    # Apply range limits for each channel. RGB values must be between 0 and 1
    R = np.clip(R, 0, 1)
    G = np.clip(G, 0, 1)
    B = np.clip(B, 0, 1)

    # Apply a gamma correction to the image
    gamma = 2.2
    R = np.power(R, 1 / gamma)
    G = np.power(G, 1 / gamma)
    B = np.power(B, 1 / gamma)

    if pseudoGreen:
        # Calculate the "True" Green
        G = 0.45 * R + 0.1 * G + 0.45 * B
        G = np.maximum(G, 0)
        G = np.minimum(G, 1)

    return np.dstack([R, G, B])


def FireTemperature(C):
    """
    Fire Temperature RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/Fire_Temperature_RGB.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    R, G, B = load_RGB_channels(C, (7, 6, 5))

    # Normalize each channel by the appropriate range of values (clipping happens in function)
    R = normalize(R, 273, 333)
    G = normalize(G, 0, 1)
    B = normalize(B, 0, 0.75)

    # Apply the gamma correction to Red channel.
    #   corrected_value = value^(1/gamma)
    gamma = 0.4
    R = np.power(R, 1 / gamma)

    # The final RGB array :)
    return np.dstack([R, G, B])


def AirMass(C):
    """
    Air Mass RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/QuickGuide_GOESR_AirMassRGB_final.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    R = C["CMI_C08"].data - C["CMI_C10"].data
    G = C["CMI_C12"].data - C["CMI_C13"].data
    B = C["CMI_C08"].data - 273.15  # remember to convert to Celsius

    # Normalize each channel by the appropriate range of values. e.g. R = (R-minimum)/(maximum-minimum)
    R = normalize(R, -26.2, 0.6)
    G = normalize(G, -42.2, 6.7)
    B = normalize(B, -64.65, -29.25)

    # Invert B
    B = 1 - B

    # The final RGB array :)
    return np.dstack([R, G, B])


def DayCloudPhase(C):
    """
    Day Cloud Phase Distinction RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/Day_Cloud_Phase_Distinction.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    R, G, B = load_RGB_channels(C, (13, 2, 5))

    # Normalize each channel by the appropriate range of values. (Clipping happens inside function)
    R = normalize(R, -53.5, 7.5)
    G = normalize(G, 0, 0.78)
    B = normalize(B, 0.01, 0.59)

    # Invert R
    R = 1 - R

    # The final RGB array :)
    return np.dstack([R, G, B])


def DayConvection(C):
    """
    Day Convection RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/QuickGuide_GOESR_DayConvectionRGB_final.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    # NOTE: Each R, G, B is a channel difference.
    R = C["CMI_C08"].data - C["CMI_C10"].data
    G = C["CMI_C07"].data - C["CMI_C13"].data
    B = C["CMI_C05"].data - C["CMI_C02"].data

    # Normalize each channel by the appropriate range of values.
    R = normalize(R, -35, 5)
    G = normalize(G, -5, 60)
    B = normalize(B, -0.75, 0.25)

    # The final RGB array :)
    return np.dstack([R, G, B])


def DayCloudConvection(C):
    """
    Day Convection RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/QuickGuide_DayCloudConvectionRGB_final.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    R, G, B = load_RGB_channels(C, (2, 2, 13))

    # Normalize each channel by the appropriate range of values.
    R = normalize(R, 0, 1)
    G = normalize(G, 0, 1)
    B = normalize(B, -70.15, 49.85)

    # Invert B
    B = 1 - B

    # Apply the gamma correction to Red channel.
    #   corrected_value = value^(1/gamma)
    gamma = 1.7
    R = np.power(R, 1 / gamma)
    G = np.power(G, 1 / gamma)

    # The final RGB array :)
    return np.dstack([R, G, B])


def DayLandCloud(C):
    """
    Day Land Cloud Fire RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/QuickGuide_GOESR_daylandcloudRGB_final.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    R, G, B = load_RGB_channels(C, (5, 3, 2))

    # Normalize each channel by the appropriate range of values  e.g. R = (R-minimum)/(maximum-minimum)
    R = normalize(R, 0, 0.975)
    G = normalize(G, 0, 1.086)
    B = normalize(B, 0, 1)

    # The final RGB array :)
    return np.dstack([R, G, B])


def DayLandCloudFire(C):
    """
    Day Land Cloud Fire RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/QuickGuide_GOESR_DayLandCloudFireRGB_final.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    R, G, B = load_RGB_channels(C, (6, 3, 2))

    # Normalize each channel by the appropriate range of values  e.g. R = (R-minimum)/(maximum-minimum)
    R = normalize(R, 0, 1)
    G = normalize(G, 0, 1)
    B = normalize(B, 0, 1)

    # The final RGB array :)
    return np.dstack([R, G, B])


def WaterVapor(C):
    """
    Simple Water Vapor RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/Simple_Water_Vapor_RGB.pdf
    """
    # Load the three channels into appropriate R, G, and B variables.
    R, G, B = load_RGB_channels(C, (13, 8, 10))

    # Normalize each channel by the appropriate range of values. e.g. R = (R-minimum)/(maximum-minimum)
    R = normalize(R, -70.86, 5.81)
    G = normalize(G, -58.49, -30.48)
    B = normalize(B, -28.03, -12.12)

    # Invert the colors
    R = 1 - R
    G = 1 - G
    B = 1 - B

    # The final RGB array :)
    return np.dstack([R, G, B])


def DifferentialWaterVapor(C):
    """
    Differential Water Vapor RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/QuickGuide_GOESR_DifferentialWaterVaporRGB_final.pdf
    """
    # Load the three channels into appropriate R, G, and B variables.
    R = C["CMI_C10"].data - C["CMI_C08"].data
    G = C["CMI_C10"].data - 273.15
    B = C["CMI_C08"].data - 273.15

    # Normalize each channel by the appropriate range of values. e.g. R = (R-minimum)/(maximum-minimum)
    R = normalize(R, -3, 30)
    G = normalize(G, -60, 5)
    B = normalize(B, -64.65, -29.25)

    # Gamma correction
    R = np.power(R, 1 / 0.2587)
    G = np.power(G, 1 / 0.4)
    B = np.power(B, 1 / 0.4)

    # Invert the colors
    R = 1 - R
    G = 1 - G
    B = 1 - B

    # The final RGB array :)
    return np.dstack([R, G, B])


def DaySnowFog(C):
    """
    Day Snow-Fog RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/QuickGuide_DaySnowFog.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    R = C["CMI_C03"].data
    G = C["CMI_C05"].data
    B = C["CMI_C07"].data - C["CMI_C13"].data

    # Normalize values
    R = normalize(R, 0, 1)
    G = normalize(G, 0, 0.7)
    B = normalize(B, 0, 30)

    # Apply a gamma correction to the image
    gamma = 1.7
    R = np.power(R, 1 / gamma)
    G = np.power(G, 1 / gamma)
    B = np.power(B, 1 / gamma)

    # The final RGB array :)
    return np.dstack([R, G, B])


def NighttimeMicrophysics(C):
    """
    Nighttime Microphysics RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/QuickGuide_GOESR_NtMicroRGB_final.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    R = C["CMI_C15"].data - C["CMI_C13"].data
    G = C["CMI_C13"].data - C["CMI_C07"].data
    B = C["CMI_C13"].data - 273.15

    # Normalize values
    R = normalize(R, -6.7, 2.6)
    G = normalize(G, -3.1, 5.2)
    B = normalize(B, -29.6, 19.5)

    # The final RGB array :)
    return np.dstack([R, G, B])


def Dust(C):
    """
    SulfurDioxide RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/Dust_RGB_Quick_Guide.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    R = C["CMI_C15"].data - C["CMI_C13"].data
    G = C["CMI_C14"].data - C["CMI_C11"].data
    B = C["CMI_C13"].data - 273.15

    # Normalize values
    R = normalize(R, -6.7, 2.6)
    G = normalize(G, -0.5, 20)
    B = normalize(B, -11.95, 15.55)

    # Apply a gamma correction to the image
    gamma = 2.5
    G = np.power(G, 1 / gamma)

    # The final RGB array :)
    return np.dstack([R, G, B])


def SulfurDioxide(C):
    """
    SulfurDioxide RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/Quick_Guide_SO2_RGB.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    R = C["CMI_C09"].data - C["CMI_C10"].data
    G = C["CMI_C13"].data - C["CMI_C11"].data
    B = C["CMI_C07"].data - 273.15

    # Normalize values
    R = normalize(R, -4, 2)
    G = normalize(G, -4, 5)
    B = normalize(B, -30.1, 29.8)

    # The final RGB array :)
    return np.dstack([R, G, B])


def Ash(C):
    """
    Ash RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/GOES_Ash_RGB.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    R = C["CMI_C15"].data - C["CMI_C13"].data
    G = C["CMI_C14"].data - C["CMI_C11"].data
    B = C["CMI_C13"].data - 273.15

    # Normalize values
    R = normalize(R, -6.7, 2.6)
    G = normalize(G, -6, 6.3)
    B = normalize(B, -29.55, 29.25)

    # The final RGB array :)
    return np.dstack([R, G, B])


def SplitWindowDifference(C):
    """
    Split Window Difference RGB (greyscale):
    http://cimss.ssec.wisc.edu/goes/OCLOFactSheetPDFs/ABIQuickGuide_SplitWindowDifference.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    data = C["CMI_C15"].data - C["CMI_C13"].data

    # Normalize values
    data = normalize(data, -10, 10)

    # The final RGB array :)
    return np.dstack([data, data, data])


def NightFogDifference(C):
    """
    Night Fog Difference RGB (greyscale):
    http://cimss.ssec.wisc.edu/goes/OCLOFactSheetPDFs/ABIQuickGuide_NightFogBTD.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    data = C["CMI_C13"].data - C["CMI_C07"].data

    # Normalize values
    data = normalize(data, -90, 15)

    # Invert data
    data = 1 - data

    # The final RGB array :)
    return np.dstack([data, data, data])


if __name__ == "__main__":

    # The following test files were downloaded from AWS
    # https://noaa-goes17.s3.amazonaws.com/ABI-L2-MCMIPC/2019/268/20/OR_ABI-L2-MCMIPC-M6_G17_s20192682001196_e20192682003575_c20192682004096.nc
    # https://noaa-goes16.s3.amazonaws.com/ABI-L2-MCMIPC/2019/268/19/OR_ABI-L2-MCMIPC-M6_G16_s20192681901205_e20192681903578_c20192681904147.nc

    # FILE = 'OR_ABI-L2-MCMIPC-M6_G16_s20192681901205_e20192681903578_c20192681904147.nc'
    FILE = "OR_ABI-L2-MCMIPC-M6_G17_s20192682001196_e20192682003575_c20192682004096.nc"

    C = xarray.open_dataset(FILE)

    for i, func in enumerate(
        [
            TrueColor,
            FireTemperature,
            AirMass,
            DayCloudPhase,
            DayConvection,
            DayLandCloudFire,
            WaterVapor,
            DaySnowFog,
        ]
    ):
        plt.figure(i)
        RGB = func(C)
        plt.imshow(RGB)
        plt.title(func.__name__)
        plt.show()
