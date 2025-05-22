from dydx_v4_client import NodeClient, Wallet
from dydx_v4_client.indexer.rest.indexer_client import IndexerClient
from dydx_v4_client.network import TESTNET
from constants import INDEXER_ACCOUNT_ENDPOINT, INDEXER_ENDPOINT_MAINNET, MNEMONIC, DYDX_ADDRESS, MARKET_DATA_MODE
from func_public import getCandlesRecent
from constants import RESOLUTION, EMA_PERIOD, SMOOTHING_FACTOR

import time

import matplotlib.pyplot as plt

async def calculate_price_ema_pair(client, market):
    """
    Calculate the Exponential Moving Average (EMA) for a given market.
    """
    period = EMA_PERIOD
    close_prices = await get_close_prices(client,market)
    ema_values = []
    # print(f"Close Prices: {close_prices[(len(close_prices)-period-2):]}")
    # Start with SMA as the first EMA value
    sma = sum(close_prices[:period]) / period
    ema_values.append(sma)
    # Compute EMA for the rest
    for price in close_prices[period:]:
        ema_prev = ema_values[-1]
        ema = (price * SMOOTHING_FACTOR) + (ema_prev * (1 - SMOOTHING_FACTOR))
        ema_values.append(ema)
    # Reverse the EMA values to match the order of close prices
    # ema_values.reverse()
    # Return the EMA values
    # print(f"EMA Values: {ema_values}")
    # print(f"EMA Values Length: {len(ema_values)}")
    
    # Return the last EMA value
    lastPrice = close_prices[-1]
    lastEMA = ema_values[-1]

    return (lastPrice, lastEMA)
    

async def get_close_prices(client, market):
    """
    Get close prices for a given market.
    """
    # Define output
    close_prices = []

    # Protect API
    time.sleep(0.2)

    # Get Prices from DYDX V4
    response = await client.indexer.markets.get_perpetual_market_candles(
        market = market, 
        resolution = RESOLUTION,
        limit = EMA_PERIOD*2 + 1  # Get enough data for EMA calculation
    )
    # Candles
    candles = response
    # Structure data
    for candle in candles["candles"]:
        close_prices.append(float(candle["close"]))
        # print(candle["close"])
    close_prices.reverse()

    return close_prices