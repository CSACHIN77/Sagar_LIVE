import threading
import socketio
import json
from datetime import datetime
from utils import Logger
import time
from Publisher import Publisher

logger = Logger('socket_log.txt')

class MDSocket_io:
    def __init__(self, port, publisher, reconnection=True, reconnection_delay=1, reconnection_delay_max=5000, randomization_factor=0.5):
        self.publisher = publisher
        self.sid = socketio.Client(logger=False, engineio_logger=False)
        self.market_socket_data = []
        
        # Register event handlers
        self.register_event_handlers()
        self.current_data_time  = None
        # Connection settings
        self.reconnection_delay = reconnection_delay
        self.randomization_factor = randomization_factor
        self.reconnection_delay_max = reconnection_delay_max
        self.port = port
        self.connection_url = f'http://{self.port}'
        self.subscribed_symbols = list()

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
            overallData = json.loads(data['data']['OverallData'])
           
            exchangeInstrumentID = overallData['ExchangeInstrumentID']
            if exchangeInstrumentID in self.subscribed_symbols:
                self.publisher.publish_data(data)
                
            self.current_data_time = overallData
            self.current_data_time = self.current_data_time['LastUpdateTime']
            # print(self.current_data_time)
        except Exception as e:
            pass
            # print(f"Error processing data: {e}")

    def on_disconnect(self):
        print('Market Data Socket disconnected!')
        logger.log(f'Socket disconnected @ {datetime.now()}')

    def on_error(self, data):
        print('Market Data Error:', data)

    def disconnect(self):
        self.sid.disconnect()

    def subscribe_symbols(self, instruments):
        # new_instruments = []
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