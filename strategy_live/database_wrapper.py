from typing import Any, Dict, Union

def strike_selection_wrapper(params: Dict[str, Any]) -> Union[Dict[str, Any], None]:
    """
    Wraps the strike selection criteria into a standardized format based on the input parameters.

    Args:
        params (Dict[str, Any]): A dictionary containing strike selection criteria and associated values.

    Returns:
        Union[Dict[str, Any], None]: A dictionary with the standardized strike selection structure, or None if the criteria is invalid.
    """
    if params['strike_selection_criteria'].lower() == 'strike':
        return {
            'strike_selection': params['strike_selection_criteria'],
            'value': params['strike_type']
        }
    elif params['strike_selection_criteria'].lower() == 'closestpremium':
        return {
            'strike_selection': 'closest_premium',
            'value': float(params['closest_premium'])
        }
    elif params['strike_selection_criteria'].lower() == 'atmstraddlepremiumpercent':
        return {
            'strike_selection': 'atm_straddle_premium',
            'value': float(params['atm_straddle_premium'])
        }
    elif params['strike_selection_criteria'].lower() == 'percentofatmstrike':
        return {
            'strike_selection': 'atm_pct',
            'value': {'atm_strike': params['percent_of_atm_strike_sign'], 'input': float(params['percent_of_atm_strike_value'])}
        }
    elif params['strike_selection_criteria'].lower() == 'straddlewidth':
        return {
            'strike_selection': 'straddle_width',
            'value': {'atm_strike': params['straddle_width_sign'], 'input': float(params['straddle_width_value'])}
        }
    else:
        return None

def leg_stoploss_wrapper(leg: Dict[str, Any]) -> Union[list, bool]:
    """
    Wraps the stop-loss criteria for a leg into a standardized format.

    Args:
        leg (Dict[str, Any]): A dictionary containing leg details including stop-loss criteria.

    Returns:
        Union[list, bool]: A list containing stop-loss criteria and its value, or False if no criteria exist.
    """
    if leg['strike_selection_criteria_stop_loss']:
        return [leg['strike_selection_criteria_stop_loss_sign'], float(leg['strike_selection_criteria_stop_loss'])]
    else:
        return False

def leg_trail_sl_wrapper(leg: Dict[str, Any]) -> Union[Dict[str, Any], bool]:
    """
    Wraps the trailing stop-loss criteria for a leg into a standardized format.

    Args:
        leg (Dict[str, Any]): A dictionary containing leg details including trailing stop-loss criteria.

    Returns:
        Union[Dict[str, Any], bool]: A dictionary with the trailing stop-loss structure, or False if no criteria exist.
    """
    if leg['strike_selection_criteria_profit_reaches']:
        if leg['strike_selection_criteria_trailing_options'] == 'lock':
            return {
                "type": 'lock',
                "priceMove": leg['strike_selection_criteria_profit_reaches'],
                "sl_adjustment": leg['strike_selection_criteria_lock_profit'],
                "strike_selection_criteria_lock_profit_sign": leg['strike_selection_criteria_lock_profit_sign']
            }
        else:
            return {
                "type": "lock_and_trail",
                "priceMove": leg['strike_selection_criteria_profit_reaches'],
                "sl_adjustment": leg['strike_selection_criteria_lock_profit'],
                "strike_selection_criteria_lock_profit_sign": leg['strike_selection_criteria_lock_profit_sign'],
                "strike_selection_criteria_trail_profit": leg['strike_selection_criteria_trail_profit']
            }
    else:
        return False

def roll_strike_wrapper(leg: Dict[str, Any]) -> Union[Dict[str, Any], bool]:
    """
    Wraps the roll strike criteria for a leg into a standardized format.

    Args:
        leg (Dict[str, Any]): A dictionary containing leg details including roll strike criteria.

    Returns:
        Union[Dict[str, Any], bool]: A dictionary with the roll strike structure, or False if no criteria exist.
    """
    if leg['roll_strike']:
        return {
            'roll_level': leg['roll_strike'],
            'roll_strike_type': leg['roll_strike_strike_type']
        }
    else:
        return False

def sm_rb_wrapper(leg: Dict[str, Any]) -> Union[Dict[str, Any], bool]:
    """
    Wraps the simple momentum or range breakout criteria for a leg into a standardized format.

    Args:
        leg (Dict[str, Any]): A dictionary containing leg details including simple momentum or range breakout criteria.

    Returns:
        Union[Dict[str, Any], bool]: A dictionary with the simple momentum or range breakout structure, or False if no criteria exist.
    """
    if leg['simple_momentum_range_breakout'] == 'sm':
        return {
            'simple_momentum_sign': leg['simple_momentum_sign'],
            'simple_momentum_direction': leg['simple_momentum_direction'],
            'simple_momentum': leg['simple_momentum']
        }
    elif leg['simple_momentum_range_breakout'] == 'rb':
        return {
            'range_breakout': leg['range_breakout']
        }
    else:
        return False
