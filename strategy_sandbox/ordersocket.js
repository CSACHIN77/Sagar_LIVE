const express = require('express');
const http = require('http');
const fs = require('fs');
const { Server } = require('socket.io');
const ioClient = require('socket.io-client');

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

// Separate namespace for trade updates
// const tradeSocket = io.of('/tradeSocket');

let pendingOrders = [];
let orderbook = [];
let tradebook = [];
function formatDateToCustom(dateISO) {
  const date = new Date(dateISO);
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are 0-indexed
  const year = date.getFullYear();
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  return `${day}-${month}-${year} ${hours}:${minutes}:${seconds}`;
}
// Middleware to parse JSON bodies for HTTP POST requests
app.use(express.json());

// Load order book and trade book from JSON files
const loadOrderBook = () => {
  try {
    const data = fs.readFileSync('orderbook.json', 'utf-8');
    orderbook = JSON.parse(data);
  } catch (err) {
    console.error("Error loading orderbook.json:", err.message);
  }
};

const loadTradeBook = () => {
  try {
    const data = fs.readFileSync('tradebook.json', 'utf-8');
    tradebook = JSON.parse(data);
  } catch (err) {
    console.error("Error loading tradebook.json:", err.message);
  }
};

// Save order book and trade book to JSON files
const saveOrderBook = () => {
  console.log("saving tradebook")
  fs.writeFileSync('orderbook.json', JSON.stringify(orderbook, null, 2));
};

const saveTradeBook = () => {
  fs.writeFileSync('tradebook.json', JSON.stringify(tradebook, null, 2));
};

// Load existing data on server startup
loadOrderBook();
loadTradeBook();

// Log function to write to ordersocket.log
const logToFile = (message) => {
  fs.appendFileSync('ordersocket.log', `${formatDateToCustom(new Date().toISOString())} - ${message}\n`);
};

// Connect to marketSocket server
const marketSocket = ioClient.connect('http://localhost:5001');

// Variable to store the latest LTPs for each instrument
const latestLTPs = {};

// Listen for LTP updates from marketSocket
// marketSocket.on('message', (data) => {
//   try {
//     console.log(data.data);
//     if (data && data.data && data.data.OverallData) {
//       const marketData = JSON.parse(data.data.OverallData);
//       const { ExchangeInstrumentID, LastTradedPrice } = marketData;

//       latestLTPs[ExchangeInstrumentID] = LastTradedPrice;
//       // console.log(latestLTPs)
//       pendingOrders = pendingOrders.filter(order => {
//         if (
//           order.exchangeInstrumentID === ExchangeInstrumentID &&
//           // order.OrderType === 'Limit' &&
//           order.OrderSide === 'sell' &&
//           LastTradedPrice <= order.OrderPrice // Condition to check if price meets or goes below target
//         ) {
//           // If LTP has reached or is below the order price, execute the order
//           order.OrderStatus = 'Filled';
//           // order.OrderAverageTradedPrice = LastTradedPrice;
//           order.OrderAverageTradedPrice = order.OrderPrice;
//           order.LastUpdateDateTime = formatDateToCustom(new Date().toISOString());

//           // Save Filled order to order book
//           orderbook.push(order);
//           saveOrderBook();

//           // Emit the order update via WebSocket
//           io.emit('orderUpdate', order);
//           logToFile(`Order Filled: ${JSON.stringify(order)}`);

//           // Prepare and emit trade update
//           const tradeUpdate = {
//             LoginID: order.LoginID || "XTS",
//             ClientID: order.ClientID || "XTSCLI",
//             AppOrderID: order.AppOrderID,
//             OrderReferenceID: order.OrderReferenceID || "",
//             GeneratedBy: order.GeneratedBy || "TWSAPI",
//             ExchangeOrderID: `EXCHANGE${Date.now()}`, // Generate a unique exchange order ID
//             OrderCategoryType: order.OrderCategoryType || "NORMAL",
//             ExchangeSegment: order.ExchangeSegment || "NSECM",
//             ExchangeInstrumentID: order.exchangeInstrumentID,
//             OrderSide: order.OrderSide,
//             OrderType: order.OrderType,
//             ProductType: order.ProductType || "NRML",
//             TimeInForce: order.TimeInForce || "DAY",
//             OrderPrice: order.OrderPrice,
//             OrderQuantity: order.OrderQuantity || 1,
//             OrderStopPrice: order.OrderStopPrice || 0,
//             OrderStatus: "Filled",
//             OrderAverageTradedPrice: LastTradedPrice,
//             LeavesQuantity: 0,
//             CumulativeQuantity: order.OrderQuantity || 1,
//             OrderDisclosedQuantity: order.OrderDisclosedQuantity || 0,
//             OrderGeneratedDateTime: order.OrderGeneratedDateTime || formatDateToCustom(new Date().toISOString()),
//             ExchangeTransactTimeAPI: formatDateToCustom(new Date().toISOString()),
//             LastUpdateDateTime: order.LastUpdateDateTime,
//             OrderUniqueIdentifier: order.OrderUniqueIdentifier || "454845",
//             OrderLegStatus: "SingleOrderLeg",
//             LastTradedPrice: LastTradedPrice,
//             LastTradedQuantity: order.OrderQuantity || 1,
//             LastExecutionTransactTime: formatDateToCustom(new Date().toISOString()),
//             ExecutionID: `EXEC${Date.now()}`, // Unique execution ID
//             ExecutionReportIndex: 3,
//             IsSpread: false,
//             MessageCode: 9005,
//             MessageVersion: 1,
//             TokenID: 0,
//             ApplicationType: 0,
//             SequenceNumber: 0
//           };

