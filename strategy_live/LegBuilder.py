from utils import filter_dataframe
import re
import json
import pandas as pd
from utils import get_atm
from LegUtils import get_expiry_df, assign_strategy_variables, apply_strike_selection_criteria, apply_closest_premium_selection_criteria,apply_straddle_width_selection_criteria
import time
from io import StringIO
from datetime import datetime, timedelta
import asyncio
from utils import Logger, update_tradebook, slice_orders, get_rolling_strike
import os
import sys
sys.path.append(os.path.abspath('../../Sagar_common'))

try:
    from common_function import fetch_parameter
except ImportError as e:
    print(f"Error importing 'fetch_parameter': {e}")
environment = "dev"
creds = fetch_parameter(environment, "live_creds")
class LegBuilder:
    def __init__(self, xts, soc, interactive_soc, leg_name, strategy, publisher, total_lots, position, option_type, expiry, strike_selection_criteria, strike, roll_strike,
                 new_strike_selection_criteria, stop_loss, trailing_sl, no_of_reentry, simple_momentum=False, range_breakout=False):
        self.xts = xts
        self.pegasus = Logger('pegasus.txt')
        self.soc = soc
        self.leg_name = leg_name
        self.interactive = interactive_soc
        self.strategy = strategy
        self.publisher = publisher
        self.total_lots = total_lots
        self.position = position
        self.option_type = 3 if option_type == 'CE' else 4
        self.expiry = 0 if expiry == 'current' else (1 if expiry=='next_expiry' else 2 if expiry == 'monthly' else None)
        self.strike_selection_criteria = strike_selection_criteria
        self.strike = strike
        self.roll_strike = roll_strike
        self.stop_loss = stop_loss
        self.trailing_sl = trailing_sl
        self.no_of_reentry = no_of_reentry
        self.reentry_count = 0
        self.simple_momentum = simple_momentum
        self.range_breakout = range_breakout
        self.current_price = None
        self.current_profit_loss = 0  
        self.order_status = None
        self.index, self.df, self.base = assign_strategy_variables(self.strategy)
        self.expiry_df , self.combined_expiry_df = get_expiry_df(self.df, self.index, self.expiry, self.option_type)
        self.trade_data = []
        self.tradebook = []
        self.market_data =[]
        self.trigger_tolerance = 2
        self.trade_position = None
        self.max_profit = 0
        self.max_loss = 0
        self.pnl = 0 
        self.sl_price = 0
        self.appOrderID = None
        self.trade_data_event = asyncio.Event()
        self.market_data_event = asyncio.Event()
        self.realised_pnl = 0
        self.instrument = None


    def execute_limit_order(self, order_param):
        print(f"calling execute order with parameters {order_param}")
        order = self.xts.place_limit_order(order_param)
        self.appOrderID = order['AppOrderID']


    async def receive_trades(self,data):
        print(f'trade data received from publisher for {self.leg_name}')#and data is \n {data}')
        self.trade_data.append(data)
        print('trade data has been appended')
        try:
            dt = datetime.strptime(data['ExchangeTransactTimeAPI'], '%d-%m-%Y %H:%M:%S')
            data['ExchangeTransactTimeAPI'] = dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            dt = datetime.strptime(data['ExchangeTransactTimeAPI'], '%Y-%m-%d %H:%M:%S')
            data['ExchangeTransactTimeAPI'] = dt.strftime('%Y-%m-%d %H:%M:%S')
        # print(data)
        if data['OrderUniqueIdentifier'].endswith(('sm', 'rb')):
            try:
                self.trade_data_event.set()
                self.leg_place_order()

            except:
                pass

        elif not  data['OrderUniqueIdentifier'].endswith('sl'):
            self.trade_data_event.set()
            print("trade data event set")
        
        if data['OrderUniqueIdentifier'].endswith('sl'):
            update_tradebook(data, self.sl_price)
            self.trade_position = None
            print('changed trade_position to none')
            print(f'no of renentry {self.no_of_reentry} and reentry count {self.reentry_count}')
            if (self.no_of_reentry) and (self.no_of_reentry> self.reentry_count):
                    print('checking for reentry')
                    self.reentry_count = self.reentry_count + 1
                    print('running re entry logic')
                    await self.reentry_logic()
                    
            else:
             pass
        elif data['OrderUniqueIdentifier'].endswith('momentum'):
            self.trade_position = True
            self.xts.place
            update_tradebook(data, self.entry_price)
        elif data['OrderUniqueIdentifier'].endswith('cover'):
            update_tradebook(data)
            print("updated db for covering pending orders")

        else:
            update_tradebook(data, self.entry_price)

        self.pegasus.log(data)
        print(data['ExchangeTransactTimeAPI'])
        print(f'trade data appended')


    async def receive_data(self,data):
        self.market_data.append(data)
        self.market_data_event.set()

    async def reentry_logic(self):
        print('inside reentry function')
        order_placed=False
        
        while True :
            time_now = datetime.now()
            if self.strategy.last_entry_time > time_now:
                current_price = self.market_data[-1:][0]
                current_price = current_price['LastTradedPrice']
                if (self.position.lower() =='buy') and (not order_placed):
                    if current_price >= self.entry_price:
                        print(f'current price {current_price} has come back to entry_price {self.entry_price}')
                        print('re-entering the trade')
                        
                        order = self.xts.place_market_order({"exchangeInstrumentID": self.instrument_id, "orderSide": self.position,
                                                            "orderQuantity":int(self.lot_size) *self.total_lots,"limitPrice":0,
                                                                "stopPrice": 1, "orderUniqueIdentifier": self.leg_name})
                        self.appOrderID = order['AppOrderID']
                        self.strategy.logger.log(f'{self.leg_name} : {self.instrument.tradingsymbol}, Re-entry, {self.position} order placed at {self.entry_price}')
                        order_placed=True
                        print('breaking out of while loop')
                        break
                elif (self.position.lower()=='sell') and (not order_placed):
                    if current_price <= self.entry_price:
                        print(f'current price {current_price} has come back to entry_price {self.entry_price}')
                        print('re-entering the trade')
                        
                        order = self.xts.place_market_order({"exchangeInstrumentID": self.instrument_id, "orderSide": self.position,
                                                            "orderQuantity":int(self.lot_size) *self.total_lots,"limitPrice":0,
                                                                "stopPrice": 1, "orderUniqueIdentifier": self.leg_name})
                        self.appOrderID = order['AppOrderID']
                        self.strategy.logger.log(f'{self.leg_name} : {self.instrument.tradingsymbol}, Re-entry, {self.position} order placed at {self.entry_price}')
                        order_placed=True
                        print('breaking out of while loop')
                        break
            else:
                # print('last entry time is over')
                pass
        if order_placed:
            print('waiting for trade data')
            # await self.trade_data_event.wait()
            #optimize it
            await asyncio.sleep(5)
            print('wait is over in reentry logic')
            latest_trade = self.trade_data[-1:][0]
            if latest_trade['OrderStatus']=='Filled':
                order_placed=False
                self.trade_entry_price = float(latest_trade['OrderAverageTradedPrice'])
                trade_side = latest_trade['OrderSide']
                traded_quantity = latest_trade['OrderQuantity']
                entry_timestmap = latest_trade['ExchangeTransactTime']
                entry_slippage = self.trade_entry_price - self.entry_price
                trade = {'symbol': self.instrument_id, 'entry_price': self.entry_price, 'trade_price': self.trade_entry_price,  'trade' : trade_side, 'quantity' : traded_quantity, 'timestamp': entry_timestmap, 'entry_slippage': round((self.entry_price - self.trade_entry_price), 2)}
                # print(f'instrument traded at avg price of {self.trade_entry_price}, side {trade_side},\n with quantity {traded_quantity} and executed at  {entry_timestmap} and slippage is {entry_slippage}')
                # print(trade)
            # print(f'placing SL order now for {self.leg_name} SL points {self.stop_loss}')
            # if self.stop_loss[0].lower()=='points':
            #     self.stop_loss = self.stop_loss[1]
            # elif self.stop_loss[0].lower() == 'percent':
            #     self.stop_loss = round(self.trade_entry_price*self.stoploss[1]/100, 2)
            if trade_side.upper() == 'BUY':
                self.trade_position = 'long'
                print('trade position is long')
                self.sl_price = self.trade_entry_price - self.stop_loss
                trigger_price = self.sl_price - self.trigger_tolerance
            else: 
                self.trade_position = 'short'
                print('trade position is short')
                self.sl_price = self.trade_entry_price + self.stop_loss
                trigger_price = self.sl_price + self.trigger_tolerance
            orderSide = trade_side #'BUY' if trade_side.upper() == 'SELL' else 'SELL'
            orderid = f"{self.leg_name}_sl"
            print({"exchangeInstrumentID": self.instrument_id, "orderSide": orderSide,
                                            "orderQuantity":traded_quantity,
                                              "limitPrice": trigger_price, 'stopPrice':self.sl_price, 'orderUniqueIdentifier': orderid})
            order =  self.xts.place_SL_order({"exchangeInstrumentID": self.instrument_id, "orderSide": orderSide,
                                            "orderQuantity":traded_quantity, "limitPrice": trigger_price, 'stopPrice':self.sl_price, 'orderUniqueIdentifier': orderid})    
            self.appOrderID = order['AppOrderID']
            self.strategy.logger.log(f'{self.leg_name} : {self.instrument.tradingsymbol}, Re-entry SL {orderSide} order placed at {self.sl_price}')
            self.trade_data_event.clear()
    
    async def stoploss_trail(self, ltp, trade_position):

        # print("inside stoploss_trail function")
        if (self.trailing_sl) and trade_position =='long':
            price_gap = ltp - self.entry_price
            if price_gap > self.trailing_sl["priceMove"]:
                orders = self.interactive.orders

                trail_increment_factor = price_gap//self.trailing_sl["priceMove"]
                original_sl = self.trade_entry_price - self.stop_loss
                updated_sl = original_sl + trail_increment_factor*self.trailing_sl["sl_adjustment"]
                if updated_sl > self.sl_price:
                    print(f"sl {self.sl_price} adjusted to {updated_sl} current_price is {ltp} and entry_price {self.entry_price} in {self.leg_name}")
                    self.sl_price = updated_sl
                    order_uid = f"{self.leg_name}_sl"
                    for order in orders[::-1]:
                        print(order)
                        if order["orderUniqueIdentifier"] ==order_uid:
                            app_id = order["appOrderID"]
                            print(f"type of app_id is {type(app_id)} {app_id}")
                            break
                    params = {
                        "appOrderID": app_id,
                        "modifiedProductType": "NRML",
                        "modifiedOrderType": "STOPLIMIT",
                        "modifiedOrderQuantity": self.lot_size*self.total_lots,
                        "modifiedDisclosedQuantity": 0,
                        "modifiedLimitPrice": float(updated_sl-self.trigger_tolerance),
                        "modifiedStopPrice": float(updated_sl),
                        "modifiedTimeInForce": "DAY",
                        "orderUniqueIdentifier": order_uid
                        }
                    self.xts.modify_order(params)
                    self.strategy.logger.log(f'{self.leg_name} : {self.instrument.tradingsymbol}, SL updated to {self.sl_price}')
                else:
                    pass
        elif (self.trailing_sl) and (trade_position=='short') :       
            price_gap = self.entry_price - ltp 
            if price_gap > self.trailing_sl["priceMove"]:
                orders = self.interactive.orders
                print(self.stop_loss, self.trade_entry_price)
                trail_increment_factor = price_gap//self.trailing_sl["priceMove"]
                original_sl =  self.stop_loss + self.trade_entry_price
                updated_sl = original_sl - trail_increment_factor*self.trailing_sl["sl_adjustment"]
                if updated_sl < self.sl_price:
                    print(f"sl {self.sl_price} adjusted to {updated_sl} current_price is {ltp} and entry_price {self.entry_price}")
                    self.sl_price = updated_sl
                    order_uid = f"{self.leg_name}_sl"
                    for order in orders[::-1]:
                        if order["OrderUniqueIdentifier"] ==order_uid:
                            
                            app_id = order["AppOrderID"]
                           
                            break
                    params = {
                        "appOrderID": app_id,
                        "modifiedProductType": "NRML",
                        "modifiedOrderType": "STOPLIMIT",
                        "modifiedOrderQuantity": int(self.lot_size*self.total_lots),
                        "modifiedDisclosedQuantity": 0,
                        "modifiedLimitPrice": float(updated_sl+self.trigger_tolerance),
                        "modifiedStopPrice": float(updated_sl),
                        "modifiedTimeInForce": "DAY",
                        "orderUniqueIdentifier": order_uid
                        }
                    self.xts.modify_order(params)
                    self.strategy.logger.log(f'{self.leg_name} : {self.instrument.tradingsymbol}, SL updated to {self.sl_price}')

                else:
                    pass
            

    
    def selection_criteria(self):
        """
            Apply selection criteria based on user-defined parameters to determine the option to be traded.
        """
        choice = self.strike_selection_criteria['strike_selection']
        choice_value = self.strike_selection_criteria['value']
        print(f"choice is {choice} and choice_value is {choice_value}")
    
        if  choice.lower() == 'strike':
            self.option_symbol, self.lot_size, self.instrument_id = apply_strike_selection_criteria(choice_value, self.strike, self.expiry_df, self.option_type, self.base)
            print(f"selected option is {self.option_symbol}")
        elif choice.lower() =='closest_premium':
            self.option_symbol, self.lot_size, self.instrument_id, nearest_premium = apply_closest_premium_selection_criteria(self.xts, choice_value, self.expiry_df)
            print(f"selected option is {self.option_symbol}")
        elif choice.lower() in ['straddle_width', 'atm_pct', 'atm_straddle_premium']:
            self.option_symbol, self.lot_size, self.instrument_id = apply_straddle_width_selection_criteria(self.xts, choice, choice_value, self.combined_expiry_df, self.strike, self.expiry_df, self.base)

        self.xts.subscribe_symbols([{'exchangeSegment': 2, 'exchangeInstrumentID': self.instrument_id}])
        response = self.xts.get_quotes([{'exchangeSegment': 2, 'exchangeInstrumentID': self.instrument_id}])
        ltp_data = response['result']['listQuotes']
        ltp = json.loads(ltp_data[0])['LastTradedPrice']
        self.entry_price = float(ltp)
 
        self.instrument = self.expiry_df[self.expiry_df['instrument_token']== self.instrument_id].iloc[0]
        self.strategy.logger.log(f'{self.leg_name} : {self.instrument.tradingsymbol}, entry_price before placing order is {self.entry_price}')
       
        if self.range_breakout:
            timeframe = self.range_breakout['timeframe']
            start_time = self.strategy.entry_time
            end_time = start_time + timedelta(minutes=timeframe)
            start_time = start_time.strftime('%b %d %Y %H%M%S')
            end_time = end_time.strftime('%b %d %Y %H%M%S')
            # trade_side = self.range_breakout['']
            params = {
                "exchangeSegment": 2,
                "exchangeInstrumentID": self.instrument_id,
                "startTime": start_time,
                "endTime": end_time,
                "compressionValue": 60
            }
            print(params)
            print(f'sleeping for {timeframe} minutes')
            time.sleep(timeframe*60)
            data= self.xts.get_historical_data(params)['result']['dataReponse']
            data = data.replace(',', '\n')
            historical_data = pd.read_csv(StringIO(data), sep = '|', usecols=range(7), header = None, low_memory=False)
            new_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi']
            historical_data.columns = new_columns
            # historical_data['instrument_token'] = exchange_instrument_id
            # historical_data['tradingsymbol'] = tradingsymbol
            historical_data['timestamp'] = pd.to_datetime(historical_data['timestamp'], unit='s')
            print(historical_data)
            print(f"highest high is {max(historical_data['high'])}, and low is {min(historical_data['low'])}")
            if self.range_breakout['side'].lower()=='high':
                self.entry_price = max(historical_data['high'])
                print(f'high of range is {self.entry_price}')
            elif self.range_breakout['side'].lower()=='low':
                self.entry_price = min(historical_data['low'])
                print('low of range is {self.entry_price}')
            if self.position.lower() == 'buy':
                limit_price = int(self.entry_price)
                trigger_price = int(self.entry_price + self.trigger_tolerance)
            elif self.position.lower() == 'sell':
                limit_price = float(self.entry_price)
                trigger_price = float(self.entry_price - self.trigger_tolerance)
            print(trigger_price, self.entry_price, self.position)
            print(f"Range for {self.range_breakout['timeframe'] is  min(historical_data['low']) and  max(historical_data['high']) }")
            print(f"User selected {self.range_breakout['side']} option, and entry price is {self.entry_price}")
            order =  self.xts.place_SL_order({"exchangeInstrumentID": self.instrument_id, "orderSide": self.position, "orderQuantity":int(self.total_lots * self.lot_size), "limitPrice": trigger_price, 'stopPrice':self.entry_price, 'orderUniqueIdentifier': f"{self.leg_name}_rb"})
            print('order placed for range breakout')
            self.strategy.logger.log(f'{self.leg_name} : {self.instrument.tradingsymbol}, order placed for range breakout with entry price {limit_price}')
            print(order)
            return
        elif self.simple_momentum:
            if self.simple_momentum['value_type'].lower()=='points':
                sm_value = self.simple_momentum['value']
            elif self.simple_momentum['value_type'].lower()=='percentage':
                sm_value = round((self.entry_price*self.simple_momentum['value'])/100, 2)
            if self.simple_momentum['direction'].lower() =='increment':
                self.entry_price = self.entry_price + sm_value
            elif self.simple_momentum['direction'].lower() =='decay':
                self.entry_price = self.entry_price - sm_value
            if self.position.lower() == 'buy':
                limit_price = int(self.entry_price)
                trigger_price = int(self.entry_price + self.trigger_tolerance)
            elif self.position.lower() == 'sell':
                limit_price = float(self.entry_price)
                trigger_price = float(self.entry_price - self.trigger_tolerance)
            print(trigger_price, self.entry_price, self.position)
            
            order =  self.xts.place_SL_order({"exchangeInstrumentID": self.instrument_id,
                                               "orderSide": self.position,
                                                 "orderQuantity":int(self.total_lots * self.lot_size),
                                                   "limitPrice": trigger_price, 'stopPrice':self.entry_price,
                                                     'orderUniqueIdentifier': f"{self.leg_name}_sm"})
            print(f"Order placed for {self.simple_momentum['direction']}  of value {sm_value} and entry price is {limit_price}")
            print(order)
            return
        else:
            pass
            # self.freeze_quantity = int(self.df[[self.df.instrument_token]==self.instrument_id].FreezeQty.values[0])-1
            # if (int(self.lot_size) *self.total_lots) > self.freeze_quantity:
            #     valid_quantity_list = slice_orders(int(self.lot_size) *self.total_lots, self.freeze_quantity)
            #     for quantity in valid_quantity_list:
            #         order = self.xts.place_market_order({"exchangeInstrumentID": self.instrument_id, "orderSide": self.position,
            #                           "orderQuantity":quantity,"limitPrice":0,
            #                             "stopPrice": 1, "orderUniqueIdentifier": self.leg_name})
                    
        order_param = {"exchangeInstrumentID": self.instrument_id, "orderSide": self.position,
                                      "orderQuantity":int(self.lot_size) *self.total_lots,"limitPrice":0,
                                        "stopPrice": 1, "orderUniqueIdentifier": self.leg_name}
        self.execute_limit_order(order_param)
            
        self.strategy.logger.log(f'{self.leg_name} : {self.instrument.tradingsymbol} market order placed')
        self.publisher.add_trade_subscriber(self)
        self.publisher.add_subscriber(self, [self.instrument_id])
    
    async def leg_place_order(self):        
        print('leg place order invoked')
        print('waiting for the trade data to be set')
        try:
            await asyncio.wait_for(self.trade_data_event.wait(), timeout=5)
            self.trade_data_event.clear()
        except asyncio.TimeoutError:
           
           print("modify order to market order logic here")
           history_order = self.xts.order_history(self.appOrderID)
           print(history_order)
           if history_order['type']=='success':
            modifiedProductType = history_order['result'][0]['ProductType']
            modifiedOrderType = history_order['result'][0]['OrderType']
            modifiedOrderQuantity = history_order['result'][0]['LeavesQuantity']
            orderUniqueIdentifier = history_order['result'][0]['OrderUniqueIdentifier']   
           modified_order = {

                "appOrderID": self.appOrderID,
                "modifiedProductType": modifiedProductType,
                "modifiedOrderType": "MARKET",
                "modifiedOrderQuantity": modifiedOrderQuantity,
                "modifiedDisclosedQuantity": 0,
                "modifiedLimitPrice": 0,
                "modifiedStopPrice": 0,
                "modifiedTimeInForce": "DAY",
                "orderUniqueIdentifier": orderUniqueIdentifier
            }
           modified_order = self.xts.modify_order(modified_order)
        latest_trade = self.trade_data[-1:][0]
        if latest_trade['OrderStatus']=='Filled':
            self.trade_entry_price = float(latest_trade['OrderAverageTradedPrice'])
            trade_side = latest_trade['OrderSide']
            traded_quantity = latest_trade['OrderQuantity']
            entry_timestmap = latest_trade['ExchangeTransactTime']
            entry_slippage = self.trade_entry_price - self.entry_price
            trade = {'symbol': self.instrument_id, 'entry_price': self.entry_price, 'trade_price': self.trade_entry_price,  'trade' : trade_side, 'quantity' : traded_quantity, 'timestamp': entry_timestmap, 'entry_slippage': round((self.entry_price - self.trade_entry_price), 2)}
            self.strategy.logger.log(f'{self.leg_name} : {self.instrument.tradingsymbol}, order filled {self.entry_price}')
            
        # print(f'placing SL order now for {self.leg_name} SL points {self.stop_loss}')
        if self.stop_loss[0].lower()=='points':
            self.stop_loss = self.stop_loss[1]
        elif self.stop_loss[0].lower() == 'percent':
            self.stop_loss = round(self.trade_entry_price*self.stoploss[1]/100, 2)
        if trade_side.upper() == 'BUY':
            self.trade_position = 'long'
            print('trade position is long')
            self.sl_price = self.trade_entry_price - self.stop_loss
            trigger_price = self.sl_price - self.trigger_tolerance
        else: 
            self.trade_position = 'short'
            print('trade position is short')
            self.sl_price = self.trade_entry_price + self.stop_loss
            trigger_price = self.sl_price + self.trigger_tolerance
        orderSide = 'BUY' if trade_side.upper() == 'SELL' else 'SELL'
        orderid = f"{self.leg_name}_sl"
        
        order =  self.xts.place_SL_order({"exchangeInstrumentID": self.instrument_id,
                                           "orderSide": orderSide, "orderQuantity":traded_quantity, "limitPrice": trigger_price, 'stopPrice':self.sl_price, 'orderUniqueIdentifier': orderid})
        self.strategy.logger.log(f'{self.leg_name} : {self.instrument.tradingsymbol}, SL order placed with limit price {self.sl_price}')
        # self.pegasus.log(order)

    async def calculate_mtm(self):
        quantity = self.lot_size*self.total_lots 
        print(f'entering calculate_mtm for {self.leg_name}')
        print('waiting for tick data')
        await self.market_data_event.wait()
        self.market_data_event.clear()
        print(f'trade position {self.trade_position} for {self.leg_name}')
        time_now = datetime.now()
        while self.strategy.exit_time > time_now:
            time_now = datetime.now()
            if  not self.trade_position:
                self.realised_pnl = self.realised_pnl + self.pnl
                self.pnl = 0
                # print(f'm2m  {self.leg_name} is {self.realised_pnl} and there is no position')
                
            else:
                current_ltp = self.market_data[-1:][0]['LastTradedPrice']
                if self.trade_position.lower()== 'long':
                    self.pnl = round((current_ltp - self.trade_entry_price)*quantity, 2) + self.realised_pnl
                    # await self.stoploss_trail(current_ltp, "long")
                    if self.roll_strike:
                        await self.roll_strike_handler(current_ltp, "long")
                    # print(f'm2m  {self.leg_name} is {self.pnl}')
                    # if self.pnl > self.max_profit:
                    #     self.max_profit
                    # elif self.pnl < self.max_loss:
                    #     self.max_loss = self.pnl
                    # print(f'm2m  {self.leg_name} is {self.pnl} ')
                else :
                    self.pnl = round((self.trade_entry_price - current_ltp )*quantity, 2) + self.realised_pnl
                    await self.stoploss_trail(current_ltp, "short")
                    await self.roll_strike_handler(current_ltp, "short")
                    # print(f'm2m  {self.leg_name} is {self.pnl}')
                    # if self.pnl > self.max_profit:
                    #     self.max_profit
                    # elif self.pnl < self.max_loss:
                    #     self.max_loss = self.pnl
                    # print(f'm2m  {self.leg_name} is {self.pnl} ')
            await asyncio.sleep(3)
        # self.strategy.total_pnl += self.pnl
            
    # async def roll_strike_handler(self,ltp, position):
    #         print('entering roll_strike handler')
    #         if self.roll_strike: 
    #             if ((position=="long") and ((ltp-self.trade_entry_price)> self.roll_strike["roll_strike_value"])):
    #                 #square off existing order
    #                 #cancel trigger order
    #                 current_ltp = self.strategy.get_underlyingltp()
    #                 current_atm = get_atm(current_ltp, self.base)
    #                 roll_strike_atm = get_rolling_strike(current_atm, self.option_type, self.roll_strike['roll_strike_type'], self.base)
    #                 print(f"roll strike handler current ltp is {current_ltp}")
    #                 # selected_option = self.expiry_df[self.expiry_df['strike']== roll_strike_atm]
    #                 selected_strike = int(roll_strike_atm)
    #                 print(selected_strike)
    #                 selected_roll_strike = int(selected_strike - self.base*self.roll_strike["roll_level"])
    #                 roll_option_name = self.expiry_df[self.expiry_df['strike'].astype(int)== selected_roll_strike]
    #                 print(f"selected strike is {roll_option_name['tradingsymbol'].values[0]}")
    #             if ((position=="short") and ((self.trade_entry_price-ltp)> self.roll_strike["roll_strike_value"])):
    #                 #square off existing order
    #                 #cancel trigger order
    #                 # selected_option = self.expiry_df[self.expiry_df['strike']== roll_strike_atm]
    #                 current_ltp = self.strategy.get_underlyingltp()
    #                 current_atm = get_atm(current_ltp, self.base)
    #                 roll_strike_atm = get_rolling_strike(current_atm, self.option_type, self.roll_strike['roll_strike_type'], self.base)
    #                 selected_strike = int(roll_strike_atm)
    #                 print(selected_strike)
    #                 selected_roll_strike = int(selected_strike + self.base*self.roll_strike["roll_level"])
    #                 roll_option_name = self.expiry_df[self.expiry_df['strike'].astype(int)== selected_roll_strike] 
    #                 print(f"selected strike is {roll_option_name['tradingsymbol'].values[0]}")
    #             else:
    #                 print('no need to roll strike')
    
            
    async def roll_strike_handler(self, ltp, position):
        print('entering roll_strike handler')
        if self.roll_strike and position in ("long", "short"):
            current_roll_pnl = ltp - self.trade_entry_price
            sign = 1 if position == "long" else -1
            price_diff = sign * current_roll_pnl

            if price_diff > self.roll_strike["roll_strike_value"]:
                # Square off existing order
                # Cancel trigger order

                current_ltp = self.strategy.get_underlyingltp()
                current_atm = get_atm(current_ltp, self.base)
                roll_strike_atm = get_rolling_strike(
                    current_atm,
                    self.option_type,
                    self.roll_strike['roll_strike_strike_type'],
                    self.base
                )
                print(f"roll strike handler current ltp is {current_ltp}")

                selected_strike = int(roll_strike_atm)
                print(selected_strike)

                # Adjust the strike based on position
                adjustment = sign * self.base * self.roll_strike["roll_level"]
                selected_roll_strike = int(selected_strike + adjustment)

                roll_option_name = self.expiry_df[
                    self.expiry_df['strike'].astype(int) == selected_roll_strike
                ]
                print(f"selected strike is {roll_option_name['tradingsymbol'].values[0]}")
            else:
                print('Roll Strike is False')




    
