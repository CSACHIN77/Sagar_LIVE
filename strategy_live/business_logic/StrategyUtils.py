import json
from datetime import datetime
from utils import filter_dataframe, get_atm, report_generator
import asyncio

def get_underlying_ltp(strategy_instance) -> float:
            underlying_ltp = None
            try:
                if strategy_instance.underlying.lower() == 'spot':
                    print('Selected underlying is spot')
                    print(strategy_instance.index_ex_id)
                    print(f"strategy instrument is in this format {[strategy_instance.index_ex_id]}")
                    data = strategy_instance.xts.get_quotes([strategy_instance.index_ex_id])
                    print(f"data in get_underlying_ltp is {data}")
                    if data['type'] == 'success':
                        quotes = data['result']['listQuotes']
                        quotes = json.loads(quotes[0])
                        underlying_ltp = quotes['LastTradedPrice']
                        print(f'underlying ltp is {underlying_ltp}')
                else:
                    fut_df = strategy_instance.df[(strategy_instance.df['name'].str.upper() == strategy_instance.index) & (strategy_instance.df['series'] == 'FUTIDX')]
                    fut_df = fut_df.sort_values('expiry')
                    fut_df.reset_index(inplace=True, drop=True)
                    current_fut_name, current_fut_instrument_token = fut_df.loc[0, 'tradingsymbol'], int(fut_df.loc[0, 'instrument_token'])
                    print(current_fut_name)
                    data = strategy_instance.xts.get_quotes([{'exchangeInstrumentID': current_fut_instrument_token, 'exchangeSegment': 2}])
                    if data['type'] == 'success':
                        quotes = data['result']['listQuotes'][0]
                        # print(json.loads(quotes)['LastTradedPrice'])
                        underlying_ltp = json.loads(quotes)['LastTradedPrice']
                        print(f' futures price is {underlying_ltp}')
                        if strategy_instance.underlying.lower() == 'implied_futures':
                            expiry = strategy_instance.implied_futures_expiry
                            opt_df, monthly_expiry_list = filter_dataframe(strategy_instance.df, [strategy_instance.index])
                            expiry_list = list(set(opt_df['expiry']))
                            expiry_list.sort()
                            if (strategy_instance.implied_futures_expiry == 2) & (expiry_list[0]== monthly_expiry_list[0]):
                                expiry_day = monthly_expiry_list[1]
                            elif((strategy_instance.implied_futures_expiry == 2)):
                                expiry_day = monthly_expiry_list[0]
                            else:
                                expiry_day = expiry_list[strategy_instance.implied_futures_expiry]
                            print(f'expiry selected is {"current" if strategy_instance.implied_futures_expiry == 0 else "next" if strategy_instance.implied_futures_expiry == 1 else "monthly"} and expiry day for implied futures is {expiry_day}')
                            derived_atm = get_atm(underlying_ltp, strategy_instance.base)
                            # print('selected underlying is {implied_futures}')
                            options_df = strategy_instance.df[(strategy_instance.df['series'] == 'OPTIDX') & (strategy_instance.df['name'].str.upper() == strategy_instance.index)]
                            options_df['strike'] = options_df['strike'].astype(int)
                            temp = options_df[(options_df['strike'] == derived_atm) & (options_df['expiry'] == expiry_day)]
                            ce_atm = int(temp[temp['option_type'] == 3].instrument_token.values[0])
                            pe_atm = int(temp[temp['option_type'] == 4].instrument_token.values[0])
                            ce_data = strategy_instance.xts.get_quotes([{'exchangeInstrumentID': ce_atm, 'exchangeSegment': 2}])
                            pe_data = strategy_instance.xts.get_quotes([{'exchangeInstrumentID': pe_atm, 'exchangeSegment': 2}])
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
                strategy_instance.logger.log(f"Underlying LTP: {underlying_ltp}, Underlying: {strategy_instance.underlying}")
                return underlying_ltp
                # return None
            except Exception as e:
                print(f'error occured in get_underlying_ltp block {e}')
                
                return None
            

def get_index_details(strategy_instance, exchange_segment: int):
        indexList = strategy_instance.xts.get_index_list(exchange_segment)['indexList']
        idx_list = {}
        for idx in indexList:
            idx_name = idx.split('_')[0]
            ex_id = int(idx.split('_')[1])
            idx_list[idx_name] = int(ex_id)
        return {'exchangeSegment': 1, 'exchangeInstrumentID': idx_list[strategy_instance.index]}