//           // Save to tradebook
//           tradebook.push(tradeUpdate);
//           saveTradeBook();

//           // Emit trade update on tradeSocket namespace
//           io.emit('tradeUpdate', tradeUpdate);
//           logToFile(`Trade update emitted: ${JSON.stringify(tradeUpdate)}`);

//           return false; // Remove from pending list
//         }
//         return true; // Keep order in pending list if not Filled
//       });
//     } else {
//       logToFile(`Invalid data received from marketSocket: ${JSON.stringify(data)}`);
//     }
//   } catch (error) {
//     logToFile(`Error parsing marketSocket data: ${error.message}`);
//   }
// });
marketSocket.on('message', (data) => {
  try {
    // Check if data and data.data are valid and is an array
    if (data && Array.isArray(data.data)) {
      // console.log("Processing market data...");
      
      data.data.forEach((entry) => {
        // Ensure entry contains OverallData
        if (entry && entry.OverallData) {
          const marketData = entry.OverallData;
          const { ExchangeInstrumentID, LastTradedPrice } = marketData;

          if (ExchangeInstrumentID !== undefined && LastTradedPrice !== undefined) {
            // Store the latest LastTradedPrice for each ExchangeInstrumentID
            latestLTPs[ExchangeInstrumentID] = LastTradedPrice;


            // Process pending order
            // console.log("pending orders", pendingOrders);
            pendingOrders = pendingOrders.filter((order) => {
              if (
                order.exchangeInstrumentID === ExchangeInstrumentID &&
                order.OrderSide.toLowerCase() === 'sell' &&
                LastTradedPrice <= order.OrderPrice // Check if price meets or goes below target
              ) {
                // If LTP has reached or is below the order price, execute the order
                console.log("pending orders", pendingOrders);
                order.OrderStatus = 'Filled';
                order.OrderAverageTradedPrice = order.OrderPrice;
                order.LastUpdateDateTime = formatDateToCustom(new Date().toISOString());

                // Save filled order to orderbook
                orderbook.push(order);
                saveOrderBook();

                // Emit the order update via WebSocket
                io.emit('orderUpdate', order);
                logToFile(`Order Filled: ${JSON.stringify(order)}`);

                // Prepare and emit trade update
                const tradeUpdate = {
                  LoginID: order.LoginID || "XTS",
                  ClientID: order.ClientID || "XTSCLI",
                  AppOrderID: order.AppOrderID,
                  OrderReferenceID: order.OrderReferenceID || "",
                  GeneratedBy: order.GeneratedBy || "TWSAPI",
                  ExchangeOrderID: `EXCHANGE${Date.now()}`, // Generate unique exchange order ID
                  OrderCategoryType: order.OrderCategoryType || "NORMAL",
                  ExchangeSegment: order.ExchangeSegment || "NSECM",
                  ExchangeInstrumentID: order.exchangeInstrumentID,
                  OrderSide: order.OrderSide,
                  OrderType: order.OrderType,
                  ProductType: order.ProductType || "NRML",
                  TimeInForce: order.TimeInForce || "DAY",
                  OrderPrice: order.OrderPrice,
                  OrderQuantity: order.OrderQuantity || 1,
                  OrderStopPrice: order.OrderStopPrice || 0,
                  OrderStatus: "Filled",
                  OrderAverageTradedPrice: LastTradedPrice,
                  LeavesQuantity: 0,
                  CumulativeQuantity: order.OrderQuantity || 1,
                  OrderDisclosedQuantity: order.OrderDisclosedQuantity || 0,
                  OrderGeneratedDateTime: order.OrderGeneratedDateTime || formatDateToCustom(new Date().toISOString()),
                  ExchangeTransactTimeAPI: formatDateToCustom(new Date().toISOString()),
                  LastUpdateDateTime: order.LastUpdateDateTime,
                  OrderUniqueIdentifier: order.OrderUniqueIdentifier || "454845",
                  OrderLegStatus: "SingleOrderLeg",
                  LastTradedPrice: LastTradedPrice,
                  LastTradedQuantity: order.OrderQuantity || 1,
                  LastExecutionTransactTime: formatDateToCustom(new Date().toISOString()),
                  ExecutionID: `EXEC${Date.now()}`, // Unique execution ID
                  ExecutionReportIndex: 3,
                  IsSpread: false,
                  MessageCode: 9005,
                  MessageVersion: 1,
                  TokenID: 0,
                  ApplicationType: 0,
                  SequenceNumber: 0,
                };

                // Save to tradebook
                tradebook.push(tradeUpdate);
                saveTradeBook();

                // Emit trade update on tradeSocket namespace
                io.emit('tradeUpdate', tradeUpdate);
                logToFile(`Trade update emitted: ${JSON.stringify(tradeUpdate)}`);

                return false; // Remove from pending orders
              }
              return true; // Keep order in pending list if not filled
            });
          }
        }
      });
    } else {
      logToFile(`Invalid data received from marketSocket: ${JSON.stringify(data)}`);
    }
  } catch (error) {
    logToFile(`Error parsing marketSocket data: ${error.message}`);
  }
});

