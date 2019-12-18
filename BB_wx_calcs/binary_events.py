## Brian Blaylock
## March 25, 2019

"""
Basic verification method of binary events with contingency table.

Forecast Validation  - Detailed assessment of the forecast of a specific event.
Forecast Verification- Assurance of the overall quality f all the forecasts.

Primary Source:
    Jollliffe, I. T., D. B. Stephenson, 2012: Forecast Verification, 
        A Practitioner's Guide in Atmospheric Science. Pages 32-59.
        ISBN 13: 9780470660713.
        - Chapter 3 (Hogan and Mason) Deterministic Forecasts of binary events.
        - Tables 3.1 and 3.3

Other Sources:
    http://www.wxonline.info/topics/verif2.html
    http://www.cawcr.gov.au/projects/verification/
"""

import numpy as np

def contingency_table(forecast_binary, observed_binary, print_table=True):
    '''
    Return the contingency table values of a, b, c, and d for two binary fields.

    Input: 
        forecast_binary - Array of True/False if the event was forecasted
        observed_binary - Array of True/False if the event was observed
    
    NOTE: Forecast_binary and observed_binary must be the same shape.
    '''
    # a) Hits:                  Forecasted and observed
    a = np.sum(np.logical_and(forecast_binary, observed_binary))

    # b) False Alarm:           Forecasted, but not observed
    b = np.sum(forecast_binary) - a

    # c) Misses                 Observed, but not forecasted
    c = np.sum(observed_binary) - a

    # d) Correct Rejection:     Not forecasted and not observed
    d = np.sum(np.logical_and(forecast_binary==False, observed_binary==False))

    # Run some checks:
    # n) Total Number
    n = a+b+c+d

    # a+b) Total Forecasted
    total_forecasted = np.sum(forecast_binary)

    # a+c) Total Observed
    total_observed = np.sum(observed_binary)

    # Checks 
    if type(forecast_binary) == np.ma.core.MaskedArray:
        total_grid_points =  np.sum(np.invert(forecast_binary.mask))
    else:
        total_grid_points = np.size(forecast_binary)

    assert total_grid_points == n, ("Total Number of Grid points does not equal n")
    assert total_forecasted == a+b, ("Total forecasted points does not equal a+b")
    assert total_observed == a+c, ("Total observed points does not equal a+c")

    if print_table:
        print_contingency_table(a, b, c, d)

    return a, b, c, d


def print_contingency_table(a, b, c, d):
    print('          {:^20}'.format('Observed'))
    print('         |{:^10}{:^10}| {:}'.format('Yes', 'No', 'Total'))
    print('--------------------------------------------')
    print(' Fxx Yes |{:10,}{:10,}| {:10,}'.format(a, b, a+b))
    print(' Fxx No  |{:10,}{:10,}| {:10,}'.format(c, d, c+d))
    print('--------------------------------------------')
    print('Total    |{:10,}{:10,}| {:10,}'.format(a+c, b+d, a+b+c+d))
    print('\n')
    print('Hit Rate: {:.2f}%'.format(hit_rate(a,b,c,d)*100))
    print('False Alarm Rate: {:.2f}%'.format(false_alarm_rate(a,b,c,d)*100))
    print('False Alarm Ratio: {:.2f}%'.format(false_alarm_ratio(a,b,c,d)*100))
    print('Proportion Correct: {:.2f}%'.format(proportion_correct(a,b,c,d)*100))
    print('/n')

# -----------------------------------------------------------------------------

def base_rate(a, b, c, d):
    """
    The probability that an observed categorical event will occur.
    """
    s = (a+c)/(a+b+c+d)
    return s

def forecast_rate(a, b, c, d):
    r = (a+b)/(a+b+c+d)
    return r

def frequency_bias(a, b, c, d):
    """
    Total events forecasted divided by the total events observed. Bias Score.
    "How did the forecast frequency of "yes" events compare to the observed
    frequency of "yes" events?"
        Perfect Score: B = 1
        Underforecast: B < 1
        Overforcast  : B > 1
    Does not measure how well the forecast corresponds to the observations,
    only measures relative frequencies.
    If condition is never observed (0), then B is infinity.
    """
    B = (a+b)/(a+c)
    return B

# -----------------------------------------------------------------------------

def hit_rate(a, b, c, d):
    """
    Also known as Probability of Detection (POD).
    "What fraction of the observed "yes" events were correctly forecast?"
        Range [0,1]; Perfect Score = 1
    Sensitive to hits, but ignores false alarms. Very sensitive to the
    climatological frequency of the event. Good for rare events.Can be
    artificially improved by issuing more "yes" forecasts to increase the
    number of hits. Should be used in conjunction with the false alarm ratio.
    """
    H = a/(a+c)
    return H

