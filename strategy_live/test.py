# underlying_ltp = self.strategy.get_underlying_ltp()
index = 'NIFTY 50'
base = 100 if index == 'NIFTY BANK' else 50 
underlying_atm = 23500
# instrument_atm = get_atm(underlying_ltp, base)

def get_rolling_strike(atm, option_type, strike_type, base=1):
    """
    Calculate the strike price based on ATM, option type, and strike type.

    Args:
        atm (int or float): The at-the-money (ATM) strike price.
        option_type (str): The option type, either "CE" or "PE".
        strike_type (str): The strike type, e.g., "ATM", "OTM1", "ITM1", etc.
        base (int or float): The base step value to calculate strikes. Default is 1.

    Returns:
        float: The calculated strike price.
    """
    strike_type = strike_type.upper()  # Convert to uppercase for consistency
    option_type = option_type.upper()  # Convert to uppercase for consistency

    if not isinstance(atm, (int, float)):
        raise ValueError("ATM must be a number.")
    if option_type not in ["CE", "PE"]:
        raise ValueError("Option type must be 'CE' or 'PE'.")
    if not strike_type.startswith(("ATM", "OTM", "ITM")):
        raise ValueError("Strike type must start with 'ATM', 'OTM', or 'ITM'.")

    if strike_type == "ATM":
        return atm

    direction = strike_type[:3]  # "OTM" or "ITM"
    magnitude = int(strike_type[3:])  # Extract the numerical value after "OTM" or "ITM"

    if option_type == "CE":
        if direction == "OTM":
            return atm + magnitude * base
        elif direction == "ITM":
            return atm - magnitude * base
    elif option_type == "PE":
        if direction == "OTM":
            return atm - magnitude * base
        elif direction == "ITM":
            return atm + magnitude * base

    if not isinstance(atm, (int, float)):
        raise ValueError("ATM must be a number.")
    if option_type not in ["CE", "PE"]:
        raise ValueError("Option type must be 'CE' or 'PE'.")
    if not strike_type.startswith(("ATM", "OTM", "ITM")):
        raise ValueError("Strike type must start with 'ATM', 'OTM', or 'ITM'.")

    if strike_type == "ATM":
        return atm

    direction = strike_type[:3]  # "OTM" or "ITM"
    magnitude = int(strike_type[3:])  # Extract the numerical value after "OTM" or "ITM"

    if option_type == "CE":
        if direction == "OTM":
            return atm + magnitude * base
        elif direction == "ITM":
            return atm - magnitude * base
    elif option_type == "PE":
        if direction == "OTM":
            return atm - magnitude * base
        elif direction == "ITM":
            return atm + magnitude * base


print(get_rolling_strike(underlying_atm, "ce", "otm3", 100))




import asyncio
from datetime import datetime
from Strategy import Strategy
from LegBuilder import LegBuilder
from MarketSocket import MDSocket_io
from InteractiveSocket import OrderSocket_io
from datetime import datetime
from Broker import XTS
import os
import sys
from utils import get_atm, create_tradebook_table, broker_login
from Publisher import Publisher
import time
import json
publisher = Publisher()
create_tradebook_table()
import warnings
import asyncio
warnings.filterwarnings("ignore")
port = "https://ttblaze.iifl.com"
xts = XTS()  
sys.path.append(os.path.abspath('../../Sagar_common'))
try:
    from common_function import fetch_parameter
except ImportError as e:
    print(f"Error importing 'fetch_parameter': {e}")
environment = "dev"
creds = fetch_parameter(environment, "live_creds")
market_token, interactive_token, userid = broker_login(xts, creds)
xts.market_token, xts.interactive_token, xts.userid  = market_token, interactive_token, userid
# xts.update_master_db()

# res = xts.get_quotes([{'exchangeSegment': 1, 'exchangeInstrumentID': 26000}])
# ltp_json = json.loads(res['result']['listQuotes'][0])
# print(ltp_json['LastTradedPrice'])

# soc = MDSocket_io(token = market_token, port=port, userID=userid,publisher=publisher) #initialize 
interactive_soc = OrderSocket_io(interactive_token, userid, port, publisher)
# # soc.on_connect = on_connect
# el = soc.get_emitter()
# el.on('connect', soc.on_connect)
# el.on('1512-json-full', soc.on_message1512_json_full)
# soc.connect()

interactive_soc.connect()
# interactive_soc.on_trade = on_trade
interactive_el = interactive_soc.get_emitter()
interactive_el.on('trade', interactive_soc.on_trade)
interactive_el.on('order', interactive_soc.on_order)
res = xts.get_quotes([{'exchangeInstrumentID': 1660, 'exchangeSegment': 1}])
# print(res)
# 1660, 3045
order = {"exchangeInstrumentID": 3045, "orderSide": "BUY",
        "orderQuantity":1,"limitPrice":0,
            "stopPrice": 1, "orderUniqueIdentifier": "itc"
        }
# xts.place_market_order(order)
# xts.order_history(1311089033)
# # order = xts.place_SL_order({"exchangeInstrumentID": 3045, "orderSide": "SELL", "orderQuantity":2, "limitPrice": 855, 'stopPrice':856, 'orderUniqueIdentifier': 'rb'})
order = xts.place_limit_order({"exchangeInstrumentID": 11915
, "orderSide": "BUY", "orderQuantity":1, "limitPrice": 20.7, 'stopPrice':0, 'orderUniqueIdentifier': 'DEEPAK'})
# # print(order['result'])
if order['type'] == 'success':
    appID = order['result']['AppOrderID']
# print(order)
history_order = xts.order_history(appID)
print(history_order)
if history_order['type']=='success':
    # order_id = history_order['result']['OrderID']
    modifiedProductType = history_order['result'][0]['ProductType']
    modifiedOrderType = history_order['result'][0]['OrderType']
    modifiedOrderQuantity = history_order['result'][0]['LeavesQuantity']
    # modifiedDisclosedQuantity = history_order['result'][0]['DisclosedQuantity']
    # modifiedLimitPrice = history_order['result'][0]['LimitPrice']
    # modifiedStopPrice = history_order['result'][0]['StopPrice']
    # modifiedTimeInForce = history_order['result'][0]['TimeInForce']
    orderUniqueIdentifier = history_order['result'][0]['OrderUniqueIdentifier']
# print(order_id, modifiedProductType, modifiedOrderType, modifiedOrderQuantity, modifiedDisclosedQuantity, modifiedLimitPrice, modifiedStopPrice, modifiedTimeInForce, orderUniqueIdentifier)
# # print(xts.get_positions())
order = {

  "appOrderID": appID,
  "modifiedProductType": modifiedProductType,
  "modifiedOrderType": "MARKET",
  "modifiedOrderQuantity": modifiedOrderQuantity,
  "modifiedDisclosedQuantity": 0,
  "modifiedLimitPrice": 0,
  "modifiedStopPrice": 0,
  "modifiedTimeInForce": "DAY",
  "orderUniqueIdentifier": orderUniqueIdentifier
}
time.sleep(15)
modified_order = xts.modify_order(order)
print(modified_order)
# print(xts.modify_order(m))

# print(xts.order_history(modified_order['AppOrderID']))


# {"exchangeInstrumentID": self.instrument_id, "orderSide": self.position,
#                                                             "orderQuantity":int(self.lot_size) *self.total_lots,"limitPrice":0,
#                                                                 "stopPrice": 1, "orderUniqueIdentifier": self.leg_name}