// Handle WebSocket order placement from client
io.on('connection', (socket) => {
  console.log('Client connected to OrderSocket');
  // logToFile('Client connected to OrderSocket');

  socket.on('placeOrder', (orderParams) => {
    const { OrderType, OrderSide, exchangeInstrumentID, OrderPrice } = orderParams;
    logToFile(`Received placeOrder event: ${JSON.stringify(orderParams)}`);
    console.log(`Received placeOrder event: ${JSON.stringify(orderParams)}`);
    if (OrderType === 'Limit' && OrderSide === 'BUY') {
      const latestLTP = latestLTPs[exchangeInstrumentID];
  
      if (latestLTP !== undefined) {
        if (latestLTP <= OrderPrice) {
          // Execute immediately if LTP is below or equal to OrderPrice
          orderParams.OrderPrice = OrderPrice;
          orderParams.OrderStatus = 'Filled';
          orderParams.OrderAverageTradedPrice = OrderPrice;
          orderParams.LastUpdateDateTime = formatDateToCustom(new Date().toISOString());
          orderParams.OrderUniqueIdentifier = orderParams.OrderUniqueIdentifier || `UID-${Date.now()}`;
  
          // Emit detailed order update
          socket.emit('orderUpdate', {
            ...orderParams,
            OrderCategoryType: 'NORMAL',
            ExchangeOrderID: `EXCHANGE${Date.now()}`,
            ProductType: 'NRML',
            TimeInForce: 'DAY',
            OrderDisclosedQuantity: orderParams.OrderDisclosedQuantity || 0,
            LeavesQuantity: 0,
            CumulativeQuantity: orderParams.OrderQuantity || 1,
            OrderGeneratedDateTime: formatDateToCustom(new Date().toISOString()),
            ExchangeTransactTimeAPI: formatDateToCustom(new Date().toISOString()),
            LastTradedPrice: latestLTP,
            LastExecutionTransactTime: formatDateToCustom(new Date().toISOString()),
            ExecutionID: `EXEC${Date.now()}`,
            ExecutionReportIndex: 3,
            IsSpread: false,
            MessageCode: 9005,
            MessageVersion: 1,
            TokenID: 0,
            ApplicationType: 0,
            SequenceNumber: 0
          });
          logToFile(`Order Filled immediately: ${JSON.stringify(orderParams)}`);
        } else {
          // Set order to pending if LTP is above OrderPrice
          orderParams.OrderStatus = 'New';
          pendingOrders.push(orderParams);
  
          // Emit pending order with details
          socket.emit('orderUpdate', {
            ...orderParams,
            OrderCategoryType: 'NORMAL',
            ExchangeOrderID: `EXCHANGE${Date.now()}`,
            ProductType: 'NRML',
            TimeInForce: 'DAY',
            OrderDisclosedQuantity: orderParams.OrderDisclosedQuantity || 0,
            LeavesQuantity: orderParams.OrderQuantity || 1,
            CumulativeQuantity: 0,
            OrderGeneratedDateTime: formatDateToCustom(new Date().toISOString()),
            ExchangeTransactTimeAPI: null,
            LastTradedPrice: null,
            LastExecutionTransactTime: null,
            ExecutionID: null,
            ExecutionReportIndex: 0,
            IsSpread: false,
            MessageCode: 9005,
            MessageVersion: 1,
            TokenID: 0,
            ApplicationType: 0,
            SequenceNumber: 0
          });
          logToFile(`Order pending: ${JSON.stringify(orderParams)}`);
        }
      } else {
        logToFile(`No LTP available for instrument ID ${exchangeInstrumentID}`);
      }
    }
  });
  

  socket.on('disconnect', () => {
    console.log('Client disconnected from OrderSocket');
    // logToFile('Client disconnected from OrderSocket');
  });
});



