import asyncio
from datetime import datetime
from Strategy import Strategy
from LegBuilder import LegBuilder
from datetime import datetime

import os
import sys
from utils import get_atm, create_tradebook_table, broker_login, initialize_sockets, get_path
from Logger.MyLogger import Logger
from Publisher import Publisher
import time
publisher = Publisher()
create_tradebook_table()
import warnings
import asyncio
from pathlib import Path
import mysql.connector
warnings.filterwarnings("ignore")
port = "https://ttblaze.iifl.com"

sys.path.append(get_path("Sagar_common"))

# Add the parent directory (Sagar_LIVE) to the Python path

try:
    from common_function import fetch_parameter
except ImportError as e:
    print(f"Error importing 'fetch_parameter': {e}")
environment = "dev"

Logger.print("Test")

if environment =="dev":
    from MarketSocket.sandboxMarketSocket import MDSocket_io
    from Broker.xtsBroker import XTS
    from InteractiveSocket.xtsInteractiveSocket import OrderSocket_io
    xts = XTS()  
    creds = fetch_parameter(environment, "live_creds")
    market_token, interactive_token, userid = broker_login(xts, creds)
    xts.market_token, xts.interactive_token, xts.userid  = market_token, interactive_token, userid
    # xts.update_master_db()
    interactive_soc, soc = initialize_sockets(market_token, interactive_token, port, userid, publisher)
    xts.get_master({'exchangeSegmentList': ['NSEFO']})
    # xts.get_master_db()

    
else :
    from MarketSocket.sandboxMarketSocket import MDSocket_io
    from InteractiveSocket.sandboxInteractiveSocket import OrderSocket_io
    from Broker.sandboxBroker import XTS
    port = "localhost:5001" 
    interactive_port = '8050'
    soc = MDSocket_io( port=port, publisher=publisher) #initialize 
    interactive_soc = OrderSocket_io(interactive_port, publisher)
    # soc.on_connect = on_connect
    # el = soc.get_emitter()
    # el.on('connect', soc.on_connect)
    # el.on('1512-json-full', soc.on_message1512_json_full)
    soc.connect()
    interactive_soc.connect()
    # interactive_soc.on_trade = on_trade
    interactive_el = interactive_soc.get_emitter()
    interactive_el.on('trade', interactive_soc.on_trade)
    interactive_el.on('order', interactive_soc.on_order)
    xts = XTS(soc)  

# Database credentials and connection setup
def fetch_db_connection(env, key):
    db_creds = fetch_parameter(env, key)
    return mysql.connector.connect(**db_creds)

# Fetch strategy and leg details from the database
def fetch_strategy_and_legs(strategy_ids):
    """
    Fetch strategies and their corresponding legs based on the provided strategy IDs.

    Parameters:
        strategy_ids (list[int]): List of strategy IDs to fetch.

    Returns:
        dict: A dictionary mapping strategy IDs to their details and associated legs.
    """
    connection = fetch_db_connection("dev", "db_sagar_strategy")
    cursor = connection.cursor(dictionary=True)

    try:
        strategy_query = "SELECT * FROM strategy WHERE id IN (%s)" % (', '.join(['%s'] * len(strategy_ids)))
        cursor.execute(strategy_query, strategy_ids)
        strategies = cursor.fetchall()
        print(strategies)
        results = {}
        for strategy in strategies:
            strategy_id = strategy['id']
            results[strategy_id] = {
                'strategy_details': strategy,
                'legs': []
            }
            leg_query = "SELECT * FROM leg WHERE strategy_id = %s"
            cursor.execute(leg_query, (strategy_id,))
            legs = cursor.fetchall()
            results[strategy_id]['legs'] = legs
        return results
    finally:
        cursor.close()
        connection.close()

