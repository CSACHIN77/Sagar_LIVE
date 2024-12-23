from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
import pandas as pd
from dateutil import parser
import json
import os
import re
import time
from io import StringIO
from datetime import datetime, timedelta
import logging

environment = "dev"

def get_atm(price, base):
    return  round(price / base) * base

def get_base(index, strikeDiffernces):
    base = 100 # default
    if index == "NIFTY":
        base = strikeDiffernces["NIFTY_BASE"]
    elif index == "NIFTY BANK":
        base = strikeDiffernces["BANKNIFTY_BASE"]
    elif index == "FINNIFTY":
        base = strikeDiffernces["FINNIFTY_BASE"]
    elif index == "MIDCAPNIFTY":
        base = strikeDiffernces["MIDCAPNIFTY_BASE"]
    elif index == "SENSEX":
        base = strikeDiffernces["SENSEX_BASE"]
    return base
      

def get_rolling_strike(atm, option_type, strike_type, base=100):
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
    option_type = "CE" if option_type == 3 else "PE"
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
def filter_dataframe(df, instruments):
    filtered_data = df[(df['segment'] == 'NSEFO') & 
                       (df['series'] == 'OPTIDX') & 
                       (df['name'].str.upper().isin(instruments))]
    futures_data = df[(df['segment'] == 'NSEFO') & 
                       (df['series'] == 'FUTIDX') & 
                       (df['name'].str.upper().isin(instruments))]
    monthly_expiry_list = list(futures_data['expiry'])
    monthly_expiry_list.sort()

    return filtered_data, monthly_expiry_list

class Logger:
    def __init__(self, filename):
        self.filename = filename

    def log(self, message, current_data_time=""):
        if environment.lower() == 'dev':
            # print(message)
            """Append a message with a timestamp to the log file."""
            with open(self.filename, 'a') as file:
                # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if current_data_time == "": 
                    file.write(f"{message}\n")
                else:
                    file.write(f"{current_data_time}: {message}\n")


def find_keys_by_value(d, target_value):
    keys = [key for key, value in d.items() if value == target_value]
    return keys

def update_tradebook(data, price=0):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='pegasus'
        )

        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS sagar_execution")
        cursor.close()

        connection.database = 'sagar_execution'
        if connection.is_connected():
            cursor = connection.cursor()
            current_date = datetime.now().strftime("%Y%m%d") 
            table_name = f"tradebook_{current_date}"
            query = f"""INSERT INTO {table_name} (AppOrderID, TradingSymbol, ExchangeInstrumentID, OrderSide, OrderType,
                                              OrderPrice,Quantity, OrderAverageTradedPrice, ExchangeTransactTimeAPI, 
                                              OrderUniqueIdentifier, CalculationPrice)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       ON DUPLICATE KEY UPDATE
                       TradingSymbol=VALUES(TradingSymbol),
                       ExchangeInstrumentID=VALUES(ExchangeInstrumentID),
                       OrderSide=VALUES(OrderSide),
                       OrderType=VALUES(OrderType),
                       OrderPrice=VALUES(OrderPrice),
                        Quantity = VALUES(Quantity),
                       OrderAverageTradedPrice=VALUES(OrderAverageTradedPrice),
                       ExchangeTransactTimeAPI=VALUES(ExchangeTransactTimeAPI),
                       OrderUniqueIdentifier=VALUES(OrderUniqueIdentifier),
                       CalculationPrice=VALUES(CalculationPrice);"""
            data['ExchangeTransactTimeAPI'] = datetime.strptime(data['ExchangeTransactTimeAPI'], '%Y-%m-%d %H:%M:%S')
            data['ExchangeTransactTimeAPI'] = data['ExchangeTransactTimeAPI'].strftime('%Y-%m-%d %H:%M:%S')

            tuple_data = (data['AppOrderID'], data['TradingSymbol'], data['ExchangeInstrumentID'], data['OrderSide'], 
                          data['OrderType'], data['OrderPrice'], data['CumulativeQuantity'], data['OrderAverageTradedPrice'], 
                          data['ExchangeTransactTimeAPI'], data['OrderUniqueIdentifier'], price)

            # Executing the query
            cursor.execute(query, tuple_data)
            connection.commit()

    except mysql.connector.Error as error:
        print("Failed to update record to database: {}".format(error))

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

