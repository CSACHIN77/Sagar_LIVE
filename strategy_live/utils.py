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

def apply_strike_selection_criteria(choice_value, strike, expiry_df, option_type, base=100):
    """
    Select an option contract based on the specified strike selection criteria.

    This function processes different strike selection options such as ATM, ITM, or OTM, 
    adjusts the strike price accordingly, and identifies the corresponding option contract 
    from the given expiry DataFrame.

    Parameters:
        choice_value (str): The strike selection criteria ('ATM', 'ITM', 'OTM') with optional depth for ITM/OTM.
        strike (int): The initial ATM strike price.
        expiry_df (DataFrame): A DataFrame containing option contract details including strikes and tokens.
        option_type (int): The type of the option (3 for CE, 4 for PE).
        base(int): strike gap of the given instrument

    Returns:
        tuple: 
            - option_symbol (str): The tradingsymbol of the selected option.
            - lot_size (int): The lot size associated with the selected option.
            - instrument_id (int): The unique instrument ID of the selected option.

    Raises:
        ValueError: If no suitable option is found for the given criteria.
    """
    choice_value = choice_value.upper()
    if choice_value == 'ATM':
        option_symbol = expiry_df[(expiry_df['strike'].astype(int) == strike)]
        instrument_id = int(option_symbol['instrument_token'].values[0])
        lot_size = int(option_symbol['lot_size'].values[0])
    elif choice_value.startswith('ITM'):
        itm_depth = re.findall(r'\d+', choice_value)
        if itm_depth:
            if option_type == 3:
                strike = strike - base * int(itm_depth[0])
            else:
                strike = strike + base * int(itm_depth[0])
            option_symbol = expiry_df[(expiry_df['strike'].astype(int) == strike)]
            instrument_id = int(option_symbol['instrument_token'].values[0])
            lot_size = int(option_symbol['lot_size'].values[0])
    elif choice_value.startswith('OTM'):
        itm_depth = re.findall(r'\d+', choice_value)
        if itm_depth:
            if option_type == 3:
                strike = strike + base * int(itm_depth[0])
            else:
                strike = strike - base * int(itm_depth[0])
            option_symbol = expiry_df[(expiry_df['strike'].astype(int) == strike)]
            instrument_id = int(option_symbol['instrument_token'].values[0])
            lot_size = int(option_symbol['lot_size'].values[0])
    else:
        raise ValueError(f"Invalid choice_value: {choice_value}. Must be 'ATM', 'ITM', or 'OTM'.")

    return option_symbol, lot_size, instrument_id


def apply_closest_premium_selection_criteria(xts, choice_value, expiry_df):
    """
    Select the option contract closest to a specified premium value.

    This function identifies and selects the nearest option contract based on the difference
    between the given premium value and the last traded prices (LTP) of all available contracts.
    The option with the smallest price difference is chosen.

    Parameters:
        xts: An instance of the trading for XTS api, used for fetching market data.
        choice_value: The target premium value for selecting the option.
        expiry_df: A DataFrame containing option contract details including strikes, instrument tokens, and lot sizes.

    Returns:
        option_symbol: The tradingsymbol of the selected option.
        lot_size: The lot size associated with the selected option.
        instrument_id: The unique instrument ID of the selected option.
        nearest_premium: The premium value of the selected option.

    Raises:
        ValueError: If no suitable option is found.
    """
    exid_list = list(expiry_df['instrument_token'])
    chunks = [exid_list[i:i + 50] for i in range(0, len(exid_list), 50)]
    exchange_instrument_ids, last_traded_prices = [], []

    for chunk in chunks:
        premium_instruments_chunk = [{'exchangeSegment': 2, 'exchangeInstrumentID': exid} for exid in chunk]
        response = xts.get_quotes(premium_instruments_chunk)
        ltp_data = response['result']['listQuotes']
        for item in ltp_data:
            item_dict = eval(item)
            exchange_instrument_ids.append(item_dict['ExchangeInstrumentID'])
            last_traded_prices.append(item_dict['LastTradedPrice'])

    df = pd.DataFrame({
        'exchangeInstrumentID': exchange_instrument_ids,
        'LastTradedPrice': last_traded_prices,
    })
    df['PriceDifference'] = abs(df['LastTradedPrice'] - choice_value)
    option_data_sorted = df.sort_values(by='PriceDifference')

    if option_data_sorted.empty:
        raise ValueError("No suitable options found based on the given premium.")

    nearest_option = option_data_sorted.iloc[0]
    nearest_premium = nearest_option.LastTradedPrice
    instrument_id = int(nearest_option.exchangeInstrumentID)
    nearest_option_name = expiry_df[expiry_df['instrument_token'] == instrument_id]
    option_symbol = nearest_option_name.iloc[0].tradingsymbol
    lot_size = nearest_option_name.iloc[0].lot_size

    return option_symbol, lot_size, instrument_id, nearest_premium

