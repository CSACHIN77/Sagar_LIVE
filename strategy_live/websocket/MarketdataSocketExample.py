from datetime import datetime
import pandas as pd
import time
from Connect import XTSConnect
from MarketDataSocketClient import MDSocket_io
socket_data =[]
# MarketData API Credentials
API_KEY = "1f440830af1d82a7a09251"
API_SECRET = "Dllf432@Co"
source = "WEBAPI"
# Initialise
xt = XTSConnect(API_KEY, API_SECRET, source)
class Logger:
    def __init__(self):
        self.log_file = open("streaming_data.txt", "a")  # Open log file in append mode
    
    def log(self, message):
        # timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # print(message)  # Print to console
        self.log_file.write(message + "\n")  # Write to log file
logger = Logger()
# Login for authorization token
response = xt.marketdata_login()

# Store the token and userid
set_marketDataToken = response['result']['token']
set_muserID = response['result']['userID']
print("Login: ", response)

# Connecting to Marketdata socket
soc = MDSocket_io(set_marketDataToken, set_muserID)

# Instruments for subscribing
Instruments = [
                # {'exchangeSegment': 1, 'exchangeInstrumentID': 2885},
                # {'exchangeSegment': 1, 'exchangeInstrumentID': 26000}
                {'exchangeSegment': 2, 'exchangeInstrumentID': 68092}
               ]
Instruments = [{'exchangeSegment': 2, 'exchangeInstrumentID': 68092}, {'exchangeSegment': 2, 'exchangeInstrumentID': 68093}, {'exchangeSegment': 2, 'exchangeInstrumentID': 67516}, {'exchangeSegment': 2, 'exchangeInstrumentID': 67517}]
df = pd.read_csv('nsecm_master.csv')
# Instruments = []
# for idx, row in df[0:799].iterrows():
#     Instruments.append({'exchangeSegment': 1, 'exchangeInstrumentID': row['ExchangeInstrumentID']})
print(Instruments)
# Instruments = [{'exchangeSegment': 2, 'exchangeInstrumentID': 68092}]
# time.sleep(5)
# Callback for connection
def on_connect():
    """Connect from the socket."""
    print('Market Data Socket connected successfully!')
    # # Subscribe to instruments
    print('Sending subscription request for Instruments - \n' + str(Instruments))
    response = xt.send_subscription(Instruments, 1512)
    print('Sent Subscription request!')
    print("Subscription response: ", response)

# Callback on receiving message
def on_message(data):
    # print('I received a message!')
    print(data)
    pass

# Callback for message code 1501 FULL
def on_message1501_json_full(data):
    # print('I received a 1501 Touchline message!' + data)
    pass

# Callback for message code 1502 FULL
def on_message1502_json_full(data):
    # print('I received a 1502 Market depth message!' + data)
    # print(data)
    # logger.log(data)
    # socket_data.append(data)
    pass

# Callback for message code 1505 FULL
def on_message1505_json_full(data):
    # print('I received a 1505 Candle data message!' + data)
    pass
    print(data)
    logger.log(data)
# Callback for message code 1507 FULL
def on_message1507_json_full(data):
    # print('I received a 1507 MarketStatus data message!' + data)
    pass

# Callback for message code 1510 FULL
def on_message1510_json_full(data):
    # print('I received a 1510 Open interest message!' + data)
    pass

# Callback for message code 1512 FULL
def on_message1512_json_full(data):
    # print('I received a 1512 Level1,LTP message!' + data)
    print(data)
    logger.log(data)


# Callback for message code 1105 FULL
def on_message1105_json_full(data):
    # print('I received a 1105, Instrument Property Change Event message!' + data)
    print(data)


# Callback for message code 1501 PARTIAL
def on_message1501_json_partial(data):
    # print('I received a 1501, Touchline Event message!' + data)
    pass

# Callback for message code 1502 PARTIAL
def on_message1502_json_partial(data):
    # print('I received a 1502 Market depth message!' + data)
    pass

# Callback for message code 1505 PARTIAL
def on_message1505_json_partial(data):
    # print('I received a 1505 Candle data message!' + data)
    print(data)

# Callback for message code 1510 PARTIAL
def on_message1510_json_partial(data):
    # print('I received a 1510 Open interest message!' + data)
    pass

# Callback for message code 1512 PARTIAL
def on_message1512_json_partial(data):
    # print('I received a 1512, LTP Event message!' + data)
    print(data)
    logger.log(data)



# Callback for message code 1105 PARTIAL
def on_message1105_json_partial(data):
    # print('I received a 1105, Instrument Property Change Event message!' + data)
    pass

# Callback for disconnection
def on_disconnect():
    print('Market Data Socket disconnected!')


# Callback for error
def on_error(data):
    """Error from the socket."""
    print('Market Data Error', data)


# Assign the callbacks.
soc.on_connect = on_connect
soc.on_message = on_message
# soc.on_message1502_json_full = on_message1502_json_full
# soc.on_message1505_json_full = on_message1505_json_full
# soc.on_message1507_json_full = on_message1507_json_full
# soc.on_message1510_json_full = on_message1510_json_full
# soc.on_message1501_json_full = on_message1501_json_full
soc.on_message1512_json_full = on_message1512_json_full
# soc.on_message1105_json_full = on_message1105_json_full
# soc.on_message1502_json_partial = on_message1502_json_partial
# soc.on_message1505_json_partial = on_message1505_json_partial
# soc.on_message1510_json_partial = on_message1510_json_partial
# soc.on_message1501_json_partial = on_message1501_json_partial
# soc.on_message1512_json_partial = on_message1512_json_partial
# soc.on_message1105_json_partial = on_message1105_json_partial
soc.on_disconnect = on_disconnect
soc.on_error = on_error


# Event listener
el = soc.get_emitter()
el.on('connect', on_connect)
# el.on('1501-json-full', on_message1501_json_full)
# el.on('1502-json-full', on_message1502_json_full)
# el.on('1507-json-full', on_message1507_json_full)
el.on('1512-json-full', on_message1512_json_full)
# el.on('1105-json-full', on_message1105_json_full)

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
soc.connect()
time.sleep(5)
# print('socket connected')
# soc.disconnect()
