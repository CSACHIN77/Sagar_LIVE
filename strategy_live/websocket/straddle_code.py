import pandas as pd
from Connect import XTSConnect
import json
from datetime import datetime
from MarketDataSocketClient import MDSocket_io

creds = {
    'api_key_market' : '1f440830af1d82a7a09251',
    'api_secret_market' : 'Dllf432@Co',
    'api_trading_key' : 'e409ac8bd3f08ffc796583',
    'api_trading_secret' : 'Htuh007@ub'
}
class Logger:
    def __init__(self):
        self.log_file = open("streaming_data.txt", "a")  # Open log file in append mode
    
    def log(self, message):
        # timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # print(message)  # Print to console
        print(message)
        self.log_file.write(message + "\n")  # Write to log file
logger = Logger()
iifl_instruments = pd.read_csv('fut_master.csv',low_memory=False)

def on_message1512_json_full(data):
    # print('I received a 1512 Level1,LTP message!' + data)
    print(data)
    logger.log(data)
def on_message1512_json_partial(data):
    # print('I received a 1512, LTP Event message!' + data)
    print(data)
    logger.log(data)

def on_message(data):
    # print('I received a message!')
    print(data)
    pass

# Callback for message code 1501 FULL
def on_message1501_json_full(data):
    # print('I received a 1501 Touchline message!' + data)
    pass

config = [{
    'instrument': 'NIFTY 50',
    'start_time': "09:20",
    'end_time': "10:30",
    'expiry': 0, #CURRENT, NEAR, FAR
    'options_strike': 0, # 0 FOR STRADDLE, 1 FOR ITM STRANGLE, -1 FOR OTM STRANGLE AND SO ON
    'premium_based': {True, 100},
    'order_wait_period': 10,
    'stop_loss': {'individual', 20} # COMBINED or INDIVIDUAL
    },
    {
    'instrument':'NIFTY BANK',
    'start_time': "09:20",
    'end_time': "10:30",
    'expiry': 0, #CURRENT, NEAR, FAR
    'options_strike': 0, # 0 FOR STRADDLE, 1 FOR ITM STRANGLE, -1 FOR OTM STRANGLE AND SO ON
    'premium_based': {True, 100},
    'order_wait_period': 10,
    'stop_loss': {'individual', 20} # COMBINED or INDIVIDUAL
    }]
def atm_strike(ltp, base):
    a = (ltp // base) * base
    b = a + base
    return int(b if ltp - a > b - ltp else a)

def iifl_login(creds):
    # broker_name = creds['broker_name']
    api_key_market = creds['api_key_market']
    api_secret_market = creds['api_secret_market']
    api_trading_key = creds['api_trading_key']
    api_trading_secret = creds['api_trading_secret']
    
    xtm = XTSConnect(api_key_market, api_secret_market, source='WEBAPI')
    xt = XTSConnect(api_trading_key, api_trading_secret, source='WEBAPI')
    response = xtm.marketdata_login()
    set_marketDataToken = response['result']['token']
    set_muserID = response['result']['userID']
    response2 = xt.interactive_login()
    if response['type'] == 'success' and response2['type']=='success':
        print(response['type'], response2['type'])
        return set_marketDataToken, set_muserID, xt, xtm
    else:
        print('error logging in')
try:
    print('login invoked')
    set_marketDataToken, set_muserID, xt, xtm = iifl_login(creds)
    # soc = MDSocket_io(set_marketDataToken, set_muserID)
    print('logged in ')
except Exception as e:
    logger.log('error occured while login, exiting')
 
instruments = [item['instrument'] for item in config]
print(instruments)
index_list = xtm.get_index_list(1)['result']['indexList']
idx_list = {}
for idx in index_list:
    idx_name = idx.split('_')[0]
    ex_id = idx.split('_')[1]
    idx_list[idx_name] = int(ex_id)
instrument_ex_id_list =[]
instrument_name_exid ={}
for instrument in instruments:
    instrument_name_exid[idx_list[instrument]] = instrument
    instrument_ex_id_list.append({'exchangeSegment':1, 'exchangeInstrumentID':idx_list[instrument]})
# print(instrument_ex_id_list)
print(instrument_name_exid)
# print(xtm.get_index_list(1))
genesis_time = datetime.now()
response = xtm.get_quote(
    Instruments=instrument_ex_id_list,
    xtsMessageCode=1512,
    publishFormat='JSON')
ltp_data = response['result']['listQuotes']
print(instrument_ex_id_list)
options_list = []
for x in ltp_data:
    x = json.loads(x)
    ltp = x['LastTradedPrice']
    if x['ExchangeInstrumentID']==26001:
        base = 100
    else:
        base = 50
    atm = atm_strike(ltp, base)
    symbol = instrument_name_exid[x['ExchangeInstrumentID']]
    print(symbol, atm)
    ce_symbols = iifl_instruments[(iifl_instruments.UnderlyingIndexName.str.upper() == symbol) & (iifl_instruments.StrikePrice ==str(atm))&(iifl_instruments.OptionType==3)].sort_values('ContractExpiration')
    pe_symbols = iifl_instruments[(iifl_instruments.UnderlyingIndexName.str.upper() == symbol) & (iifl_instruments.StrikePrice ==str(atm))&(iifl_instruments.OptionType==4)].sort_values('ContractExpiration')
    print(ce_symbols.iloc[0].Description, ce_symbols.iloc[0].ExchangeInstrumentID)
    print(pe_symbols.iloc[0].Description, pe_symbols.iloc[0].ExchangeInstrumentID)
    options_list.append({ce_symbols.iloc[0].Description : {'exchangeSegment': 2, 'exchangeInstrumentID': ce_symbols.iloc[0].ExchangeInstrumentID}})
    options_list.append({pe_symbols.iloc[0].Description : {'exchangeSegment': 2, 'exchangeInstrumentID': pe_symbols.iloc[0].ExchangeInstrumentID}})
    logger.log(f'{symbol} ATM : {atm}')
    
# instrument_list = xtm.search_by_instrumentid(instrument_ex_id_list)['result']
# print(instrument_list)
# print(options_list)
symbols_to_subscribe = []
for x in options_list:
    for key, value in x.items():
        symbols_to_subscribe.append(value)
print(symbols_to_subscribe[0:1])
print(f'total time since calculation : {datetime.now()- genesis_time}')




soc = MDSocket_io(set_marketDataToken, set_muserID)

# Instruments for subscribing
Instruments = symbols_to_subscribe
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