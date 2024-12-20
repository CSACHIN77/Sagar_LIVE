import threading
import socketio
import json
from datetime import datetime
import time
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
        """
        Registers event handlers for specific socket events. Each handler corresponds
        to a specific event emitted by the server and triggers an appropriate callback.

        Functionality:
        - Sets up event listeners for the socket connection to handle various events, such as:
            - `connect`: Triggered when the socket successfully connects (handled by `on_connect`).
            - `disconnect`: Triggered when the socket disconnects (handled by `on_disconnect`).
            - `error`: Triggered when an error occurs (handled by `on_error`).
            - `1501-json-full`: Handles data for event `1501-json-full` (handled by `on_message1501_json_full`).
            - `1512-json-full`: Handles data for event `1512-json-full` (handled by `on_message1512_json_full`).

        Notes:
        - The `disconnect` and `error` event handlers are registered multiple times, which is redundant.
        - Consider removing duplicate registrations for `disconnect` and `error` to streamline the code.
        """
        self.sid.on('connect', self.on_connect)
        self.sid.on('error', self.on_error)
        self.sid.on('1501-json-full', self.on_message1501_json_full)
        self.sid.on('1512-json-full', self.on_message1512_json_full)
        self.sid.on('disconnect', self.on_disconnect)  

    def on_connect(self):
        pass
        # print('Market Data Socket connected successfully!')
        # logger.log(f'socket reconnected @ {datetime.now()}')

    def on_message1501_json_full(self, data):
        print('I received a 1501 Level1, Touchline message!', data)


    def on_message1512_json_full(self, data):
        """
        Handles the '1512-json-full' event by processing the incoming JSON data and publishing it.

        Parameters:
        data (str): A JSON string containing the full message data for the '1512-json-full' event.

        Functionality:
        - Parses the incoming JSON string into a Python dictionary using `json.loads`.
        - Publishes the parsed data using the `publisher` object's `publish_data` method.
        """
        data = json.loads(data) 
        self.publisher.publish_data(data)  

        
        
    def on_disconnect(self):
        #handles event for disconnect
        pass
    
    def on_error(self, data):
        print('Market Data Error:', data)

    def get_emitter(self):
        return self.eventlistener

    def disconnect(self):
        self.sid.disconnect()