def map_strategy_details(strategy_details, index):
    return {
        'name': strategy_details['name'],
        'index': index,
        'underlying': strategy_details['underlying'],
        'strategy_type': strategy_details['strategy_type'],
        'entry_time': strategy_details['entry_time'],
        'last_entry_time': strategy_details['last_entry_time'],
        'exit_time': strategy_details['exit_time'],
        'square_off': strategy_details['square_off'],
        'overall_sl': strategy_details['overall_sl'],
        'overall_target': strategy_details['overall_target'],
        'trailing_for_strategy': strategy_details.get('trailing_for_strategy', False),
        'implied_futures_expiry': strategy_details['implied_futures_expiry']
    }

def map_leg_details(legs):
    return [
        {
            'id': leg['id'],
            'strategy_id': leg['strategy_id'],
            'leg_no': leg['leg_no'],
            'lots': leg['lots'],
            'position': leg['position'],
            'option_type': leg['option_type'],
            'expiry': leg['expiry'].lower(),
            'strike_selection': {
                'strike_selection': leg['strike_selection_criteria'],
                'value': leg.get('strike_type', None).lower()
            },
            'simple_momentum': leg['simple_momentum'],
            'range_breakout': leg['range_breakout'],
            'stoploss' : [leg['strike_selection_criteria_stop_loss_sign'], leg['strike_selection_criteria_stop_loss']],
            'reentry' : leg['no_of_reentry']
        }
        for leg in legs
    ]

async def process_leg(leg):
    Logger.print(f"Processing leg: {leg}")
    leg.selection_criteria()
    if leg.simple_momentum == False and leg.range_breakout == False:
        await leg._leg_place_order()
    await leg.calculate_mtm()

async def run_strategy(xts, strategy_details, legs):
    total_legs =[]
    counter = 1
    strategy = Strategy(xts, **strategy_details)
    Logger.print(f"Running strategy: {strategy_details['name']}")
    time_now = datetime.now()
    if environment !='dev':
        while soc.current_data_time is None:
            print("waiting for current_data_time to set.")
            await asyncio.sleep(1)
    if time_now < strategy.entry_time:
        print(f'sleeping for {(strategy.entry_time - time_now).total_seconds()}')
        await asyncio.sleep((strategy.entry_time - time_now).total_seconds())
    underlying_ltp = strategy.get_underlying()
    if not underlying_ltp:
        retry_counter = 0
        while retry_counter <=3:
            print(f"retrying underlying_ltp retrieval for {retry_counter + 1} times")
            underlying_ltp = strategy.get_underlying()
            if underlying_ltp :
                return underlying_ltp
            retry_counter += 1
            await asyncio.sleep(2)
        underlying_ltp = None
    if underlying_ltp:
        base = strategy.base
        underlying_atm = get_atm(underlying_ltp, base)
        for leg in legs:
            leg_class = LegBuilder(xts, 'soc', interactive_soc, f"{strategy.name}leg{counter}", strategy, publisher, leg['lots'],
                                leg['position'], leg['option_type'], leg['expiry'], leg['strike_selection'],underlying_atm, roll_strike=False,
                                new_strike_selection_criteria=3, stop_loss=leg['stoploss'], trailing_sl=False, no_of_reentry=leg['reentry'],
                                simple_momentum=False, range_breakout=False
                                )
            counter +=1 
            total_legs.append(leg_class)
        await asyncio.gather(
            process_leg(total_legs[0]),
            process_leg(total_legs[1]),
            strategy._calculate_overall_pnl(total_legs)
        )
    # Process all legs for the strategy
    # await asyncio.gather(*(process_leg(leg) for leg in legs))
    
# Main execution function
async def main():
    strategy_ids = [41]  
    strategies_with_legs = fetch_strategy_and_legs(strategy_ids)

    for strategy_id, data in strategies_with_legs.items():
        strategy_details = map_strategy_details(data['strategy_details'], "NIFTY 50")
        legs = map_leg_details(data['legs'])
        await run_strategy(xts, strategy_details, legs)

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
