import sys
from utils import get_path
import mysql.connector
sys.path.append(get_path("Sagar_common"))
try:
    from common_function import fetch_parameter
except ImportError as e:
    print(f"Error importing 'fetch_parameter': {e}")

def strategy_mapper(strategy_details, index):
    mapped_strategy = {}
    mapped_strategy['name'] = strategy_details['name']
    mapped_strategy['underlying'] = strategy_details['underlying']
    mapped_strategy['strategy_type'] = strategy_details['strategy_type']
    mapped_strategy['entry_time'] = strategy_details['entry_time']
    mapped_strategy['last_entry_time'] = strategy_details['last_entry_time']
    mapped_strategy['exit_time'] = strategy_details['exit_time']
    mapped_strategy['square_off'] = strategy_details['square_off']
    mapped_strategy['overall_sl'] = strategy_details['overall_sl']
    mapped_strategy['overall_target'] = strategy_details['overall_target']
    mapped_strategy['trailing_for_strategy'] = False #strategy_details['trailing_for_strategy']
    mapped_strategy['implied_futures_expiry'] = strategy_details['implied_futures_expiry']
    mapped_strategy['index'] = index
    print(mapped_strategy)

def fetch_strategy_and_legs(strategy_ids):
    """
    Fetch strategies and their corresponding legs based on the provided strategy IDs.

    Parameters:
        strategy_ids (list[int]): List of strategy IDs to fetch.

    Returns:
        dict: A dictionary mapping strategy IDs to their details and associated legs.
    """
    db_creds_strategy = fetch_parameter("dev", "db_sagar_strategy")

    # Establish a connection to the MySQL database
    connection = mysql.connector.connect(**db_creds_strategy)
    cursor = connection.cursor(dictionary=True)

    try:
        # Prepare the query to fetch strategies
        strategy_query = "SELECT * FROM strategy WHERE id IN (%s)" % (', '.join(['%s'] * len(strategy_ids)))
        cursor.execute(strategy_query, strategy_ids)
        strategies = cursor.fetchall()

        # Initialize a dictionary to store results
        results = {}

        # Fetch legs for each strategy
        for strategy in strategies:
            strategy_id = strategy['id']
            results[strategy_id] = {
                'strategy_details': strategy,
                'legs': []
            }

            # Fetch legs associated with the current strategy
            leg_query = "SELECT * FROM leg WHERE strategy_id = %s"
            cursor.execute(leg_query, (strategy_id,))
            legs = cursor.fetchall()

            results[strategy_id]['legs'] = legs

        return results

    finally:
        cursor.close()
        connection.close()

strategy_ids = [41]  
strategies_with_legs = fetch_strategy_and_legs(strategy_ids)

for strategy_id, data in strategies_with_legs.items():
    print(f"Strategy ID: {strategy_id}")
    # strategy_mapper(data['strategy_details'], 'NIFTY BANK')
    # print("Details:", data['strategy_details'])
    # print("Legs:")
    
    leg_mapper = []
    for leg in data['legs']:
        leg_mapper.append(leg)
        # leg_mapper.append({
        #             'id': leg['id'],
        #             'strategy_id': leg['strategy_id'],
        #             'leg_no': leg['leg_no'],
        #             'lots': leg['lots'],
        #             'position': leg['position'],
        #             'option_type': leg['option_type'],
        #             'expiry': leg['expiry'],
        #             'no_of_reentry': leg['no_of_reentry'],
        #             'strike_selection_criteria': leg['strike_selection_criteria'],
        #             'closest_premium': leg['closest_premium'],
        #             'strike_type': leg['strike_type'],
        #             'straddle_width_value': leg['straddle_width_value'],
        #             'straddle_width_sign': leg['straddle_width_sign'],
        #             'percent_of_atm_strike_value': leg['percent_of_atm_strike_value'],
        #             'percent_of_atm_strike_sign': leg['percent_of_atm_strike_sign'],
        #             'atm_straddle_premium': leg['atm_straddle_premium'],
        #             'strike_selection_criteria_stop_loss': leg['strike_selection_criteria_stop_loss'],
        #             'strike_selection_criteria_stop_loss_sign': leg['strike_selection_criteria_stop_loss_sign'],
        #             'strike_selection_criteria_trailing_options': leg['strike_selection_criteria_trailing_options'],
        #             'strike_selection_criteria_lock_profit': leg['strike_selection_criteria_lock_profit'],
        #             'strike_selection_criteria_profit_reaches': leg['strike_selection_criteria_profit_reaches'],
        #             'strike_selection_criteria_lock_profit_sign': leg['strike_selection_criteria_lock_profit_sign'],
        #             'strike_selection_criteria_increase_in_profit': leg['strike_selection_criteria_increase_in_profit'],
        #             'strike_selection_criteria_trail_profit': leg['strike_selection_criteria_trail_profit'],
        #             'strike_selection_criteria_trail_profit_sign': leg['strike_selection_criteria_trail_profit_sign'],
        #             'roll_strike': leg['roll_strike'],
        #             'roll_strike_strike_type': leg['roll_strike_strike_type'],
        #             'roll_strike_stop_loss': leg['roll_strike_stop_loss'],
        #             'roll_strike_stop_loss_sign': leg['roll_strike_stop_loss_sign'],
        #             'roll_strike_trailing_options': leg['roll_strike_trailing_options'],
        #             'roll_strike_profit_reaches': leg['roll_strike_profit_reaches'],
        #             'roll_strike_lock_profit': leg['roll_strike_lock_profit'],
        #             'roll_strike_lock_profit_sign': leg['roll_strike_lock_profit_sign'],
        #             'roll_strike_increase_in_profit': leg['roll_strike_increase_in_profit'],
        #             'roll_strike_trail_profit': leg['roll_strike_trail_profit'],
        #             'roll_strike_trail_profit_sign': leg['roll_strike_trail_profit_sign'],
        #             'simple_momentum_range_breakout': leg['simple_momentum_range_breakout'],
        #             'simple_momentum': leg['simple_momentum'],
        #             'simple_momentum_sign': leg['simple_momentum_sign'],
        #             'simple_momentum_direction': leg['simple_momentum_direction'],
        #             'range_breakout': leg['range_breakout']
        #         })
        

    print(leg_mapper)
        


        