def get_orderbook_db():
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(
            host='localhost',  
            database='sagar_execution',
            user='root',
            password='pegasus'
        )
        if connection.is_connected():
            cursor = connection.cursor()
            query = """SELECT AppOrderID, OrderUniqueIdentifier, ExchangeInstrumentID FROM tradebook"""
            cursor.execute(query)
            rows = cursor.fetchall()
            # Creating DataFrame with column names
            tradebook = pd.DataFrame(rows, columns=['AppOrderID', 'OrderUniqueIdentifier', 'ExchangeInstrumentID'])
            return tradebook
    except Exception as e:
        print(f'An error occurred: {e}')
    finally:
        # Ensuring that cursor and connection are closed
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def parse_date(date_str):
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        print('error occured')


def calculate_slippage(row, is_entry):
    if is_entry:
        if row['OrderSide_entry'] == 'Sell':
            return row['OrderAverageTradedPrice_entry'] - row['CalculationPrice_entry']
        else:
            return row['CalculationPrice_entry'] - row['OrderAverageTradedPrice_entry']
    else:
        if row['OrderSide_exit'] == 'Buy':
            return row['CalculationPrice_exit'] - row['OrderAverageTradedPrice_exit']
        else:
            return row['OrderAverageTradedPrice_exit'] - row['CalculationPrice_exit']
        
def create_tradebook_table():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='sagar_execution',
            user='root',
            password='pegasus'
        )

        if connection.is_connected():
            cursor = connection.cursor()
            current_date = datetime.now().strftime("%Y%m%d")  # Format: YYYYMMDD
            table_name = f"tradebook_{current_date}"
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

            create_table_query = f"""
            CREATE TABLE {table_name} (
                AppOrderID INT NOT NULL,
                TradingSymbol VARCHAR(255) NOT NULL,
                ExchangeInstrumentID INT NOT NULL,
                OrderSide VARCHAR(50) NOT NULL,
                OrderType VARCHAR(50) NOT NULL,
                OrderPrice DECIMAL(10, 2),
                Quantity INT NOT NULL,
                OrderAverageTradedPrice DECIMAL(10, 2),
                ExchangeTransactTimeAPI DATETIME,
                OrderUniqueIdentifier VARCHAR(255) NOT NULL,
                CalculationPrice DECIMAL(10, 2),
                PRIMARY KEY (AppOrderID)
            );
            """

            # Execute the create table command
            cursor.execute(create_table_query)
            connection.commit()
            print("Table created successfully")

    except mysql.connector.Error as error:
        print(f"Failed to create table in MySQL: {error}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")




def report_generator(strategy):
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='pegasus',
        database='sagar_execution'
    )

    cursor = conn.cursor()
    current_date = datetime.now().strftime("%Y%m%d")  
    table_name = f"tradebook_{current_date}"
    query = f"SELECT * FROM {table_name} WHERE OrderUniqueIdentifier LIKE '{strategy.name}%'"

    tradebook_df = pd.read_sql_query(query, conn)
    cursor.close()
    conn.close()
    entry_df = tradebook_df[~tradebook_df['OrderUniqueIdentifier'].str.endswith(('_sl', '_cover'))]
    exit_df = tradebook_df[tradebook_df['OrderUniqueIdentifier'].str.endswith(('_sl', '_cover'))]
    entry_df = entry_df.sort_values(by=['TradingSymbol', 'ExchangeTransactTimeAPI'])
    exit_df = exit_df.sort_values(by=['TradingSymbol', 'ExchangeTransactTimeAPI'])
    entry_df.reset_index(inplace=True, drop=True)
    exit_df.reset_index(inplace=True, drop=True)
    df = pd.merge(entry_df, exit_df, left_index=True, right_index=True, how='outer')
    df.rename(columns={
        'ExchangeInstrumentID_x': 'instrument_id',
        'OrderSide_x': 'trade',
        'OrderSide_y': 'exit_orderside',
        'OrderPrice_x': 'entry_orderprice',
        'OrderPrice_y': 'exit_orderprice',
        'Quantity_x': 'Quantity',
        'ExchangeTransactTimeAPI_x': 'entry_time',
        'ExchangeTransactTimeAPI_y': 'exitTimeStamp',
        'CalculationPrice_x': 'trigger_entry_price',
        'CalculationPrice_y': 'trigger_exit_price',
        'OrderAverageTradedPrice_x': 'traded_entry_price',
        'OrderAverageTradedPrice_y': 'traded_exit_price',
        'OrderUniqueIdentifier_x': 'entry_uid',
        'OrderUniqueIdentifier_y': 'exit_uid',
        'Quantity_y': 'exit_quantity',
        'TradingSymbol_x': 'symbol'
        }, inplace=True)
    
    columns_to_drop = [
        'AppOrderID_x', 'AppOrderID_y',
        'TradingSymbol_y', 'ExchangeInstrumentID_y',
        'OrderType_x', 
        'OrderType_y'
    ]
    df.drop(columns=columns_to_drop, inplace=True)
    df['entry_slippage'] = df.apply(lambda x: x['trigger_entry_price'] - x['traded_entry_price'] if x['trade'] == 'buy' else x['traded_entry_price'] - x['trigger_entry_price'], axis=1)
    
    df['exit_slippage'] = df.apply(lambda x: x['traded_exit_price'] - x['trigger_exit_price'] if x['trade'] == 'buy' else x['trigger_exit_price'] - x['traded_exit_price'], axis=1)
    
    df['pnl'] = df.apply(lambda x: (x['traded_exit_price'] - x['traded_entry_price'])*x["Quantity"] if x['trade'] == 'buy' else (x['traded_entry_price'] - x['traded_exit_price'])*x["Quantity"], axis=1)
    return df