app.post('/placeMarketOrder', (req, res) => {
  console.log("place market order invoked", req.body);
  try {
    const {
      exchangeInstrumentID,
      orderSide,
      orderQuantity,
      orderUniqueIdentifier,
    } = req.body;

    if (!exchangeInstrumentID || !orderSide || !orderQuantity || !orderUniqueIdentifier) {
      return res.status(400).json({ message: 'Missing required parameters.' });
    }

    if (orderSide.toUpperCase() !== 'BUY' && orderSide.toUpperCase() !== 'SELL') {
      return res.status(400).json({ message: 'Invalid orderSide. Must be either BUY or SELL.' });
    }

    const latestPrice = latestLTPs[exchangeInstrumentID];
    console.log(latestLTPs)
    if (latestPrice === undefined) {
      return res.status(400).json({ message: 'No latest price available for the given instrument ID.' });
    }

    // Generate AppOrderID
    const AppOrderID = `APP${Date.now()}`;

    // Create the market order object
    const marketOrder = {
      exchangeSegment: "NSEFO",
      productType: "NRML",
      orderType: "MARKET",
      timeInForce: "DAY",
      disclosedQuantity: 0,
      limitPrice: 0,
      stopPrice: 0,
      OrderUniqueIdentifier: orderUniqueIdentifier,
      AppOrderID, // Use generated AppOrderID
      exchangeInstrumentID,
      OrderSide: orderSide.toUpperCase(),
      OrderQuantity: orderQuantity,
      OrderPrice: latestPrice,
      OrderStatus: "Filled",
      OrderAverageTradedPrice: latestPrice,
      LastUpdateDateTime: formatDateToCustom(new Date().toISOString()),
    };

    // Save market order to order book
    orderbook.push(marketOrder);
    saveOrderBook();

    // Prepare trade update
    const tradeUpdate = {
      LoginID: "XTS",
      ClientID: "XTSCLI",
      AppOrderID, // Use generated AppOrderID
      OrderReferenceID: "",
      GeneratedBy: "TWSAPI",
      ExchangeOrderID: `EXCHANGE${Date.now()}`, // Unique ExchangeOrderID
      OrderCategoryType: "NORMAL",
      ExchangeSegment: "NSEFO",
      ExchangeInstrumentID: exchangeInstrumentID,
      OrderSide: orderSide.toUpperCase(),
      OrderType: "MARKET",
      ProductType: "NRML",
      TimeInForce: "DAY",
      OrderPrice: latestPrice,
      OrderQuantity: orderQuantity,
      OrderStopPrice: 0,
      OrderStatus: "Filled",
      OrderAverageTradedPrice: latestPrice,
      LeavesQuantity: 0,
      CumulativeQuantity: orderQuantity,
      OrderDisclosedQuantity: 0,
      OrderGeneratedDateTime: formatDateToCustom(new Date().toISOString()),
      ExchangeTransactTimeAPI: formatDateToCustom(new Date().toISOString()),
      LastUpdateDateTime: formatDateToCustom(new Date().toISOString()),
      OrderUniqueIdentifier: orderUniqueIdentifier,
      OrderLegStatus: "SingleOrderLeg",
      LastTradedPrice: latestPrice,
      LastTradedQuantity: orderQuantity,
      LastExecutionTransactTime: formatDateToCustom(new Date().toISOString()),
      ExecutionID: `EXEC${Date.now()}`, // Unique Execution ID
      ExecutionReportIndex: 3,
      IsSpread: false,
      MessageCode: 9005,
      MessageVersion: 1,
      TokenID: 0,
      ApplicationType: 0,
      SequenceNumber: 0,
    };

    // Save to tradebook
    tradebook.push(tradeUpdate);
    saveTradeBook();

    // Emit updates via WebSocket
    io.emit('orderUpdate', marketOrder);
    io.emit('tradeUpdate', tradeUpdate);

    logToFile(`Market ${orderSide} order placed and filled: ${JSON.stringify(marketOrder)}`);
    logToFile(`Trade update emitted: ${JSON.stringify(tradeUpdate)}`);
    marketOrder.AppOrderID = AppOrderID;
    res.status(200).json({
      message: `Market ${orderSide} order placed and filled successfully`,
      
      order: marketOrder,
      trade: tradeUpdate,
    });
  } catch (error) {
    console.error("Error placing market order:", error.message);
    res.status(500).json({ message: 'Error placing market order' });
  }
});


app.post('/placeOrder', (req, res) => {
  console.log("place order api is getting called");

  const orderParams = req.body;
  const { OrderType, OrderSide, exchangeInstrumentID, OrderPrice} = orderParams;
  console.log("orderParams:", orderParams);

  AppOrderID = orderParams.AppOrderID || Date.now();
  const latestLTP = latestLTPs[exchangeInstrumentID];

  if (OrderType.toUpperCase() === 'LIMIT') {
    // Common setup for both BUY and SELL
    orderParams.LoginID = "XTS";
    orderParams.ClientID = "SYMP1";
    orderParams.AppOrderID = orderParams.AppOrderID || Date.now();
    orderParams.OrderReferenceID = orderParams.OrderReferenceID || "";
    orderParams.GeneratedBy = orderParams.GeneratedBy || "TWSAPI";
    orderParams.ExchangeOrderID = orderParams.ExchangeOrderID || `EXCHANGE${Date.now()}`;
    orderParams.OrderCategoryType = orderParams.OrderCategoryType || "NORMAL";
    orderParams.ExchangeSegment = orderParams.ExchangeSegment || "NSECM";
    orderParams.ExchangeInstrumentID = orderParams.exchangeInstrumentID;
    orderParams.OrderSide = orderParams.OrderSide;
    orderParams.OrderType = orderParams.OrderType;
    orderParams.ProductType = orderParams.ProductType || "NRML";
    orderParams.TimeInForce = orderParams.TimeInForce || "DAY";
    orderParams.OrderQuantity = orderParams.OrderQuantity || 1;
    orderParams.OrderStopPrice = orderParams.OrderStopPrice || 0;
    orderParams.OrderDisclosedQuantity = orderParams.OrderDisclosedQuantity || 0;
    orderParams.OrderGeneratedDateTime = orderParams.OrderGeneratedDateTime || formatDateToCustom(new Date().toISOString());
    orderParams.LastUpdateDateTime = orderParams.LastUpdateDateTime || formatDateToCustom(new Date().toISOString());
    orderParams.OrderExpiryDate = orderParams.OrderExpiryDate || "01-01-1980 00:00:00";
    orderParams.CancelRejectReason = orderParams.CancelRejectReason || "";
    orderParams.OrderUniqueIdentifier = orderParams.OrderUniqueIdentifier || "454845";
    orderParams.OrderLegStatus = orderParams.OrderLegStatus || "SingleOrderLeg";
    orderParams.IsSpread = orderParams.IsSpread || false;
    orderParams.BoLegDetails = orderParams.BoLegDetails || 0;
    orderParams.BoEntryOrderId = orderParams.BoEntryOrderId || "";
    orderParams.MessageCode = orderParams.MessageCode || 9004;
    orderParams.MessageVersion = orderParams.MessageVersion || 4;
    orderParams.TokenID = orderParams.TokenID || 0;
    orderParams.ApplicationType = orderParams.ApplicationType || 0;
    orderParams.SequenceNumber = orderParams.SequenceNumber || 0;

    if (latestLTP !== undefined) {
      if (OrderSide.toUpperCase() === 'BUY') {
        // Logic for BUY orders
        orderParams.OrderPrice = latestLTP <= orderParams.OrderPrice ? orderParams.OrderPrice : 0;
        orderParams.OrderStatus = latestLTP <= orderParams.OrderPrice ? "Filled" : "New";
        orderParams.OrderAverageTradedPrice = latestLTP;
        orderParams.LeavesQuantity = latestLTP <= orderParams.OrderPrice ? 0 : orderParams.OrderQuantity || 1;
        orderParams.CumulativeQuantity = latestLTP <= orderParams.OrderPrice ? orderParams.OrderQuantity || 1 : 0;

        if (latestLTP <= OrderPrice) {
          // Execute immediately if LTP is below or equal to OrderPrice
          handleImmediateOrderExecution(orderParams, latestLTP, res, "BUY");
        } else {
          // Place order as pending
          handlePendingOrder(orderParams, res);
        }
      } else if (OrderSide.toUpperCase() === 'SELL') {
        // Logic for SELL orders
        orderParams.OrderPrice = latestLTP >= orderParams.OrderPrice ? orderParams.OrderPrice : 0;
        orderParams.OrderStatus = latestLTP >= orderParams.OrderPrice ? "Filled" : "New";
        orderParams.OrderAverageTradedPrice = latestLTP;
        orderParams.LeavesQuantity = latestLTP >= orderParams.OrderPrice ? 0 : orderParams.OrderQuantity || 1;
        orderParams.CumulativeQuantity = latestLTP >= orderParams.OrderPrice ? orderParams.OrderQuantity || 1 : 0;

        if (latestLTP >= OrderPrice) {
          // Execute immediately if LTP is above or equal to OrderPrice
          handleImmediateOrderExecution(orderParams, latestLTP, res, "SELL");
        } else {
          // Place order as pending
          handlePendingOrder(orderParams, res);
        }
      } else {
        res.status(400).json({ message: 'Only BUY and SELL Limit orders are supported.' });
        logToFile(`Invalid order side: ${JSON.stringify(orderParams)}`);
      }
    } else {
      res.status(400).json({ message: 'No LTP available for the given instrument ID.' });
      logToFile(`No LTP available for instrument ID ${exchangeInstrumentID}`);
    }
  } else {
    res.status(400).json({ message: 'Only LIMIT orders are supported.' });
    logToFile(`Invalid order type: ${JSON.stringify(orderParams)}`);
  }
});

