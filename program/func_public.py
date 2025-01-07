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

# Construct market prices
def ConstructMarketPrices(client):
  """
    Construct market prices
    This function constructs the market prices for all the available markets
    and returns a dataframe with the prices.
  """
  pass
#   # Get markets
#   markets = await get_markets(client)
#   markets = markets["markets"]

#   # Initialize
#   market_prices = {}

#   # Get market prices
#   for market in markets:
#     ticker = market["market"]
#     try:
#       market_price = await client.indexer.markets.get_market_price(ticker)
#       market_prices[ticker] = market_price
#     except Exception as e:
#       print(f"Error fetching market price for {ticker}: {e}")

#   # Construct dataframe
#   dataframeMarketPrices = pd.DataFrame(market_prices).T
#   dataframeMarketPrices.columns = ["price"]

#   # Return
#   return dataframeMarket