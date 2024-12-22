import asyncio
from utils import get_atm, get_rolling_strike

def execute_limit_order(leg, order_param):
    print(f"calling execute order with parameters {order_param}")
    order = leg.xts.place_limit_order(order_param)
    appOrderID = order['AppOrderID']
    print(f"app order id in execute_limit_order is {appOrderID}")
    return appOrderID



async def leg_place_order(leg_instance):        
        print('leg place order invoked')
        print('waiting for the trade data to be set')
        try:
            await asyncio.wait_for(leg_instance.trade_data_event.wait(), timeout=5)
            leg_instance.trade_data_event.clear()
        except asyncio.TimeoutError:
           
           print("modify order to market order logic here")
           history_order = leg_instance.xts.order_history(leg_instance.appOrderID)
           print(history_order)
           if history_order['type']=='success':
                modifiedProductType = history_order['result'][0]['ProductType']
                modifiedOrderType = history_order['result'][0]['OrderType']
                modifiedOrderQuantity = history_order['result'][0]['LeavesQuantity']
                orderUniqueIdentifier = history_order['result'][0]['OrderUniqueIdentifier']   
           modified_order = {

                "appOrderID": leg_instance.appOrderID,
                "modifiedProductType": modifiedProductType,
                "modifiedOrderType": "MARKET",
                "modifiedOrderQuantity": modifiedOrderQuantity,
                "modifiedDisclosedQuantity": 0,
                "modifiedLimitPrice": 0,
                "modifiedStopPrice": 0,
                "modifiedTimeInForce": "DAY",
                "orderUniqueIdentifier": orderUniqueIdentifier
            }
           modified_order = leg_instance.xts.modify_order(modified_order)
           print(f"modified order is {modified_order}")
           print(f"leg instance is {leg_instance.leg_name}")
           if modified_order['type']=='success':
                leg_instance.strategy.logger.log(f'{leg_instance.leg_name} : {leg_instance.instrument.tradingsymbol}, order modified to market order')
           else:
                leg_instance.strategy.logger.log(f'{leg_instance.leg_name} : {leg_instance.instrument.tradingsymbol}, order modification failed')
           return

        latest_trade = leg_instance.trade_data[-1:][0]
        if latest_trade['OrderStatus']=='Filled':
            leg_instance.trade_entry_price = float(latest_trade['OrderAverageTradedPrice'])
            trade_side = latest_trade['OrderSide']
            traded_quantity = latest_trade['OrderQuantity']
            entry_timestmap = latest_trade['ExchangeTransactTimeAPI']
            entry_slippage = leg_instance.trade_entry_price - leg_instance.entry_price
            trade = {'symbol': leg_instance.instrument_id, 'entry_price': leg_instance.entry_price, 'trade_price': leg_instance.trade_entry_price,  'trade' : trade_side, 'quantity' : traded_quantity, 'timestamp': entry_timestmap, 'entry_slippage': round((leg_instance.entry_price - leg_instance.trade_entry_price), 2)}
            leg_instance.strategy.logger.log(f'{leg_instance.leg_name} : {leg_instance.instrument.tradingsymbol}, order filled {leg_instance.entry_price}')
            
        # print(f'placing SL order now for {leg_instance.leg_name} SL points {leg_instance.stop_loss}')
        if leg_instance.stop_loss[0].lower()=='points':
            leg_instance.stop_loss = leg_instance.stop_loss[1]
        elif leg_instance.stop_loss[0].lower() == 'percent':
            leg_instance.stop_loss = round(leg_instance.trade_entry_price*leg_instance.stoploss[1]/100, 2)
        if trade_side.upper() == 'BUY':
            leg_instance.trade_position = 'long'
            print('trade position is long')
            leg_instance.sl_price = leg_instance.trade_entry_price - leg_instance.stop_loss
            trigger_price = leg_instance.sl_price - leg_instance.trigger_tolerance
        else: 
            leg_instance.trade_position = 'short'
            print('trade position is short')
            leg_instance.sl_price = leg_instance.trade_entry_price + leg_instance.stop_loss
            trigger_price = leg_instance.sl_price + leg_instance.trigger_tolerance
        orderSide = 'BUY' if trade_side.upper() == 'SELL' else 'SELL'
        orderid = f"{leg_instance.leg_name}_sl"
        
        order =  leg_instance.xts.place_SL_order({"exchangeInstrumentID": leg_instance.instrument_id,
                                           "orderSide": orderSide, "orderQuantity":traded_quantity, "limitPrice": trigger_price, 'stopPrice':leg_instance.sl_price, 'orderUniqueIdentifier': orderid})
        leg_instance.strategy.logger.log(f'{leg_instance.leg_name} : {leg_instance.instrument.tradingsymbol}, SL order placed with limit price {leg_instance.sl_price}')
        # leg_instance.pegasus.log(order)




