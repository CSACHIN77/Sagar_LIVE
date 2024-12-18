import asyncio
import os, json
from datetime import datetime, timedelta
from Strategy import Strategy
from LegBuilder import LegBuilder
from sandboxMarketSocket import MDSocket_io
from sandboxInteractiveSocket import OrderSocket_io
from datetime import datetime
from sandboxBroker import XTS
from creds import creds
from utils import get_atm, create_tradebook_table, broker_login
from Publisher import Publisher
import time
publisher = Publisher()
create_tradebook_table()
import warnings
import asyncio
warnings.filterwarnings("ignore")
port = "localhost:5001" 
interactive_port = '8050'
xts = XTS()  

# market_token, interactive_token, userid = broker_login(xts, creds)
# xts.market_token, xts.interactive_token, xts.userid  = market_token, interactive_token, userid
# xts.update_master_db()
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

# xts.get_master({'exchangeSegmentList': ['NSEFO']})

async def process_leg(leg):
    leg.get_expiry_df()
    leg.selection_criteria()
    await leg.leg_place_order()
    await leg.calculate_mtm()
  
async def run_strategy(xts, strategy_details, leg_attributes):
    strategy = Strategy(xts, **strategy_details)
    while soc.current_data_time is None:
        print("waiting for current_data_time to set.")
        await asyncio.sleep(1)

    time_now = datetime.fromtimestamp(soc.current_data_time) - timedelta(days= 1, hours=5, minutes=30) #datetime.now()
    print(f"time is {datetime.now()}")
    print(time_now.time(), strategy.entry_time.time())
    if time_now.time() < strategy.entry_time.time():
        print(f'sleeping for {(strategy.entry_time.time() - time_now.time()).total_seconds()}')
        await asyncio.sleep((strategy.entry_time - time_now).total_seconds())

    underlying_ltp = strategy.get_underlying_ltp()
    
    print(f"underlying ltp is {underlying_ltp}")
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
        base = 100 if strategy.index == 'NIFTY BANK' else 50
        underlying_atm = get_atm(underlying_ltp, base)

        
        legs = []

        print(leg_attributes)
        for leg_name, leg_details in leg_attributes.items():
            leg1 = LegBuilder(xts, soc, interactive_soc, f"{strategy.name}{leg_name}", strategy, publisher, total_lots=leg_details["total_lots"], 
                             position=leg_details["position"],option_type=leg_details["option_type"], expiry=leg_details["expiry"],
                             strike_selection_criteria=leg_details["strike_selection_criteria"], strike=underlying_atm, roll_strike=leg_details["roll_strike"],
                             new_strike_selection_criteria=leg_details["new_strike_selection_criteria"], stop_loss=leg_details["stop_loss"],
                             trailing_sl=leg_details["trailing_sl"], no_of_reentry=leg_details["no_of_reentry"], 
                             simple_momentum=leg_details["simple_momentum"], range_breakout=leg_details["range_breakout"])
            
            legs.append(leg1)
        
        #leg2 = LegBuilder(xts, soc, interactive_soc, f"{strategy.name}leg2", strategy, publisher, 2, 'buy', 'PE', 'current',
        #                {'strike_selection': 'strike', 'value': 'OTM3'}, underlying_atm, roll_strike=False,
        #                new_strike_selection_criteria=3, stop_loss=['points', 20], trailing_sl=False, no_of_reentry=2, 
        #                simple_momentum=False, range_breakout=False)
        # leg2 = LegBuilder(xts, soc, interactive_soc, f"{strategy.name}leg2", strategy, publisher, 2, 'sell', 'PE', 'current',
        #                 {'strike_selection': 'closest_premium', 'value': 400}, underlying_atm, roll_strike=False,
        #                 new_strike_selection_criteria=3, stop_loss=['points', 15], trailing_sl={"priceMove": 20, "sl_adjustment": 4}, no_of_reentry=2, 
        #                 simple_momentum=False, range_breakout=False)
        
        # legs = [leg1, leg2]
        # legs = [leg1]
        print(legs)
        legs_coros = [process_leg(leg) for leg in legs]
        
        await asyncio.gather(
            *legs_coros,
            #process_leg(leg1),
            #process_leg(leg2),
            strategy.calculate_overall_pnl(legs)
        )
    else:
        print('unable to find underlying ltp, exiting !!')
        return
        


async def main():

    stg_files = None
    # if strategy folder exists
    stg_folder = os.path.join("strategy")
    if os.path.exists(stg_folder):
        # read all the strategy file starting with stg
        stg_files = [file for file in os.listdir(stg_folder) if file.startswith("stg") and file.endswith(".json") and not "__" in file]
        print(stg_files)
        i = 0
        all_strategy = []
        while(i < len(stg_files)):
            stg_path = os.path.join(stg_folder,stg_files[i])
            i=i+1

            stg = None
            with open(stg_path, 'r') as file:
                stg = json.load(file)
                
            if stg:
                strategy_details = {
                    'name': stg["name"], 'index': stg["index"], 'underlying': stg["underlying"], 'strategy_type': stg["strategy_type"],
                    'entry_time': stg["entry_time"], 'last_entry_time': stg["last_entry_time"], 'exit_time': stg["exit_time"], 'square_off': stg["square_off"],
                    'overall_sl': stg["overall_sl"], 'overall_target': stg["overall_target"],                   
                    'trailing_for_strategy': stg["trailing_for_strategy"], 
                    'implied_futures_expiry': stg["implied_futures_expiry"], 
                    'socket': soc
                }

                # Extract leg attributes
                leg_attributes = {key: value for key, value in stg.items() if key.startswith("leg") and key[3:].isdigit()}
                
                all_strategy.append({"stg": strategy_details, "legs": leg_attributes})

                # rename file with "__" at the end to identify it's running
                #os.rename(stg_path, stg_path+"__")

        stg_coros = [run_strategy(xts, item["stg"], item["legs"]) for item in all_strategy]
        print(stg_coros)
        await asyncio.gather(
            *stg_coros
            # run_strategy(xts, strategy_details, leg_attributes)
            )
            

asyncio.run(main())
