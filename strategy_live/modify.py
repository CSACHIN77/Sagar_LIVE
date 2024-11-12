
# print(type(int(10)))
import asyncio
from datetime import datetime
from Strategy import Strategy
from LegBuilder import LegBuilder
from MarketSocket import MDSocket_io
from InteractiveSocket import OrderSocket_io
from datetime import datetime
from Broker import XTS
from creds import creds
from utils import get_atm, create_tradebook_table, broker_login
from Publisher import Publisher
import time
publisher = Publisher()
import warnings
import asyncio
warnings.filterwarnings("ignore")
port = "https://developers.symphonyfintech.in"
xts = XTS()  
market_token, interactive_token, userid = broker_login(xts, creds)
xts.market_token, xts.interactive_token, xts.userid  = market_token, interactive_token, userid
# 1210027863

params = {
"appOrderID": 1210040973,
"modifiedProductType": "NRML",
"modifiedOrderType": "STOPLIMIT",
"modifiedOrderQuantity": 30,
"modifiedDisclosedQuantity": 0,
"modifiedLimitPrice": 358,
"modifiedStopPrice": 357,
"modifiedTimeInForce": "DAY",
"orderUniqueIdentifier": "123abc"
}
order = xts.modify_order(params)
# print(order)