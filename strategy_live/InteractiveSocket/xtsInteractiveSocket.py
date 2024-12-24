import socketio
import threading
import json
import pandas as pd
import asyncio
import time
from datetime import datetime
# from utils import Logger, update_tradebook
class OrderSocket_io:
    def __init__(self, token, userID, port, publisher, reconnection=True, reconnection_attempts=0, reconnection_delay=1,
                 reconnection_delay_max=50000, randomization_factor=0.5, logger=False, binary=False, json=None,
                 **kwargs):
        self.sid = socketio.Client(logger=logger, engineio_logger=logger)
        self.eventlistener = self.sid
        self.publisher = publisher
        self.reconnection_delay = reconnection_delay
        self. randomization_factor=randomization_factor
        self.reconnection_delay_max = reconnection_delay_max
        self.register_event_handlers()
        self.orders = []
        self.position = []
        self.trades = []
        self.port = port
        self.userID = userID
        self.token = token
        # self.logger = Logger('orders.txt')
        self.stoploss_app_id =[]
        # self.publisher = publisher
        self.connection_url = f'{self.port}/?token={self.token}&userID={self.userID}&apiType=INTERACTIVE'
        self.check_event = asyncio.Event()
    def connect(self, headers={}, transports='websocket', namespaces=None, socketio_path='/interactive/socket.io',
                verify=False):
        threading.Thread(target=self.start_socket_connection).start()

    def start_socket_connection(self):
                while True:
                    if not self.sid.connected:
                        try:
                            # try:
                                self.sid.connect(
                                    url=self.connection_url,
                                    headers= {},#self.headers,
                                    transports='websocket',
                                    namespaces=None,
                                    socketio_path='/interactive/socket.io'
                                )
                                self.sid.wait()  
                            # except:
                            #     print("already connected")
                        except socketio.exceptions.ConnectionError as e:
                            # print(f"error in order socket {e}")
                            pass
                            # time.sleep(self.reconnection_delay)
                            # self.reconnection_delay = min(self.reconnection_delay * (1 + self.randomization_factor), self.reconnection_delay_max) 
                    else:                
                        pass


    def register_event_handlers(self):
        """
        Registers event handlers for various socket events. Each event handler 
        corresponds to a specific event emitted by the server and triggers the 
        appropriate callback method.

        Events and their corresponding handlers:
        - 'connect': Triggered when the socket connects to the server (handled by `on_connect`).
        - 'message': Handles incoming general messages (handled by `on_message`).
        - 'joined': Triggered when a user joins (handled by `on_joined`).
        - 'error': Handles error events (handled by `on_error`).
        - 'order': Handles order-related updates (handled by `on_order`).
        - 'trade': Handles trade updates (handled by `on_trade`).
        - 'position': Handles position updates (handled by `on_position`).
        - 'tradeConversion': Handles trade conversion updates (handled by `on_tradeconversion`).
        - 'logout': Handles logout events (handled by `on_messagelogout`).
        - 'disconnect': Triggered when the socket disconnects from the server (handled by `on_disconnect`).
        """
        self.sid.on('connect', self.on_connect)
        self.sid.on('message', self.on_message)
        self.sid.on('joined', self.on_joined)
        self.sid.on('error', self.on_error)
        self.sid.on('order', self.on_order)
        self.sid.on('trade', self.on_trade)
        self.sid.on('position', self.on_position)
        self.sid.on('tradeConversion', self.on_tradeconversion)
        self.sid.on('logout', self.on_messagelogout)
        self.sid.on('disconnect', self.on_disconnect)


    def on_connect(self):
        print('Interactive socket connected successfully!')

    def on_message(self):
        print('I received a message!')

    def on_joined(self, data):
        pass

    def on_error(self, data):
        print('Interactive socket error!' + data)

    def on_order(self, data):
        """
        Handles the 'order' event, processes incoming order data, and updates internal state.

        Parameters:
        data (str): A JSON string representing the order details.

        Functionality:
        - Parses the incoming JSON data and appends it to the `orders` list.
        - Checks the `OrderStatus` field and performs actions based on its value:
            - If `OrderStatus` is 'OPEN' and the `AppOrderID` exists in the `stoploss_app_id` list, 
            prints a message indicating the order is being modified.
            - If `OrderStatus` is 'NEW' and the `OrderType` is 'STOPLIMIT', 
            appends the `AppOrderID` to the `stoploss_app_id` list and prints a confirmation message.
        - Debugging messages are printed for insights during execution.
        """
        data = json.loads(data)
        self.orders.append(data)
        # print(data)
        if data['OrderStatus'].upper() == 'OPEN':
            if data['AppOrderID'] in self.stoploss_app_id:
                print(f"Modifying order because SL is getting skipped")
        if data['OrderStatus'].upper() == 'NEW':
            # self.logger.log(data)  # Optional: Log data if logging is enabled
            if data['OrderType'].upper() == 'STOPLIMIT':
                print('adding app order id of trigger stoploss orders')
                self.stoploss_app_id.append(data['AppOrderID'])
                print(type(data['AppOrderID']))

            

    def on_trade(self, data):
        data= json.loads(data)

        print(f'interactive on_trade method being called @ {datetime.now()}')
        # if data['OrderUniqueIdentifier'] == 'leg1':
        #     print(data)
        self.publisher.publish_trade(data)
       

    def on_position(self, data):
        """
        Handles the 'position' event, processes incoming position data, and optionally logs or stores it.

        Parameters:
        data (str): A JSON string containing position details.

        Functionality:
        - Parses the incoming JSON string into a Python dictionary.
        - Optional actions (commented out):
            - Logs the position data to the `position` list.
            - Converts the `position` list into a Pandas DataFrame.
            - Exports the DataFrame to a CSV file named 'net_position.csv'.
        - Debugging messages or additional processing can be added as needed.
        """
        # print("Position Retrieved!" + data)  # Debugging: Print a message when position data is received
        data = json.loads(data)  # Parse the JSON string into a dictionary
        # print(data)  # Debugging: Print the parsed position data
        # self.position.append(data)  # Store the position data in a list
        # df = pd.DataFrame(self.position)  # Convert the list of positions to a Pandas DataFrame
        # df.to_csv('net_position.csv', index=False)  # Export the DataFrame to a CSV file

        

    def on_tradeconversion(self, data):
        print("Trade Conversion Received!" + data)

    def on_messagelogout(self, data):
        print("User logged out!" + data)

    def on_disconnect(self):
        # print('Interactive Socket disconnected!')
        pass

    def get_emitter(self):
        return self.eventlistener

    def disconnect(self):
        self.sid.disconnect()
