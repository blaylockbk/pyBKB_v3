## Brian Blaylock
## August 8, 2019

"""
(Been meaning to do this for a long time. Probably should get started before
I graduate.)

`make_RGB.py` takes a GOES-East or GOES-West Multichannel data file
(with label ABI-L2-MCMIPC) and generates the RGB array for it that can be
plotted with plt.imshow. RGB is a stacked np.array(). The values must range
between 0 and 1. Values are normalized between the specified range:
    R_normalized = (R-minimumLimit)/(maximumLimit-minimumLimit)
If a gamma correction is required, it follows the pattern:
    R_corrected = R**(1/gamma)

These RGB recipes are from the GOES Quick Guides found here:
http://rammb.cira.colostate.edu/training/visit/quick_guides/

The input for all is the variable C, which represents the file GOES file opened
with xarray:

    FILE = 'OR_ABI-L2-MCMIPC-M6_G17_s20192201631196_e20192201633575_c20192201634109.nc'
    C = xarray.open_dataset(FILE)

"""

def TrueColor(C, trueGreen=True):
    """
    True Color RGB: 
    http://cimss.ssec.wisc.edu/goes/OCLOFactSheetPDFs/ABIQuickGuide_CIMSSRGB_v2.pdf

    trueGreen - True give you the calculated "True" green color
                False give you the "veggie" channel
    """
    # Load the three channels into appropriate R, G, and B variables
    R = C['CMI_C02'].data
    G = C['CMI_C03'].data
    B = C['CMI_C01'].data

    # Apply range limits for each channel. RGB values must be between 0 and 1
    R = np.clip(R, 0, 1)
    G = np.clip(G, 0, 1)
    B = np.clip(B, 0, 1)

    # Apply a gamma correction to the image
    gamma = 2.2
    R = np.power(R, 1/gamma)
    G = np.power(G, 1/gamma)
    B = np.power(B, 1/gamma)

    if trueGreen:
        # Calculate the "True" Green
        G = 0.45 * R + 0.1 * G + 0.45 * B
        G = np.maximum(G_true, 0)
        G = np.minimum(G_true, 1)

    return np.dstack([R, G, B])


def FireTemperature(C):
    """
    Fire Temperature RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/Fire_Temperature_RGB.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    R = C['CMI_C07'].data
    G = C['CMI_C06'].data
    B = C['CMI_C05'].data

    # Normalize each channel by the appropriate range of values  
    R = (R-273)/(333-273)
    G = (G-0)/(1-0)
    B = (B-0)/(0.75-0)

    # Apply range limits for each channel. RGB values must be between 0 and 1
    R = np.clip(R, 0, 1)
    G = np.clip(G, 0, 1)
    B = np.clip(B, 0, 1)

    # Apply the gamma correction to Red channel.
    #   corrected_value = value^(1/gamma)
    gamma = 0.4
    R = np.power(R, 1/gamma)

    # The final RGB array :)
    return np.dstack([R, G, B])


def AirMass(C):
    """
    Air Mass RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/QuickGuide_GOESR_AirMassRGB_final.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    R = C['CMI_C08'].data - C['CMI_C10'].data
    G = C['CMI_C12'].data - C['CMI_C13'].data
    B = C['CMI_C08'].data-273.15 # remember to convert to Celsius

    # Normalize each channel by the appropriate range of values. e.g. R = (R-minimum)/(maximum-minimum)
    R = (R--26.2)/(0.6--26.2)
    G = (G--42.2)/(6.7--42.2)
    B = (B--64.65)/(-29.25--64.65)

    # Invert B
    B = 1-B

    # Apply range limits for each channel. RGB values must be between 0 and 1
    R = np.clip(R, 0, 1)
    G = np.clip(G, 0, 1)
    B = np.clip(B, 0, 1)

    # The final RGB array :)
    return np.dstack([R, G, B])


