const { io } = require('socket.io-client');

// Connect to OrderSocket server
const socket = io('http://localhost:8050');

// Sample order data
// const sampleOrder = {
//     OrderType: 'Limit',
//     OrderSide: 'BUY',
//     exchangeInstrumentID: 12345,
//     OrderPrice: 100.50,
//     OrderQuantity: 10
// };

// Connection event handlers
socket.on('connect', () => {
    console.log('Connected to OrderSocket server');
    
    // Place an order once connected
    // console.log('Placing order:', sampleOrder);
    // socket.emit('placeOrder', sampleOrder);
});

socket.on('disconnect', () => {
    console.log('Disconnected from OrderSocket server');
});

// Listen for order updates
socket.on('orderUpdate', (orderData) => {
    console.log('Received order update:', orderData);
    
    if (orderData.OrderStatus === 'Executed') {
        console.log(`Order executed at price: ${orderData.OrderAverageTradedPrice}`);
    } else if (orderData.OrderStatus === 'Pending') {
        console.log('Order is pending, waiting for market conditions');
    }
});

// Error handling
socket.on('error', (error) => {
    console.error('Socket error:', error);
});

// Keep the process running
process.on('SIGINT', () => {
    console.log('Closing socket connection');
    socket.close();
    process.exit();
});