async def roll_strike_handler(leg_instance, ltp, position):
        print('entering roll_strike handler')
        if leg_instance.roll_strike and position in ("long", "short"):
            current_roll_pnl = ltp - leg_instance.trade_entry_price
            sign = 1 if position == "long" else -1
            price_diff = sign * current_roll_pnl

            if price_diff > leg_instance.roll_strike["roll_strike_value"]:
                # Square off existing order
                # Cancel trigger order

                current_ltp = leg_instance.strategy.get_underlyingltp()
                current_atm = get_atm(current_ltp, leg_instance.base)
                roll_strike_atm = get_rolling_strike(
                    current_atm,
                    leg_instance.option_type,
                    leg_instance.roll_strike['roll_strike_strike_type'],
                    leg_instance.base
                )
                print(f"roll strike handler current ltp is {current_ltp}")

                selected_strike = int(roll_strike_atm)
                print(selected_strike)

                # Adjust the strike based on position
                adjustment = sign * leg_instance.base * leg_instance.roll_strike["roll_level"]
                selected_roll_strike = int(selected_strike + adjustment)

                roll_option_name = leg_instance.expiry_df[
                    leg_instance.expiry_df['strike'].astype(int) == selected_roll_strike
                ]
                print(f"selected strike is {roll_option_name['tradingsymbol'].values[0]}")
            else:
                print('Roll Strike is False')


async def stoploss_trail(leg_instance, ltp, trade_position):

    # print("inside stoploss_trail function")
    if (leg_instance.trailing_sl) and trade_position =='long':
        price_gap = ltp - leg_instance.entry_price
        if price_gap > leg_instance.trailing_sl["priceMove"]:
            orders = leg_instance.interactive.orders

            trail_increment_factor = price_gap//leg_instance.trailing_sl["priceMove"]
            original_sl = leg_instance.trade_entry_price - leg_instance.stop_loss
            updated_sl = original_sl + trail_increment_factor*leg_instance.trailing_sl["sl_adjustment"]
            if updated_sl > leg_instance.sl_price:
                print(f"sl {leg_instance.sl_price} adjusted to {updated_sl} current_price is {ltp} and entry_price {leg_instance.entry_price} in {leg_instance.leg_name}")
                leg_instance.sl_price = updated_sl
                order_uid = f"{leg_instance.leg_name}_sl"
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
                    "modifiedOrderQuantity": leg_instance.lot_size*leg_instance.total_lots,
                    "modifiedDisclosedQuantity": 0,
                    "modifiedLimitPrice": float(updated_sl-leg_instance.trigger_tolerance),
                    "modifiedStopPrice": float(updated_sl),
                    "modifiedTimeInForce": "DAY",
                    "orderUniqueIdentifier": order_uid
                    }
                leg_instance.xts.modify_order(params)
                leg_instance.strategy.logger.log(f'{leg_instance.leg_name} : {leg_instance.instrument.tradingsymbol}, SL updated to {leg_instance.sl_price}')
            else:
                pass
    elif (leg_instance.trailing_sl) and (trade_position=='short') :       
        price_gap = leg_instance.entry_price - ltp 
        if price_gap > leg_instance.trailing_sl["priceMove"]:
            orders = leg_instance.interactive.orders
            print(leg_instance.stop_loss, leg_instance.trade_entry_price)
            trail_increment_factor = price_gap//leg_instance.trailing_sl["priceMove"]
            original_sl =  leg_instance.stop_loss + leg_instance.trade_entry_price
            updated_sl = original_sl - trail_increment_factor*leg_instance.trailing_sl["sl_adjustment"]
            if updated_sl < leg_instance.sl_price:
                print(f"sl {leg_instance.sl_price} adjusted to {updated_sl} current_price is {ltp} and entry_price {leg_instance.entry_price}")
                leg_instance.sl_price = updated_sl
                order_uid = f"{leg_instance.leg_name}_sl"
                for order in orders[::-1]:
                    if order["OrderUniqueIdentifier"] ==order_uid:
                        
                        app_id = order["AppOrderID"]
                        
                        break
                params = {
                    "appOrderID": app_id,
                    "modifiedProductType": "NRML",
                    "modifiedOrderType": "STOPLIMIT",
                    "modifiedOrderQuantity": int(leg_instance.lot_size*leg_instance.total_lots),
                    "modifiedDisclosedQuantity": 0,
                    "modifiedLimitPrice": float(updated_sl+leg_instance.trigger_tolerance),
                    "modifiedStopPrice": float(updated_sl),
                    "modifiedTimeInForce": "DAY",
                    "orderUniqueIdentifier": order_uid
                    }
                leg_instance.xts.modify_order(params)
                leg_instance.strategy.logger.log(f'{leg_instance.leg_name} : {leg_instance.instrument.tradingsymbol}, SL updated to {leg_instance.sl_price}')

            else:
                pass