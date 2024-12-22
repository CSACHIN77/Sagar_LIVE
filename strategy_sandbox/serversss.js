require('dotenv').config();
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const mysql = require('mysql2/promise');
const fs = require('fs');
const path = require('path');

// Constants and configurations
const PORT = 5001;
const {
  host,
  user,
  password,
  database,
  table_name: TABLE_NAME,
  MODE,
  DATA_PER_MINUTE
} = require('./constants');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, { cors: { origin: "*" } });
const LAST_ID_FILE = path.join(__dirname, 'last_id.txt');

// Database pool configuration
const pool = mysql.createPool({
  host,
  user,
  password,
  database,
  waitForConnections: true,
  connectionLimit: 5,
  queueLimit: 0,
  charset: 'utf8mb4'
});

// Function to read the last processed ID
const readLastId = () => fs.existsSync(LAST_ID_FILE) ? parseInt(fs.readFileSync(LAST_ID_FILE, 'utf-8')) : 0;

// Function to write the last processed ID
const writeLastId = (lastId) => fs.writeFileSync(LAST_ID_FILE, String(lastId));

// Handle Socket.io connection
io.on('connection', (socket) => {
  console.log('Client connected');
  socket.emit('message', { data: 'Connected to server' });

  socket.on('disconnect', () => {
    console.log('Client disconnected');
  });
});

// Function to convert UNIX timestamp to GMT date
const convertToGMT = (timestamp) => new Date(timestamp * 1000).toISOString();

// Function to log batch information
const logBatchInfo = (batch, timestamp) => {
  console.log('\n==== New Batch Pushed ====');
  console.log(`Timestamp: ${convertToGMT(timestamp)} GMT`);
  const currentTime = new Date().toLocaleString();
  console.log(`Current Time: ${currentTime}`);

  console.log(`Batch Size: ${batch.length} records`);
  console.log(`ID Range: ${batch[0].id} to ${batch[batch.length - 1].id}`);
  // console.log('First record in batch:', batch[0]);
  // console.log('Last record in batch:', batch[batch.length - 1]);
  console.log('========================\n');
};

// Fetch and push data based on `database_time` mode
const pushDataInRealTime = async () => {
  let lastId = readLastId();

  while (true) {
    try {
      const query = `SELECT id, OverallData, LastUpdateTime FROM ${TABLE_NAME} WHERE id > ${lastId} ORDER BY LastUpdateTime ASC LIMIT 1000000`;
      const conn = await pool.getConnection();
      // Log the complete query
      // console.log('Executing query:', query);

      // Execute the query
      const [rows] = await conn.query(query);
     
      // const query = `SELECT id, OverallData FROM ${TABLE_NAME} ORDER BY LastUpdateTime LIMIT 100000`;
      // console.log('Executing query:', query); // Log the query and parameters
  
      // const [rows] = await conn.query(
      //   `SELECT id, OverallData, LastUpdateTime FROM ${TABLE_NAME} WHERE id > ? ORDER BY LastUpdateTime ASC LIMIT 100000`, [lastId]
      // );
      
      conn.release();

      let i = 0;
      while (i < rows.length) {
        const batch = [];
        const row = rows[i];
        const currentOverallData = row.OverallData;
        const currentLastUpdateTime = currentOverallData.LastUpdateTime;

        // Collect all rows with the same LastUpdateTime
        while (i < rows.length) {
          const row = rows[i];
          const overallData = row.OverallData;
          if (overallData.LastUpdateTime === currentLastUpdateTime) {
            batch.push({
              id: row.id,
              OverallData: overallData
            });
            i++;
          } else {
            break;
          }
        }

        // Emit the batch and log information
        console.log(batch);
        io.emit('message', { data: batch });
        logBatchInfo(batch, currentLastUpdateTime);

        // Update lastId after processing the batch
        writeLastId(batch[batch.length - 1].id);
        lastId = batch[batch.length - 1].id;

        // Calculate time difference to the next batch
        if (i < rows.length) {
          const nextOverallData = rows[i].OverallData;
          const nextLastUpdateTime = nextOverallData.LastUpdateTime;
          const timeDifference = (nextLastUpdateTime - currentLastUpdateTime) * 1000;
          
          console.log(`Waiting ${timeDifference}ms for next batch...\n`);
          // Wait for the time difference
          await new Promise(resolve => setTimeout(resolve, timeDifference));
        }
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  }
};

// Fetch and push data based on `data_per_minute` mode
const pushDataPerMinute = async (dataPerMinute) => {
  let lastId = readLastId();
  const intervalPerData = (60 * 1000) / dataPerMinute;

  while (true) {
    try {
      const conn = await pool.getConnection();
      const [rows] = await conn.query(
        `SELECT id, OverallData FROM ${TABLE_NAME} WHERE id > ? ORDER BY id ASC`, [lastId]
      );
      conn.release();

      for (const row of rows) {
        const overallData = JSON.parse(row.OverallData);
        const lastUpdateTime = overallData.LastUpdateTime;

        // Create a single-item batch for consistency in logging
        const batch = [{
          id: row.id,
          OverallData: overallData
        }];

        io.emit('message', { data: row });
        logBatchInfo(batch, lastUpdateTime);

        writeLastId(row.id);
        lastId = row.id;

        console.log(`Waiting ${intervalPerData}ms before next data point...\n`);
        await new Promise(resolve => setTimeout(resolve, intervalPerData));
      }
    } catch (error) {
      console.error('Error polling database:', error);
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  }
};

// Start the server based on the selected mode
server.listen(PORT, () => {
  console.log(`Socket.IO server running at http://localhost:${PORT}/`);
  console.log(`Mode selected: ${MODE}`);
  
  if (MODE === 'database_time') {
    pushDataInRealTime();
  } else if (MODE === 'data_per_minute') {
    pushDataPerMinute(DATA_PER_MINUTE);
  } else {
    console.error('Invalid MODE selected. Choose either "database_time" or "data_per_minute".');
  }
});