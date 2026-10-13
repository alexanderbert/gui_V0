import os
from dotenv import load_dotenv
from dictionaryvar import DictVar
import tkinter as tk

load_dotenv()


positioner_output_text = None

network_state = f"{os.environ.get('HOST_IP')}"

positioner_mode_value = None
starting_azimuth_value = 0
ending_azimuth_value = 0
starting_el_value = 0
ending_el_value = 0
speed_value = 20
increment_value = 1.5
slip_detect_value = 1
repeat_value = 1
#IF S needs to be changed, change here
S_FLAG_VALUE = 300
expected_Q_VALUE_VALUE = 0
radar_choice = None


radars_found = None

# def on_change_radar_choice(widget, value):
#


def init_state(app_instance):
    global positioner_output_text
    positioner_output_text = tk.StringVar(master=app_instance)
    positioner_output_text.set("HELLO")
    global radars_found
    radars_found = DictVar(master = app_instance)
    starting_radar = {"Select A Radar": "--------"}
    radars_found.set_dict(starting_radar)
    # RADAR CHIOCE
    global radar_choice
    radar_choice = tk.StringVar(master = app_instance)
    #GETS VALUE OF FIRST
    #radar_choice.set(starting_radar["Select A Radar"])
    for key, value in radars_found.get_dict().items():
        radar_choice.set(key)