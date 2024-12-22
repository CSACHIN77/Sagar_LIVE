# import threading
# import socketio
# import json
# from datetime import datetime
# from utils import Logger
# import time
# from Publisher import Publisher

# logger = Logger('socket_log.txt')

# class MDSocket_io:
#     def __init__(self, port, publisher, reconnection=True, reconnection_delay=1, reconnection_delay_max=5000, randomization_factor=0.5):
#         self.publisher = publisher
#         self.sid = socketio.Client(logger=False, engineio_logger=False)
#         self.market_socket_data = []
#         self.counter = 1
#         self.register_event_handlers()
#         self.current_data_time  = None
#         self.reconnection_delay = reconnection_delay
#         self.randomization_factor = randomization_factor
#         self.reconnection_delay_max = reconnection_delay_max
#         self.port = port
#         self.connection_url = f'http://{self.port}'
#         self.subscribed_symbols = list()

#     def connect(self):
#         threading.Thread(target=self.start_socket_connection).start()
        
#     def start_socket_connection(self):
#         while True:
#             if not self.sid.connected:
#                 try:
#                     self.sid.connect(
#                         url=self.connection_url,
#                         transports='websocket',
#                         namespaces=None
#                     )
#                     self.sid.wait()
#                 except socketio.exceptions.ConnectionError as e:
#                     print("Connection error:", e)
#                     time.sleep(self.reconnection_delay)
#                     self.reconnection_delay = min(self.reconnection_delay * (1 + self.randomization_factor), self.reconnection_delay_max)
#             else:
#                 time.sleep(1)

#     def register_event_handlers(self):
#         self.sid.on('connect', self.on_connect)
#         self.sid.on('disconnect', self.on_disconnect)
#         self.sid.on('error', self.on_error)
#         self.sid.on('message', self.on_message)

#     def on_connect(self):
#         print('Market Data Socket connected successfully!')
#         logger.log(f'Socket reconnected @ {datetime.now()}')

#     def on_message(self, data):
#         try:
#             if isinstance(data['data'], list):
#                 for instrument_data in data['data']:
#                     overallData = instrument_data['OverallData']
#                     # print(overallData)
#                     exchangeInstrumentID = overallData['ExchangeInstrumentID']
#                     if exchangeInstrumentID in self.subscribed_symbols:
#                         self.publisher.publish_data(overallData)
                        
#                     self.current_data_time = overallData
#                     self.current_data_time = overallData['LastUpdateTime']
#                 # print(self.current_data_time)
#         except Exception as e:
#             # print(data['data'])
#             print(f"Error processing data: {e} ")

#     def on_disconnect(self):
#         print('Market Data Socket disconnected!')
#         logger.log(f'Socket disconnected @ {datetime.now()}')

#     def on_error(self, data):
#         print('Market Data Error:', data)

#     def disconnect(self):
#         self.sid.disconnect()

#     def subscribe_symbols(self, instruments):
#         # new_instruments = []
#         for instrument in instruments:
#             ex_id = instrument['exchangeInstrumentID']
#             if ex_id not in self.subscribed_symbols:
#                 self.subscribed_symbols.append(ex_id)
#                 print(f"{ex_id} subscribed to instruments")

#     def unsubscribe_symbols(self, instruments):
#         for instrument in instruments:
#             ex_id = instrument['exchangeInstrumentID']
#             if ex_id in self.subscribed_symbols:
#                 self.subscribed_symbols.remove(ex_id)
#         print(f"unsubscribed from instruments")


import threading
import socketio
import json
from datetime import datetime
from utils import Logger
import time
from Publisher import Publisher
import redis
from collections import deque

logger = Logger('socket_log.txt')

class MDSocket_io:
    def __init__(self, port, publisher, reconnection=True, reconnection_delay=1, reconnection_delay_max=5000, randomization_factor=0.5):
        self.publisher = publisher
        self.sid = socketio.Client(logger=False, engineio_logger=False)
        self.market_socket_data = []
        self.counter = 1
        self.register_event_handlers()
        self.current_data_time = None
        self.reconnection_delay = reconnection_delay
        self.randomization_factor = randomization_factor
        self.reconnection_delay_max = reconnection_delay_max
        self.port = port
        self.connection_url = f'http://{self.port}'
        self.subscribed_symbols = list()
        self._market_data = None
        # Redis initialization
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.data_queue = deque()
        
        # Start the Redis consumer thread
        threading.Thread(target=self.process_redis_data, daemon=True).start()

    def connect(self):
        threading.Thread(target=self.start_socket_connection).start()
        
    def start_socket_connection(self):
        while True:
            if not self.sid.connected:
                try:
                    self.sid.connect(
                        url=self.connection_url,
                        transports='websocket',
                        namespaces=None
                    )
                    self.sid.wait()
                except socketio.exceptions.ConnectionError as e:
                    print("Connection error:", e)
                    time.sleep(self.reconnection_delay)
                    self.reconnection_delay = min(self.reconnection_delay * (1 + self.randomization_factor), self.reconnection_delay_max)
            else:
                time.sleep(1)

    def register_event_handlers(self):
        self.sid.on('connect', self.on_connect)
        self.sid.on('disconnect', self.on_disconnect)
        self.sid.on('error', self.on_error)
        self.sid.on('message', self.on_message)

    def on_connect(self):
        print('Market Data Socket connected successfully!')
        logger.log(f'Socket reconnected @ {datetime.now()}')

    def on_message(self, data):
        try:
            if isinstance(data['data'], list):
                # Push the entire data list to Redis
                self._market_data = data['data']
                timestamp = datetime.now().timestamp()
                data_with_timestamp = {
                    'timestamp': timestamp,
                    'data': data['data']
                }
                self.redis_client.rpush('market_data', json.dumps(data_with_timestamp))
                
        except Exception as e:
            print(f"Error processing data: {e}")

    def process_redis_data(self):
        """Process data from Redis in the order it was received"""
        while True:
            try:
                # Get the oldest data from Redis
                raw_data = self.redis_client.lpop('market_data')
                if raw_data:
                    data = json.loads(raw_data)
                    market_data = data['data']
                    
                    # Process each instrument data in the list
                    for instrument_data in market_data:
                        
                        overallData = instrument_data['OverallData']
                        exchangeInstrumentID = overallData['ExchangeInstrumentID']
                        if exchangeInstrumentID in self.subscribed_symbols:
                            self.publisher.publish_data(overallData)
                        if self.counter ==1:
                            print(overallData)
                            self.counter +=1
                        #self.current_data_time = overallData
                        self.current_data_time = overallData['LastUpdateTime']
                
                time.sleep(0.001)  # Small delay to prevent CPU overuse
                
            except Exception as e:
                print(f"Error processing Redis data: {e}")
                time.sleep(1)  # Longer delay on error

    def on_disconnect(self):
        print('Market Data Socket disconnected!')
        logger.log(f'Socket disconnected @ {datetime.now()}')

    def on_error(self, data):
        print('Market Data Error:', data)

    def disconnect(self):
        self.sid.disconnect()

    def subscribe_symbols(self, instruments):
        for instrument in instruments:
            ex_id = instrument['exchangeInstrumentID']
            if ex_id not in self.subscribed_symbols:
                self.subscribed_symbols.append(ex_id)
                print(f"{ex_id} subscribed to instruments")

    def unsubscribe_symbols(self, instruments):
        for instrument in instruments:
            ex_id = instrument['exchangeInstrumentID']
            if ex_id in self.subscribed_symbols:
                self.subscribed_symbols.remove(ex_id)
        print(f"unsubscribed from instruments")