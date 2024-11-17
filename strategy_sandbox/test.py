from sandboxBroker import XTS
import pandas as pd
from sandboxInteractiveSocket import OrderSocket_io
import asyncio
from datetime import datetime
from Strategy import Strategy
from LegBuilder import LegBuilder
from datetime import datetime
from utils import get_atm, create_tradebook_table, broker_login
from Publisher import Publisher
import time
create_tradebook_table()
import warnings
import asyncio
warnings.filterwarnings("ignore")
from sandboxMarketSocket import MDSocket_io
port = "localhost:5001"  
publisher = Publisher()
xts = XTS()
socket_client = MDSocket_io(port=port, publisher=publisher)

socket_client.connect()
socket_client.subscribe_symbols([{'exchangeSegment':2, 'exchangeInstrumentID': 26000}])

# print(xts.get_quotes([{'exchangeSegment': 2, 'exchangeInstrumentID': 26000}, {'exchangeSegment': 2, 'exchangeInstrumentID': 26001}], socket=socket_client))

# time.sleep(30)
# socket_client.subscribe_symbols([{'exchangeSegment':2, 'exchangeInstrumentID': 36846}, {'exchangeSegment':2, 'exchangeInstrumentID': 43941}])

# print(socket_client.subscribed_symbols)
# print(f"unsubscribing")
# socket_client.unsubscribe_symbols([{'exchangeSegment':2, 'exchangeInstrumentID': 36846}])
# time.sleep(5)
# time.sleep(5)
# print(type(socket_client.current_data_time))
# xts.get_orders()
# order_params = {
#   "OrderType": "Limit",
#   "OrderSide": "BUY",
#   "exchangeInstrumentID": 36846,
#   "OrderPrice": 294,
#   "OrderQuantity": 1,
#   "TimeInForce": "DAY"
# }




# xts.place_order(order_params)
# xts.cancel_orders("NSECM", 36846)
# print(xts.get_tradebook())
# publisher = Publisher()  # Replace with your actual publisher
# interactive_soc = InteractiveSocket(port=8050, publisher=publisher)
# # socket.connect()





# interactive_soc.connect()
# # interactive_soc.on_trade = on_trade
# # interactive_el = socket.get_emitter()
# # interactive_el.on('trade', interactive_soc.on_trade)
# # interactive_el.on('order', interactive_soc.on_order)

# # xts.get_master({'exchangeSegmentList': ['NSEFO']})

# async def process_leg(leg):
#     leg.get_expiry_df()
#     leg.selection_criteria()
#     await leg.leg_place_order()
#     await leg.calculate_mtm()
  
# async def run_strategy(xts, strategy_details):
#     strategy = Strategy(xts, **strategy_details)
#     time_now = datetime.now()
#     print(f"time is {datetime.now()}")
#     print(time_now, strategy.entry_time)
#     if time_now < strategy.entry_time:
#         print(f'sleeping for {(strategy.entry_time - time_now).total_seconds()}')
#         await asyncio.sleep((strategy.entry_time - time_now).total_seconds())

#     underlying_ltp = strategy.get_underlying_ltp()
#     if not underlying_ltp:
#         retry_counter = 0
#         while retry_counter <=3:
#             print(f"retrying underlying_ltp retrieval for {retry_counter + 1} times")
#             underlying_ltp = strategy.get_underlying_ltp()
#             if underlying_ltp :
#                 return underlying_ltp
#             retry_counter += 1
#             await asyncio.sleep(2)
#         underlying_ltp = None
        
#     if underlying_ltp:
#         print(f'{strategy.index} selected {strategy.underlying} and the last traded price is {underlying_ltp}')
#         base = 100 if strategy.index == 'NIFTY 50' else 50
#         underlying_atm = get_atm(underlying_ltp, base)

