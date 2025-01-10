from func_private import place_market_order, checkOrderStatus, cancel_order
from datetime import datetime
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

        # Guard: Aborder if order failed
        if orderStatusM1 != "live":
            self.orderDict["pairStatus"] = "ERROR"
            self.orderDict["comments"] = f"{self.market1} failed to fill"
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
        orderStatusM2 = await self.checkOrderStatusById(self.orderDict["orderIdM2"])

        # Guard: Aborder if order failed
        if orderStatusM2 != "live":
            self.orderDict["pairStatus"] = "ERROR"
            self.orderDict["comments"] = f"{self.market1} failed to fill"

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

                    # ABORT
                    exit(1)
            except Exception as e:
                self.orderDict["pairStatus"] = "ERROR"
                self.orderDict["comments"] = f"Close Market 1 {self.market1}: , {e}"
                print("ABORT PROGRAM")
                print("Unexpected Error")
                print(orderStatusCloseOrder)

                # ABORT
                exit(1)

        # Return success result
        else:
            print("")
            print("SUCCESS: LIVE PAIR")
            print("")
            self.orderDict["pairStatus"] = "LIVE"
            return self.orderDict