def apply_straddle_width_selection_criteria(xts, choice, choice_value, combined_expiry_df, strike, expiry_df, base=100):
    """
    Select an option contract based on straddle width criteria.

    This function calculates the combined premium of a straddle at a specific strike
    and applies the selection criteria, such as finding the closest premium or adjusting
    the strike based on percentage or premium value.

    Parameters:
        xts: An instance of the trading platform's API client for fetching market data.
        choice (str): The selection criteria ('atm_straddle_premium', 'atm_pct', etc.).
        choice_value (Union[float, dict]): The value or parameters for the selection criteria.
        combined_expiry_df (DataFrame): A DataFrame containing option contracts for the straddle calculation.
        strike (int): The initial strike price for the straddle.
        expiry_df (DataFrame): A DataFrame containing option contract details including strikes and tokens.
        base (int): The base unit for adjusting the strike (default is 100).

    Returns:
        tuple:
            - option_symbol (str): The tradingsymbol of the selected option.
            - lot_size (int): The lot size associated with the selected option.
            - instrument_id (int): The unique instrument ID of the selected option.

    Raises:
        ValueError: If no suitable option is found or if invalid selection criteria are provided.

    Examples:
        1. To find the option closest to a specific straddle premium:
            apply_straddle_width_selection_criteria(xts, 'atm_straddle_premium', 200, combined_expiry_df, 17000, expiry_df)

        2. To adjust the strike by a percentage:
            apply_straddle_width_selection_criteria(xts, 'atm_pct', {'atm_strike': '+', 'input': 0.02}, combined_expiry_df, 17000, expiry_df)
    """
    straddle_df = combined_expiry_df[combined_expiry_df['strike'].astype(int) == int(strike)]
    options_list = []
    instrument_tokens = list(straddle_df['instrument_token'])

    # Fetching quotes for all instruments in the straddle
    for instrument_token in instrument_tokens:
        options_list.append({'exchangeSegment': 2, 'exchangeInstrumentID': instrument_token})
    results = xts.get_quotes(options_list)

    if results['type'] == 'success':
        ltp_data = results['result']['listQuotes']

    # Calculate combined premium
    combined_premium = sum(json.loads(ltp_item)['LastTradedPrice'] for ltp_item in ltp_data)

    # Handle different selection criteria
    if choice.lower() == 'atm_straddle_premium':
        combined_premium = round(((combined_premium * choice_value) / 100), 2)
        print(f'atm_straddle_premium has {combined_premium} value ')
        return apply_closest_premium_selection_criteria(xts, combined_premium, expiry_df)

    elif choice.lower() == 'atm_pct':
        if choice_value['atm_strike'] == '+':
            atm_points = choice_value['input'] * strike
            strike = get_atm(strike + atm_points, base)
        elif choice_value['atm_strike'] == '-':
            atm_points = choice_value['input'] * strike
            strike = get_atm(strike - atm_points, base)
        selected_option = expiry_df[expiry_df['strike'].astype(int) == strike].iloc[0]
        return selected_option.tradingsymbol, selected_option.lot_size, int(selected_option.instrument_token)

    elif choice_value['atm_strike'] in ['+', '-']:
        direction = 1 if choice_value['atm_strike'] == '+' else -1
        selected_strike = strike + direction * combined_premium * choice_value['input']
        selected_strike = get_atm(selected_strike, base)
        selected_option = expiry_df[expiry_df['strike'].astype(int) == selected_strike].iloc[0]
        return selected_option.tradingsymbol, selected_option.lot_size, int(selected_option.instrument_token)

    raise ValueError(f"Invalid selection criteria: {choice}")

        
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
           