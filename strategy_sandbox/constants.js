module.exports = {
    host: 'localhost',
    user: 'root',
    password: 'pegasus',
    database: 'sagar_dataharvesting',
    table_name: 'data_harvesting_20241114',
    MODE: 'database_time', // database_time or 'data_per_minute'
    DATA_PER_MINUTE: 0,   // Only used if MODE is 'data_per_minute'
  };
  