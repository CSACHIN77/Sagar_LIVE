# import mysql.connector
# import os
# import pandas as pd
# import warnings
# from datetime import datetime
# import re
# class IndexCreator:
#     def __init__(self, db_config):
#         self.db_config = db_config
#         self.db_connection = None

#     def connect_to_database(self):
#         self.db_connection = mysql.connector.connect(**self.db_config)

#     def close_database_connection(self):
#         if self.db_connection:
#             self.db_connection.close()

#     def create_indices(self):
#         if self.db_connection:
#             cursor = self.db_connection.cursor()
#             try:
#                 cursor.execute("SHOW TABLES;")
#                 tables = [table[0] for table in cursor.fetchall()]
#                 for table in tables:
#                     if table != 'upload_status':
#                         self.create_index(cursor, table, 'timestamp')
#                         self.create_index(cursor, table, 'symbol')
#                         self.create_index(cursor, table, 'type')
#             except mysql.connector.Error as err:
#                 print(f"Error creating indices: {err}")
#             finally:
#                 cursor.close()
#                 self.db_connection.close()

#     def create_index(self, cursor, table_name, column_name):
#         index_name = f"idx_{table_name}_{column_name}"
#         try:
#             cursor.execute(f"CREATE INDEX {index_name} ON {table_name}({column_name})")
#             print(f"Index '{index_name}' created on column '{column_name}' in table '{table_name}'.")
#         except mysql.connector.Error as err:
#             print(f"Error creating index on column '{column_name}' in table '{table_name}': {err}")


# class DataProcessor:
#     def __init__(self, directory_paths, db_config):
#         self.directory_paths = directory_paths
#         self.db_config = db_config
#         self.error_log_file = "error_log.txt"
#         self.db_connection = None  
#         self.total_files_processed = 0
#         self.total_files_uploaded = 0
#         self.total_rows_updated = 0
#         self.df_count = 0

#     def connect_to_database(self):
#         self.db_connection = mysql.connector.connect(**self.db_config)

#     def close_database_connection(self):
#         if self.db_connection:
#             self.db_connection.close()

#     def count_and_list_tables(self):
#         cursor = self.db_connection.cursor()
#         cursor.execute("SHOW TABLES")
#         tables = cursor.fetchall()
#         table_count = len(tables)
#         table_names = [table[0] for table in tables]
#         return table_count, table_names

#     def create_upload_status_table(self):
#         if self.db_connection:
#             cursor = self.db_connection.cursor()
#             cursor.execute('''CREATE TABLE IF NOT EXISTS upload_status (
#                                 id INT AUTO_INCREMENT PRIMARY KEY,
#                                 file_name VARCHAR(255),
#                                 upload_count INT,
#                                 total_files_processed INT,
#                                 status BOOLEAN,
#                                 remarks TEXT,
#                                 upload_time DATETIME
#                             )''')
#             self.db_connection.commit()

#     def check_upload_status(self, file_name):
#         if self.db_connection:
#             cursor = self.db_connection.cursor()
#             cursor.execute("SELECT status FROM upload_status WHERE file_name=%s", (file_name,))
#             result = cursor.fetchone()
#             return result[0] if result else None
#         return None

#     def update_upload_status(self, file_name, upload_count, total_files_processed, status, remarks, upload_time):
#         if self.db_connection:
#             cursor = self.db_connection.cursor()
#             cursor.execute("INSERT INTO upload_status (file_name, upload_count, total_files_processed, status, remarks, upload_time) VALUES (%s, %s, %s, %s, %s, %s)", 
#                            (file_name, upload_count, total_files_processed, status, remarks, upload_time))
#             self.db_connection.commit()

#     def check_format(self, file_path):
#         return True 

#     def read_csv(self, file_path):
#         return pd.read_csv(file_path)

#     def process_data(self, force_upload=False):
#         with open(self.error_log_file, "a") as error_log:
#             for directory_path in self.directory_paths:
#                 for month_dir in os.listdir(directory_path):
#                     month_dir_path = os.path.join(directory_path, month_dir)
#                     if os.path.isdir(month_dir_path):
#                         for file_name in os.listdir(month_dir_path):
#                             if file_name.endswith('.csv'):
#                                 self.total_files_processed += 1
#                                 file_path = os.path.join(month_dir_path, file_name)
#                                 upload_status = self.check_upload_status(file_name)
#                                 if (upload_status is None or not upload_status) or force_upload:
#                                     print(f"Reading file: {file_path}")
#                                     try:
#                                         if self.check_format(file_path):
#                                             df = self.read_csv(file_path)
#                                             df.columns = df.columns.str.replace(' ', '')
#                                             df = df.rename(columns={
#                                                 'Ticker': 'symbol',
#                                                 'Date': 'date',
#                                                 'Time': 'time',
#                                                 'Open': 'open',
#                                                 'High': 'high',
#                                                 'Low': 'low',
#                                                 'Close': 'close',
#                                                 'Volume': 'volume',
#                                                 'OpenInterest': 'oi'
#                                             })
#                                             timestamp_pattern = r'\d{2}/\d{2}/\d{4}'

