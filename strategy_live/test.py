# underlying_ltp = self.strategy.get_underlying_ltp()
index = 'NIFTY 50'
base = 100 if index == 'NIFTY BANK' else 50 
underlying_atm = 23500
# instrument_atm = get_atm(underlying_ltp, base)

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


print(get_rolling_strike(underlying_atm, "ce", "otm3", 100))