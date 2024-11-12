from Strategy import Strategy
from LegBuilder import LegBuilder
from MarketSocket import MDSocket_io
from InteractiveSocket import OrderSocket_io
from datetime import datetime
from Broker import XTS
from creds import creds
from utils import get_atm
from Publisher import Publisher
import time
xts = XTS()
import warnings
import asyncio
warnings.filterwarnings("ignore")
port = "https://developers.symphonyfintech.in"
# port = "https://ttblaze.iifl.com"
publisher = Publisher()

market_token, userid =xts.market_login(creds['market_secret'], creds['market_key'])
# market_token, userid = xts.market_login("Dllf432@Co", "1f440830af1d82a7a09251")

interactive_token, userid = xts.interactive_login("Lsxn758$GM", "831d039e6b733ad7566192")
xts.update_master_db()
soc = MDSocket_io(token = market_token, port=port, userID=userid,publisher=publisher) #initialize 
interactive_soc = OrderSocket_io(interactive_token, userid, port, publisher)
# soc.on_connect = on_connect
el = soc.get_emitter()
el.on('connect', soc.on_connect)
el.on('1512-json-full', soc.on_message1512_json_full)
soc.connect()

interactive_soc.connect()
# interactive_soc.on_trade = on_trade
interactive_el = interactive_soc.get_emitter()
interactive_el.on('trade', interactive_soc.on_trade)
interactive_el.on('order', interactive_soc.on_order)

# xts.get_master({'exchangeSegmentList': ['NSEFO']})
strategy1 = Strategy(xts, name='strategy1', index='NIFTY 50', underlying='implied_futures', strategy_type='intraday', entry_time="10:45",
                    last_entry_time="14:30", exit_time =  "15:20", square_off="partial", overall_sl =  1000,
                    overall_target=1000, trailing_for_strategy="lock", implied_futures_expiry='current')

# strategy1.get_index_details(1)
# time_now = datetime.now()
# print(time_now, strategy1.entry_time)
# # if time_now < strategy1.entry_time:
# #     print(f'sleeping for {(strategy1.entry_time - time_now).total_seconds()}')
# #     time.sleep((strategy1.entry_time - time_now).total_seconds())

underlying_ltp = strategy1.get_underlying_ltp()
# print(f'{strategy1.index} selected {strategy1.underlying} and the last traded price is {underlying_ltp}')
base = 100 if strategy1.index == 'NIFTY 50' else 50
underlying_atm = get_atm(underlying_ltp, base)
# print(f'ATM strike for the {strategy1.index} is {underlying_atm}')


async def process_leg(leg):
    leg.get_expiry_df()
    leg.selection_criteria()
    # leg.leg_place_order()
    # await leg.calculate_mtm()
    

async def main():
    leg1 = LegBuilder(xts, 'soc', 'interactive_soc','leg1', strategy1, publisher, 2, 'sell', 'PE', 'current', 
                      {'strike_selection': 'closest_premium', 'value':150}, underlying_atm,roll_strike=2,
                        new_strike_selection_criteria=3, stop_loss=['points', 30], trailing_sl=5, no_of_reentry=6, simple_momentum={'value_type': 'percentage', 'value': 20, 'direction':'increment'}, range_breakout=False )
    # leg2 = LegBuild      roll_strike=2, new_strike_selection_criteria=3, stop_loss=['points', 40], trailing_sl=5, no_of_reentry=6, simple_momentum=7, range_breakout=8)
    # leg3 = LegBuilder(xts, 'soc', 'interactive_soc', 'leg3', strategy1,publisher,  3, 'buy', 'CE', 'current', {'strike_selection': 'closest_premium', 'value':200}, underlying_atm,
    #                    roll_strike=2, new_strike_selection_criteria=3, stop_loss=['points', 25], trailing_sl=5, no_of_reentry=6, simple_momentum=7, range_breakout=8)
    # # leg4 = LegBuilder(xts, 'soc', 'interactive_soc', 'leg2', strategy1,publisher,  3, 'sell', 'CE', 'current', {'strike_selection': 'strike', 'value': 'OTM3'}, underlying_atm,
    # #                    roll_strike=2, new_strike_selection_criteria=3, stop_loss=['points', 15], trailing_sl=5, no_of_reentry=6, simple_momentum=7, range_breakout=8)
    # leg5 = LegBuilder(xts, 'soc', 'interactive_soc', 'leg2', strategy1,publisher,  3, 'buy', 'CE', 'current', {'strike_selection': 'strike', 'value': 'ITM1'}, underlying_atm,
    #                    roll_strike=2, new_strike_selection_criteria=3, stop_loss=['points', 15], trailing_sl=5, no_of_reentry=6, simple_momentum=7, range_breakout=8)
    # leg6 = LegBuilder(xts, 'soc', 'interactive_soc', 'leg2', strategy1,publisher,  3, 'sell', 'CE', 'current', {'strike_selection': 'strategy1_width', 'value': {'atm_strike':'-', 'input': 0.5}}, underlying_atm,
    #                    roll_strike=2, new_strike_selection_criteria=3, stop_loss=['points', 15], trailing_sl=5, no_of_reentry=6, simple_momentum=7, range_breakout=8)
    legs = [leg1]
    await asyncio.gather(
        process_leg(leg1),
        # process_leg(leg1),
        # process_leg(leg2),
        # strategy1.calculate_overall_pnl(legs)

        # process_leg(leg4),
        # process_leg(leg5),
        # process_leg(leg6),

    )

asyncio.run(main())




'''
steps to do if the SL is triggered, trade_position = False
increase re-entry count
if re-entry count is less than re-entry provided

'''