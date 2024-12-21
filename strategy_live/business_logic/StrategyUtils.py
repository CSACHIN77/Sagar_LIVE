import json
from utils import filter_dataframe, get_atm
def get_underlying_ltp(strategy_instance) -> float:
            underlying_ltp = None
            try:
                if strategy_instance.underlying.lower() == 'spot':
                    print('Selected underlying is spot')
                    print(strategy_instance.index_ex_id)
                    data = strategy_instance.xts.get_quotes([strategy_instance.index_ex_id])
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