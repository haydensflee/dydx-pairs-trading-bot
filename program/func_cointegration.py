'''
func_cointegration.py
This file contains functions that are used to test for cointegration between two time series.
Python script from 
https://www.pythonforfinance.net/2016/05/09/python-backtesting-mean-reversion-part-2/
'''

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint
from scipy.stats import linregress
from constants import MAX_HALF_LIFE, WINDOW

class SmartError(Exception):
    pass

def HalfLifeMeanReversion(series):
    """
    Calculate the half-life of mean reversion for a given time series.

    The half-life of mean reversion is the time it takes for a time series to revert halfway back to its mean.

    Parameters:
    series (array-like): The time series data for which the half-life of mean reversion is to be calculated.

    Returns:
    float: The calculated half-life of mean reversion.

    Raises:
    SmartError: If the series length is less than or equal to 1.
    SmartError: If the slope value is too close to zero, making it impossible to calculate the half-life.
    """
    if len(series) <= 1:
        raise SmartError("Series length must be greater than 1.")
    difference = np.diff(series)
    laggedSeries = series[:-1]
    slope, _, _, _, _ = linregress(laggedSeries, difference)
    if np.abs(slope) < np.finfo(np.float64).eps:
        raise SmartError("Cannot calculate half life. Slope value is too close to zero.")
    halfLife = -np.log(2) / slope
    return halfLife


# Calculate ZScore
def calculateZScore(spread):
    spreadSeries = pd.Series(spread)
    # print(spreadSeries)
    mean = spreadSeries.rolling(center=False, window=WINDOW).mean()
    std = spreadSeries.rolling(center=False, window=WINDOW).std()
    x = spreadSeries.rolling(center=False, window=1).mean()
    zScore = (x - mean) / std
    # print("mean: ", mean.values.tolist()[-1])
    # print("std: ", std.values.tolist()[-1])
    # print(std)
    # print("x: ", x.values.tolist()[-1])
    # print("zScore: ", zScore.values.tolist()[-1])
    # Check for NaN values
    # if np.isnan(zScore).any():
    #     raise SmartError("NaN values found in zScore calculation.")
    # # Check for infinite values
    return zScore


# Calculate Cointegration
def CalculateCointegration(series_1, series_2):
  series_1 = np.array(series_1).astype(np.float64)
  series_2 = np.array(series_2).astype(np.float64)
  coint_flag = 0
  coint_res = coint(series_1, series_2)
  print("stattools coint success")
#   print(series_1)
#   print(series_2)
  coint_t = coint_res[0]
  p_value = coint_res[1]
  critical_value = coint_res[2][1]

  # Better way to fit data vs older version
  series_2_with_constant = sm.add_constant(series_2) 
#   print(series_1,series_2_with_constant, series_2)

  model = sm.OLS(series_1, series_2_with_constant).fit()
  print("model fitted")
  hedge_ratio = model.params[1]
  intercept = model.params[0]
#   print("hr and intercept", hedge_ratio,intercept)

  spread = series_1 - (series_2  * hedge_ratio) - intercept
#   print("spread: ", spread)
  half_life = HalfLifeMeanReversion(spread)
  t_check = coint_t < critical_value
  coint_flag = 1 if p_value < 0.05 and t_check else 0
  print("calc coint done")
  return coint_flag, hedge_ratio, half_life


# Store Cointegration Results
def StoreCointegrationResults(dfMarketPrices):
    """
    StoreCointegrationResults identifies and stores cointegrated pairs from market price data.

    This function takes a DataFrame of market prices, identifies pairs of markets that are cointegrated,
    and saves the results to a CSV file named 'cointegrated_pairs.csv'. The function returns a string
    indicating that the results have been saved.

    Parameters:
    dfMarketPrices (pd.DataFrame): A DataFrame containing market prices with columns representing different markets.

    Returns:
    str: A message indicating that the cointegrated pairs have been successfully saved.

    The function performs the following steps:
    1. Initializes a list of market names and an empty list to store pairs that meet the cointegration criteria.
    2. Iterates over each pair of markets to check for cointegration.
    3. If a pair is cointegrated and meets the half-life criteria, it is added to the list of criteria-met pairs.
    4. Creates a DataFrame from the list of criteria-met pairs and saves it to a CSV file.
    5. Prints a success message and returns the string "saved".

    Note:
    - The function assumes the existence of a `calculateCointegration` function that returns a cointegration flag,
      hedge ratio, and half-life for a given pair of market price series.
    - The function also assumes the existence of a constant `MAX_HALF_LIFE` that defines the maximum allowable half-life
      for a pair to be considered cointegrated.
    """

    # Initialize
    markets = dfMarketPrices.columns.to_list()
    criteriaMetPairs = []

    # Find cointegrated pairs
    # Start with our base pair
    for index, baseMarket in enumerate(markets[:-1]):
        series1 = dfMarketPrices[baseMarket].values.astype(np.float64).tolist()
        # Get Quote Pair
        for quoteMarket in markets[index +1:]:
            series2 = dfMarketPrices[quoteMarket].values.astype(np.float64).tolist()
            if series2==series1:
                print("same series")
                continue
         
            # Check cointegration
            cointFlag, hedgeRatio, halfLife = CalculateCointegration(series1, series2)
            # Log pair
            if cointFlag == 1 and halfLife <= MAX_HALF_LIFE and halfLife > 0:
                criteriaMetPairs.append({
                    "baseMarket": baseMarket,
                    "quoteMarket": quoteMarket,
                    "hedgeRatio": hedgeRatio,
                    "halfLife": halfLife,
                })

    # Create and save DataFrame
    dfCriteriaMet = pd.DataFrame(criteriaMetPairs)
    dfCriteriaMet.to_csv("cointegrated_pairs.csv")
    del dfCriteriaMet

    # Return result
    print("Cointegrated pairs successfully saved")
    return "saved"