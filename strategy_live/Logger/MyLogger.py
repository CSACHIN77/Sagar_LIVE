import os
import sys
from datetime import datetime, timedelta
from utils import get_path

sys.path.append(get_path('Sagar_common'))


try:
    from common_function import fetch_parameter
except ImportError as e:
    print(f"Error importing 'fetch_parameter': {e}")

environment = "dev"
log_settings = fetch_parameter(environment, "log_settings")

class Logger:
    def __init__(self, filename = ""):
        self.filename = filename
    
    def log(self, message, current_data_time=""):
        if environment.lower() == 'dev' and log_settings["strategy_wise_log_files"]:
            # print(message)
            """Append a message with a timestamp to the log file."""
            if self.filename == "":
                print("log filename is not set.")
            else:
                current_directory = os.path.split(os.path.abspath(__file__))[0]
                log_file_path = os.path.join(current_directory, self.filename) 
                with open(log_file_path, 'a') as file:
                    # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if current_data_time == "": 
                        file.write(f"{message}\n")
                    else:
                        current_data_time = datetime.fromtimestamp(current_data_time) - timedelta(days= 1, hours=5, minutes=30)
                        file.write(f"{current_data_time}: {message}\n")               

    @staticmethod
    def print(message):
        if log_settings["print_enabled"]:
            print(message)