// Helper functions
function handleImmediateOrderExecution(orderParams, latestLTP, res, side) {
  orderParams.LastUpdateDateTime = formatDateToCustom(new Date().toISOString());
  orderbook.push(orderParams);
  saveOrderBook();
  io.emit('orderUpdate', orderParams);
  logToFile(`Order Filled immediately via HTTP (${side}): ${JSON.stringify(orderParams)}`);

  // Trade update logic
  const tradeUpdate = prepareTradeUpdate(orderParams, latestLTP);
  tradebook.push(tradeUpdate);
  saveTradeBook();
  io.emit('tradeUpdate', tradeUpdate);
  logToFile(`Trade update emitted (${side}): ${JSON.stringify(tradeUpdate)}`);

  res.status(200).json({ message: `Order Filled immediately (${side})`, order: orderParams });
}

function handlePendingOrder(orderParams, res) {
  pendingOrders.push(orderParams);
  orderbook.push(orderParams);
  saveOrderBook();
  io.emit('orderUpdate', orderParams);
  logToFile(`Order pending via HTTP: ${JSON.stringify(orderParams)}`);
  res.status(200).json({ message: 'Order placed, waiting for market conditions.', order: orderParams });
}

function prepareTradeUpdate(orderParams, latestLTP) {
  return {
    LoginID: orderParams.LoginID || "XTS",
    ClientID: orderParams.ClientID || "XTSCLI",
    AppOrderID: orderParams.AppOrderID || Date.now(),
    OrderReferenceID: orderParams.OrderReferenceID || "",
    GeneratedBy: orderParams.GeneratedBy || "TWSAPI",
    ExchangeOrderID: `EXCHANGE${Date.now()}`,
    OrderCategoryType: orderParams.OrderCategoryType || "NORMAL",
    ExchangeSegment: orderParams.ExchangeSegment || "NSECM",
    ExchangeInstrumentID: orderParams.exchangeInstrumentID,
    OrderSide: orderParams.OrderSide,
    OrderType: orderParams.OrderType,
    ProductType: orderParams.ProductType || "NRML",
    TimeInForce: orderParams.TimeInForce || "DAY",
    OrderPrice: latestLTP,
    OrderQuantity: orderParams.OrderQuantity || 1,
    OrderStopPrice: orderParams.OrderStopPrice || 0,
    OrderStatus: "Filled",
    OrderAverageTradedPrice: latestLTP,
    LeavesQuantity: 0,
    CumulativeQuantity: orderParams.OrderQuantity || 1,
    OrderDisclosedQuantity: orderParams.OrderDisclosedQuantity || 0,
    OrderGeneratedDateTime: orderParams.OrderGeneratedDateTime || formatDateToCustom(new Date().toISOString()),
    ExchangeTransactTimeAPI: formatDateToCustom(new Date().toISOString()),
    LastUpdateDateTime: orderParams.LastUpdateDateTime,
    OrderUniqueIdentifier: orderParams.OrderUniqueIdentifier || "454845",
    OrderLegStatus: "SingleOrderLeg",
    LastTradedPrice: latestLTP,
    LastTradedQuantity: orderParams.OrderQuantity || 1,
    LastExecutionTransactTime: formatDateToCustom(new Date().toISOString()),
    ExecutionID: `EXEC${Date.now()}`,
    ExecutionReportIndex: 3,
    IsSpread: false,
    MessageCode: 9005,
    MessageVersion: 1,
    TokenID: 0,
    ApplicationType: 0,
    SequenceNumber: 0
  };
}
app.post('/modifyOrder', (req, res) => {
  const {
    appOrderID,
    modifiedProductType,
    modifiedOrderType,
    modifiedOrderQuantity,
    modifiedDisclosedQuantity,
    modifiedLimitPrice,
    modifiedStopPrice,
    modifiedTimeInForce,
    orderUniqueIdentifier,
  } = req.body;

  // Validate required parameters
  if (!appOrderID || !modifiedProductType || !modifiedOrderType || !modifiedOrderQuantity || 
      !modifiedLimitPrice || !modifiedStopPrice || !modifiedTimeInForce || !orderUniqueIdentifier) {
    return res.status(400).json({ message: 'Missing required parameters.' });
  }

  // Find the order in the order book
  const orderIndex = orderbook.findIndex(order => order.AppOrderID === appOrderID);
  if (orderIndex === -1) {
    return res.status(404).json({ message: 'Order not found.' });
  }

  const order = orderbook[orderIndex];

  // If order is already filled, modification is not allowed
  if (order.OrderStatus === 'Filled') {
    return res.status(400).json({ message: 'Cannot modify a filled order.' });
  }

  // Modify the order details
  order.ProductType = modifiedProductType;
  order.OrderType = modifiedOrderType;
  order.OrderQuantity = modifiedOrderQuantity;
  order.OrderDisclosedQuantity = modifiedDisclosedQuantity;
  order.OrderPrice = modifiedLimitPrice;
  order.OrderStopPrice = modifiedStopPrice;
  order.TimeInForce = modifiedTimeInForce;
  order.LastUpdateDateTime = formatDateToCustom(new Date().toISOString());

  // Check if the order is now market type
  if (modifiedOrderType === 'MARKET') {
    const latestLTP = latestLTPs[order.exchangeInstrumentID];
    if (latestLTP === undefined) {
      return res.status(400).json({ message: 'No latest price available for the given instrument ID.' });
    }

    // Convert to market and save to tradebook
    order.OrderStatus = 'Filled';
    order.OrderAverageTradedPrice = latestLTP;
    order.LeavesQuantity = 0;
    order.CumulativeQuantity = modifiedOrderQuantity;

    const tradeUpdate = {
      LoginID: order.LoginID,
      ClientID: order.ClientID,
      AppOrderID: order.AppOrderID,
      OrderReferenceID: order.OrderReferenceID,
      GeneratedBy: order.GeneratedBy,
      ExchangeOrderID: `EXCHANGE${Date.now()}`,
      OrderCategoryType: order.OrderCategoryType,
      ExchangeSegment: order.ExchangeSegment,
      ExchangeInstrumentID: order.exchangeInstrumentID,
      OrderSide: order.OrderSide,
      OrderType: order.OrderType,
      ProductType: order.ProductType,
      TimeInForce: order.TimeInForce,
      OrderPrice: latestLTP,
      OrderQuantity: order.OrderQuantity,
      OrderStopPrice: order.OrderStopPrice,
      OrderStatus: order.OrderStatus,
      OrderAverageTradedPrice: latestLTP,
      LeavesQuantity: 0,
      CumulativeQuantity: order.OrderQuantity,
      OrderDisclosedQuantity: order.OrderDisclosedQuantity,
      OrderGeneratedDateTime: order.OrderGeneratedDateTime,
      ExchangeTransactTimeAPI: formatDateToCustom(new Date().toISOString()),
      LastUpdateDateTime: order.LastUpdateDateTime,
      OrderUniqueIdentifier: orderUniqueIdentifier,
      OrderLegStatus: 'SingleOrderLeg',
      LastTradedPrice: latestLTP,
      LastTradedQuantity: order.OrderQuantity,
      LastExecutionTransactTime: formatDateToCustom(new Date().toISOString()),
      ExecutionID: `EXEC${Date.now()}`,
      ExecutionReportIndex: 3,
      IsSpread: false,
      MessageCode: 9005,
      MessageVersion: 1,
      TokenID: 0,
      ApplicationType: 0,
      SequenceNumber: 0,
    };

    tradebook.push(tradeUpdate);
    saveTradeBook();
    io.emit('tradeUpdate', tradeUpdate);
    logToFile(`Trade update emitted: ${JSON.stringify(tradeUpdate)}`);
  }

  // Save the modified order
  orderbook[orderIndex] = order;
  saveOrderBook();

  io.emit('orderUpdate', order);
  logToFile(`Order modified: ${JSON.stringify(order)}`);
  res.status(200).json({ message: 'Order modified successfully.', order });
});

