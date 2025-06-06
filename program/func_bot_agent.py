'''
func_bot_agent.py
This file contains the BotAgent class, which is used to manage the opening and checking of trades. The BotAgent class is used by the main function in the main.py file to open and check trades. The BotAgent class is responsible for placing market orders, checking the status of orders, and cancelling orders. The BotAgent class is used to manage the trading process for the bot.
'''
from func_private import place_market_order, checkOrderStatus, cancel_order
from datetime import datetime
from func_messaging import send_message
import time

from pprint import pprint


# Class: Agent for managing opening and checking trades
class BotAgent:

    """
    Primary function of BotAgent handles opening and checking order status
    """

    # Initialize class
    def __init__(
        self,
        client,
        market1,
        market2,
        baseSide,
        baseSize,
        basePrice,
        quoteSide,
        quoteSize,
        quotePrice,
        acceptFailsafeBasePrice,
        zScore,
        halfLife,
        hedgeRatio,
    ):

        # Initialize class variables
        self.client = client
        self.market1 = market1
        self.market2 = market2
        self.baseSide = baseSide
        self.baseSize = baseSize
        self.basePrice = basePrice
        self.quoteSide = quoteSide
        self.quoteSize = quoteSize
        self.quotePrice = quotePrice
        self.acceptFailsafeBasePrice = acceptFailsafeBasePrice
        self.zScore = zScore
        self.halfLife = halfLife
        self.hedgeRatio = hedgeRatio

        # Initialize output variable
        # Pair status options are FAILED, LIVE, CLOSE, ERROR
        self.orderDict = {
            "market1": market1,
            "market2": market2,
            "hedgeRatio": hedgeRatio,
            "zScore": zScore,
            "halfLife": halfLife,
            "orderIdM1": "",
            "orderM1Size": baseSize,
            "orderM1Side": baseSide,
            "orderTimeM1": "",
            "orderIdM2": "",
            "orderM2Size": quoteSize,
            "orderM2Side": quoteSide,
            "orderTimeM2": "",
            "pairStatus": "",
            "comments": "",
        }

    # Check order status by id
    async def checkOrderStatusById(self, orderId):

        # Allow time to process
        time.sleep(2)

        # Check order status
        orderStatus = await checkOrderStatus(self.client, orderId)

        # Guard: If order cancelled move onto next Pair
        if orderStatus == "CANCELED":
            print(f"{self.market1} vs {self.market2} - Order cancelled...")
            self.orderDict["pairStatus"] = "FAILED"
            return "failed"

        # Guard: If order not filled wait until order expiration
        if orderStatus != "FAILED":
            time.sleep(15)
            orderStatus = await checkOrderStatus(self.client, orderId)

            # Guard: If order cancelled move onto next Pair
            if orderStatus == "CANCELED":
                print(f"{self.market1} vs {self.market2} - Order cancelled...")
                self.orderDict["pairStatus"] = "FAILED"
                return "failed"

            # Guard: If not filled, cancel order
            if orderStatus != "FILLED":
                await cancel_order(self.client, orderId)
                self.orderDict["pairStatus"] = "ERROR"
                print(f"{self.market1} vs {self.market2} - Order error. Cancellation request sent, please check open orders..")
                return "error"

        # Return live
        return "live"

    # Open trades
    async def openTrades(self):
        """
        Opens trades for a pair of markets by placing market orders sequentially.

        This function performs the following steps:
        1. Places a market order for the first market.
        2. Checks if the first order is live.
        3. Places a market order for the second market.
        4. Checks if the second order is live.
        5. If the second order fails, attempts to close the first order.

        Returns:
            dict: A dictionary containing the status and details of the orders.

        Raises:
            Exception: If there is an error placing any of the orders or checking their status.
        """

        # Print status
        print("---")
        print(f"{self.market1}: Placing first order...")
        print(f"Side: {self.baseSide}, Size: {self.baseSize}, Price: {self.basePrice}")
        print("---")

        # Place Base Order
        try:
            (baseOrder, orderId) = await place_market_order(
                self.client,
                market=self.market1,
                side=self.baseSide,
                size=self.baseSize,
                price=self.basePrice,
                reduce_only=False
            )

            # Store the order id
            self.orderDict["orderIdM1"] = orderId
            self.orderDict["orderTimeM1"] = datetime.now().isoformat()
            print("First order sent...")
        except Exception as e:
            print(e)
            self.orderDict["pairStatus"] = "ERROR"
            self.orderDict["comments"] = f"Market 1 {self.market1}: , {e}"
            return self.orderDict

        # Ensure order is live before processing
        print("Checking first order status...")
        print(self.orderDict["orderIdM1"])
        orderStatusM1 = await self.checkOrderStatusById(self.orderDict["orderIdM1"])
        print(orderStatusM1)

        # Guard: Abort if order failed
        # Guard: Aborder if order failed
        if orderStatusM1 != "live" or baseOrder==-1:
            print("first order failed")
            self.orderDict["pair_status"] = "ERROR"
            self.orderDict["comments"] = f"{self.market1} failed to fill"
            print(self.orderDict["orderIdM1"],baseOrder)
            return "failed"
            return self.orderDict

        # Print status - opening second order
        print("---")
        print(f"{self.market2}: Placing second order...")
        print(f"Side: {self.quoteSide}, Size: {self.quoteSize}, Price: {self.quotePrice}")
        print("---")

        # Place Quote Order
        try:
            (quoteOrder, orderId) = await place_market_order(
                self.client,
                market=self.market2,
                side=self.quoteSide,
                size=self.quoteSize,
                price=self.quotePrice,
                reduce_only=False
            )

            # Store the order id
            print(orderId)
            self.orderDict["orderIdM2"] = orderId
            self.orderDict["orderTimeM2"] = datetime.now().isoformat()
            print("Second order sent...")
        except Exception as e:
            self.orderDict["pairStatus"] = "ERROR"
            self.orderDict["comments"] = f"Market 2 {self.market2}: , {e}"
            return self.orderDict

        # Ensure order is live before processing
        print("Checking second order status...")
        print(self.orderDict["orderIdM2"])
        print(self.orderDict)
        orderStatusM2 = await self.checkOrderStatusById(self.orderDict["orderIdM2"])
        print("Order status M2: ", orderStatusM2)
        print("quoteOrder: ", quoteOrder)
        # Guard: Abort if order failed
        if orderStatusM2 != "live" or quoteOrder==-1:
            self.orderDict["pairStatus"] = "ERROR"
            self.orderDict["comments"] = f"{self.market1} failed to fill"
            print("abort due to order failure")
            # Close order 1:
            try:
                (closeOrder, orderId) = await place_market_order(
                    self.client,
                    market=self.market1,
                    side=self.quoteSide,
                    size=self.baseSize,
                    price=self.acceptFailsafeBasePrice,
                    reduce_only=True
                )

                # Ensure order is live before proceeding
                time.sleep(2)
                orderStatusCloseOrder = await checkOrderStatus(self.client, orderId)
                if orderStatusCloseOrder != "FILLED":
                    print("ABORT PROGRAM")
                    print("Unexpected Error")
                    print(orderStatusCloseOrder)
                    send_message(f"Failed to execute. Code red. Error code: 100")
                    # ABORT
                    exit(1)
            except Exception as e:
                self.orderDict["pairStatus"] = "ERROR"
                self.orderDict["comments"] = f"Close Market 1 {self.market1}: , {e}"
                print("ABORT PROGRAM")
                print("Unexpected Error")
                print(orderStatusCloseOrder)

                send_message(f"Failed to execute. Code red. Error code: 101")
                # ABORT
                exit(1)
            return "failed"
        # Return success result
        else:
            print("")
            print("SUCCESS: LIVE PAIR")
            print("")
            self.orderDict["pairStatus"] = "LIVE"
            return self.orderDict