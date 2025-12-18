MAIN_ROWS = 20
MAIN_COLUMNS = 20

FPGA_COMMAND_ALPHA = ["-S", "-D", "-w", "-s", "-e", "-b", "-g", "-y", "-V", '-C', '-u']

COMMAND_UPDATE = {
    "-w": {"title": "Pulse width", "text": "Pulse width (i.e. input=3.0 -> pulseWidth = 3.0e-6µS)", "unit": "µS", "default_value": "60.0", 'col': 0, 'row': 0, "shorthand": "Pulse W", "lowerbound": 0.5, "upperbound": 60},
    "-s": {"title": "Pulse setup", "text": "Pulse setup (time before pulse)", "unit": "µS", "default_value": "0.0", "col": 0, 'row': 0, "shorthand": "Pulse setup", "lowerbound": 0.0, "upperbound": 10.0},
    "-e": {"title": "Pulse holdover", "text": "Pulse holdover (time after pulse)", "unit": "µS", "default_value": "-0.5", "col": 0, 'row': 0, "shorthand": "Pulse holdover", "lowerbound": -10.0, "upperbound": 10.0},
    "-S": {"title": "Pulse per sec", "text": "How many pulses per second to analyze", "unit": "fps", "default_value": "800", 'col':0, 'row': 0, "shorthand": "Pulse/s", "lowerbound": 100, "upperbound": 1600},
    "-D": {"title": "Pulse to read", "text": "How many pulses to read before analyzing", "unit": "delay", "default_value": "200", 'col':0, 'row': 0, "shorthand": "Pulse to read", "lowerbound": 0.0, "upperbound": 1.0},
    "-y": {"title": "FIR center frequency", "text": "FIR: pass filter center frequency in MHz referenced to IF", "unit": "cfMHz","default_value": "5.8", 'col': 0, 'row': 0, "shorthand": "FIR center f"},
    "-V": {"title": "FIR override", "text": "FIR: if non-zero, override pass filter bandwidth in MHz", "unit": "bwMHz","default_value": "6.3", 'col': 0, 'row': 0, "shorthand": "FIR override"},
    "-C": {"title": "FIR Parks width", "text": "FIR: Parks Width of ratio of Nyquist Frequency", "unit": "pwNyq","default_value": "0.05", 'col': "0.05", 'row': 0, "shorthand": "FIR Parks W"},
    "-b": {"title": "RX start", "text": "RX pretrigger offset start (from tx)", "unit": "µS","default_value": "2.0", "col": 0, 'row': 0, "shorthand": "RX start", "lowerbound": 0.0, "upperbound": 10.0},
    "-g": {"title": "RX Stop", "text": "RX pretrigger offset stop (from tx)", "unit": "µS","default_value": "0.8", "col": 0, 'row': 0, "shorthand": "RX stop", "lowerbound": -10.0, "upperbound": 10.0},
    "-Q": {"title": "Pulses to read", "text": "Pulses to read before exiting", "unit": "µS","default_value": "0", "col": 0, 'row': 0},
    "-u": {"title": "Reverse Trigger", "text": "Reverse trigger to sig gen. REQUIRED on R1/R2", "unit": None, "default_value": "True", 'col': 0, 'row': 0, "shorthand": "Reverse trigger"},
    "-z": {"title": "Pulse Offset", "text": "Pulse pps offset", "unit": "µS","default_value": "0", "col": 0, 'row': 0, "shorthand": "Pulse offset"},
}
SHUTOFF_COMMANDS = {
    "-1": {"text": "Gate off transmitter (no test mode)", 'col': 0, 'row': 0},
    "-2": {'text': "Power off and gate off transmitter (no test mode)", 'col': 0, 'row': 0}
}

OUTPUT_FIELDS = {
    0: "X dc Offset: ",
    1: "Y dc Offset: ",
    2: "X: (min, max): ",
    3: "Y (min, max): ",
    4: "X power: ",
    5: "Y power: ",
    6: "rate: "
}