def get_today_datetime(timestamp):
    hour, minute = map(int, timestamp.split(':'))
    return datetime.datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)

def initialize_sockets(market_token, interactive_token, port, userid, publisher):
    """
    Initializes and sets up the Market Data Socket and Order Socket, 
    connects to the Market Data Socket, and returns both sockets.

    Parameters:
    market_token (str): The token for the market data connection.
    interactive_token (str): The token for the order socket connection.
    port (int): The port for the connection.
    userid (str): The user ID for authentication.
    publisher (str): The publisher string for the connection.

    Returns:
    tuple: A tuple containing:
        - interactive_soc (OrderSocket_io): Initialized order socket object.
        - soc (MDSocket_io): Initialized market data socket object.
    """
    # Initialize market data socket
    soc = MDSocket_io(token=market_token, port=port, userID=userid, publisher=publisher)

    # Initialize order socket
    interactive_soc = OrderSocket_io(interactive_token, userid, port, publisher)

    # Get emitter and set up event listeners
    el = soc.get_emitter()
    el.on('connect', soc.on_connect)
    el.on('1512-json-full', soc.on_message1512_json_full)

    # Connect market data socket
    soc.connect()
    interactive_soc.connect()
    interactive_el = interactive_soc.get_emitter()
    interactive_el.on('trade', interactive_soc.on_trade)
    interactive_el.on('order', interactive_soc.on_order)
    return interactive_soc, soc







        
def broker_login(xts, creds):
    tokens_file = 'tokens.json'
    
    if os.path.exists(tokens_file):
        with open(tokens_file, 'r') as file:
            data = json.load(file)
        last_date = datetime.strptime(data['date'], '%Y-%m-%d')
        if last_date.date() == datetime.now().date():
            market_token = data['market_token']
            interactive_token = data['interactive_token']
            userid = data['userid']
            print("Using stored tokens.")
            return market_token, interactive_token, userid
    
    market_token, userid = xts.market_login(creds['market_secret'], creds['market_key'])
    interactive_token, _ = xts.interactive_login(creds['interactive_secret'], creds["interactive_key"])
    
    with open(tokens_file, 'w') as file:
        json.dump({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'market_token': market_token,
            'interactive_token': interactive_token,
            'userid': userid
        }, file)
    print("Stored new tokens.")
    
    return market_token, interactive_token, userid



def slice_orders(total_quantity, freeze_quantity):
    order_quantities = []
    while total_quantity > freeze_quantity:
        order_quantities.append(freeze_quantity)
        total_quantity -= freeze_quantity
    if total_quantity > 0:
        order_quantities.append(total_quantity)
    return order_quantities


