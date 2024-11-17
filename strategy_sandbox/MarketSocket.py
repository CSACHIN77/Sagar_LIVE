import threading
import socketio
import json
from datetime import datetime
from utils import Logger
import time
logger = Logger('socket_log.txt')
class MDSocket_io:
    def __init__(self, token, userID, port, publisher, reconnection=True, reconnection_attempts=0, reconnection_delay=1,
                 reconnection_delay_max=50000, randomization_factor=0.5, logger=False, binary=False, json=None,
                 **kwargs):
        self.publisher = publisher
        self.sid = socketio.Client(logger=False, engineio_logger=False)
        self.eventlistener = self.sid
        self.market_socket_data =[]
        # Register event handlers
        self.register_event_handlers()
        self.reconnection_delay = reconnection_delay
        self. randomization_factor=randomization_factor
        self.reconnection_delay_max = reconnection_delay_max
        self.port = port
        self.userID = userID
        self.token = token

        self.publishFormat = 'JSON'
        self.broadcastMode = "Full"
        self.headers = {'Content-Type': 'application/json', 'Authorization': token}
        self.connection_url = f'{self.port}/?token={self.token}&userID={self.userID}&publishFormat={self.publishFormat}&broadcastMode={self.broadcastMode}'

    def connect(self):
        threading.Thread(target=self.start_socket_connection).start()
        
    def start_socket_connection(self):
        # self.sid.connect(url=self.connection_url, headers=self.headers, transports='websocket', namespaces=None, socketio_path='/apimarketdata/socket.io')
        # self.sid.wait()
        while True:
                    if not self.sid.connected:
                        try:
                            try:
                                self.sid.connect(
                                    url=self.connection_url,
                                    headers=self.headers,
                                    transports='websocket',
                                    namespaces=None,
                                    socketio_path='/apimarketdata/socket.io'
                                )
                                self.sid.wait()  
                            except:
                                print("already connected")
                        except socketio.exceptions.ConnectionError as e:
                            pass
                            # time.sleep(self.reconnection_delay)
                            # self.reconnection_delay = min(self.reconnection_delay * (1 + self.randomization_factor), self.reconnection_delay_max) 
                    else:                
                        pass
    def register_event_handlers(self):
        self.sid.on('connect', self.on_connect)
        self.sid.on('disconnect', self.on_disconnect)
        self.sid.on('error', self.on_error)
        self.sid.on('1501-json-full', self.on_message1501_json_full)
        self.sid.on('1512-json-full', self.on_message1512_json_full)
        self.sid.on('disconnect', self.on_disconnect)
        self.sid.on('error', self.on_error)
    def on_connect(self):
        print('Market Data Socket connected successfully!')
        logger.log(f'socket reconnected @ {datetime.now()}')
    def on_message1501_json_full(self, data):
        print('I received a 1501 Level1, Touchline message!', data)

    def on_message1512_json_full(self, data):
        data = json.loads(data)
        
        self.publisher.publish_data(data)
        # print(f'sent data to publisher @ {datetime.now()}')
        
    def on_disconnect(self):
        print('Market Data Socket disconnected!')
        logger.log(f'socket disconnected @ {datetime.now()}')
    def on_error(self, data):
        print('Market Data Error:', data)

    def get_emitter(self):
        return self.eventlistener

    def disconnect(self):
        self.sid.disconnect()
