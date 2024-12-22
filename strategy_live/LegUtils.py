import re
from utils import get_atm
import json
import pandas as pd
from utils import filter_dataframe
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
        pass
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
    option_symbol_df = expiry_df[(expiry_df['strike'].astype(int) == strike)]
    instrument_id, lot_size, option_symbol = get_option_details(option_symbol_df)
    return option_symbol, lot_size, instrument_id

def get_option_details(option_symbol_df):
    """
    Extracts and returns the instrument ID, lot size, and trading symbol from the given DataFrame.

    Parameters:
    option_symbol_df (DataFrame): DataFrame containing option symbol details, including 
                                  'instrument_token', 'lot_size', and 'tradingsymbol'.

    Returns:
    tuple: A tuple containing:
        - instrument_id (int): The instrument token as an integer.
        - lot_size (int): The lot size as an integer.
        - option_symbol (str): The trading symbol as a string.
    """
    print(f"option symbol df is {option_symbol_df}")
    instrument_id = int(option_symbol_df['instrument_token'].values[0])
    lot_size = int(option_symbol_df['lot_size'].values[0])
    option_symbol = option_symbol_df['tradingsymbol'].iloc[0]
    return instrument_id, lot_size, option_symbol

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



def assign_strategy_variables(strategy):
    """
    Extracts and returns key attributes from the given strategy object.

    Parameters:
        strategy: An object containing the strategy details.

    Returns:
        tuple: Contains the index, DataFrame (df), and base values of the strategy.
    """
    return strategy.index, strategy.df, strategy.base




def get_expiry_df(df, index, expiry, option_type):
    """
    Filters the options data based on the given index, expiry type, and option type.
    Returns two DataFrames:
    1. `expiry_df`: Options data for the specified expiry day and option type.
    2. `combined_expiry_df`: All options data for the specified expiry day, irrespective of option type.
    """
    opt_df, monthly_expiry_list = filter_dataframe(df, [index])
    expiry_list = sorted(set(opt_df['expiry']))
    if expiry == 2 and expiry_list[0] == monthly_expiry_list[0]:
        expiry_day = monthly_expiry_list[1]
    elif expiry == 2:
        expiry_day = monthly_expiry_list[0]
    else:
        expiry_day = expiry_list[expiry]
    combined_expiry_df = opt_df[opt_df['expiry'] == expiry_day]
    expiry_df = combined_expiry_df[combined_expiry_df['option_type'] == option_type]
    return expiry_df, combined_expiry_df