#                                             if df['date'].str.match(timestamp_pattern).any():
#                                                 df['timestamp'] = df['date'] + ' ' + df['time']
#                                                 df['timestamp'] = pd.to_datetime(df['timestamp'], format='%d/%m/%Y %H:%M:%S')
                                            
#                                             else:
#                                                 df['timestamp'] = df.date + ' ' + df.time
#                                                 df['timestamp'] = pd.to_datetime(df['timestamp'], format='%d-%m-%Y %H:%M:%S')
#                                             df['timestamp'] = df['timestamp'].dt.floor('min')
                                            
#                                             df.drop(columns=['time','date'], inplace=True)
#                                             df.columns = map(str.lower, df.columns)
#                                             self.process_dataframe(df, file_path, force_upload)
#                                             if force_upload:
#                                                 self.update_upload_status(os.path.basename(file_path), self.df_count, self.total_rows_updated, True, "File reuploaded successfully.", datetime.now())

#                                     except Exception as e:
#                                         error_log.write(f"Error processing file {file_path}: {str(e)}, process_data block\n")
#                                         self.update_upload_status(file_name, self.df_count, self.total_rows_updated, False, str(e), datetime.now())
#                                 else:
#                                     print(f"Skipping file {file_name}: Already uploaded.")
#                                     self.update_upload_status(file_name, 0, 0, False, "File already uploaded.", datetime.now())
#                                     self.total_files_uploaded += 1
#                             else:
#                                 error_log.write(f"File format mismatch: {file_path}\n")

#         print(f"Total files processed: {self.total_files_processed}")
#         print(f"Total files uploaded: {self.total_files_uploaded}")

#     def extract_symbol_details(self, input_string):
#         pattern = re.compile(r'(.+?)(\d{2}[A-Z]{3}\d{2})(.+)')
#         match = pattern.search(input_string)
#         if match:
#             instrument_symbol = match.group(1).strip().replace('-', '_').replace('&', '_')  
#             strike_type = match.group(3).strip()
#             strike_type = strike_type[:-4]
#             strike = strike_type[:-2]
#             type_ = strike_type[-2:]
#             matched_date = match.group(2)
#             date_object = datetime.strptime(matched_date, '%d%b%y').date()
#             if strike=='F':
#                 strike=None
#                 type_='FUT'
                
#         else:
#             pattern = re.compile(r'^(.+?)-(I{1,3})\.NFO$')
#             match = pattern.match(input_string)
#             instrument_symbol = match.group(1).replace('-', '_').replace('&', '_')  
#             date_object = match.group(2)
#             type_ = 'FUT'
#             strike = None
#         return instrument_symbol, date_object, strike, type_

#     def process_dataframe(self, df, file_path, force_upload=False):
#         try:
#             df[['instrument_symbol', 'expiry', 'strike', 'type']] = df['symbol'].apply(
#                 lambda x: pd.Series(self.extract_symbol_details(x)))
#             df.reset_index(drop=True, inplace=True)
#             futures_data = df
#             self.df_count = len(df)
#             if force_upload:
#                 self.delete_existing_data(file_path, df)
#             self.insert_data_to_database(futures_data, file_name=file_path)
#             if not force_upload:
#                 self.update_upload_status(os.path.basename(file_path), self.df_count, self.total_rows_updated, True, "File uploaded successfully.", datetime.now())
#             self.total_files_uploaded += 1
#         except Exception as e:
#             with open(self.error_log_file, "a") as error_log:
#                 error_log.write(f"Error processing DataFrame: {str(e)} in {file_path}, process block\n")
#                 print(f'Error processing DataFrame: {str(e)} in {file_path}, process block\n')
#                 self.update_upload_status(os.path.basename(file_path), self.df_count, self.total_rows_updated, False, "File couldn't upload.", datetime.now())

#     def insert_data_to_database(self, df, file_name):
#         try:
#             self.total_rows_updated = 0
#             if self.db_connection:
#                 cursor = self.db_connection.cursor()
#                 for instrument_symbol, symbol_data in df.groupby('instrument_symbol'):
#                     year = re.search(r'(\d{4})', file_name).group(1)
#                     table_name = f"{instrument_symbol}_{year}"
                    
#                     cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
#                     table_exists = cursor.fetchone()
                    
#                     if not table_exists:
#                         cursor.execute(f'''CREATE TABLE IF NOT EXISTS {table_name} (
#                                             id INT AUTO_INCREMENT PRIMARY KEY,
#                                             timestamp DATETIME,
#                                             symbol VARCHAR(40),
#                                             expiry DATE,
#                                             type VARCHAR(4),
#                                             strike FLOAT,
#                                             open FLOAT,
#                                             high FLOAT,
#                                             low FLOAT,
#                                             close FLOAT,
#                                             oi INT,
#                                             volume INT,
#                                             provider VARCHAR(100),
#                                             upload_time DATETIME,
#                                             implied_futures_weekly FLOAT,
#                                             implied_futures_monthly FLOAT
#                                         )''')
#                         self.db_connection.commit()
                    
