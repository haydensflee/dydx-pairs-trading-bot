from constants import ZSCORE_THRESH, USD_PER_TRADE, USD_MIN_COLLATERAL
from func_utils import format_number
from func_public import getCandlesRecent
from func_cointegration import calculateZScore
from func_private import isOpenPositions, get_markets, get_account
from func_bot_agent import BotAgent
import pandas as pd
import json

from pprint import pprint

IGNORE_ASSETS = ["BTC-USD_x", "BTC-USD_y"] # Ignore these assets which are not trading on testnet

# Open positions
async def openPositions(client):

  """
    Manage finding triggers for trade entry
    Store trades for managing later on on exit function
  """

  # Load cointegrated pairs
  df = pd.read_csv("cointegrated_pairs.csv")

  # Get markets from referencing of min order size, tick size etc
  markets = await get_markets(client)

  # Initialize container for BotAgent results
  bot_agents = []

  # Opening JSON file
  try:
    open_positions_file = open("bot_agents.json")
    open_positions_dict = json.load(open_positions_file)
    for p in open_positions_dict:
      bot_agents.append(p)
  except:
    bot_agents = []

  # Find ZScore triggers
  for index, row in df.iterrows():

    # Extract variables
    base_market = row["baseMarket"]
    quote_market = row["quoteMarket"]
    hedge_ratio = row["hedgeRatio"]
    half_life = row["halfLife"]
    # print(f"Base: {base_market} and Quote: {quote_market} with hedge ratio: {hedge_ratio} and half life: {half_life}")
    # Continue if ignore asset
    if base_market in IGNORE_ASSETS or quote_market in IGNORE_ASSETS:
      continue

    # Get prices
    try:
      series_1 = await getCandlesRecent(client, base_market)
      series_2 = await getCandlesRecent(client, quote_market)
    except Exception as e:
      print(e)
      continue
    
    # Get ZScore
    if len(series_1) > 0 and len(series_1) == len(series_2):
      spread = series_1 - (hedge_ratio * series_2)
      z_score = calculateZScore(spread).values.tolist()[-1]
      # print("spread: ", spread)
      print(f"Z-Score: {z_score} for {base_market} and {quote_market}")
      # Establish if potential trade
      if abs(z_score) >= ZSCORE_THRESH:

        # Ensure like-for-like not already open (diversify trading)
        is_base_open = await isOpenPositions(client, base_market)
        is_quote_open = await isOpenPositions(client, quote_market)

        # Place trade
        if not is_base_open and not is_quote_open:

          # Determine side
          base_side = "BUY" if z_score < 0 else "SELL"
          quote_side = "BUY" if z_score > 0 else "SELL"

          # Get acceptable price in string format with correct number of decimals
          base_price = series_1[-1]
          quote_price = series_2[-1]
          # Z-score<0 means market is a buy
          accept_base_price = float(base_price) * 1.01 if z_score < 0 else float(base_price) * 0.99
          accept_quote_price = float(quote_price) * 1.01 if z_score > 0 else float(quote_price) * 0.99
          # Failsafe price to make sure order gets filled to close and exit a trade.
          failsafe_base_price = float(base_price) * 0.05 if z_score < 0 else float(base_price) * 1.7
          base_tick_size = markets["markets"][base_market]["tickSize"]
          quote_tick_size = markets["markets"][quote_market]["tickSize"]

          # Format prices
          accept_base_price = format_number(accept_base_price, base_tick_size)
          accept_quote_price = format_number(accept_quote_price, quote_tick_size)
          accept_failsafe_base_price = format_number(failsafe_base_price, base_tick_size)

          # Get size
          base_quantity = 1 / base_price * USD_PER_TRADE
          quote_quantity = 1 / quote_price * USD_PER_TRADE
          base_step_size = markets["markets"][base_market]["stepSize"]
          quote_step_size = markets["markets"][quote_market]["stepSize"]

          # Format sizes
          base_size = format_number(base_quantity, base_step_size)
          quote_size = format_number(quote_quantity, quote_step_size)

          # Ensure size (minimum order size greater than $1 according to V4 documentation)
          base_min_order_size = 1 / float(markets["markets"][base_market]["oraclePrice"])
          quote_min_order_size = 1 / float(markets["markets"][quote_market]["oraclePrice"])

          # Combine checks
          check_base = float(base_quantity) > base_min_order_size
          check_quote = float(quote_quantity) > quote_min_order_size

          # If checks pass, place trades
          if check_base and check_quote:

            # Check account balance
            account = await get_account(client)
            free_collateral = float(account["freeCollateral"])
            print(f"Balance: {free_collateral} and minimum at {USD_MIN_COLLATERAL}")

            # Guard: Ensure collateral
            if free_collateral < USD_MIN_COLLATERAL:
              break
            print(base_market, base_side, base_size, accept_base_price)
            print(quote_market, quote_side, quote_size, accept_quote_price)
            exit(1)
            
            # Create Bot Agent
            bot_agent = BotAgent(
              client,
              market1=base_market,
              market2=quote_market,
              baseSide=base_side,
              baseSize=base_size,
              basePrice=accept_base_price,
              quoteSide=quote_side,
              quoteSize=quote_size,
              quotePrice=accept_quote_price,
              acceptFailsafeBasePrice=accept_failsafe_base_price,
              zScore=z_score,
              halfLife=half_life,
              hedgeRatio=hedge_ratio
            )

            # Open Trades
            bot_open_dict = await bot_agent.openTrades()

            # Guard: Handle failure
            if bot_open_dict == "failed":
              continue

            # Handle success in opening trades
            if bot_open_dict["pairStatus"] == "LIVE":

              # Append to list of bot agents
              bot_agents.append(bot_open_dict)
              del(bot_open_dict)

              # Save trade
              with open("bot_agents.json", "w") as f:
                json.dump(bot_agents, f)

              # Confirm live status in print
              print("Trade status: Live")
              print("---")

  # Save agents
  print(f"Success: Manage open trades checked")
  if len(bot_agents) > 0:
    with open("bot_agents.json", "w") as f:
      json.dump(bot_agents, f)