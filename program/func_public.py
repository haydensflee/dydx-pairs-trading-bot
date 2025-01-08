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
        fromTimeframe = timeframeObject["from_iso"]
        toTimeframe = timeframeObject["to_iso"]

        # Protect rate limits/api
        time.sleep(0.2)

        candles = await client.indexer.markets.get_perpetual_market_candles(
            market = market, 
            resolution = RESOLUTION, 
            from_iso = fromTimeframe,
            to_iso = toTimeframe,
            limit = 100
        )

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

    # Set initial dataframe to store all prices. Later we can see which ones are cointegrated.
    closePrices = await GetCandlesHistorical(client, tradeableMarkets[0])
    # Example price: {'BTC-USD': '96640', 'datetime': '2024-12-22T06:00:00.000Z'}

    dataframe = pd.DataFrame(closePrices)
    dataframe.set_index("datetime", inplace=True)
    # print(dataframe.head())
    # Example dataframe.head(): 2024-12-22T06:00:00.000Z   96640

    # Append other prices to dataframe.
    # Note: You can limit the amount to loop through here to save time in development
    for market in tradeableMarkets[1:]:
        closePricesAdd = await GetCandlesHistorical(client, market)
        dataframeAdd = pd.DataFrame(closePricesAdd)
        dataframeAdd.set_index("datetime", inplace=True)
        dataframe = pd.merge(dataframe, dataframeAdd, how="outer", on="datetime", copy=False)
        del dataframeAdd

     # Check any columns with NaNs
    nans = dataframe.columns[dataframe.isna().any()].tolist()
    if len(nans) > 0:
        print("Dropping columns: ")
        print(nans)
        dataframe.drop(columns=nans, inplace=True)

    # Return result
    print(dataframe)
    return dataframe
  # Get markets
    markets = await client.indexer.markets.get_perpetual_markets()
    # markets = markets["markets"].keys()

    # Initialize
    market_prices = {}
    print("test")

    # Get market prices
    counter=0
    for market in markets["markets"].keys():
        counter+=1
        ticker = market["market"]
        try:
            market_price = await client.indexer.markets.get_market_price(ticker)
            market_prices[ticker] = market_price
        except Exception as e:
            print(f"Error fetching market price for {ticker}: {e}")
        if counter==5:
            break
    # Construct dataframe
    dataframeMarketPrices = pd.DataFrame(market_prices).T
    dataframeMarketPrices.columns = ["price"]

    # Return
    print(dataframeMarketPrices)
    return dataframeMarketPrices