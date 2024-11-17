import socketio
import sys
import json

# Initialize a Socket.IO client
sio = socketio.Client()

# Define event handlers
@sio.event
def connect():
    print('Connected to OrderSocket server')

@sio.event
def disconnect():
    print('Disconnected from OrderSocket server')

# Listen for order updates on the main namespace
@sio.on('orderUpdate')
def on_order_update(data):
    print('Received order update:', json.dumps(data, indent=4))
    
    if data.get('OrderStatus') == 'Executed':
        print(f"Order executed at price: {data.get('OrderAverageTradedPrice')}")
    elif data.get('OrderStatus') == 'Pending':
        print('Order is pending, waiting for market conditions')

# Listen for trade updates on the /tradeSocket namespace
@sio.on('tradeUpdate', namespace='/tradeSocket')
def on_trade_update(data):
    print('Received trade update:', json.dumps(data, indent=4))
    # Display specific fields from the trade update if needed
    # print(f"Trade symbol: {data.get('TradingSymbol')}, Net Position: {data.get('NetPosition')}, MTM: {data.get('MTM')}")

@sio.event
def connect_error(data):
    print("The connection failed!")

# Connect to the server (both main and /tradeSocket namespaces)
try:
    sio.connect('http://localhost:8050')
except Exception as e:
    print(f"Connection error: {e}")
    sys.exit(1)

# Keep the client running to listen for events
try:
    sio.wait()
except KeyboardInterrupt:
    print("Closing connection")
    sio.disconnect()
    sys.exit(0)