// app.post('/placeOrder', (req, res) => {
//   console.log("place order api is getting called");

//   const orderParams = req.body;
//   const { OrderType, OrderSide, exchangeInstrumentID, OrderPrice } = orderParams;
//   console.log("orderParams:", orderParams)

//   AppOrderID = orderParams.AppOrderID || Date.now()
//   if (OrderType.toUpperCase() === 'LIMIT' && OrderSide.toUpperCase() === 'BUY') {
//     const latestLTP = latestLTPs[exchangeInstrumentID];
//     orderParams.LoginID = "XTS";
//     orderParams.ClientID = "SYMP1";
//     orderParams.AppOrderID = orderParams.AppOrderID || Date.now();
//     orderParams.OrderReferenceID = orderParams.OrderReferenceID || "";
//     orderParams.GeneratedBy = orderParams.GeneratedBy || "TWSAPI";
//     orderParams.ExchangeOrderID = orderParams.ExchangeOrderID || `EXCHANGE${Date.now()}`;
//     orderParams.OrderCategoryType = orderParams.OrderCategoryType || "NORMAL";
//     orderParams.ExchangeSegment = orderParams.ExchangeSegment || "NSECM";
//     orderParams.ExchangeInstrumentID = orderParams.exchangeInstrumentID;
//     orderParams.OrderSide = orderParams.OrderSide;
//     orderParams.OrderType = orderParams.OrderType;
//     orderParams.ProductType = orderParams.ProductType || "NRML";
//     orderParams.TimeInForce = orderParams.TimeInForce || "DAY";
//     orderParams.OrderPrice = latestLTP <= orderParams.OrderPrice ? orderParams.OrderPrice : 0;
//     orderParams.OrderQuantity = orderParams.OrderQuantity || 1;
//     orderParams.OrderStopPrice = orderParams.OrderStopPrice || 0;
//     orderParams.OrderStatus = latestLTP <= orderParams.OrderPrice ? "Filled" : "New";
//     orderParams.OrderAverageTradedPrice = latestLTP;
//     orderParams.LeavesQuantity = latestLTP <= orderParams.OrderPrice ? 0 : orderParams.OrderQuantity || 1;
//     orderParams.CumulativeQuantity = latestLTP <= orderParams.OrderPrice ? orderParams.OrderQuantity || 1 : 0;
//     orderParams.OrderDisclosedQuantity = orderParams.OrderDisclosedQuantity || 0;
//     orderParams.OrderGeneratedDateTime = orderParams.OrderGeneratedDateTime || formatDateToCustom(new Date().toISOString());
//     orderParams.ExchangeTransactTimeAPI = latestLTP <= orderParams.OrderPrice ? formatDateToCustom(new Date().toISOString()) : "";
//     orderParams.LastUpdateDateTime = orderParams.LastUpdateDateTime || formatDateToCustom(new Date().toISOString());
//     orderParams.OrderExpiryDate = orderParams.OrderExpiryDate || "01-01-1980 00:00:00";
//     orderParams.CancelRejectReason = orderParams.CancelRejectReason || "";
//     orderParams.OrderUniqueIdentifier = orderParams.OrderUniqueIdentifier || "454845";
//     orderParams.OrderLegStatus = orderParams.OrderLegStatus || "SingleOrderLeg";
//     orderParams.IsSpread = orderParams.IsSpread || false;
//     orderParams.BoLegDetails = orderParams.BoLegDetails || 0;
//     orderParams.BoEntryOrderId = orderParams.BoEntryOrderId || "";
//     orderParams.MessageCode = orderParams.MessageCode || 9004;
//     orderParams.MessageVersion = orderParams.MessageVersion || 4;
//     orderParams.TokenID = orderParams.TokenID || 0;
//     orderParams.ApplicationType = orderParams.ApplicationType || 0;
//     orderParams.SequenceNumber = orderParams.SequenceNumber || 0;


