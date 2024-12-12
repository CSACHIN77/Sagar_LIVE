import json
from datetime import datetime
from utils import update_tradebook
import asyncio
class Publisher:
    def __init__(self):
        self.subscribers = []
        self.running = False
        self.trade_subscriber = []

    def add_subscriber(self, subscriber, instrument_token):
        self.subscribers.append({'subscriber': subscriber, 'instrument_token': instrument_token})
        print(f'subscribed {subscriber.leg_name}')

    def remove_subscriber(self, subscriber):
        for sub in self.subscribers:
            if sub['subscriber'] == subscriber:
                self.subscribers.remove(sub)

    def publish_data(self, data):
        # data = data['data']['OverallData']
        # data = json.loads(data)
        for sub in self.subscribers:
            for instrument in sub['instrument_token']:
                # print(f"data_instrument {data['ExchangeInstrumentID']} and instrument is {instrument}")
                if data['ExchangeInstrumentID'] == instrument:
                    # print(f'received data  in publisher {data} @ {datetime.now()}')
                    asyncio.run(sub['subscriber'].receive_data(data))
                
    def publish_trade(self, data):
        print('publish trade is invoked')
        for sub in self.trade_subscriber:
            # print(data)
            # print(sub['subscriber'].leg_name)
            if (data['OrderUniqueIdentifier']).startswith(sub['subscriber'].leg_name):
                print(f"sending data to {sub['subscriber'].leg_name}")
                asyncio.run(sub['subscriber'].receive_trades(data))

    # async def publish_trade(self, data):
    #     print('publish trade is invoked')
    #     for sub in self.trade_subscriber:
    #         if (data['OrderUniqueIdentifier']).startswith(sub['subscriber'].leg_name):
    #             print(f"sending data to {sub['subscriber'].leg_name}")
    #             await sub['subscriber'].receive_trades(data)

    # def publish_trade(self, data):
    #     loop = asyncio.get_event_loop()
    #     print('publish trade is invoked')
    #     for sub in self.trade_subscriber:
    #         if (data['OrderUniqueIdentifier']).startswith(sub['subscriber'].leg_name):
    #             print(f"sending data to {sub['subscriber'].leg_name}")
    #             loop.create_task(sub['subscriber'].receive_trades(data))

    def add_trade_subscriber(self, leg):
        self.trade_subscriber.append({'subscriber': leg})
        print(f'subscribed {leg.leg_name}')
    def start_publishing(self):
        self.running = True

    def stop_publishing(self):
        self.running = False