def DayCloudPhase(C):
    """
    Day Cloud Phase Distinction RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/Day_Cloud_Phase_Distinction.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    R = C['CMI_C13'].data-273.15 # convert from Kelvin to Celsius
    G = C['CMI_C02'].data
    B = C['CMI_C05'].data

    # Normalize each channel by the appropriate range of values. e.g. R = (R-minimum)/(maximum-minimum)
    R = 1-(R--53.5)/(7.5--53.5)
    G = (G-0)/(.78-0)
    B = (B-.01)/(0.59--0.01)

    # Apply range limits for each channel. RGB values must be between 0 and 1
    R = np.clip(R, 0, 1)
    G = np.clip(G, 0, 1)
    B = np.clip(B, 0, 1)

    # The final RGB array :)
    return np.dstack([R, G, B])


def DayConvection(C):
    """
    Day Convection RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/QuickGuide_GOESR_DayConvectionRGB_final.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    R = C['CMI_C08'].data - C['CMI_C10'].data
    G = C['CMI_C07'].data - C['CMI_C13'].data
    B = C['CMI_C05'].data - C['CMI_C02'].data

    # Normalize each channel by the appropriate range of values. e.g. R = (R-minimum)/(maximum-minimum)
    R = (R--35)/(5--35)
    G = (G--5)/(60--5)
    B = (B--0.75)/(0.25--0.75)

    # Apply range limits for each channel. RGB values must be between 0 and 1
    R = np.clip(R, 0, 1)
    G = np.clip(G, 0, 1)
    B = np.clip(B, 0, 1)

    # The final RGB array :)
    return np.dstack([R, G, B])


def DayLandCloudFire(C):
    """
    Day Land Cloud Fire RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/QuickGuide_GOESR_DayLandCloudFireRGB_final.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    R = C['CMI_C06'].data
    G = C['CMI_C03'].data
    B = C['CMI_C02'].data

    # Normalize each channel by the appropriate range of values  e.g. R = (R-minimum)/(maximum-minimum)
    R = (R-0)/(1-0)
    G = (G-0)/(1-0)
    B = (B-0)/(1-0)

    # Apply range limits for each channel. RGB values must be between 0 and 1
    R = np.clip(R, 0, 1)
    G = np.clip(G, 0, 1)
    B = np.clip(B, 0, 1)

    # Apply the gamma correction to Red channel.
    #   corrected_value = value^(1/gamma)
    gamma = 1
    R = np.power(R, 1/gamma)

    # The final RGB array :)
    return np.dstack([R, G, B])


def WaterVapor(C):
    """
    Simple Water Vapor RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/Simple_Water_Vapor_RGB.pdf
    """
    # Load the three channels into appropriate R, G, and B variables.
    # Remember to convert to Celsius and invert values
    R = C['CMI_C13'].data-273.15
    G = C['CMI_C08'].data-273.15
    B = C['CMI_C10'].data-273.15

    # Normalize each channel by the appropriate range of values. e.g. R = (R-minimum)/(maximum-minimum)
    R = (R--70.86)/(5.81--70.86)
    G = (G--58.49)/(-30.48--58.49)
    B = (B--28.03)/(-12.12--28.03)

    # Invert the colors
    R = 1-R
    G = 1-G
    B = 1-B

    # Apply range limits for each channel. RGB values must be between 0 and 1
    R = np.clip(R, 0, 1)
    G = np.clip(G, 0, 1)
    B = np.clip(B, 0, 1)

    # The final RGB array :)
    return np.dstack([R, G, B])


def DaySnowFog(C):
    """
    Day Snow-Fog RGB:
    http://rammb.cira.colostate.edu/training/visit/quick_guides/QuickGuide_DaySnowFog.pdf
    """
    # Load the three channels into appropriate R, G, and B variables
    R = C['CMI_C03'].data  # 
    G = C['CMI_C05'].data
    B = C['CMI_C07'].data - C['CMI_C13'].data

    # Normalize values    
    R = (R-0)/(1-0)
    G = (G-0)/(0.7-0)
    B = (B-0)/(30-0)

    # Apply range limits for each channel. RGB values must be between 0 and 1
    R = np.clip(R, 0, 1)
    G = np.clip(G, 0, 1)
    B = np.clip(B, 0, 1)

    # Apply a gamma correction to the image
    gamma = 1.7
    R = np.power(R, 1/gamma)
    G = np.power(G, 1/gamma)
    B = np.power(B, 1/gamma)

    # The final RGB array :)
    return np.dstack([R, G, B])