def false_alarm_rate(a, b, c, d):
    """
    Also known as Probability of False Detection (POFD)
    "What fraction of the observed "no" events were incorrectly forecast as
    "yes"?"
        Perfect Score = 0
    Sensitive to false alarms, but ignores misses. Can be artificially improved
    by issuing fewer "yes" forecasts to reduce the number of false alarms. 
    Not often reported for deterministic forecasts, but is an important 
    component of the Relative Operating Characteristic (ROC) used widely for 
    probabilistic forecasts.
    """
    F = b/(b+d)
    return F

def false_alarm_ratio(a, b, c, d):
    """
    "What fraction of the predicted "yes" events actually did not occur
    (i.e., were false alarms)?"
        Perfect Score = 0
    Sensitive to false alarms, but ignores misses. Very sensitive to the
    climatological frequency of the event. Should be used in conjunction with
    the hit rate. 
    """
    FAR = b/(a+b)
    return FAR

def success_ratio(a, b, c, d):
    """
    The same as 1-FAR.
    "What fraction of the forecast "yes" events were correctly observed?"
        Perfect Score = 1
    
    Gives information about the likelihood of an observed event, given that it
    was forecast. It is sensitive to false alarms but ignores misses.
    """
    SR = a/(a+b)
    return SR

def proportion_correct(a, b, c, d):
    """
    Also known as Accuracy.
        "Overall, what fraction of the forecasts were correct?"
        Perfect Score = 1
    """
    PC = (a+d)/(a+b+c+d)
    return PC

def critical_success_index(a, b, c, d):
    """
    Also known as Threat Score (TS) or Gilbert Score (GS). 
    "How well did the forecast "yes" events correspond to the observed "yes"
    events?"
        Perfect Score = 1
    
    The total number of correct event forecasts (hits) divided by the total
    number of event forecasts plus the number of misses. Strongly dependent
    on the base rate because it is not affected by the number of non-event
    forecasts that are not observed (correct rejections).
    
    Measures the fraction of observed and/or forecast events that were 
    correctly predicted. It can be thought of as the accuracy when correct 
    negatives have been removed from consideration, that is, TS is only 
    concerned with forecasts that count. Sensitive to hits, penalizes both 
    misses and false alarms. Does not distinguish source of forecast error. 
    Depends on climatological frequency of events (poorer scores for rarer 
    events) since some hits can occur purely due to random chance.
    """
    CSI = a/(a+b+c)
    return CSI

def gilbert_skill_score(a, b, c, d):
    """
    Also known as the Equitable Threat Score (ETS).
    Widely used for the verification of deterministic forecasts of rare events
    such as precipitation above a large threshold. However, the score is not
    "equitable."
    "How well did the forecast "yes" events correspond to the observed "yes" 
    events (accounting for hits due to chance)?"
        Range: [-1/3, 1]; Zero is no skill; Perfect Score = 1

    Measures the fraction of observed and/or forecast events that were
    correctly predicted, adjusted for hits associated with random chance
    (for example, it is easier to correctly forecast rain occurrence in a wet
    climate than in a dry climate). The ETS is often used in the verification
    of rainfall in NWP models because its "equitability" allows scores to be
    compared more fairly across different regimes. Sensitive to hits. Because
    it penalizes both misses and false alarms in the same way, it does not
    distinguish the source of forecast error.

    `a_r` (a random) is the number of hits expected a forecasts independent
    of observations (pure chance). Since (n) is in the denominator, GSS depends
    explicitly on the number of correct rejections (d). In other words, `a_r`
    is the expected (a) for a random forecast with the same forecast rate (r)
    and base rate (s).
    """
    n = a+b+c+d
    a_r = (a+b)*(a+c)/n  
    GSS = (a-a_r)/(a+b+c-a_r)
    return GSS

def equitable_threat_score(a, b, c, d):
    # Same as the gilbert skill score
    ETS = gilbert_skill_score(a, b, c, d)
    return ETS

def heidke_skill_score(a, b, c, d):
    """
    Based on the proportion correct that takes into account the number of hits
    due to chance.
    "What was the accuracy of the forecast relative to that of random chance?"
        Range [-1,1]; Zero is no skill; Perfect score = 1
    """
    n = a+b+c+d
    a_r = ((a+b)*(a+c))/n
    d_r = (b+d)*(c+d)/n
    HSS = (a+d-a_r-d_r)/(n-a_r-d_r)
    return HSS

def peirce_skill_score(a, b, c, d):
    """
    Also known as the Hanssen and Kuipers discriminant or True Skill Statistic.
    Ratio of hits to total number of events observed minus the ratio of false
    alarms to total number of non-events observed (i.e. PSS = H-F).
    "How well did the forecast separate the "yes" events from the "no" events?"
        Range [-1,1]; Perfect Score = 1
    
    Uses all elements in contingency table. Does not depend on climatological 
    event frequency. The expression is identical to PSS = POD - POFD, but the 
    Peirce Skill score can also be interpreted as 
            (accuracy for events) + (accuracy for non-events) - 1
    For rare events, PSS is unduly weighted toward the first term (same as
    POD), so this score may be more useful for more frequent events.
    """
    PSS = (a*d - b*c)/((b+d)*(a+c))

