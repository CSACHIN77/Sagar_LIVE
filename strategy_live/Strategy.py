import json
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
from utils import get_atm, filter_dataframe, report_generator
import asyncio
import sys
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
        self.base = 100 if self.index == 'NIFTY BANK' else 50
        self.total_pnl = 0
        self.trail_flag = False
        # self.legs = legs
    

    def get_underlying_ltp(self) -> float:
            underlying_ltp = None
            try:
                if self.underlying.lower() == 'spot':
                    print('Selected underlying is spot')
                    print(self.index_ex_id)
                    data = self.xts.get_quotes([self.index_ex_id])
                    if data['type'] == 'success':
                        quotes = data['result']['listQuotes']
                        quotes = json.loads(quotes[0])
                        underlying_ltp = quotes['LastTradedPrice']
                        print(f'underlying ltp is {underlying_ltp}')
                else:
                    fut_df = self.df[(self.df['name'].str.upper() == self.index) & (self.df['series'] == 'FUTIDX')]
                    fut_df = fut_df.sort_values('expiry')
                    fut_df.reset_index(inplace=True, drop=True)
                    current_fut_name, current_fut_instrument_token = fut_df.loc[0, 'tradingsymbol'], int(fut_df.loc[0, 'instrument_token'])
                    print(current_fut_name)
                    data = self.xts.get_quotes([{'exchangeInstrumentID': current_fut_instrument_token, 'exchangeSegment': 2}])
                    if data['type'] == 'success':
                        quotes = data['result']['listQuotes'][0]
                        # print(json.loads(quotes)['LastTradedPrice'])
                        underlying_ltp = json.loads(quotes)['LastTradedPrice']
                        print(f' futures price is {underlying_ltp}')
                        if self.underlying.lower() == 'implied_futures':
                            expiry = self.implied_futures_expiry
                            opt_df, monthly_expiry_list = filter_dataframe(self.df, [self.index])
                            expiry_list = list(set(opt_df['expiry']))
                            expiry_list.sort()
                            if (self.implied_futures_expiry == 2) & (expiry_list[0]== monthly_expiry_list[0]):
                                expiry_day = monthly_expiry_list[1]
                            elif((self.implied_futures_expiry == 2)):
                                expiry_day = monthly_expiry_list[0]
                            else:
                                expiry_day = expiry_list[self.implied_futures_expiry]
                            print(f'expiry selected is {"current" if self.implied_futures_expiry == 0 else "next" if self.implied_futures_expiry == 1 else "monthly"} and expiry day for implied futures is {expiry_day}')
                            derived_atm = get_atm(underlying_ltp, self.base)
                            # print('selected underlying is {implied_futures}')
                            options_df = self.df[(self.df['series'] == 'OPTIDX') & (self.df['name'].str.upper() == self.index)]
                            options_df['strike'] = options_df['strike'].astype(int)
                            temp = options_df[(options_df['strike'] == derived_atm) & (options_df['expiry'] == expiry_day)]
                            ce_atm = int(temp[temp['option_type'] == 3].instrument_token.values[0])
                            pe_atm = int(temp[temp['option_type'] == 4].instrument_token.values[0])
                            # print(ce_atm, pe_atm)
                            # print(derived_atm)
                            ce_data = self.xts.get_quotes([{'exchangeInstrumentID': ce_atm, 'exchangeSegment': 2}])
                            pe_data = self.xts.get_quotes([{'exchangeInstrumentID': pe_atm, 'exchangeSegment': 2}])
                            if ce_data['type'] == 'success':
                                quotes = ce_data['result']['listQuotes'][0]
                                ce_price = float(json.loads(quotes)['LastTradedPrice'])
                                underlying_ltp = derived_atm + ce_price
                                print(f'ce_price is {ce_price}')
                                
                            if pe_data['type'] == 'success':
                                quotes = pe_data['result']['listQuotes'][0]
                                pe_price = float(json.loads(quotes)['LastTradedPrice'])
                                underlying_ltp = underlying_ltp -  pe_price
                                print(f'pe_price is {pe_price}')
                            print(f'implied futures is {underlying_ltp}')
                print(underlying_ltp)
                return underlying_ltp
                # return None
            except Exception as e:
                print(f'error occured in get_underlying_ltp block {e}')
                
                return None




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
                print('squaring off everything, as SL got hit')
                # legs[0].soc.disconnect()
                break
            if self.total_pnl >self.overall_target:
                print(f'total_pnl {self.total_pnl} is above overall target {self.overall_target}')
                for leg in legs:
                    self.xts.complete_square_off(leg)
                print('squaring off everything, target acheived')
                # legs[0].soc.disconnect()

                break
            time_now = datetime.now()
            await asyncio.sleep(3)
        print('squaring off because time is over')
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