async def calculate_overall_pnl(strategy_instance,legs) -> float:
        print('strategy pnl getting called')
        time_now = datetime.now()
        # trailing_for_strategy={"type": "lock", "profit": 10, "profit_lock": 5}
        while strategy_instance.exit_time > time_now: 
            strategy_instance.total_pnl = sum(leg.pnl for leg in legs)
            print(f'total_pnl of the strategy {strategy_instance.name} is {strategy_instance.total_pnl}')
            if (strategy_instance.trailing_for_strategy) and (not strategy_instance.trail_flag):
                # print('entering trail logic')
                if strategy_instance.trailing_for_strategy["type"]=="lock_and_trail":
                    if strategy_instance.trailing_for_strategy["profit"] <= strategy_instance.total_pnl:
                        # strategy_instance.trail_count = strategy_instance.trail_count + 1
                        if strategy_instance.trail_count == 0:
                            strategy_instance.overall_sl= 0 - (strategy_instance.trailing_for_strategy["lock_value"])
                            strategy_instance.trail_count = strategy_instance.trail_count + 1
                            strategy_instance.trailing_for_strategy["profit"] = strategy_instance.trailing_for_strategy["profit"] + strategy_instance.trailing_for_strategy["lock_value"]
                            # print(strategy_instance.overall_sl, strategy_instance.trail_count)
                            print(f'trailing stop loss updated to {abs(strategy_instance.overall_sl)} updated')
                            print(f'trailing PROFIT  updated to {strategy_instance.trailing_for_strategy["profit"]} updated')
                        else:
                            strategy_instance.overall_sl = strategy_instance.overall_sl - strategy_instance.trailing_for_strategy["trail_value"]
                            strategy_instance.trail_count = strategy_instance.trail_count + 1
                            print(strategy_instance.overall_sl, strategy_instance.trail_count)
                            print(f'trailing stop loss updated to {abs(strategy_instance.overall_sl)} updated next trail level is {strategy_instance.trailing_for_strategy["profit"]}')
                        strategy_instance.trailing_for_strategy["profit"] = strategy_instance.trailing_for_strategy["profit"] + strategy_instance.trailing_for_strategy["lock_value"]
                        print(f'trailing stop loss updated to {abs(strategy_instance.overall_sl)} updated next trail level is {strategy_instance.trailing_for_strategy["profit"]}')
            
                if strategy_instance.trailing_for_strategy["type"]=="lock":
                    if strategy_instance.trailing_for_strategy["profit"] <= strategy_instance.total_pnl:
                        strategy_instance.trail_count = strategy_instance.trail_count + 1
                        strategy_instance.overall_sl= 0 - (strategy_instance.trailing_for_strategy["lock_value"])
                        # strategy_instance.trailing_for_strategy["profit"] = (strategy_instance.trail_count+1)*strategy_instance.trailing_for_strategy["profit"]
                        strategy_instance.trail_flag = True
                        print(f'trailing stop loss updated to {abs(strategy_instance.overall_sl)} ')
                        # strategy_instance.trailing_for_strategy["profit"] = (strategy_instance.trail_count+1)*strategy_instance.trailing_for_strategy["profit"]
            
            if strategy_instance.total_pnl <( 0 - strategy_instance.overall_sl):
                # print(f'total_pnl {strategy_instance.total_pnl} is below overall stoploss {strategy_instance.overall_sl}')
                for leg in legs:
                    strategy_instance.xts.complete_square_off(leg)

                strategy_instance.logger.log(f'squaring off everything, as SL got hit')
                print('squaring off everything, as SL got hit')
                # legs[0].soc.disconnect()
                break
            if strategy_instance.total_pnl >strategy_instance.overall_target:
                print(f'total_pnl {strategy_instance.total_pnl} is above overall target {strategy_instance.overall_target}')
                for leg in legs:
                    strategy_instance.xts.complete_square_off(leg)
                print('squaring off everything, target acheived')
                strategy_instance.logger.log(f'squaring off everything, target acheived')
                # legs[0].soc.disconnect()

                break
            time_now = datetime.now()
            await asyncio.sleep(3)
        print('squaring off because time is over')
        strategy_instance.logger.log(f'squaring off because time is over')
        
        for leg in legs:
                    strategy_instance.xts.complete_square_off(leg)
        asyncio.sleep(5)
        report_generator(strategy_instance)
        return