'''
constants.py
This file contains all the constants that are used in the program.
Constants are effectively triggers, which are used to define the behavior of the program and can be changed to modify the program's behavior.
'''
from decouple import config

# For gathering tesnet data or live market data for cointegration calculation
MARKET_DATA_MODE = "TESTNET" # vs "MAINNET"

# Close all open positions and orders
ABORT_ALL_POSITIONS = False

# Find Cointegrated Pairs
FIND_COINTEGRATED = False

# Calculate EMA
CALCUATE_EMA = True

# Manage Exits
MANAGE_EXITS = False

# Place Trades
PLACE_TRADES = False

# Resolution
RESOLUTION = "30MINS"

# Stats Window
WINDOW = 21

# Thresholds - Opening
MAX_HALF_LIFE = 24
ZSCORE_THRESH = 1.01 #1.5
USD_PER_TRADE = 10
USD_MIN_COLLATERAL = 100

# Thresholds - Closing
CLOSE_AT_ZSCORE_CROSS = True

# Endpoint for Account Queries on Testnet
INDEXER_ENDPOINT_TESTNET = "https://indexer.v4testnet.dydx.exchange"
INDEXER_ENDPOINT_MAINNET = "https://indexer.dydx.trade"
INDEXER_ACCOUNT_ENDPOINT = INDEXER_ENDPOINT_TESTNET

# Environment Variables
DYDX_ADDRESS = config("DYDX_ADDRESS")
SECRET_PHRASE = config("SECRET_PHRASE")
MNEMONIC = (SECRET_PHRASE)
TELEGRAM_TOKEN = config("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = config("TELEGRAM_CHAT_ID")

# EMA 
EMA_PERIOD = 20
SMOOTHING_FACTOR = 2 / (EMA_PERIOD + 1)
