import asyncio
import time
import ta
from constants import ABORT_ALL_POSITIONS, FIND_COINTEGRATED, PLACE_TRADES, MANAGE_EXITS, CALCUATE_EMA
from func_connections import connect_dydx
from func_private import abort_all_positions
from func_public import ConstructMarketPrices
from func_cointegration import StoreCointegrationResults
from func_entry_pairs import openPositions
from func_exit_pairs import manage_trade_exits
from func_messaging import send_message
from func_ema import calculate_price_ema_pair, placeOrder, get_close_prices_100_days, getSignals
from func_utils import wait_until_half_hour, wait_until_midnight

import sys, os, json
from datetime import datetime


async def main():
  # Message on start
  send_message("Bot launch successful")
  startCount = 0
  
  # Connect to client
  try:
    print("")
    print("Program started...")
    print("Connecting to Client...")
    client = await connect_dydx()
  except Exception as e:
    print("Error connecting to client: ", e)
    send_message(f"Error connecting to client {e}")
    exit(1)
  send_message("Connected to Client")
#   # Abort all open positions
  if ABORT_ALL_POSITIONS:
    botAgentsEmpty = False
    while not botAgentsEmpty:
      try:
        print("")
        print("Closing open positions...")
        await abort_all_positions(client)
      except Exception as e:
        print("Error closing all positions: ", e)
        send_message(f"Error closing all positions {e}")
        # exit(1)
      file_path = "bot_agents.json"
      with open(file_path, 'r') as file:
        botAgentsLine = json.load(file)
      if botAgentsLine == []:
        botAgentsEmpty = True
  print("Positions closed.")
  
  # Wait until 30 minute update happens
  # wait_until_half_hour()

  # Need to be able to get all market prices. Put into table, then find, based on prices, which pairs are cointegrated
  # Bot doesn't need to continually fetch market prices. Only about once an hour/once a day since it takes a while.

  if CALCUATE_EMA:
    dataframe = await get_close_prices_100_days(client, "ETH-USD")
    print(dataframe)
    
    signalDataframe = await getSignals(dataframe)
    print(signalDataframe[signalDataframe['buy_signal']])
    print(signalDataframe[signalDataframe['sell_signal']])
    lastSignalDataframe = signalDataframe.iloc[-1]
    buy_signal = lastSignalDataframe['buy_signal']
    sell_signal = lastSignalDataframe['sell_signal']
    print(f"Last signal dataframe:\n{lastSignalDataframe}")
    print(f"Buy signal: {buy_signal}, Sell signal: {sell_signal}")
    send_message(f"Last signal dataframe:\n{lastSignalDataframe}")
    send_message(f"Detected signal \nBuy signal: {buy_signal}, Sell signal: {sell_signal}")

  #   try:
  #     print("Calculating EMA...")
  #     lastPrice, lastEma = await calculate_price_ema_pair(client, "ETH-USD")
  #   except Exception as e:
  #     print("Error calculating EMA: ", e)
  #     send_message(f"Error calculating EMA {e}")
  #     exit(1)
  # print(f"Last Price: {lastPrice}")
  # if lastPrice > lastEma:
  #   lastAction = "BUY"
  #   print("start action: BUY")
    
  # else:
  #   print("start action: SELL")
  #   lastAction = "SELL"

  # # delete
  # # lastAction = "BUY"
  # try:
  #   print("Placing initial order...")
  #   send_message("Placing initial order...")
  #   order,order_id = await placeOrder(client, "ETH-USD", 0.1, lastPrice, lastAction)
  # except Exception as e:
  #   print("Error placing initial order: ", e)
  #   send_message(f"Error placing initial order {e}")
  #   exit(1)
  
  # if order is None or order_id is None:
  #   print("Error placing initial order: Order or Order ID is None")
  #   send_message("Error placing initial order: Order or Order ID is None")
  #   exit(1)
  
  while True:
    wait_until_half_hour()
    wait_until_half_hour()
    time.sleep(1)
    send_message("Starting new loop...")
    dataframe = await get_close_prices_100_days(client, "ETH-USD")
    signalDataframe = await getSignals(dataframe)
    lastSignalDataframe = signalDataframe.iloc[-1]
    buy_signal = lastSignalDataframe['buy_signal']
    sell_signal = lastSignalDataframe['sell_signal']
    if buy_signal or sell_signal:
      send_message(f"Detected signal \nBuy signal: {buy_signal}, Sell signal: {sell_signal}")
      send_message(f"Last signal dataframe:\n{lastSignalDataframe}")

    

    # Calculate EMA
    # if CALCUATE_EMA:
    #   try:
    #     print("Calculating EMA...")
    #     send_message("Calculating EMA...")

    #     lastPrice, lastEma = await calculate_price_ema_pair(client, "ETH-USD")
    #   except Exception as e:
    #     print("Error calculating EMA: ", e)
    #     send_message(f"Error calculating EMA {e}")
    #     exit(1)
    # makeNewOrder = False
    # if lastPrice > lastEma and lastAction != "BUY":
    #   lastAction = "BUY"
    #   print("Last action: BUY")
    #   send_message("Last action: BUY")
    #   makeNewOrder = True
    # elif lastPrice <= lastEma and lastAction != "SELL":
    #   lastAction = "SELL"
    #   print("Last action: SELL")
    #   send_message("Last action: SELL")
    #   makeNewOrder = True


    # delete
    # if lastAction == "BUY":
    #   lastAction="SELL"
    # else:
    #   lastAction="BUY"
    # makeNewOrder = True
    # lastAction = "SELL"
    # if makeNewOrder:
    #   try:
    #     print("Placing order...")
    #     send_message("Placing order...")
    #     send_message(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    #     for i in range(50):
    #       try:
    #           order, order_id = await placeOrder(client, "ETH-USD", 0.1, lastPrice, lastAction)
    #           break  # success
    #       except Exception as e:
    #           print(f"Attempt {i+1}: gRPC failed: {e}")
    #           time.sleep(2 ** i)  # backoff
        
    #   except Exception as e:
    #     print("Restarting...")
    #     startCount+=1
    #     send_message(f"Error placing order: {e}. Restarting...")
    #     send_message(f"Restarting while loop due to error - {startCount}")
    #     try:
    #       print("")
    #       print("Closing open positions...")
    #       await abort_all_positions(client)
    #     except Exception as e:
    #       print("Error closing all positions: ", e)
    #       send_message(f"Error closing all positions {e}. Check manually.")
    #       exit(1)
    #     time.sleep(1)
    #     continue

    

    
    time.sleep(1)






