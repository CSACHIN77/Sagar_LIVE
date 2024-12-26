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
import warnings
warnings.filterwarnings("ignore")

port = "localhost:5001"
interactive_port = '8050'
xts = XTS()
publisher = Publisher()
create_tradebook_table()

soc = MDSocket_io(port=port, publisher=publisher) 
interactive_soc = OrderSocket_io(interactive_port, publisher)

soc.connect()
interactive_soc.connect()

interactive_el = interactive_soc.get_emitter()
interactive_el.on('trade', interactive_soc.on_trade)
interactive_el.on('order', interactive_soc.on_order)

async def process_leg(leg):
    leg.get_expiry_df()
    leg.selection_criteria()
    await leg.leg_place_order()

    while not leg.strategy.stop_event.is_set():
        await leg.calculate_mtm()
        await asyncio.sleep(1)  

    print(f"{leg.name} stopping as strategy finished.")
    return

async def run_strategy(xts, strategy_details, leg_attributes):
    strategy = Strategy(xts, **strategy_details)

    while soc.current_data_time is None:
        print("waiting for current_data_time to set.")
        await asyncio.sleep(1)

    time_now = datetime.fromtimestamp(soc.current_data_time) - timedelta(days=1, hours=5, minutes=30)
    print(f"time is {datetime.now()}")
    print(time_now.time(), strategy.entry_time.time())
    if time_now.time() < strategy.entry_time.time():
        sleep_duration = (strategy.entry_time - time_now).total_seconds()
        print(f"sleeping for {sleep_duration} seconds until entry time")
        await asyncio.sleep(sleep_duration)

    # underlying_ltp =  strategy.get_underlying_ltp()
    underlying_ltp =  strategy.get_underlying_ltp()
    print(f"underlying ltp is {underlying_ltp}")

    if not underlying_ltp:
        retry_counter = 0
        while retry_counter <= 3:
            print(f"retrying underlying_ltp retrieval for {retry_counter + 1} times")
            underlying_ltp = strategy.get_underlying_ltp()
            if underlying_ltp:
                break
            retry_counter += 1
            await asyncio.sleep(2)
        else:
            print('unable to find underlying ltp, exiting !!')
            return

    print(f'{strategy.index} selected {strategy.underlying} and the last traded price is {underlying_ltp}')
    base = 100 if strategy.index == 'NIFTY BANK' else 50
    underlying_atm = get_atm(underlying_ltp, base)

    legs = []
    for leg_name, leg_details in leg_attributes.items():
        leg_obj = LegBuilder(
            xts, soc, interactive_soc, f"{strategy.name}{leg_name}", strategy, publisher,
            total_lots=leg_details["total_lots"], position=leg_details["position"],
            option_type=leg_details["option_type"], expiry=leg_details["expiry"],
            strike_selection_criteria=leg_details["strike_selection_criteria"],
            strike=underlying_atm, roll_strike=leg_details["roll_strike"],
            new_strike_selection_criteria=leg_details["new_strike_selection_criteria"],
            stop_loss=leg_details["stop_loss"], trailing_sl=leg_details["trailing_sl"],
            no_of_reentry=leg_details["no_of_reentry"], 
            simple_momentum=leg_details["simple_momentum"],
            range_breakout=leg_details["range_breakout"]
        )
        legs.append(leg_obj)

    leg_tasks = [asyncio.create_task(process_leg(leg)) for leg in legs]
    pnl_task = asyncio.create_task(strategy.calculate_overall_pnl(legs))
    done, pending = await asyncio.wait([pnl_task], return_when=asyncio.ALL_COMPLETED)
    strategy.stop_event.set()

    await asyncio.gather(*leg_tasks, return_exceptions=True)

    print(f"Strategy {strategy.name} finished gracefully.")


async def main():
    stg_folder = os.path.join("strategy")
    if os.path.exists(stg_folder):
        stg_files = [file for file in os.listdir(stg_folder) if file.startswith("stg") and file.endswith(".json") and not "__" in file]
        print(stg_files)

        all_strategy_tasks = []
        for stg_file in stg_files:
            stg_path = os.path.join(stg_folder, stg_file)
            with open(stg_path, 'r') as file:
                stg = json.load(file)

            if stg:
                strategy_details = {
                    'name': stg["name"],
                    'index': stg["index"],
                    'underlying': stg["underlying"],
                    'strategy_type': stg["strategy_type"],
                    'entry_time': stg["entry_time"],
                    'last_entry_time': stg["last_entry_time"],
                    'exit_time': stg["exit_time"],
                    'square_off': stg["square_off"],
                    'overall_sl': stg["overall_sl"],
                    'overall_target': stg["overall_target"],
                    'trailing_for_strategy': stg["trailing_for_strategy"],
                    'implied_futures_expiry': stg["implied_futures_expiry"],
                    'socket': soc
                }

                leg_attributes = {key: value for key, value in stg.items() if key.startswith("leg") and key[3:].isdigit()}

                task = asyncio.create_task(run_strategy(xts, strategy_details, leg_attributes))
                all_strategy_tasks.append(task)

        await asyncio.gather(*all_strategy_tasks, return_exceptions=True)

asyncio.run(main())
