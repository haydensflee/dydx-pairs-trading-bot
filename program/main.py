import asyncio
import time
from constants import ABORT_ALL_POSITIONS, FIND_COINTEGRATED, PLACE_TRADES, MANAGE_EXITS
from func_connections import connect_dydx
from func_private import abort_all_positions
from func_public import ConstructMarketPrices
from func_cointegration import StoreCointegrationResults

async def main():
  # Message on start
  # send_message("Bot launch successful")
  print("hello world")

  # Connect to client
  try:
    print("")
    print("Program started...")
    print("Connecting to Client...")
    client = await connect_dydx()
  except Exception as e:
    print("Error connecting to client: ", e)
    exit(1)

#   # Abort all open positions
  if ABORT_ALL_POSITIONS:
    try:
      print("")
      print("Closing open positions...")
      await abort_all_positions(client)
    except Exception as e:
      print("Error closing all positions: ", e)
      # send_message(f"Error closing all positions {e}")
      exit(1)

  # Need to be able to get all market prices. Put into table, then find, based on prices, which pairs are cointegrated
  # Bot doesn't need to continually fetch market prices. Only about once an hour/once a day since it takes a while.

  if FIND_COINTEGRATED:
    # Construct Market Prices
    try:
      print("Fetching market prices, please allow 3 minutes...")
      dataframeMarketPrices = await ConstructMarketPrices(client)
    except Exception as e:
      print("Error constructing market prices: ", e)
      exit(1)

    # Store Cointegration Pairs
    try:
      print("Storing cointegration pairs...")
      storesResult = StoreCointegrationResults(dataframeMarketPrices)
      if storesResult != "saved":
        print("Error storing cointegration pairs")
        exit(1)
    except Exception as e:
      print("Error constructing market prices: ", e)
      exit(1)


if __name__ == "__main__":
    asyncio.run(main())