def clayton_skill_score(a, b, c, d):
    """
    Ratio of hits to total number of events forecast minus the ratio of correct
    rejections to total number of non-events forecast.
    Analogous to the PSS except it is stratified on the forecasts rather than
    the observations.
    """
    CSS = a/(a+b) - c/(c+d)
    return CSS

def doolittle_skill_score(a, b, c, d):
    DSS = (a*d - b*c)/np.sqrt((a+b)(c+d)(a+c)(b+d))
    return DSS

def log_of_odds_ratio(a, b, c, d):
    theta = a*d/(b*c)
    LOR = np.log(theta)
    return LOR

def odds_ratio_skill_score(a, b, c, d):
    Q = (a*d-b*c)/(a*d+b*c)
    return Q

"""
===============================================================================
Fractions Skill Score

 Roberts, N.M. and H.W. Lean, 2008: Scale-Selective Verification of Rainfall
    Accumulations from High-Resolution Forecasts of Convective Events. Mon. 
    Wea. Rev., 136, 78–97, https://doi.org/10.1175/2007MWR2123.1
===============================================================================
"""

def fraction(values):
    '''
    For each set of binary values for the window, compute the fraction of the
    window that is True.
    '''
    return np.sum(values)/np.size(values)

def radial_footprint(radius):
    """A footprint with the given radius"""
    y,x = np.ogrid[-radius: radius+1, -radius: radius+1]
    footprint = x**2+y**2 <= radius**2
    footprint = 1*footprint.astype(float)
    return footprint

def fractions_skill_score(obs_binary, fxx_binary, window=None, radius=None):
    """
    Fractions Skill Score:
        As the size of the neighborhood is increased, the sharpness is reduced.
        NOTE: This is the generic form.
        A SPECIAL function in BB_HRRR.GLM_events_HRRR.fractions_skill_score is
        for multiple forecast grids and masks for multiple domains of interest.
    
    Input:
        obs_binary - Observed Binary Field (True/False)
        fxx_binary - Forecasted Binary Field (True/False)
        window     - Square box window with size as number of grid points. 
                     Preferably an odd number so that the window is equal in
                     all directions. (Used if radius==None)
        radius     - Radius of the footprint. (Used if window==None)
    """
    assert np.size(obs_binary) == np.size(fxx_binary), ('Observed Binary and Forecasted Binary input must be same size.')
    assert np.logical_or(window != None, radius != None), ('"window" or "radius" must be specified, but not both.')
    assert np.logical_or(window == None, radius == None), ('"window" or "radius" must be specified, but not both.')

    ## a. Convert to binary fields: Convert input from boolean arrays to floats
    #     so we can compute fraction values.
    print('Convert Boolean field to float (1=True, 0=False)')
    obs_binary = np.array(obs_binary, dtype=float)
    fxx_binary = np.array(fxx_binary, dtype=float)

    ## b. Generate fractions: Compute the fractions of the area
    #     "These quantities assess the spatial density in the binary fields."
    #     "Points outside the domain are assigned a value of zero."
    #                                                     - Roberts et al. 2008
    import scipy.ndimage as ndimage
    return_this = {}

    # Two different methods: A "window" box or a radial footprint as the filter.    
    print('Generate fractions for the neighborhood')
    if window != None:
        print('Window size: %sx%s grid boxes' % (window, window))
        return_this['window'] = window
        obs_fracs = ndimage.generic_filter(obs_binary, fraction, size=window, mode='constant', cval=0)
        fxx_fracs = ndimage.generic_filter(fxx_binary, fraction, size=window, mode='constant', cval=0)
    
    elif radius != None:
        # "It might be preferable to use a different kernel, such as a circular mean filter..."
        print('Footprint radius: %s grid boxes' % radius)
        return_this['radius'] = radius
        obs_fracs = ndimage.generic_filter(obs_binary, fraction, footprint=radial_footprint(radius), mode='constant', cval=0)
        fxx_fracs = ndimage.generic_filter(fxx_binary, fraction, footprint=radial_footprint(radius), mode='constant', cval=0)

    ## c. Compute fractions skill score:
    print('Compute fractions skill score')
    MSE = np.mean((obs_fracs - fxx_fracs)**2)
    MSE_ref = np.mean(obs_fracs**2) + np.mean(fxx_fracs**2)

    FSS = 1 - (MSE/MSE_ref)

    return_this['FSS'] = FSS,
    return_this['Observed Fraction'] = obs_fracs
    return_this['Forecast Fraction'] = fxx_fracs

    return return_this
