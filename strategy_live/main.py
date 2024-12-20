import asyncio
from datetime import datetime
from Strategy import Strategy
from LegBuilder import LegBuilder
from MarketSocket import MDSocket_io
from datetime import datetime
from Broker import XTS
import os
import sys
from utils import get_atm, create_tradebook_table, broker_login, initialize_sockets
from Publisher import Publisher
import time
publisher = Publisher()
create_tradebook_table()
import warnings
import asyncio
warnings.filterwarnings("ignore")
port = "https://ttblaze.iifl.com"
xts = XTS()  
sys.path.append(os.path.abspath('../../Sagar_common'))

try:
    from common_function import fetch_parameter
except ImportError as e:
    print(f"Error importing 'fetch_parameter': {e}")
environment = "dev"
creds = fetch_parameter(environment, "live_creds")
market_token, interactive_token, userid = broker_login(xts, creds)
xts.market_token, xts.interactive_token, xts.userid  = market_token, interactive_token, userid
interactive_soc, soc = initialize_sockets(market_token, interactive_token, port, userid, publisher)
xts.get_master({'exchangeSegmentList': ['NSEFO']})

async def process_leg(leg):
    print("processing legs")
    print(f" simple momentum for {leg.leg_name} is {leg.simple_momentum}")
    leg.selection_criteria()
    if leg.simple_momentum == False or leg.range_breakout == False:
        await leg.leg_place_order()
    await leg.calculate_mtm()
  
async def run_strategy(xts, strategy_details):
    strategy = Strategy(xts, **strategy_details)
    time_now = datetime.now()
    print(f"time is {datetime.now()}")
    print(time_now, strategy.entry_time)
    if time_now < strategy.entry_time:
        print(f'sleeping for {(strategy.entry_time - time_now).total_seconds()}')
        await asyncio.sleep((strategy.entry_time - time_now).total_seconds())

    underlying_ltp = strategy.get_underlying_ltp()
    if not underlying_ltp:
        retry_counter = 0
        while retry_counter <=3:
            print(f"retrying underlying_ltp retrieval for {retry_counter + 1} times")
            underlying_ltp = strategy.get_underlying_ltp()
            if underlying_ltp :
                return underlying_ltp
            retry_counter += 1
            await asyncio.sleep(2)
        underlying_ltp = None
        
    if underlying_ltp:
        print(f'{strategy.index} selected {strategy.underlying} and the last traded price is {underlying_ltp}')
        base = strategy.base #100 if strategy.index == 'NIFTY 50' else 50
        underlying_atm = get_atm(underlying_ltp, base)

        leg1 = LegBuilder(xts, 'soc', interactive_soc, f"{strategy.name}leg1", strategy, publisher, 2, 'sell', 'CE', 'current',
                        {'strike_selection': 'strike', 'value': 'ITM3'}, underlying_atm, roll_strike=False,
                        new_strike_selection_criteria=3, stop_loss=['points', 15], trailing_sl={"priceMove": 20, "sl_adjustment": 4}, no_of_reentry=2, 
                        simple_momentum=False, range_breakout=False)
        leg2 = LegBuilder(xts, 'soc', interactive_soc, f"{strategy.name}leg2", strategy, publisher, 2, 'sell', 'PE', 'current',
                        {'strike_selection': 'closest_premium', 'value': 200}, underlying_atm, roll_strike=False,
                        new_strike_selection_criteria=3, stop_loss=['points', 15], trailing_sl={"priceMove": 20, "sl_adjustment": 4}, no_of_reentry=2, 
                        simple_momentum=False, range_breakout=False)
        # leg1 = LegBuilder(xts, 'soc', interactive_soc, f"{strategy.name}leg1", strategy, publisher, 2, 'sell', 'CE', 'current',
        #                 {'strike_selection': 'closest_premium', 'value': 150}, underlying_atm, roll_strike=False,
        #                 new_strike_selection_criteria=3, stop_loss=['points', 10], trailing_sl={"priceMove": 10, "sl_adjustment": 4}, no_of_reentry=2, 
        #                 simple_momentum={'value_type':'points', 'value':15, 'direction': 'increment' }, range_breakout=False)
        # leg2 = LegBuilder(xts, 'soc', interactive_soc, f"{strategy.name}leg2", strategy, publisher, 2, 'sell', 'PE', 'current',
        #                 {'strike_selection': 'closest_premium', 'value': 150}, underlying_atm, roll_strike=False,
        #                 new_strike_selection_criteria=3, stop_loss=['points', 10], trailing_sl={"priceMove": 10, "sl_adjustment": 4}, no_of_reentry=2, 
        #                 simple_momentum={'value_type':'points', 'value':15, 'direction': 'increment' }, range_breakout=False)
        # # leg3 = LegBuilder(xts, 'soc', 'interactive_soc', f"{strategy.name}leg3", strategy, publisher, 2, 'sell', 'PE', 'current',
        # #                   {'strike_selection': 'strike', 'value': "ATM"}, underlying_atm, roll_strike=2,
        # #                   new_strike_selection_criteria=3, stop_loss=['points', 50], trailing_sl={"priceMove": 4, "sl_adjustment": 4}, no_of_reentry=2, 
        # #                   simple_momentum=False, range_breakout=False)
        legs = [leg1, leg2]
        # legs = [leg1]

        await asyncio.gather(
            process_leg(leg1),
            process_leg(leg2),
            strategy.calculate_overall_pnl(legs)
        )
    else:
        print('unable to find underlying ltp, exiting !!')
        return
        

async def main():

    strategy_details_1 = {
        'name': 'strategy1', 'index': 'NIFTY BANK', 'underlying': 'spot', 'strategy_type': 'intraday',
        'entry_time': "10:17", 'last_entry_time': "16:40", 'exit_time': "16:45", 'square_off': "partial",
        'overall_sl': 3000, 'overall_target': 4000,                   
        'trailing_for_strategy': {"type": "lock_and_trail", "profit": 2000, "lock_value": 1300, "trail_level":  200, "trail_value": 100}, 
        'implied_futures_expiry': 'current'
    }
    
    
    await asyncio.gather(
        run_strategy(xts, strategy_details_1),
    )

asyncio.run(main())
