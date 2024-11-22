from datetime import datetime
import mysql.connector
from mysql.connector import Error
import pandas as pd
from dateutil import parser
import json
import os

def get_atm(price, base):
    return  round(price / base) * base

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

    def log(self, message):
        # print(message)
        """Append a message with a timestamp to the log file."""
        with open(self.filename, 'a') as file:
            # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file.write(f"{message}\n")

# def update_tradebook(data):
#     try:
#         # Connection configuration
#         connection = mysql.connector.connect(
#             host='localhost',  
#             database='sagar_execution',
#             user='root',
#             password='pegasus'
#         )
#         if connection.is_connected():
#             cursor = connection.cursor()

#             # SQL query to update the tradebook table
#             query = """INSERT INTO tradebook (AppOrderID, Tradingsymbol, ExchangeInstrumentID, OrderSide, OrderType,
#                                               OrderPrice, OrderAverageTradedPrice, ExchangeTransactTimeAPI, OrderUniqueIdentifier)
#                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
#                        ON DUPLICATE KEY UPDATE
#                        Tradingsymbol=VALUES(Tradingsymbol),
#                        ExchangeInstrumentID=VALUES(ExchangeInstrumentID),
#                        OrderSide=VALUES(OrderSide),
#                        OrderType=VALUES(OrderType),
#                        OrderPrice=VALUES(OrderPrice),
#                        OrderAverageTradedPrice=VALUES(OrderAverageTradedPrice),
#                        ExchangeTransactTimeAPI=VALUES(ExchangeTransactTimeAPI),
#                        OrderUniqueIdentifier=VALUES(OrderUniqueIdentifier);"""
#             data['ExchangeTransactTimeAPI'] = datetime.strptime(data['ExchangeTransactTimeAPI'], '%Y-%m-%d %H:%M:%S')

#             data['ExchangeTransactTimeAPI'] = data['ExchangeTransactTimeAPI'].strftime('%Y-%m-%d %H:%M:%S')

#             tuple_data = (data['AppOrderID'], data['TradingSymbol'], data['ExchangeInstrumentID'], data['OrderSide'], 
#                           data['OrderType'], data['OrderPrice'], data['OrderAverageTradedPrice'], 
#                           data['ExchangeTransactTimeAPI'], data['OrderUniqueIdentifier'])

#             # Execute the query
#             cursor.execute(query, tuple_data)
#             connection.commit()
#             print("tradebook updated successfully")

#     except Error as e:
#         print("Error while connecting to MySQL", e)
#     finally:
#         if (connection.is_connected()):
#             cursor.close()
#             connection.close()
#             print("MySQL connection is closed")

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
    df['entry_slippage'] = df.apply(lambda x: x['trigger_entry_price'] - x['traded_entry_price'] if x['trade'] == 'buy' else x['traded_entry_price'] - x['traded_entry_price'], axis=1)
    
    df['exit_slippage'] = df.apply(lambda x: x['traded_exit_price'] - x['trigger_exit_price'] if x['trade'] == 'buy' else x['trigger_exit_price'] - x['traded_exit_price'], axis=1)
    
    df['pnl'] = df.apply(lambda x: (x['traded_exit_price'] - x['traded_entry_price'])*x["Quantity"] if x['trade'] == 'buy' else (x['traded_entry_price'] - x['traded_exit_price'])*x["Quantity"], axis=1)
    return df






def get_today_datetime(timestamp):
    hour, minute = map(int, timestamp.split(':'))
    return datetime.datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)



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