def breakout_momentum_selection_criteria(xts, strategy, range_breakout, simple_momentum, instrument_id, trigger_tolerance, position, total_lots ):
        if range_breakout:
            timeframe = range_breakout['timeframe']
            start_time = strategy.entry_time
            end_time = start_time + timedelta(minutes=timeframe)
            start_time = start_time.strftime('%b %d %Y %H%M%S')
            end_time = end_time.strftime('%b %d %Y %H%M%S')
            # trade_side = range_breakout['']
            params = {
                "exchangeSegment": 2,
                "exchangeInstrumentID": instrument_id,
                "startTime": start_time,
                "endTime": end_time,
                "compressionValue": 60
            }
            print(params)
            print(f'sleeping for {timeframe} minutes')
            time.sleep(timeframe*60)
            data= xts.get_historical_data(params)['result']['dataReponse']
            data = data.replace(',', '\n')
            historical_data = pd.read_csv(StringIO(data), sep = '|', usecols=range(7), header = None, low_memory=False)
            new_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi']
            historical_data.columns = new_columns
            # historical_data['instrument_token'] = exchange_instrument_id
            # historical_data['tradingsymbol'] = tradingsymbol
            historical_data['timestamp'] = pd.to_datetime(historical_data['timestamp'], unit='s')
            print(historical_data)
            print(f"highest high is {max(historical_data['high'])}, and low is {min(historical_data['low'])}")
            if range_breakout['side'].lower()=='high':
                entry_price = max(historical_data['high'])
                print(f'high of range is {entry_price}')
            elif range_breakout['side'].lower()=='low':
                entry_price = min(historical_data['low'])
                print('low of range is {entry_price}')
            if position.lower() == 'buy':
                limit_price = int(entry_price)
                trigger_price = int(entry_price + trigger_tolerance)
            elif position.lower() == 'sell':
                limit_price = float(entry_price)
                trigger_price = float(entry_price - trigger_tolerance)
            print(trigger_price, entry_price, position)
            print(f"Range for {range_breakout['timeframe'] is  min(historical_data['low']) and  max(historical_data['high']) }")
            print(f"User selected {range_breakout['side']} option, and entry price is {entry_price}")
            order =  xts.place_SL_order({"exchangeInstrumentID": instrument_id, "orderSide": position, "orderQuantity":int(total_lots * lot_size), "limitPrice": trigger_price, 'stopPrice':entry_price, 'orderUniqueIdentifier': f"{leg_name}_rb"})
            print('order placed for range breakout')
            strategy.logger.log(f'{leg_name} : {instrument.tradingsymbol}, order placed for range breakout with entry price {limit_price}')
            print(order)
            return
        elif simple_momentum:
            if simple_momentum['value_type'].lower()=='points':
                sm_value = simple_momentum['value']
            elif simple_momentum['value_type'].lower()=='percentage':
                sm_value = round((entry_price*simple_momentum['value'])/100, 2)
            if simple_momentum['direction'].lower() =='increment':
                entry_price = entry_price + sm_value
            elif simple_momentum['direction'].lower() =='decay':
                entry_price = entry_price - sm_value
            if position.lower() == 'buy':
                limit_price = int(entry_price)
                trigger_price = int(entry_price + trigger_tolerance)
            elif position.lower() == 'sell':
                limit_price = float(entry_price)
                trigger_price = float(entry_price - trigger_tolerance)
            print(trigger_price, entry_price, position)
            
            order =  xts.place_SL_order({"exchangeInstrumentID": instrument_id,
                                               "orderSide": position,
                                                 "orderQuantity":int(total_lots * lot_size),
                                                   "limitPrice": trigger_price, 'stopPrice':entry_price,
                                                     'orderUniqueIdentifier': f"{leg_name}_sm"})
            print(f"Order placed for {simple_momentum['direction']}  of value {sm_value} and entry price is {limit_price}")
            print(order)
            return
        else:
            pass


def convert_end_time_format(end_time):
        """Convert end_time from 'Jul 13 2020 153000' to '2014-12-10 03:48:56' format."""
        try:
            # Parse the provided end_time
            parsed_time = datetime.strptime(end_time, "%b %d %Y %H%M%S")
            # Format to match lastupdatetime format
            return parsed_time.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            print("Error in time format conversion:", e)
            return None
        
def get_data_from_mysql(instrument_id, end_time, db_creds):
    try:
        # Convert end_time to the required format
        formatted_end_time = convert_end_time_format(end_time)
        if not formatted_end_time:
            print("Invalid end_time format. Exiting.")
            return None

        # Connect to the MySQL database
        connection = mysql.connector.connect(
            host=db_creds['host'],
            user=db_creds['user'],
            password=db_creds['password'],
            database=db_creds['database']
        )
        cursor = connection.cursor(dictionary=True)

        # Query to directly fetch LastTradedPrice
        query = """
            SELECT LastTradedPrice
            FROM data_harvesting_20241210
            WHERE lastupdatetime <= %s
            AND exchangeInstrumentID = %s
        """
        print(query, formatted_end_time, instrument_id)
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
        highest_price = max(last_traded_prices)
        lowest_price = min(last_traded_prices)
        print("Highest LastTradedPrice:", highest_price, "Lowest LastTradedPrice:", lowest_price)
        return {"HighestLastTradedPrice": highest_price, "LowestLastTradedPrice": lowest_price}

    except mysql.connector.Error as err:
        print("Error: ", err)
        return None

