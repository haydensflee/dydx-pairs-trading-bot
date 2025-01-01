import asyncio
import time
from constants import ABORT_ALL_POSITIONS, FIND_COINTEGRATED, PLACE_TRADES, MANAGE_EXITS
from func_connections import connect_dydx
from func_private import abort_all_positions

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

if __name__ == "__main__":
    asyncio.run(main())