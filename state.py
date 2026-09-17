import os
from dotenv import load_dotenv

load_dotenv()



network_state = f"{os.environ.get('HOST_IP')}"

starting_azimuth_value = 0
ending_azimuth_value = 0
starting_el_value = 0
ending_el_value = 0
speed_value = 20
increment_value = 1.5
#IF S needs to be changed, change here
S_FLAG_VALUE = 300


