"""
func_public.py
This module contains public functions for the dydx pairs trading bot.
Connect to dydx through public requests where we don't need a private client.
"""
from func_utils import get_ISO_times
from pprint import pprint
import pandas as pd
import numpy as np
import time
from constants import RESOLUTION

# Get relevant time periods for ISO from and to
ISOTimes = get_ISO_times()

pprint(ISOTimes)

# Get Candles Recent. Pulls recent prices to calculate current zscore
async def getCandlesRecent(client, market):

  # Define output
  close_prices = []

  # Protect API
  time.sleep(0.2)

  # Get Prices from DYDX V4
  response = await client.indexer.markets.get_perpetual_market_candles(
    market = market, 
    resolution = RESOLUTION
  )
  # Candles
  candles = response
  # Structure data
  for candle in candles["candles"]:
    close_prices.append(candle["close"])

  # Construct and return close price series
  close_prices.reverse()
  prices_result = np.array(close_prices).astype(np.float64)
  return prices_result

# Function for candlestick data from iso time history
async def GetCandlesHistorical(client, market):
    """
        Get candles historical
        This function gets the historical candles for a given market and returns a dataframe with the candles.
    """
    closePrices = []

    # Extract historical price data for each timeframe
    for timeframe in ISOTimes.keys():
        # Confirm times needed
        timeframeObject = ISOTimes[timeframe]
        fromTimeframe = timeframeObject["from_iso"]+ ".000Z"
        toTimeframe = timeframeObject["to_iso"]+ ".000Z"

        # Protect rate limits/api
        time.sleep(0.2)

        response = await client.indexer.markets.get_perpetual_market_candles(
            market = market, 
            resolution = RESOLUTION, 
            from_iso = fromTimeframe,
            to_iso = toTimeframe,
            limit = 100
        )
        candles=response
        # STructure data
        for candle in candles["candles"]:
            closePrices.append({
                "datetime": candle["startedAt"],
                market: candle["close"]
            })
    
    # Construct dataframe and return (reverse to get in chronological order)
    closePrices.reverse()
    return closePrices


# Construct market prices
async def ConstructMarketPrices(client):
    """
    Construct market prices
    This function constructs the market prices for all the available markets
    and returns a dataframe with the prices.
    """
    # Declare variables
    tradeableMarkets = []
    markets = await client.indexer.markets.get_perpetual_markets()

    # For each market, find tradeable pairs
    for market in markets["markets"].keys():
        
        marketInfo = markets["markets"][market]

        if marketInfo["status"] == "ACTIVE":
            tradeableMarkets.append(market)
    print("tradeable pairs found")
    # Set initial dataframe to store all prices. Later we can see which ones are cointegrated.
    closePrices = await GetCandlesHistorical(client, tradeableMarkets[0])
    # Example price: {'BTC-USD': '96640', 'datetime': '2024-12-22T06:00:00.000Z'}

    dataframe = pd.DataFrame(closePrices)
    dataframe.set_index("datetime", inplace=True)
    # print(dataframe.head())
    # Example dataframe.head(): 2024-12-22T06:00:00.000Z   96640

    # Append other prices to dataframe.
    # Note: You can limit the amount to loop through here to save time in development
    firstMarketLength=len(await GetCandlesHistorical(client, tradeableMarkets[0]))
    for (i, market) in enumerate(tradeableMarkets[0:]):
        print(f"Extracting prices for {i + 1} of {len(tradeableMarkets)} tokens for {market}")
        closePricesAdd = await GetCandlesHistorical(client, market)
        if len(closePricesAdd) < firstMarketLength:
            print(f"Skipping {market} due to insufficient data")
            continue
        
        dataframeAdd = pd.DataFrame(closePricesAdd)
        if dataframeAdd.values[:,1].max() == dataframeAdd.values[:,1].min():
            continue
        try:
            dataframeAdd.set_index("datetime", inplace=True)
            dataframe = pd.merge(dataframe, dataframeAdd, how="outer", on="datetime", copy=False)
        except Exception as e: 
            print(f"Failed to add {market} - {e}")
        del dataframeAdd

     # Check any columns with NaNs
    nans = dataframe.columns[dataframe.isna().any()].tolist()
    if len(nans) > 0:
        print("Dropping columns: ")
        print(nans)
        dataframe.drop(columns=nans, inplace=True)

    # Return result
    return dataframe