import socketio
import threading
import json
import time
from utils import update_tradebook
from Logger.MyLogger import Logger

class OrderSocket_io:
    def __init__(self, port, publisher, reconnection=True, reconnection_attempts=0,
                 reconnection_delay=1, reconnection_delay_max=50000, randomization_factor=0.5,
                 logger=False, **kwargs):
        
        # Initialize socket.io client without token or userID
        self.sid = socketio.Client(logger=logger, engineio_logger=logger)
        self.eventlistener = self.sid
        self.publisher = publisher
        self.reconnection_delay = reconnection_delay
        self.randomization_factor = randomization_factor
        self.reconnection_delay_max = reconnection_delay_max
        self.orders = []
        self.positions = []
        self.trades = []
        self.stoploss_app_id = []
        
        # Port only, no userID or token required
        self.port = port
        self.logger = Logger('orders.txt')
        self.connection_url = f'http://localhost:{self.port}/'  
        
        # Registering event handlers
        self.register_event_handlers()

    def connect(self):
        threading.Thread(target=self.start_socket_connection).start()

    def start_socket_connection(self):
        while True:
            if not self.sid.connected:
                try:
                    self.sid.connect(
                        url=self.connection_url,
                        transports='websocket'
                    )
                    self.sid.wait()  # Keep connection alive
                except socketio.exceptions.ConnectionError as e:
                    print(f"Connection error: {e}")
                    time.sleep(self.reconnection_delay)
                    self.reconnection_delay = min(self.reconnection_delay * (1 + self.randomization_factor), self.reconnection_delay_max)

    def register_event_handlers(self):
        # Define event handlers for order, trade, etc.
        self.sid.on('connect', self.on_connect)
        self.sid.on('disconnect', self.on_disconnect)
        self.sid.on('orderUpdate', self.on_order)
        self.sid.on('tradeUpdate', self.on_trade)
        self.sid.on('position', self.on_position)
        self.sid.on('message', self.on_message)
        self.sid.on('tradeConversion', self.on_trade_conversion)
        self.sid.on('logout', self.on_logout)

    def on_connect(self):
        print('Connected to Interactive Socket successfully!')

    def on_disconnect(self):
        print('Disconnected from Interactive Socket!')

    def on_message(self, data):
        print(f'Received message: {data}')

    def on_order(self, data):
        # Parsing and logging the order data
        #note to dev : this part is not needed as the data is already in form of json unlike real ordersocket where we parse it to json format
        # data = json.loads(data) 
        self.orders.append(data)
        if data['OrderStatus'].upper() == 'OPEN':
            if data['AppOrderID'] in self.stoploss_app_id:
                print("Modifying order due to SL condition.")
        
        if data['OrderStatus'].upper() == 'NEW':
            self.logger.log(data)
            if data['OrderType'].upper() == 'STOPLIMIT':
                self.stoploss_app_id.append(data['AppOrderID'])
                print("Appended stoploss order ID.")

        # print(f"Order received: {data}")

    def on_trade(self, data):
        print("rupendra on trade socket update", data)
        # Parsing and logging trade data
        #notes to dev, similarly we dont need to convert it json as its already json
        # data = json.loads(data)
        self.trades.append(data)
        self.logger.log(data)
        
        # print(f"Trade received: {data}")
        
        # Publishing trade through the publisher
        self.publisher.publish_trade(data)

    def on_position(self, data):
        data = json.loads(data)
        self.positions.append(data)
        print(f"Position data: {data}")

    def on_trade_conversion(self, data):
        print(f"Trade Conversion event: {data}")

    def on_logout(self, data):
        print(f"User logout event: {data}")

    def get_emitter(self):
        return self.eventlistener

    def disconnect(self):
        self.sid.disconnect()
        print("Socket disconnected manually.")