#                     rows_updated = 0 
#                     for index, row in symbol_data.iterrows():
#                         timestamp_str = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
#                         expiry = row['expiry']
                        
#                         if expiry in ['I', 'II', 'III']:
#                             fut_table_name = f"{instrument_symbol}_FUT"
#                             cursor.execute(f"SHOW TABLES LIKE '{fut_table_name}'")
#                             table_exists = cursor.fetchone()
#                             if not table_exists:
#                                 cursor.execute(f'''CREATE TABLE IF NOT EXISTS {fut_table_name} (
#                                             id INT AUTO_INCREMENT PRIMARY KEY,
#                                             timestamp DATETIME,
#                                             symbol VARCHAR(40),
#                                             expiry VARCHAR(3),
#                                             type VARCHAR(40),
#                                             strike FLOAT,
#                                             open FLOAT,
#                                             high FLOAT,
#                                             low FLOAT,
#                                             close FLOAT,
#                                             oi INT,
#                                             volume INT,
#                                             provider VARCHAR(100),
#                                             upload_time DATETIME,
#                                             implied_futures_weekly FLOAT,
#                                             implied_futures_monthly FLOAT
#                                         )''')
#                                 self.db_connection.commit()
#                                 cursor.execute(f"INSERT INTO {fut_table_name} (timestamp, symbol, expiry, type, strike, open, high, low, close, oi, volume, provider, upload_time, implied_futures_weekly, implied_futures_monthly) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
#                                         (timestamp_str, row['symbol'], expiry, row['type'], row['strike'],
#                                             row['open'], row['high'], row['low'], row['close'], row['oi'], row['volume'],
#                                             os.path.basename(file_name), datetime.now(), None, None))
#                             else:
#                                 cursor.execute(f"INSERT INTO {fut_table_name} (timestamp, symbol, expiry, type, strike, open, high, low, close, oi, volume, provider, upload_time, implied_futures_weekly, implied_futures_monthly) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
#                                         (timestamp_str, row['symbol'], expiry, row['type'], row['strike'],
#                                             row['open'], row['high'], row['low'], row['close'], row['oi'], row['volume'],
#                                             os.path.basename(file_name), datetime.now(), None, None))
#                         else:
#                             cursor.execute(f'''INSERT INTO {table_name} 
#                                                 (timestamp, symbol, expiry, type, strike, open, high, low, close, oi, volume, provider, upload_time, implied_futures_weekly, implied_futures_monthly) 
#                                                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
#                                         (timestamp_str, row['symbol'], expiry, row['type'], row['strike'],
#                                             row['open'], row['high'], row['low'], row['close'], row['oi'], row['volume'],
#                                             os.path.basename(file_name), datetime.now(), None, None))
#                         rows_updated += cursor.rowcount
#                     self.total_rows_updated += rows_updated
#                 self.db_connection.commit()
#         except Exception as e:
#             print(f'error occured in {row['instrument_symbol']}, str{e}, -----{row['type']}----, end of sentence ')


#     def delete_existing_data(self, file_path, df):
#         if self.db_connection:
#             file_name = os.path.basename(file_path)
#             cursor = self.db_connection.cursor()
#             for instrument_symbol, symbol_data in df.groupby('instrument_symbol'):
#                 year = re.search(r'(\d{4})', file_path).group(1)
#                 table_name = f"{instrument_symbol}_{year}"
#                 cursor.execute(f"SELECT * FROM {table_name} WHERE provider=%s", (file_name,))
#                 deleted_rows = cursor.fetchall()
#                 cursor.execute(f"DELETE FROM {table_name} WHERE provider=%s", (file_name,))
#             self.db_connection.commit()

#     def preprocess_data(self, force_upload=False):
#         self.connect_to_database()
#         self.create_upload_status_table()
#         self.process_data(force_upload)
#         self.close_database_connection() 

   
# directory_paths = [
#     r'C:\Users\pegas\OneDrive\Desktop\vision\2021',
#     r'C:\Users\pegas\OneDrive\Desktop\vision\2020'
   
# ]
# db_config = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': 'pegasus',
# }
# connection = mysql.connector.connect(**db_config)
# cursor = connection.cursor()

# cursor.execute("CREATE DATABASE IF NOT EXISTS index_data")

# cursor.close()
# connection.close()
# db_config['database'] = 'index_data'
# index_processor = DataProcessor(directory_paths, db_config)
# index_processor.preprocess_data(force_upload=False)

# index_creator = IndexCreator(db_config)
# index_creator.connect_to_database()
# index_creator.create_indices()
# index_creator.close_database_connection()
