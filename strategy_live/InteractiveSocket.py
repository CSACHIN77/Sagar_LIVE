import socketio
import threading
import json
import pandas as pd
import asyncio
import time
from utils import Logger, update_tradebook
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
        self.logger = Logger('orders.txt')
        self.stoploss_app_id =[]
        # self.publisher = publisher
        self.connection_url = f'{self.port}/?token={self.token}&userID={self.userID}&apiType=INTERACTIVE'

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
        # self.sid.connect(url=self.connection_url, headers={}, transports='websocket', namespaces=None, socketio_path='/interactive/socket.io')
        # self.sid.wait()

    def register_event_handlers(self):
        # Define event handlers
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
        print('Interactive socket joined successfully!' + data)

    def on_error(self, data):
        print('Interactive socket error!' + data)

    def on_order(self, data):
        # print("Order placed!" + data)
        data = json.loads(data)
        self.orders.append(data)
        if data['OrderStatus'].upper()=='OPEN':
             if data['AppOrderID'] in self.stoploss_app_id:
                  print(f"Modifying order because SL is getting skipped")
        if data['OrderStatus'].upper() == 'NEW':
            self.logger.log(data)
            if data['OrderType'].upper() =='STOPLIMIT':
                print('adding app order id of trigger stoploss orders')
                self.stoploss_app_id.append(data['AppOrderID'])
                print(type(data['AppOrderID']))
            
            # print(self.orders)
        # print(data)
        # if data['OrderStatus']=='New':
        # if data['type']=='success':
        #     print(f"market {data['OrderSide']}  order placed for {data['TradingSymbol']} with quantity {data['OrderQuantity']}")

    def on_trade(self, data):
        data= json.loads(data)
        self.logger.log(data)
        print('interactive on_trade method being called')
        # if data['OrderUniqueIdentifier'] == 'leg1':
        #     print(data)
        self.publisher.publish_trade(data)
        # # self.trades.append(data)
        # if str(data['OrderUniqueIdentifier']).startswith('sl_order'):
        #     print(f'SL triggered for {data["TradingSymbol"]} @ {data["LastExecutionTransactTimeAPI"]}')
        #     print(f"re-entry can be done now for the symbol {data['TradingSymbol']}")

        # else:
        #     print(f"{data['OrderSide']} order executed for {data['TradingSymbol']} @ {data['OrderAverageTradedPrice']} quantity {data['OrderQuantity']}")

    def on_position(self, data):
        # print("Position Retrieved!" + data)
        data = json.loads(data)
        # print(data)
        # self.position.append(data)
        # df = pd.DataFrame(self.position)
        # df.to_csv('net_position.csv', index=False)
        

    def on_tradeconversion(self, data):
        print("Trade Conversion Received!" + data)

    def on_messagelogout(self, data):
        print("User logged out!" + data)

    def on_disconnect(self):
        print('Interactive Socket disconnected!')

    def get_emitter(self):
        return self.eventlistener

    def disconnect(self):
        self.sid.disconnect()
