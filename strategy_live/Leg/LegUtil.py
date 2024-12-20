from datetime import datetime, timedelta
import pandas as pd
from dateutil import parser
import re
import json
import time
from io import StringIO
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_atm

environment = "dev"

# get stike
def get_strike(choice_value, strike, option_type, base):
    choice_value = choice_value.upper()
    if choice_value == 'ATM':
        strike = strike

    elif choice_value.startswith('ITM'):
        itm_depth = re.findall(r'\d+', choice_value)
        if itm_depth:
            if option_type == 3:
                strike = strike - base * int(itm_depth[0])
            else:
                strike = strike + base * int(itm_depth[0])

    elif choice_value.startswith('OTM'):
        itm_depth = re.findall(r'\d+', choice_value)
        if itm_depth:
            if option_type == 3:
                strike = strike + base * int(itm_depth[0])
            else:
                strike = strike - base * int(itm_depth[0])
    
    else: 
        raise ValueError(f"Invalid choice_value: {choice_value}. Must be 'ATM', 'ITM', or 'OTM'.")
    return strike

def filter_symbol_df(expiry_df, key, val):
    option_symbol = expiry_df[(expiry_df[key].astype(int) == val)]
    if len(option_symbol) > 0:
        tradingsymbol = option_symbol['tradingsymbol'].values[0]
        instrument_id = int(option_symbol['instrument_token'].values[0])
        lot_size = int(option_symbol['lot_size'].values[0])
        return {"symbol": tradingsymbol, "instrument_id": instrument_id, "lot_size": lot_size}
    print("Seleted strike not found in the expiry_df")
    return None


def get_straddle_premium(xts, combined_expiry_df, strike):
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

    return combined_premium


# get closest premium strike
def closest_premium_stike_selection(xts, choice_value, expiry_df):
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
    strike = nearest_option_name.iloc[0].strike

    return strike


def straddle_width_strike_selection(xts, combined_premium, choice, choice_value, combined_expiry_df, strike, expiry_df, base):
    # Handle different selection criteria
    if choice.lower() == 'atm_straddle_premium':
        combined_premium = round(((combined_premium * choice_value) / 100), 2)
        print(f'atm_straddle_premium has {combined_premium} value ')
        return closest_premium_stike_selection(xts, combined_premium, expiry_df)

    elif choice.lower() == 'atm_pct':
        if choice_value['atm_strike'] == '+':
            atm_points = choice_value['input'] * strike
            strike = get_atm(strike + atm_points, base)
        elif choice_value['atm_strike'] == '-':
            atm_points = choice_value['input'] * strike
            strike = get_atm(strike - atm_points, base)
        return strike

    elif choice_value['atm_strike'] in ['+', '-']:
        direction = 1 if choice_value['atm_strike'] == '+' else -1
        selected_strike = strike + direction * combined_premium * choice_value['input']
        selected_strike = get_atm(selected_strike, base)
        return selected_strike

    raise ValueError(f"Invalid selection criteria: {choice}")


def get_range_breakout_value(xts, timeframe, start_time, instrument_id):
    end_time = start_time + timedelta(minutes=timeframe)
    start_time = start_time.strftime('%b %d %Y %H%M%S')
    end_time = end_time.strftime('%b %d %Y %H%M%S')
    
    # trade_side = self.range_breakout['']
    params = {
                "exchangeSegment": 2,
                "exchangeInstrumentID": instrument_id,
                "startTime": start_time,
                "endTime": end_time,
                "compressionValue": 60
            }
    print(params)

    # wait till range timeframe is completed
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
    max_high = max(historical_data['high'])
    min_low = min(historical_data['low'])
    print(f"highest high is {max(historical_data['high'])}, and low is {min(historical_data['low'])}")   
    return max_high, min_low


def get_range_breakout_order_price(breakout_side, position, range_high, range_low, trigger_tolerance):
    if breakout_side.lower()=='high':
        entry_price = range_high
        print(f'high of range is {entry_price}')
    elif breakout_side.lower()=='low':
        entry_price = range_low
        print('low of range is {entry_price}')

    if position.lower() == 'buy':
        limit_price = int(entry_price)
        trigger_price = int(entry_price + trigger_tolerance)
    elif position.lower() == 'sell':
        limit_price = float(entry_price)
        trigger_price = float(entry_price - trigger_tolerance)
        print(trigger_price, entry_price, position)
    
    return entry_price, limit_price, trigger_price

def get_momentum_order_price(value_type, value, direction, position, trigger_tolerance):
    if value_type.lower()=='points':
        sm_value = value
    elif value_type.lower()=='percentage':
        sm_value = round((entry_price * value)/100, 2)

    if direction.lower() =='increment':
        entry_price = entry_price + sm_value
    elif direction.lower() =='decay':
        entry_price = entry_price - sm_value

    if position.lower() == 'buy':
        limit_price = int(entry_price)
        trigger_price = int(entry_price + trigger_tolerance)
    elif position.lower() == 'sell':
        limit_price = float(entry_price)
        trigger_price = float(entry_price - trigger_tolerance)
    return entry_price, limit_price, trigger_price, sm_value
