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
    orderStatus = await checkOrderStatus(client, order_id)

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

