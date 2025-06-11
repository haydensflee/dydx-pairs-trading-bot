from dydx_v4_client import MAX_CLIENT_ID, Order, OrderFlags
from dydx_v4_client.node.market import Market, since_now
from dydx_v4_client.indexer.rest.constants import OrderType
from dydx_v4_client import NodeClient, Wallet
from dydx_v4_client.indexer.rest.indexer_client import IndexerClient
from dydx_v4_client.network import TESTNET
from constants import INDEXER_ACCOUNT_ENDPOINT, INDEXER_ENDPOINT_MAINNET, MNEMONIC, DYDX_ADDRESS, MARKET_DATA_MODE
from func_utils import format_number
from func_private import place_market_order, checkOrderStatus, cancel_order
from constants import RESOLUTION, EMA_PERIOD, SMOOTHING_FACTOR
from func_messaging import send_message

import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import ta

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
    
async def get_close_prices_100_days(client,market):
    # Define the market and resolution
    
    resolution = '1DAY'
    resolution = '1HOUR'  # daily candles

    # Calculate the time range for the past 100 days
    end_time = datetime.now()
    start_time = end_time - timedelta(days=100)

    # Convert to ISO 8601 format
    from_iso = start_time.isoformat()
    to_iso = end_time.isoformat()

    # Fetch the candles
    response = await client.indexer.markets.get_perpetual_market_candles(
        market=market,
        resolution=resolution,
        from_iso=from_iso,
        to_iso=to_iso,
        limit=100
    )

    candles = response['candles']
    # Convert list of candle dicts into a DataFrame
    df = pd.DataFrame(candles)

    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['startedAt'])

    # Convert price columns to numeric
    price_cols = ['open', 'high', 'low', 'close']
    df[price_cols] = df[price_cols].astype(float)

    # Optional: sort by time
    df = df.sort_values('timestamp').reset_index(drop=True)

    # Select desired columns
    df_candles = df[['timestamp', 'open', 'high', 'low', 'close']]
    return df_candles

async def getSignals(df, key_value=1, atr_period=10):

    src = df['close']

    # Calculate ATR
    atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=atr_period).average_true_range()
    nLoss = key_value * atr

    # Initialize Trailing Stop
    xATRTrailingStop = pd.Series(index=src.index, dtype='float64')
    pos = pd.Series(index=src.index, dtype='int')

    for i in range(len(df)):
        if i == 0:
            xATRTrailingStop.iloc[i] = src.iloc[i] + nLoss.iloc[i]
            pos.iloc[i] = 0
        else:
            prev_stop = xATRTrailingStop.iloc[i-1]
            prev_src = src.iloc[i-1]

            if src.iloc[i] > prev_stop and prev_src > prev_stop:
                xATRTrailingStop.iloc[i] = max(prev_stop, src.iloc[i] - nLoss.iloc[i])
            elif src.iloc[i] < prev_stop and prev_src < prev_stop:
                xATRTrailingStop.iloc[i] = min(prev_stop, src.iloc[i] + nLoss.iloc[i])
            elif src.iloc[i] > prev_stop:
                xATRTrailingStop.iloc[i] = src.iloc[i] - nLoss.iloc[i]
            else:
                xATRTrailingStop.iloc[i] = src.iloc[i] + nLoss.iloc[i]

            # Position
            if prev_src < prev_stop and src.iloc[i] > prev_stop:
                pos.iloc[i] = 1
            elif prev_src > prev_stop and src.iloc[i] < prev_stop:
                pos.iloc[i] = -1
            else:
                pos.iloc[i] = pos.iloc[i-1]

    # EMA
    ema = src.ewm(span=1, adjust=False).mean()

    above = (ema > xATRTrailingStop) & (ema.shift(1) <= xATRTrailingStop.shift(1))
    below = (xATRTrailingStop > ema) & (xATRTrailingStop.shift(1) <= ema.shift(1))

    buy = (src > xATRTrailingStop) & above
    sell = (src < xATRTrailingStop) & below

    barbuy = src > xATRTrailingStop
    barsell = src < xATRTrailingStop

    lastTrailingStop = xATRTrailingStop.iloc[-1]
    send_message(f"Last Trailing Stop: {lastTrailingStop} | Last price: {src.iloc[-1]}")

    # Add signals to the DataFrame
    df['buy_signal'] = buy
    df['sell_signal'] = sell
    df['position'] = pos

    return df


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

async def placeOrder(client, market, size, price, side):
    """
    Place an order for a given market.
    """
    marketPrice = price
    if side == "BUY":
        marketPrice = format_number(price * 1.01,price)  # Adjust price for buy orders
    elif side == "SELL":
        marketPrice = format_number(price * 0.99, price)
        
    order, order_id = await place_market_order(client, market, side, size, marketPrice, False)
    send_message(f"Order and order_id: {order}, {order_id}")
    orderStatus = await checkOrderStatus(client, order_id)
    send_message(f"Order Status: {orderStatus}")

    # if orderStatus == "CANCELED":
    #     print(f"Order {order_id} was canceled.")
    #     await cancel_order(client, order_id)
    #     return None, None
    
    # if orderStatus != "FAILED":
    #     time.sleep(15)
    #     orderStatus = await checkOrderStatus(client, order_id)

    #     # Guard: If order cancelled move onto next Pair
    #     if orderStatus == "CANCELED":
    #         print(f"Order {order_id} was canceled.")
    #         await cancel_order(client, order_id)
    #         return None, None        
    #     if orderStatus != "FILLED":
    #         await cancel_order(client, order_id)
    #         print(f"Order {order_id} was not filled. Cancellation request sent, please check open orders..")
    #         return None, None

    orderDict = {
        "market": market,
        "size": size,
        "price": marketPrice,
        "side": side,
        "order_id": order_id,
        "order": order
    }

    # Place the order
    return order, order_id

