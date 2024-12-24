import requests
import json
from datetime import datetime, timedelta
import os
import pandas as pd
from dateutil.relativedelta import relativedelta
import mysql.connector
from creds import db_creds
from utils import convert_end_time_format
import time
class XTS:
    def __init__(self, soc, base_url='http://localhost:8050'):
        self.base_url = base_url
        self.soc = soc
        self.tradebook_path = 'tradebook.json'
        self.orderbook_path = 'orderbook.json'
        self.xts_subscribed_symbols = []
        
    def subscribe_symbols(self, instruments):
        self.soc.subscribe_symbols(instruments)
    def place_market_order(self, order_params):
        # print(f"order placed through market order {order_params}")
        url = f"{self.base_url}/placeMarketOrder"
        response = requests.post(url, json=order_params)
        if response.status_code == 200:
            print("testing Order placed successfully:", response.json()['order'])
        else:
            print("Failed to place order:", response.json())
        return response.json()['order']

    def place_stop_limit_order(self, sl_order_params):
        url = f"{self.base_url}/placeSLorder"
        response = requests.post(url, json=sl_order_params)
        if response.status_code == 200:
            print("Stop-limit order placed successfully:", response.json())
        else:
            print("Failed to place stop-limit order:", response.json())
        return response.json()
    
    def order_history(self, AppOrderID):
        history_order ={}
        history_order['result']=[]
        base_path = os.path.dirname(__file__)
        file_path = os.path.abspath(os.path.join(base_path, "..", "..", "strategy_sandbox", "orderbook.json"))
        print(f"file path is {file_path}")
        print(f"app order id in order history is {AppOrderID} {type(AppOrderID)}")
        if os.path.exists(file_path):

            with open(file_path, 'r') as file:
                orders = json.load(file)
            for order in orders:
                if order.get('AppOrderID')== AppOrderID:
                    print(order)
                    history_order['type'] = 'success'
                    history_order['result']= [order]
                    return history_order
        # headers = self.headers
        # headers.update({'Authorization': self.interactive_token})
        # try:
        #     params = {"appOrderID" : AppOrderID}
        #     response = requests.get(url=self.limit_order_url, params = params, headers=headers)
        #     print(response.json())
        #     return response.json()
        # except Exception as e:
        #     print(e)
        #     return e
        
    def place_limit_order(self, order_params):
        print(f"order placed through limit order {order_params}")
        url = f"{self.base_url}/placeOrder"
        limit_order_params  = {
            'OrderType' : 'LIMIT',
            'OrderSide' : order_params['orderSide'],
            'exchangeInstrumentID' : order_params['exchangeInstrumentID'],
            'OrderPrice' : order_params['limitPrice'],
            'OrderQuantity' : order_params['orderQuantity'],
            'OrderUniqueIdentifier' : order_params['orderUniqueIdentifier']
        }
        response = requests.post(url, json=limit_order_params)
        if response.status_code == 200:
            print("Order placed successfully:", response.json())
        else:
            print("Failed to place order:", response.json())
        return response.json()['order']
    
    def modify_order(self, order_params):
        print(f"order placed through modify order {order_params}")
        url = f"{self.base_url}/modifyOrder"
        # if order_params['modifiedOrderQuantity']!= 0:
        response = requests.post(url, json=order_params)
        if response.status_code == 200:
            print("Order placed successfully:", response.json())
        else:
            print("Failed to place order:", response.json())
        return response.json()#['order']
        # else:
        # return {'type':'success'}
    def get_orders(self):
        # Check if the orderbook file exists
        if os.path.exists(self.orderbook_path):
            try:
                # Read and return the contents of the orderbook
                with open(self.orderbook_path, 'r') as file:
                    orders = json.load(file)
                    result = {
                        "type": "success",
                        "code": "s-user-0001",
                        "description": "Orders retrieved successfully",
                        "result": orders
                    }
                    
            except json.JSONDecodeError:
                # Handle JSON decoding error if file contents are invalid
                result = {
                    "type": "error",
                    "code": "e-user-0002",
                    "description": "Failed to parse orderbook data",
                    "result": {}
                }
                
        else:
            # Return empty result if the orderbook file doesn't exist
            result = {
                "type": "error",
                "code": "e-user-0003",
                "description": "Orderbook file not found",
                "result": {}
            }
        return result
    def get_tradebook(self):
        # Check if the tradebook file exists
        if os.path.exists(self.tradebook_path):
            try:
                # Read and parse the tradebook file
                with open(self.tradebook_path, 'r') as file:
                    tradebook = json.load(file)
                
                # Convert to DataFrame and return structured response
                tradebook_df = pd.DataFrame(tradebook)
                result = {
                    "type": "success",
                    "code": "s-user-0001",
                    "description": "Tradebook retrieved successfully",
                    "result": tradebook_df.to_dict(orient="records")  # Return as list of dicts
                }
            except Exception as e:
                # Handle any errors that occur while reading the file
                result = {
                    "type": "error",
                    "code": "e-user-0002",
                    "description": "Failed to read tradebook",
                    "result": {},
                    "error_message": str(e)
                }
        else:
            # Return empty result if the tradebook file doesn't exist
            result = {
                "type": "error",
                "code": "e-user-0003",
                "description": "Tradebook file not found",
                "result": {}
            }

        # print(result)  # Log the structured response
        return result

    def place_dummy_order(self):
        url = f"{self.base_url}/dummyorder"
        response = requests.post(url)
        if response.status_code == 200:
            print("Dummy order placed:", response.json())
        else:
            print("Failed to place dummy order")
        return response.json()
    

    # def cancel_orders(self, exchange_segment, exchange_instrument_id):
    #     url = f"{self.base_url}/cancelOrders"
    #     payload = {
    #         "ExchangeSegment": exchange_segment,
    #         "ExchangeInstrumentID": exchange_instrument_id
    #     }
        
    #     response = requests.post(url, json=payload)
        
    #     if response.status_code == 200:
    #         print("Orders cancelled successfully:", response.json())
    #     else:
    #         print("Failed to cancel orders:", response.text)
        
    #     return response.json()




    def get_index_list(self, exchangeSegment=1):
        file_path = "indices_list.json"
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                indices_data = json.load(file)
        else:
            indices_data =  {
            "exchangeSegment": "1",
            "indexList": [
                "NIFTY 50_26000", "NIFTY BANK_26001", "INDIA VIX_26002", "NIFTY IT_26003", "NIFTY 100_26004", 
                "NIFTY MIDCAP 50_26005", "NIFTY GS 11 15YR_26006", "NIFTY INFRA_26007", "NIFTY100 LIQ 15_26008", 
                "NIFTY REALTY_26009", "NIFTY CPSE_26010", "NIFTY GS COMPSITE_26011", "NIFTY OIL AND GAS_26012", 
                "NIFTY50 TR 1X INV_26013", "NIFTY PHARMA_26014", "NIFTY PSE_26015", "NIFTY MIDCAP 150_26016", 
                "NIFTY MIDCAP 100_26017", "NIFTY SERV SECTOR_26018", "NIFTY 500_26019", "NIFTY ALPHA 50_26020", 
                "NIFTY50 VALUE 20_26021", "NIFTY200 QUALTY30_26022", "NIFTY SMLCAP 250_26023", "NIFTY GROWSECT 15_26024", 
                "NIFTY50 PR 1X INV_26025", "NIFTY50 EQL WGT_26026", "NIFTY PSU BANK_26027", "NIFTY SMLCAP 100_26028", 
                "NIFTY LARGEMID250_26029", "NIFTY100 EQL WGT_26030", "NIFTY SMLCAP 50_26031", "NIFTY ENERGY_26032", 
                "NIFTY GS 10YR_26033", "NIFTY FIN SERVICE_26034", "NIFTY MIDSML 400_26035", "NIFTY METAL_26036", 
                "NIFTY CONSR DURBL_26037", "NIFTY DIV OPPS 50_26038", "NIFTY GS 15YRPLUS_26039", "NIFTY MEDIA_26040", 
                "NIFTY FMCG_26041", "NIFTY PVT BANK_26042", "NIFTY200MOMENTM30_26043", "HANGSENG BEES-NAV_26044", 
                "NIFTY100 LOWVOL30_26045", "NIFTY50 TR 2X LEV_26046", "NIFTY CONSUMPTION_26047", "NIFTY GS 8 13YR_26048", 
                "NIFTY100ESGSECLDR_26049", "NIFTY GS 10YR CLN_26050", "NIFTY GS 4 8YR_26051", "NIFTY AUTO_26052", 
                "NIFTY COMMODITIES_26053", "NIFTY NEXT 50_26054", "NIFTY MNC_26055", "NIFTY MID LIQ 15_26056", 
                "NIFTY HEALTHCARE_26057", "NIFTY500 MULTICAP_26058", "NIFTY ALPHALOWVOL_26059", "NIFTY FINSRV25 50_26060", 
                "NIFTY50 PR 2X LEV_26061", "NIFTY100 QUALTY30_26062", "NIFTY50 DIV POINT_26063", "NIFTY 200_26064", 
                "NIFTY MID SELECT_26121", "NIFTY MIDSML HLTH_26122", "NIFTY MULTI INFRA_26123", "NIFTY MULTI MFG_26124", 
                "NIFTY TATA 25 CAP_26125", "NIFTY IND DEFENCE_26127", "NIFTY IND TOURISM_26128", "NIFTY CAPITAL MKT_26129", 
                "NIFTY500MOMENTM50_26130", "NIFTYMS400 MQ 100_26131", "NIFTYSML250MQ 100_26132", "NIFTY TOP 10 EW_26133", 
                "BHARATBOND-APR25_26134", "BHARATBOND-APR30_26135", "BHARATBOND-APR31_26136", "BHARATBOND-APR32_26137", 
                "BHARATBOND-APR33_26138"
            ]}
            with open(file_path, "w") as file:
                json.dump(indices_data, file)
        return indices_data
    def get_master_db(self):
        df = pd.read_csv('nfo.csv', low_memory=False)
        df = df[['ExchangeInstrumentID', 'Description', 'ContractExpiration','UnderlyingIndexName', 'StrikePrice', 'OptionType', 'ExchangeSegment', 'FreezeQty', 'LotSize', 'Series']]
        df.rename(columns = {'ExchangeInstrumentID': 'instrument_token', 'Description':'tradingsymbol', 'UnderlyingIndexName': 'name',
                       'ContractExpiration':'expiry',
                      'StrikePrice': 'strike', 'OptionType':'option_type', 'ExchangeSegment':'segment', 'FreezeQty':'freezeqty'
                      ,'LotSize':'lot_size', 'Series':'series'}, inplace=True)
        print('Retrieved master database contents')
        return df
    
    
        # except Exception as e:
        #     print(e)
        #     return None
        
    def get_quotes_db(self, instruments):
        current_data_time = self.soc.current_data_time
        
        if not current_data_time:
            time.sleep(4)
            current_data_time = self.soc.current_data_time
        print(f"current time is {current_data_time}")
        normal_timestamp = datetime.fromtimestamp(current_data_time) - timedelta(days= 1, hours=5, minutes=30)
        instrument_ids = [instrument['exchangeInstrumentID'] for instrument in instruments]
        # print(f"parsed timestamp is {normal_timestamp} and instrument is {instrument_ids}")
        
        try:
            connection = mysql.connector.connect(
                host=db_creds['host'],
                user=db_creds['user'],
                password=db_creds['password'],
                database=db_creds['database']
            )

            query = f"""
                SELECT OverallData
                FROM (
                    SELECT OverallData,
                        exchangeinstrumentid,
                        ROW_NUMBER() OVER (PARTITION BY exchangeinstrumentid ORDER BY lastupdatetime DESC) as rn
                    FROM {db_creds['table_name']}
                    WHERE lastupdatetime = %s
                    AND exchangeinstrumentid IN ({','.join(['%s'] * len(instrument_ids))})
                ) as t
                WHERE t.rn = 1
            """
            query_params = [normal_timestamp] + instrument_ids
            # print(query, query_params)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, query_params)
            results = cursor.fetchall()

            response = {
                'type': 'success',
                'code': 's-quotes-0001',
                'description': 'Get quotes successfully!',
                'result': {
                    'mdp': 1512,
                    'quotesList': [
                        {'exchangeSegment': instrument['exchangeSegment'], 'exchangeInstrumentID': instrument['exchangeInstrumentID']}
                        for instrument in instruments
                    ],
                    'listQuotes': [result['OverallData'] for result in results]
                }
            }
            return response

        except mysql.connector.Error as err:
            print(f"error : {err}")
            return {
                'type': 'error',
                'code': 'e-db-0001',
                'description': f'Database error: {err}'
            }
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()


    def get_quotes(self, instruments):
        quotes = []
        while not self.soc._market_data:
            time.sleep(0.5)
        for instrument in instruments:
            exchange_segment = instrument['exchangeSegment']
            exchange_instrument_id = instrument['exchangeInstrumentID']
            for data in self.soc._market_data:
                overall_data = data.get('OverallData', {})
                # print(f"overall data is {overall_data}")
                if overall_data.get('ExchangeInstrumentID') == exchange_instrument_id:
                    quotes.append(json.dumps(overall_data))
                    break
                    print(f"overall data is {overall_data}")
        # print(f"quotes is {quotes}")
        quote_object = {
            "type": "success",
            "result": {"listQuotes": quotes}
        }
        return quote_object



    def place_SL_order(self, order_params):
        """
        Places a Stop-Limit order without monitoring execution.

        :param order_params: A dictionary containing Stop-Limit order parameters.
        :return: Response from the server after placing the order.
        """
        print(f"Placing Stop-Limit order: {order_params}")
        url = f"{self.base_url}/placeSLorder"
        try:
            # Send the Stop-Limit order to the server
            response = requests.post(url, json=order_params)
            
            if response.status_code == 200:
                order_response = response.json()['order']
                print(f"Stop-Limit order placed successfully: {order_response}")
                return {
                    "type": "success",
                    "code": "s-slorder-0001",
                    "description": "Stop-Limit order placed successfully",
                    "result": order_response,
                }
            else:
                print("Failed to place Stop-Limit order:", response.json())
                return {
                    "type": "error",
                    "code": "e-slorder-0002",
                    "description": "Failed to place Stop-Limit order",
                    "result": response.json(),
                }
        except Exception as e:
            print(f"Error in place_SL_order: {str(e)}")
            return {
                "type": "error",
                "code": "e-slorder-0003",
                "description": "Error in placing Stop-Limit order",
                "error_message": str(e),
            }

    def read_orderbook(self, file_path):
        try:
            with open(file_path, 'r') as f:
                orderbook = json.load(f)
            return orderbook
        except Exception as e:
            print(f"Error reading orderbook: {e}")
            return []
    def cancel_order(self, app_order_id, orderbook_path="orderbook.json"):
        try:
            if os.path.exists(orderbook_path):
                with open(orderbook_path, 'r') as f:
                    orderbook = json.load(f)
            else:
                print(f"Orderbook file not found: {orderbook_path}")
                return

            order_found = False
            updated_orderbook = []
            for order in orderbook:
                if order['AppOrderID'] == app_order_id:
                    order_found = True
                    print(f"Canceling order with AppOrderID: {app_order_id}")
                else:
                    updated_orderbook.append(order) 

            if not order_found:
                print(f"No order found with AppOrderID: {app_order_id}")
            else:
                with open(orderbook_path, 'w') as f:
                    json.dump(updated_orderbook, f, indent=4)
                print(f"Order with AppOrderID {app_order_id} removed from the orderbook.")

        except Exception as e:
            print(f"Error while canceling order with AppOrderID {app_order_id}: {e}")

    def complete_square_off(self, leg, orderbook_path="orderbook.json", tradebook_path="tradebook.json"):
        try:
            orderbook = self.read_orderbook(orderbook_path)
            orderbook_df = pd.DataFrame(orderbook)
            orderbook_df.to_csv("testOrderbook.csv", index=False)
            pending_orders = orderbook_df[(orderbook_df['OrderStatus'] == 'New') & 
                                        (orderbook_df['OrderUniqueIdentifier'].str.startswith(leg.leg_name))]
            if not pending_orders.empty:
                app_order_ids = list(set(pending_orders['AppOrderID']))
                for app_order in app_order_ids:
                    self.cancel_order(app_order)

            filled_orders = orderbook_df[(orderbook_df['OrderStatus'] == 'Filled') & 
                                        (orderbook_df['OrderUniqueIdentifier'].str.startswith(leg.leg_name))]

            if not filled_orders.empty:
                for idx, row in filled_orders.iterrows():
                    instrument_id = row['exchangeInstrumentID']
                    order_side = 'BUY' if row['OrderSide'] == 'SELL' else 'SELL'
                    order_quantity = row['OrderQuantity']

                    order_unique_identifier = f"{leg.leg_name}_squareoff"
                    market_order_details = {
                        "exchangeInstrumentID": int(instrument_id),
                        "orderSide": order_side,
                        "orderQuantity": int(order_quantity),
                        "limitPrice": 0,
                        "stopPrice": 0,
                        "orderUniqueIdentifier": order_unique_identifier
                    }

                    status = self.place_market_order(market_order_details)
                    print(f"Market order status: {status}")

            time.sleep(2)
            orderbook_df.to_csv('strategy_orderbook.csv', index=False)

            if os.path.exists(tradebook_path):
                with open(tradebook_path, 'r') as f:
                    tradebook = json.load(f)
                time.sleep(2)
                tradebook_df = pd.DataFrame(tradebook)
                tradebook_df.drop_duplicates(inplace=True)
                tradebook_df.to_csv('strategy_tradebook.csv', index=False)
            else:
                print(f"Tradebook file not found: {tradebook_path}")

            print("All operations completed. Returning control.")
            return "completed"

        except Exception as e:
            print(f"Error in complete_square_off: {e}")
            raise RuntimeError("Square off operation failed") from e

    def get_historical_data(self,params, db_creds=db_creds):
        """
        Fetches the highest and lowest LastTradedPrice within a specified time range and filters
        based on parameters provided in the 'params' dictionary. The function dynamically constructs
        the SQL query based on the keys present in 'params'.
        
        Args:
            params (dict): Dictionary containing filtering parameters, including:
                        - exchangeSegment (int): Exchange segment ID.
                        - exchangeInstrumentID (int): Instrument ID.
                        - startTime (str): Start time in the format 'Jul 13 2020 090000'.
                        - endTime (str): End time in the format 'Jul 13 2020 153000'.
            db_creds (dict): Dictionary containing database connection credentials:
                        - host (str): Database host.
                        - user (str): Database user.
                        - password (str): Database password.
                        - database (str): Database name.
        
        Returns:
            dict: A dictionary with keys 'HighestLastTradedPrice' and 'LowestLastTradedPrice',
                containing the highest and lowest LastTradedPrice values, respectively.
        """
        try:
            formatted_end_time = convert_end_time_format(params['endTime'])
            if not formatted_end_time:
                return None
            instrument_id = params['exchangeInstrumentID']
 
            connection = mysql.connector.connect(
                host=db_creds['host'],
                user=db_creds['user'],
                password=db_creds['password'],
                database=db_creds['database']
            )
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT LastTradedPrice
                FROM data_harvesting_20241210
                WHERE lastupdatetime <= %s
                AND exchangeInstrumentID = %s
            """
            cursor.execute(query, (formatted_end_time, instrument_id))
            results = cursor.fetchall()
            cursor.close()
            connection.close()

            if not results:
                print("No data found.")
                return None

            # Extract LastTradedPrice values
            last_traded_prices = [row['LastTradedPrice'] for row in results if row['LastTradedPrice'] is not None]

            if not last_traded_prices:
                print("No LastTradedPrice values found.")
                return None

            # Calculate highest and lowest LastTradedPrice
            higher_range = max(last_traded_prices)
            lower_range = min(last_traded_prices)
            print("Highest LastTradedPrice:", higher_range, "Lowest LastTradedPrice:", lower_range)
            return {"high": higher_range, "low": lower_range}

        except mysql.connector.Error as err:
            print("Error: ", err)
            return {"high": None, "low": None}
