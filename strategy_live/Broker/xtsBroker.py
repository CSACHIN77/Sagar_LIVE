import os
from datetime import datetime
import json
# import socketio
from io import StringIO
import requests
import pandas as pd
import mysql.connector
import re
from utils import get_orderbook_db
from utils import Logger
logger = Logger('sandbox_issues.txt')
# from async_socket import MDSocket_io
class XTS:
    def __init__(self):
        self.market_url = "https://ttblaze.iifl.com/apimarketdata/auth/login" 
        self.master_instruments_url = "https://ttblaze.iifl.com/apimarketdata/instruments/master"
        self.interactive_url = "https://ttblaze.iifl.com/interactive/user/session" 
        self.index_list_url = "https://ttblaze.iifl.com/marketdata/instruments/indexlist"
        self.quote_url = "https://ttblaze.iifl.com/marketdata/instruments/quotes"
        self.cover_order_url = "https://ttblaze.iifl.com/interactive/orders/cover"
        self.limit_order_url = "https://ttblaze.iifl.com/interactive/orders"
        self.options_symbol_url = "https://ttblaze.iifl.com/apimarketdata/instruments/instrument/optionSymbol"
        self.subscription_url =   "https://ttblaze.iifl.com/apimarketdata/instruments/subscription"
        self.cancel_all_url = "https://ttblaze.iifl.com/interactive/orders/cancelall"
        self.historical_url =  "https://ttblaze.iifl.com/apimarketdata/instruments/ohlc"
        self.daywise_position_url = "https://ttblaze.iifl.com/interactive/portfolio/positions"
        self.daywise_trade_url = "https://ttblaze.iifl.com/interactive/orders/trades"
        self.db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'pegasus',
        'database' : 'instrument_db'
        }
        self.userid = None
        self.headers = {
            "Content-Type": "application/json"
        }
        self.xts_subscribed_symbols =[]
    def market_login(self, secret_key, app_key):
        print('login process started')
        payload = {
            "secretKey": secret_key,
            "appKey": app_key,
            "source": "WebAPI"
        }
        # print(payload)
        try:
            response = requests.post(self.market_url, json=payload, headers=self.headers)
            data = response.json()
            # print(response)
            if data['type'] == 'success':
                token = data['result']['token']
                userid = data['result']['userID']
                self.market_token = token
                self.userid = userid
                print('logged in successfully')
                return token, userid
            print('finished logging in')
        except Exception as e:
            print("Error:", e)
            logger.log(f'login failed @ {datetime.now()}')
            return None


    def interactive_login(self, secret_key, app_key):
        payload = {
            "secretKey": secret_key,
            "appKey": app_key,
            "source": "WebAPI"
        }

        try:
            response = requests.post(self.interactive_url, json=payload, headers=self.headers)
            data = response.json()
            if data['type'] == 'success':
                token = data['result']['token']
                userid = data['result']['userID']
                self.interactive_token = token
                return token, userid
        except Exception as e:
            print("Error:", e)
            return None
    def get_master(self, exchangeSegmentList):
        try:
            # payload = exchangeSegmentList

            response = requests.post(self.master_instruments_url, json = exchangeSegmentList)

            instrument_details = response.json()['result']
            # print(instrument_details)
            if exchangeSegmentList['exchangeSegmentList']==['NSECM']:
                iifl_instruments = pd.read_csv(StringIO(instrument_details), sep = '|', usecols=range(19), header = None, low_memory=False)
                # new_column_names = ["ExchangeSegment","ExchangeInstrumentID","InstrumentType","Name","Description","Series","NameWithSeries","InstrumentID","PriceBand.High","PriceBand.Low","FreezeQty","TickSize","LotSize","Multiplier","UnderlyingInstrumentId","UnderlyingIndexName","ContractExpiration","StrikePrice","OptionType","DisplayName","PriceNumerator"]
                new_column_names = [
                    "ExchangeSegment",
                    "ExchangeInstrumentID",
                    "InstrumentType",
                    "Name",
                    "Description",
                    "Series",
                    "NameWithSeries",
                    "InstrumentID",
                    "PriceBand.High",
                    "PriceBand.Low",
                    "FreezeQty",
                    "TickSize",
                    "LotSize",
                    "Multiplier",
                    "DisplayName",
                    "ISIN",
                    "PriceNumerator",
                    "PriceDenominator",
                    "DetailedDescription"
                ]

                iifl_instruments.columns = new_column_names
                iifl_instruments.to_csv('nsecm.csv')
            elif exchangeSegmentList['exchangeSegmentList']==['NSEFO']:
                # print('futures')
                iifl_instruments = pd.read_csv(StringIO(instrument_details), sep = '|', usecols=range(21), header = None, low_memory=False)
                new_column_names = ["ExchangeSegment","ExchangeInstrumentID","InstrumentType","Name","Description","Series","NameWithSeries","InstrumentID","PriceBand.High","PriceBand.Low","FreezeQty","TickSize","LotSize","Multiplier","UnderlyingInstrumentId","UnderlyingIndexName","ContractExpiration","StrikePrice","OptionType","DisplayName","PriceNumerator"]
                iifl_instruments.columns = new_column_names
                iifl_instruments['ContractExpiration'] = pd.to_datetime(iifl_instruments['ContractExpiration']).dt.date
                iifl_instruments.to_csv('nfo.csv')
            return iifl_instruments
        except Exception as e:
            print(f"error occured {e}")

    def get_index_list(self, exchangeSegment):
        try:
            response = requests.get(self.index_list_url, params = {"exchangeSegment": exchangeSegment})
            data = response.json()
            if data['type']=="success":
                return data["result"]
            else:
                return None
        except Exception as e:
            print("Error:", e)
            return None

    
    def update_master_db(self):
        iifl_master = self.get_master({'exchangeSegmentList': ['NSEFO']})
        iifl = iifl_master[['ExchangeInstrumentID', 'Description', 'ContractExpiration','UnderlyingIndexName', 'StrikePrice', 'OptionType', 'ExchangeSegment', 'FreezeQty', 'LotSize', 'Series']]
        iifl.to_csv('nfo.csv')




    def get_master_db(self):
        df = pd.read_csv('nfo.csv', low_memory=False)
        df = df[['ExchangeInstrumentID', 'Description', 'ContractExpiration','UnderlyingIndexName', 'StrikePrice', 'OptionType', 'ExchangeSegment', 'FreezeQty', 'LotSize', 'Series']]
        df.rename(columns = {'ExchangeInstrumentID': 'instrument_token', 'Description':'tradingsymbol', 'UnderlyingIndexName': 'name',
                       'ContractExpiration':'expiry',
                      'StrikePrice': 'strike', 'OptionType':'option_type', 'ExchangeSegment':'segment', 'FreezeQty':'freezeqty'
                      ,'LotSize':'lot_size', 'Series':'series'}, inplace=True)
        print('Retrieved master database contents')
        return df
        connection = mysql.connector.connect(**self.db_config)
        cursor = connection.cursor()
        query = f"SELECT instrument_token, tradingsymbol, expiry, name, strike, option_type, segment FROM provider_master where provider_name='IIFL'"
        print(query)
        cursor.execute(query)
        rows = cursor.fetchall()
        master = pd.DataFrame(rows, columns = ['instrument_token', 'tradingsymbol', 'expiry', 'name', 'strike', 'option_type', 'segment'])
        cursor.close()
        connection.close()
        return master
            
    def get_quotes(self, instruments):
            headers = self.headers
            headers.update({'Authorization': self.market_token})
            payload = {"instruments": instruments, "xtsMessageCode": 1512, "publishFormat" : "JSON" }
            try:
                response = requests.post(self.quote_url,json= payload, headers=headers)
                return response.json()
            except Exception as e:
                print(e)
                return None
    def get_ltp(self, instruments):
        headers = self.headers
        headers.update({'Authorization': self.market_token})
        payload = {"instruments": instruments, "xtsMessageCode": 1501, "publishFormat" : "JSON" }
        try:
            response = requests.post(self.quote_url,json= payload, headers=headers)
            return response.json()
        except Exception as e:
            print(e)
            return None
            
    def place_cover_order(self, params):
        headers = self.headers
        headers.update({'Authorization': self.interactive_token})
        # payload = params
        try:
            params["exchangeSegment"]="NSEFO"
            # params["productType"] ="MIS"
            params["orderType"]="LIMIT"
            # params["timeInForce"]="DAY"
            params["disclosedQuantity"]=0
            # params["limitPrice"]=0
            params["orderUniqueIdentifier"]= f'{params["exchangeInstrumentID"]}'
            payload = params
            response = requests.post(self.cover_order_url, json = payload,headers=headers)
            return response.json()
        except Exception as e:
            print(e)
            return None
        
    def place_limit_order(self, params):
        headers = self.headers
        headers.update({'Authorization': self.interactive_token})
        try:
            # params["exchangeSegment"]="NSEFO"
            params["exchangeSegment"]="NSECM"
            params["productType"] ="CNC"
            params["orderType"]="LIMIT"
            params["timeInForce"]="DAY"
            params["disclosedQuantity"]=0
            params["orderUniqueIdentifier"]= f'{params["orderUniqueIdentifier"]}'
            payload = params
            response = requests.post(self.limit_order_url, json = payload,headers=headers)
            
            return  response.json()['result']
        except Exception as e:
            print(e)
            return None
    def place_SL_order(self, params):
        headers = self.headers
        headers.update({'Authorization': self.interactive_token})
        try:
            # params["exchangeSegment"]="NSEFO"
            params["exchangeSegment"]="NSECM"
            params["productType"] ="NRML"
            params["orderType"]="STOPLIMIT"
            params["timeInForce"]="DAY"
            params["disclosedQuantity"]=0
            # params["orderUniqueIdentifier"]= f'sl_order_{params["exchangeInstrumentID"]}'
            payload = params
            response = requests.post(self.limit_order_url, json = payload,headers=headers)
            return  response.json()
        except Exception as e:
            print(e)
            return None
    def place_market_order(self, params):
        headers = self.headers
        headers.update({'Authorization': self.interactive_token})
        try:
            # params["exchangeSegment"]="NSEFO"
            params["exchangeSegment"]="NSECM"
            params["productType"] ="CNC"
            params["orderType"]="MARKET"
            params["timeInForce"]="DAY"
            params["disclosedQuantity"]=0
            # params["orderUniqueIdentifier"]= params["orderID"]
            params["limitPrice"] =0
            params["stopPrice"] = 0
            payload = params
            print(payload)
            response = requests.post(self.limit_order_url, json = payload,headers=headers)
            return  response.json()['result']
        except Exception as e:
            print(e)
            return None

    def modify_order(self, params):
        headers = self.headers
        headers.update({'Authorization': self.interactive_token})
        try:
            payload = params
            response = requests.put(self.limit_order_url, data=json.dumps(params),headers=headers)
            print(response.json())
            return  response.json()['result']


        except Exception as e:
            print(e)
            return None
        

    def unsubscribe_symbols(self, instruments):

        params = {'instruments': instruments, 'xtsMessageCode': 1512}
        session = requests.Session()
        headers = self.headers
        headers.update({'Authorization': self.market_token})

        try:
            r = session.request("PUT",
                                        self.subscription_url,
                                        data=json.dumps(params),
                                        params=None,
                                        headers=headers
                                        )
            print(r.content)
        except Exception as e:
            raise e
    def getOptionSymbol(self,params):
        params = {
            "exchangeSegment": "2",
            "series": "OPTIDX",
            "symbol": params["symbol"],
            "expiryDate": params["expiryDate"],
            "strikePrice": params["strike"],
            "optionType": params["optionType"]
        }
        response = requests.get(self.options_symbol_url, params=params)

        if response.status_code == 200:
            data = response.json()['result'][0]
            return data['Description'], data['ExchangeInstrumentID']
        else:
            print("Failed to retrieve data. Status code:", response.status_code)

    def subscribe_symbols(self, instruments):
        # print(self.xts_subscribed_symbols)
        new_instruments = []
        for instrument in instruments:
            if instrument in self.xts_subscribed_symbols:
                print(f'{instrument} has already been subscribed')
            else:
                self.xts_subscribed_symbols.append(instrument)
                new_instruments.append(instrument)
        if len(new_instruments) != 0:
            params = {'instruments': new_instruments, 'xtsMessageCode': 1512}
            session = requests.Session()
            headers = self.headers
            headers.update({'Authorization': self.market_token})

            try:
                r = session.request("POST",
                                            self.subscription_url,
                                            data=json.dumps(params),
                                            params=None,
                                            headers=headers
                                            )
                # print(r.content)
            except Exception as e:
                raise e
    

    def complete_square_off(self, leg):
        headers = self.headers
        headers.update({'Authorization': self.market_token})
        try:
            total_orders = self.get_orders()['result']
            total_orders = pd.DataFrame(total_orders)
            pending_orders = total_orders[(total_orders['OrderStatus']=='New') & (total_orders['OrderUniqueIdentifier'].str.startswith(leg.leg_name))]
            if not pending_orders.empty:
             app_order_ids = list(set(pending_orders['AppOrderID']))
            #  print(app_order_ids)
             for app_order in app_order_ids:
                 self.cancel_order(app_order)

            positions = pd.DataFrame(self.get_positions())
            # positions.to_csv('positions.csv', index=False)
            positions['Quantity'] = positions['Quantity'].astype(int)
            active_positions = positions[positions['Quantity']!=0].copy()
            print(active_positions)
            active_positions.to_csv('active_positions.csv')
            for idx, row in active_positions.iterrows():
                instrument_id = row['ExchangeInstrumentId']
                # print(instrument_id, leg.instrument_id)

                if int(instrument_id) == leg.instrument_id:
                    print(instrument_id)
                    # print(type(instrument_id))
                    orderSide = 'BUY' if row['Quantity'] < 0 else 'SELL'
                    orderQuantity = abs(row['Quantity'])
                    limitPrice = 0
                    stopPrice =0
                    orderUniqueIdentifier = f"{leg.leg_name}_cover"
                    status = self.place_market_order({"exchangeInstrumentID": int(instrument_id), "orderSide": orderSide,
                                        "orderQuantity":int(orderQuantity),"limitPrice":limitPrice,
                                            "stopPrice": stopPrice, "orderUniqueIdentifier": orderUniqueIdentifier})
                    print(status)
                
            print('covered everything')
        except Exception as e:
            print(e)
            # return None
        
    def get_orderbook(self, userid):
        headers = self.headers
        headers.update({'Authorization': self.interactive_token})
        payload = {"ClientID" : userid }
        try:
            response = requests.get(self.limit_order_url,json= payload, headers=headers)
            return response.json()
        except Exception as e:
            print(e)
            return None
        
    def get_positions(self):
        headers = self.headers
        headers.update({'Authorization': self.interactive_token})
        try:
            params = {'dayOrNet': 'DayWise'}
            params['clientID'] = self.userid
            response = requests.get(self.daywise_position_url, params=params, headers=headers)
            return response.json()['result']['positionList']
        except Exception as e:
            return response
        
    def get_trades(self):
        headers = self.headers
        headers.update({'Authorization': self.interactive_token})
        try:
            # params = {'dayOrNet': 'DayWise'}
            params = {}
            params['clientID'] = self.userid
            response = requests.get(self.daywise_trade_url, params=params, headers=headers)
            return response.json()
        except Exception as e:
            return response
        
    def get_orders(self):
        headers = self.headers
        headers.update({'Authorization': self.interactive_token})
        try:
            params = {}
            params['clientID'] = self.userid
            response = requests.get(self.limit_order_url,  headers=headers)
            return response.json()
        except Exception as e:
            return response
        
    def cancel_all_orders(self, exchangeSegment, exchangeInstrumentID):
        headers = self.headers
        headers.update({'Authorization': self.interactive_token})
        try:
            params = {"exchangeSegment": "NSEFO", "exchangeInstrumentID": exchangeInstrumentID}
            params["clientID"]  = self.userid
            print(params)
            response = requests.post(url=self.cancel_all_url, json = json.dumps(params), headers=headers)
            print(response.json())
            return response.json()
        except Exception as e:
            print(e)
            return e
     
    def square_off_active_positions(self):
        try:
            positions = pd.DataFrame(self.get_positions())
        except Exception as e:
            return e
        open_positions = positions[positions['Quantity']!=0]


    def cancel_order(self, AppOrderID):
        headers = self.headers
        headers.update({'Authorization': self.interactive_token})
        try:
            params = {"appOrderID" : AppOrderID}
            print(params)
            response = requests.delete(url=self.limit_order_url, params = params, headers=headers)
            print(response.json())
            # return response.json()
        except Exception as e:
            print(e)
            return e
    def order_history(self, AppOrderID):
        headers = self.headers
        headers.update({'Authorization': self.interactive_token})
        try:
            params = {"appOrderID" : AppOrderID}
            response = requests.get(url=self.limit_order_url, params = params, headers=headers)
            print(response.json())
            return response.json()
        except Exception as e:
            print(e)
            return e
        

    def get_historical_data(self, params):
        headers = self.headers
        headers.update({'Authorization': self.market_token})
        try:
            params = params
            response = requests.get(self.historical_url, params=params, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print("Failed to retrieve data. Status code:", response.status_code)
                print("Response:", response.text)
                return None
        except Exception as e:
            print("Exception occurred:", e)
            return None