#   if FIND_COINTEGRATED:
#     # Construct Market Prices
#     try:
#       print("Fetching market prices, please allow 3 minutes...")
#       dataframeMarketPrices = await ConstructMarketPrices(client)
#       print("---")
#       print(dataframeMarketPrices)
#       print("---")
#     except Exception as e:
#       print("Error constructing market prices: ", e)
#       send_message(f"Error constructing market prices {e}")
#       exit(1)

#     # Store Cointegration Pairs
#     try:
#       print("Storing cointegration pairs...")
#       storesResult = StoreCointegrationResults(dataframeMarketPrices)
#       if storesResult != "saved":
#         print("Error storing cointegration pairs")
#         exit(1)
#     except Exception as e:
#       print("Error saving cointegrated pairs: ", e)
#       exc_type, exc_obj, exc_tb = sys.exc_info()
#       fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
#       print(exc_type, fname, exc_tb.tb_lineno)
#       send_message(f"Error saving cointegrated pairs {e}")
#       exit(1)

# # # managing existing trades and while true loop here
#  # Manage existing positions
#   while True:
#     if MANAGE_EXITS:
#       try:
#         print("")
#         print("Managing exits...")
#         await manage_trade_exits(client)
#         time.sleep(1)
#       except Exception as e:
#         print("Error managing exiting positions: ", e)
#         send_message(f"Error managing exiting positions {e}")
#         exit(1)

#     # Place trades for opening positions
#     if PLACE_TRADES:
#       try:
#         print("")
#         print("Finding trading opportunities...")
        # await openPositions(client)
#       except Exception as e:
#         print("Error trading pairs: ", e)
#         send_message(f"Error opening trades {e}")
#         exit(1)

if __name__ == "__main__":
    asyncio.run(main())