//     if (latestLTP !== undefined) {
//       if (latestLTP <= OrderPrice) {
//         // Execute immediately if LTP is below or equal to OrderPrice
//         orderParams.OrderStatus = 'Filled';
//         orderParams.OrderPrice = OrderPrice;
//         orderParams.OrderAverageTradedPrice = latestLTP;
//         orderParams.LastUpdateDateTime = formatDateToCustom(new Date().toISOString());

//         orderbook.push(orderParams);
//         saveOrderBook();
//         io.emit('orderUpdate', orderParams);
//         console.log("this placeOrder is getting called");
//         logToFile(`Order Filled immediately via HTTP: ${JSON.stringify(orderParams)}`);

//         // Prepare trade update
//         const tradeUpdate = {
//           LoginID: orderParams.LoginID || "XTS",
//           ClientID: orderParams.ClientID || "XTSCLI",
//           AppOrderID: orderParams.AppOrderID || Date.now(),
//           OrderReferenceID: orderParams.OrderReferenceID || "",
//           GeneratedBy: orderParams.GeneratedBy || "TWSAPI",
//           ExchangeOrderID: `EXCHANGE${Date.now()}`, // Unique ExchangeOrderID
//           OrderCategoryType: orderParams.OrderCategoryType || "NORMAL",
//           ExchangeSegment: orderParams.ExchangeSegment || "NSECM",
//           ExchangeInstrumentID: exchangeInstrumentID,
//           OrderSide: OrderSide,
//           OrderType: OrderType,
//           ProductType: orderParams.ProductType || "NRML",
//           TimeInForce: orderParams.TimeInForce || "DAY",
//           OrderPrice: latestLTP,
//           OrderQuantity: orderParams.OrderQuantity || 1,
//           OrderStopPrice: orderParams.OrderStopPrice || 0,
//           OrderStatus: "Filled",
//           OrderAverageTradedPrice: latestLTP,
//           LeavesQuantity: 0,
//           CumulativeQuantity: orderParams.OrderQuantity || 1,
//           OrderDisclosedQuantity: orderParams.OrderDisclosedQuantity || 0,
//           OrderGeneratedDateTime: orderParams.OrderGeneratedDateTime || formatDateToCustom(new Date().toISOString()),
//           ExchangeTransactTimeAPI: formatDateToCustom(new Date().toISOString()),
//           LastUpdateDateTime: orderParams.LastUpdateDateTime,
//           OrderUniqueIdentifier: orderParams.OrderUniqueIdentifier || "454845",
//           OrderLegStatus: "SingleOrderLeg",
//           LastTradedPrice: latestLTP,
//           LastTradedQuantity: orderParams.OrderQuantity || 1,
//           LastExecutionTransactTime: formatDateToCustom(new Date().toISOString()),
//           ExecutionID: `EXEC${Date.now()}`, // Unique Execution ID
//           ExecutionReportIndex: 3,
//           IsSpread: false,
//           MessageCode: 9005,
//           MessageVersion: 1,
//           TokenID: 0,
//           ApplicationType: 0,
//           SequenceNumber: 0
//         };

