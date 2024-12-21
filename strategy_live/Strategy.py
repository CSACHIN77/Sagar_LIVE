import json
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
from utils import get_atm, filter_dataframe, report_generator, get_base, Logger
from business_logic.StrategyUtils import *
import asyncio
import sys
import os

sys.path.append(os.path.abspath('../../Sagar_common'))

try:
    from common_function import fetch_parameter
except ImportError as e:
    print(f"Error importing 'fetch_parameter': {e}")
environment = "dev"
stike_differences = fetch_parameter(environment, "strikeDifference")

class Strategy:
    def __init__(self, xts, name: str, index: str, underlying: str, strategy_type: str, entry_time: datetime, 
                 last_entry_time: datetime, exit_time: datetime, square_off: float, overall_sl: float, 
                 overall_target: float, trailing_for_strategy: float,  implied_futures_expiry: str  = 'current') -> None:
        print('strategy ')
        self.xts = xts
        self.name = name
        self.index = index
        self.underlying = underlying
        self.implied_futures_expiry = 0 if implied_futures_expiry == 'current' else (1 if implied_futures_expiry=='next_expiry' else 2 if implied_futures_expiry == 'monthly' else None)
        print('working till here')
        self.strategy_type = strategy_type
        self.entry_time = self.convert_to_datetime(entry_time)
        self.last_entry_time = self.convert_to_datetime(last_entry_time)
        self.exit_time = self.convert_to_datetime(exit_time)
        self.square_off = square_off
        self.overall_sl = overall_sl
        self.overall_target = overall_target
        self.trailing_for_strategy = trailing_for_strategy
        self.legs: List[Any] = []
        self.trail_count = 0
        self.index_ex_id: Dict[str, int] = self.get_index_details(1)
        print('still working')
        print('calculating master db')
        self.df = self.xts.get_master_db()
        print('calculation done')
        self.base = get_base(self.index, stike_differences) #100 if self.index == 'NIFTY BANK' else 50
        self.total_pnl = 0
        self.trail_flag = False
        self.logger = Logger(f'{self.name}_log.txt')
        # self.legs = legs
    
    def get_underlying(self):
        underlying_ltp = None
        underlying_ltp = get_underlying_ltp(self)
        return underlying_ltp

    




    def get_index_details(self, exchange_segment: int) -> Dict[str, int]:
        indexList = self.xts.get_index_list(exchange_segment)['indexList']
        idx_list = {}
        for idx in indexList:
            idx_name = idx.split('_')[0]
            ex_id = int(idx.split('_')[1])
            idx_list[idx_name] = int(ex_id)
        return {'exchangeSegment': 1, 'exchangeInstrumentID': idx_list[self.index]}

    def add_leg(self, leg: Any) -> None:
        self.legs.append(leg)

    async def calculate_overall_pnl(self,legs) -> float:
        print('strategy pnl getting called')
        time_now = datetime.now()
        # trailing_for_strategy={"type": "lock", "profit": 10, "profit_lock": 5}
        while self.exit_time > time_now: 
            self.total_pnl = sum(leg.pnl for leg in legs)
            # print(f'total_pnl of the strategy {self.name} is {self.total_pnl}')
            if (self.trailing_for_strategy) and (not self.trail_flag):
                # print('entering trail logic')
                if self.trailing_for_strategy["type"]=="lock_and_trail":
                    if self.trailing_for_strategy["profit"] <= self.total_pnl:
                        # self.trail_count = self.trail_count + 1
                        if self.trail_count == 0:
                            self.overall_sl= 0 - (self.trailing_for_strategy["lock_value"])
                            self.trail_count = self.trail_count + 1
                            self.trailing_for_strategy["profit"] = self.trailing_for_strategy["profit"] + self.trailing_for_strategy["lock_value"]
                            # print(self.overall_sl, self.trail_count)
                            print(f'trailing stop loss updated to {abs(self.overall_sl)} updated')
                            print(f'trailing PROFIT  updated to {self.trailing_for_strategy["profit"]} updated')
                        else:
                            self.overall_sl = self.overall_sl - self.trailing_for_strategy["trail_value"]
                            self.trail_count = self.trail_count + 1
                            print(self.overall_sl, self.trail_count)
                            print(f'trailing stop loss updated to {abs(self.overall_sl)} updated next trail level is {self.trailing_for_strategy["profit"]}')
                        self.trailing_for_strategy["profit"] = self.trailing_for_strategy["profit"] + self.trailing_for_strategy["lock_value"]
                        print(f'trailing stop loss updated to {abs(self.overall_sl)} updated next trail level is {self.trailing_for_strategy["profit"]}')
            
                if self.trailing_for_strategy["type"]=="lock":
                    if self.trailing_for_strategy["profit"] <= self.total_pnl:
                        self.trail_count = self.trail_count + 1
                        self.overall_sl= 0 - (self.trailing_for_strategy["lock_value"])
                        # self.trailing_for_strategy["profit"] = (self.trail_count+1)*self.trailing_for_strategy["profit"]
                        self.trail_flag = True
                        print(f'trailing stop loss updated to {abs(self.overall_sl)} ')
                        # self.trailing_for_strategy["profit"] = (self.trail_count+1)*self.trailing_for_strategy["profit"]
            
            if self.total_pnl <( 0 - self.overall_sl):
                # print(f'total_pnl {self.total_pnl} is below overall stoploss {self.overall_sl}')
                for leg in legs:
                    self.xts.complete_square_off(leg)

                self.logger.log(f'squaring off everything, as SL got hit')
                print('squaring off everything, as SL got hit')
                # legs[0].soc.disconnect()
                break
            if self.total_pnl >self.overall_target:
                print(f'total_pnl {self.total_pnl} is above overall target {self.overall_target}')
                for leg in legs:
                    self.xts.complete_square_off(leg)
                print('squaring off everything, target acheived')
                self.logger.log(f'squaring off everything, target acheived')
                # legs[0].soc.disconnect()

                break
            time_now = datetime.now()
            await asyncio.sleep(3)
        print('squaring off because time is over')
        self.logger.log(f'squaring off because time is over')
        
        for leg in legs:
                    self.xts.complete_square_off(leg)
        asyncio.sleep(5)
        report_generator(self)
        return
        # sys.exit()
    def convert_to_datetime(self, timestamp):
        today_date = datetime.now().date()
        formatted_time = f"{today_date} {timestamp}:00"
        return datetime.strptime(formatted_time, '%Y-%m-%d %H:%M:%S')
