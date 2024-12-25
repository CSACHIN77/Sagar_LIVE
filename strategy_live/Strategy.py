import json
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
from utils import get_atm, filter_dataframe, report_generator, get_base, get_path
from Logger.MyLogger import Logger
from business_logic.StrategyUtils import *
import asyncio
import sys
import os
from business_logic.StrategyUtils import *

sys.path.append(get_path("Sagar_common"))

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
        self.index_ex_id: Dict[str, int] = get_index_details(self,1)
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

    async def _calculate_overall_pnl(self, legs):
        print("calculating overall pnl")
        await calculate_overall_pnl(self, legs)

    def convert_to_datetime(self, timestamp):
        today_date = datetime.now().date()
        formatted_time = f"{today_date} {timestamp}:00"
        return datetime.strptime(formatted_time, '%Y-%m-%d %H:%M:%S')