//         // Save to tradebook
//         tradebook.push(tradeUpdate);
//         saveTradeBook();

//         // Emit trade update on tradeSocket namespace
//         io.emit('tradeUpdate', tradeUpdate);
//         console.log("trades updated")
//         logToFile(`Trade update emitted: ${JSON.stringify(tradeUpdate)}`);

//         res.status(200).json({ message: 'Order Filled immediately', order: orderParams });
//       } else {
//         // Set order to pending if LTP is above OrderPrice
//         orderParams.OrderStatus = 'New';
//         pendingOrders.push(orderParams);

//         orderbook.push(orderParams);
//         saveOrderBook();
//         io.emit('orderUpdate', orderParams);
//         res.status(200).json({ message: 'Order placed, waiting for market conditions.', order: orderParams });
//         logToFile(`Order pending via HTTP: ${JSON.stringify(orderParams)}`);
//       }
//     } else {
//       res.status(400).json({ message: 'No LTP available for the given instrument ID.' });
//       logToFile(`No LTP available for instrument ID ${exchangeInstrumentID}`);
//     }
//   } else {
//     res.status(400).json({ message: 'Only BUY Limit orders are supported.' });
//     logToFile(`Invalid order type or side: ${JSON.stringify(orderParams)}`);
//   }
// });


app.get('/orders', (req, res) => {
  try {
    const data = fs.readFileSync('orderbook.json', 'utf-8');
    res.status(200).json({results: JSON.parse(data)});
  } catch (err) {
    console.error("Error reading orderbook.json:", err.message);
    res.status(500).json({ message: "Error reading order book" });
  }
});
app.post('/dummyorder', (req, res) =>{
  console.log("order placed");
});




app.post('/cancelOrders', (req, res) => {
  const { ExchangeSegment, ExchangeInstrumentID } = req.body;

  // Filter out orders that are not `New` or do not match the cancellation criteria
  const filteredOrders = orderbook.filter(order => {
    if (order.OrderStatus !== 'New') {
      return true; // Keep orders that are not `New`
    }
    if (ExchangeInstrumentID === 0) {
      return false; // Cancel all `New` orders
    }
    return order.ExchangeSegment !== ExchangeSegment || order.ExchangeInstrumentID !== ExchangeInstrumentID;
  });

  orderbook = filteredOrders;
  saveOrderBook();

  logToFile(`Canceled orders with status 'New' for ExchangeSegment: ${ExchangeSegment}, ExchangeInstrumentID: ${ExchangeInstrumentID}`);
  res.status(200).json({ message: 'Canceled orders with status `New` successfully' });
});





app.post('/placeSLOrder', (req, res) => {
  console.log("calling placeSLOrder API");

  const {
    exchangeInstrumentID,
    orderSide,
    orderQuantity,
    limitPrice,
    stopPrice,
    orderUniqueIdentifier,
  } = req.body;

  // Validate required parameters
  if (!exchangeInstrumentID || !orderSide || !orderQuantity || !limitPrice || !stopPrice || !orderUniqueIdentifier) {
    return res.status(400).json({ message: 'Missing required parameters.' });
  }

  // Generate AppOrderID
  const AppOrderID = `APP${Date.now()}`;

  // Create the Stop-Limit order object
  const slOrder = {
    exchangeInstrumentID,
    OrderSide: orderSide,
    OrderQuantity: orderQuantity,
    OrderType: 'StopLimit',
    OrderStatus: 'New', 
    OrderPrice: limitPrice,
    OrderStopPrice: stopPrice,
    OrderUniqueIdentifier: orderUniqueIdentifier,
    AppOrderID, // Include the generated AppOrderID
    LastUpdateDateTime: formatDateToCustom(new Date().toISOString()),
    OrderGeneratedDateTime: formatDateToCustom(new Date().toISOString()),
  };

  console.log("Stop-Limit order placed:", slOrder);

  pendingOrders.push(slOrder);
  orderbook.push(slOrder);
  saveOrderBook();

  io.emit('orderUpdate', slOrder);
  logToFile(`Stop-Limit order placed: ${JSON.stringify(slOrder)}`);

  res.status(200).json({
    message: 'Stop-Limit order placed successfully',
    order: slOrder,
  });
});
server.listen(8050, () => {
  console.log('OrderSocket server running on port 8050');
  // logToFile('OrderSocket server running on port 8050');
});