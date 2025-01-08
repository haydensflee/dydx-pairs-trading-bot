'''
func_bot_agent.py

'''
from func_private import place_market_order, CheckOrderStatus
from datetime import datetime, timedelta
import time
from pprint import pprint

# ----- Agent for opening and closing trades ----- #
class BotAgent:
    def __init__(self, client, market, side, size, price, reduce_only):
        self.client = client
        self.market = market
        self.side = side
        self.size = size
        self.price = price
        self.reduce_only = reduce_only
        self.order_id = None
    
    # Place Order
    async def place_order(self):
        try:
            self.order_id = await place_market_order(self.client, self.market, self.side, self.size, self.price, self.reduce_only)
            print(f"Order placed for {self.market} at {self.price} for {self.size} {self.side}.")
        except Exception as e:
            print(f"Error placing order: {e}")
            exit(1)
    
    # Check Order Status
    async def check_order_status(self):
        try:
            status = await CheckOrderStatus(self.client, self.order_id)
            print(f"Order status for {self.market}: {status}")
        except Exception as e:
            print(f"Error checking order status: {e}")
            exit(1)
    
    # Cancel Order
    async def cancel_order(self):
        try:
            await self.client.node.cancel_order(self.client.wallet, self.order_id)
            print(f"Order for {self.market} has been cancelled.")
        except Exception as e:
            print(f"Error cancelling order: {e}")
            exit(1)