#         leg1 = LegBuilder(xts, 'soc', interactive_soc, f"{strategy.name}leg1", strategy, publisher, 2, 'sell', 'CE', 'current',
#                         {'strike_selection': 'closest_premium', 'value': 200}, underlying_atm, roll_strike=False,
#                         new_strike_selection_criteria=3, stop_loss=['points', 15], trailing_sl={"priceMove": 20, "sl_adjustment": 4}, no_of_reentry=2, 
#                         simple_momentum=False, range_breakout=False)
#         leg2 = LegBuilder(xts, 'soc', interactive_soc, f"{strategy.name}leg2", strategy, publisher, 2, 'sell', 'PE', 'current',
#                         {'strike_selection': 'closest_premium', 'value': 200}, underlying_atm, roll_strike=False,
#                         new_strike_selection_criteria=3, stop_loss=['points', 15], trailing_sl={"priceMove": 20, "sl_adjustment": 4}, no_of_reentry=2, 
#                         simple_momentum=False, range_breakout=False)
#         # leg1 = LegBuilder(xts, 'soc', interactive_soc, f"{strategy.name}leg1", strategy, publisher, 2, 'sell', 'CE', 'current',
#         #                 {'strike_selection': 'closest_premium', 'value': 150}, underlying_atm, roll_strike=False,
#         #                 new_strike_selection_criteria=3, stop_loss=['points', 10], trailing_sl={"priceMove": 10, "sl_adjustment": 4}, no_of_reentry=2, 
#         #                 simple_momentum={'value_type':'points', 'value':15, 'direction': 'increment' }, range_breakout=False)
#         # leg2 = LegBuilder(xts, 'soc', interactive_soc, f"{strategy.name}leg2", strategy, publisher, 2, 'sell', 'PE', 'current',
#         #                 {'strike_selection': 'closest_premium', 'value': 150}, underlying_atm, roll_strike=False,
#         #                 new_strike_selection_criteria=3, stop_loss=['points', 10], trailing_sl={"priceMove": 10, "sl_adjustment": 4}, no_of_reentry=2, 
#         #                 simple_momentum={'value_type':'points', 'value':15, 'direction': 'increment' }, range_breakout=False)
#         # # leg3 = LegBuilder(xts, 'soc', 'interactive_soc', f"{strategy.name}leg3", strategy, publisher, 2, 'sell', 'PE', 'current',
#         # #                   {'strike_selection': 'strike', 'value': "ATM"}, underlying_atm, roll_strike=2,
#         # #                   new_strike_selection_criteria=3, stop_loss=['points', 50], trailing_sl={"priceMove": 4, "sl_adjustment": 4}, no_of_reentry=2, 
#         # #                   simple_momentum=False, range_breakout=False)
#         legs = [leg1, leg2]
#         # legs = [leg1]

#         await asyncio.gather(
#             process_leg(leg1),
#             process_leg(leg2),
#             strategy.calculate_overall_pnl(legs)
#         )
#     else:
#         print('unable to find underlying ltp, exiting !!')
#         return
        

# async def main():

#     strategy_details_1 = {
#         'name': 'strategy1', 'index': 'NIFTY BANK', 'underlying': 'spot', 'strategy_type': 'intraday',
#         'entry_time': "10:17", 'last_entry_time': "11:40", 'exit_time': "11:45", 'square_off': "partial",
#         'overall_sl': 3000, 'overall_target': 4000,                   
#         'trailing_for_strategy': {"type": "lock_and_trail", "profit": 2000, "lock_value": 1300, "trail_level":  200, "trail_value": 100}, 
#         'implied_futures_expiry': 'current'
#     }
#     # strategy_details_2 = {
#     #     'name': 'strategy2', 'index': 'NIFTY 50', 'underlying': 'spot', 'strategy_type': 'intraday',
#     #     'entry_time': "13:48", 'last_entry_time': "14:15", 'exit_time': "14:20", 'square_off': "full",
#     #     'overall_sl': 4000, 'overall_target': 4000, 
#     #     'trailing_for_strategy': {"type": "lock_and_trail", "profit": 2400, "lock_value": 1700, "trail_level":400, "trail_value": 100},
#     #     'implied_futures_expiry': 'current'
#     # }
    
#     await asyncio.gather(
#         run_strategy(xts, strategy_details_1),
#         # run_strategy(xts, strategy_details_2)
#     )

# asyncio.run(main())


