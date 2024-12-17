import asyncio

class TradeManager:
    def __init__(self):
        self.trade_data_event = asyncio.Event()
        self.trade_data = []

    async def producer(self, delay):
        """
        Simulate producing trade data with a delay.
        If delay exceeds timeout, consumer will timeout.
        """
        print(f"Producer will set trade data after {delay} seconds.")
        await asyncio.sleep(delay)
        self.trade_data.append({'LastTradedPrice': 100})  # Simulate trade data
        self.trade_data_event.set()  # Notify the consumer
        print("Producer: Trade data set.")

    async def leg_place_order(self):
        """
        Wait for trade data, but timeout if it takes longer than 5 seconds.
        """
        print('Consumer: Waiting for the trade data to be set...')
        try:
            await asyncio.wait_for(self.trade_data_event.wait(), timeout=5)
            self.trade_data_event.clear()
            latest_trade = self.trade_data[-1]
            print('Consumer: Trade data received:', latest_trade)
        except asyncio.TimeoutError:
            print('Consumer: Timeout occurred! No trade data received within 5 seconds.')

async def main():
    manager = TradeManager()
    
    # Case 1: Producer sets data within 3 seconds (success scenario)
    print("\n--- Case 1: Trade data set within timeout ---")
    asyncio.create_task(manager.producer(3))  # Producer will set data after 3 seconds
    await manager.leg_place_order()

    # Case 2: Producer takes too long to set data (timeout scenario)
    print("\n--- Case 2: Trade data exceeds timeout ---")
    asyncio.create_task(manager.producer(7))  # Producer will set data after 7 seconds
    await manager.leg_place_order()

# Run the example
asyncio.run(main())
