import asyncio
from datetime import datetime
from Strategy import Strategy
from LegBuilder import LegBuilder
from MarketSocket.xtsMarketSocket import MDSocket_io
from InteractiveSocket.xtsInteractiveSocket import OrderSocket_io
from datetime import datetime
from Broker.xtsBroker import XTS
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
from utils import get_data_from_mysql
xts = XTS()  
sys.path.append(os.path.abspath('../../Sagar_common'))
try:
    from common_function import fetch_parameter
except ImportError as e:
    print(f"Error importing 'fetch_parameter': {e}")
environment = "dev"
creds = fetch_parameter(environment, "live_creds")
db_creds = fetch_parameter(environment, "db_sagar_dataharvesting")
print(db_creds)
# print(creds)
market_token, interactive_token, userid = broker_login(xts, creds)
xts.market_token, xts.interactive_token, xts.userid  = market_token, interactive_token, userid
print(xts.get_historical_data(params = {
                "exchangeSegment": 1,
                "exchangeInstrumentID": 26000,
                "startTime": "Dec 23 2024 091500",
                "endTime": "Dec 23 2024 153000",
                "compressionValue": 60
            }))
end_time = "Dec 10 2024 153000"
instrument_id = 46775
get_data_from_mysql(instrument_id, end_time, db_creds)
# params = {
#                 "exchangeSegment": 2,
#                 "exchangeInstrumentID": 26000,
#                 "startTime": start_time,
#                 "endTime": end_time,
#                 "compressionValue": 60
#             }
#             print(params)
#             print(f'sleeping for {timeframe} minutes')
#             time.sleep(timeframe*60)
#             data= self.xts.get_historical_data(params)['result']['dataReponse']
# xts.update_master_db()

# res = xts.get_quotes([{'exchangeSegment': 1, 'exchangeInstrumentID': 26000}])
# ltp_json = json.loads(res['result']['listQuotes'][0])
# print(ltp_json['LastTradedPrice'])

# soc = MDSocket_io(token = market_token, port=port, userID=userid,publisher=publisher) #initialize 
# interactive_soc = OrderSocket_io(interactive_token, userid, port, publisher)
# # # soc.on_connect = on_connect
# # el = soc.get_emitter()
# # el.on('connect', soc.on_connect)
# # el.on('1512-json-full', soc.on_message1512_json_full)
# # soc.connect()

# interactive_soc.connect()
# # interactive_soc.on_trade = on_trade
# interactive_el = interactive_soc.get_emitter()
# interactive_el.on('trade', interactive_soc.on_trade)
# interactive_el.on('order', interactive_soc.on_order)
# # res = xts.get_quotes([{'exchangeInstrumentID': 1660, 'exchangeSegment': 1}])
# # print(res)
# # 1660, 3045
# # order = {"exchangeInstrumentID": 11915, "orderSide": "BUY",
# #         "orderQuantity":1,"limitPrice":0,
# #             "stopPrice": 1, "orderUniqueIdentifier": "itc"
# #         }
# # xts.place_market_order(order)
# # xts.order_history(1311089033)
# order = xts.place_SL_order({"exchangeInstrumentID": 11915, "orderSide": "SELL", "orderQuantity":2, "limitPrice": 19, 'stopPrice':19.2, 'orderUniqueIdentifier': 'rb'})
# appID = order['result']['AppOrderID']
# history_order = xts.order_history(appID)
# # order = xts.place_limit_order({"exchangeInstrumentID": 11915
# # , "orderSide": "BUY", "orderQuantity":1, "limitPrice": 19.8, 'stopPrice':0, 'orderUniqueIdentifier': 'DEEPAK'})
# # # # print(order['result'])
# # if order['type'] == 'success':
# #     appID = order['result']['AppOrderID']
# # print(order)
# # history_order = xts.order_history(appID)
# print(f"history order is {history_order}")
# if history_order['type']=='success':
#     order_id = history_order['result'][0]['AppOrderID']
#     modifiedProductType = history_order['result'][0]['ProductType']
#     modifiedOrderType = history_order['result'][0]['OrderType']
#     modifiedOrderType= "StopLimit"
#     modifiedOrderQuantity = history_order['result'][0]['LeavesQuantity']
#     modifiedDisclosedQuantity = history_order['result'][0]['OrderDisclosedQuantity']
#     modifiedLimitPrice = history_order['result'][0]['OrderPrice']+0.5
#     modifiedStopPrice = history_order['result'][0]['OrderStopPrice']+ 0.6
#     modifiedTimeInForce = history_order['result'][0]['TimeInForce']
#     orderUniqueIdentifier = history_order['result'][0]['OrderUniqueIdentifier']
# print(order_id, modifiedProductType, modifiedOrderType, modifiedOrderQuantity, modifiedDisclosedQuantity, modifiedLimitPrice, modifiedStopPrice, modifiedTimeInForce, orderUniqueIdentifier)
# # # # print(xts.get_positions())
# order = {

#   "appOrderID": order_id,
#   "modifiedProductType": modifiedProductType,
#   "modifiedOrderType": modifiedOrderType,
#   "modifiedOrderQuantity": modifiedOrderQuantity,
#   "modifiedDisclosedQuantity": 0,
#   "modifiedLimitPrice": modifiedLimitPrice,
#   "modifiedStopPrice": modifiedStopPrice,
#   "modifiedTimeInForce": "DAY",
#   "orderUniqueIdentifier": orderUniqueIdentifier
# }
# order = {

#   "appOrderID": appID,
#   "modifiedProductType": modifiedProductType,
#   "modifiedOrderType": "MARKET",
#   "modifiedOrderQuantity": modifiedOrderQuantity,
#   "modifiedDisclosedQuantity": 0,
#   "modifiedLimitPrice": 0,
#   "modifiedStopPrice": 0,
#   "modifiedTimeInForce": "DAY",
#   "orderUniqueIdentifier": orderUniqueIdentifier
# }
# time.sleep(15)
# modified_order = xts.modify_order(order)
# print(modified_order)
# # print(xts.modify_order(m))

# # print(xts.order_history(modified_order['AppOrderID']))


# # {"exchangeInstrumentID": self.instrument_id, "orderSide": self.position,
# #                                                             "orderQuantity":int(self.lot_size) *self.total_lots,"limitPrice":0,
# #                                                                 "stopPrice": 1, "orderUniqueIdentifier": self.leg_name}