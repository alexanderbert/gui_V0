import re
from concurrent.futures import thread
from tkinter import messagebox

import customtkinter
import os
import paramiko
import state
import threading
import tkinter as tk
import time
import queue
from state import ending_azimuth_value
KILL_RUN = False

class Positioner2Frame(customtkinter.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.rowconfigure(0, weight=4)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.grid_propagate(False)


        self.output_frame = OutputFrame(self)
        self.output_frame.grid(column=0, columnspan=2, row=0, sticky="nsew")

        self.input_frame = InputFrame(self)
        self.input_frame.grid(column=0, row=1, pady=15, sticky="nsew")

        self.command_frame = CommandFrame(self, self.input_frame, self.output_frame)
        self.command_frame.grid(column=1, row=1, pady=15, sticky="nsew")



class OutputFrame(customtkinter.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.output_text_var = tk.StringVar()
        #self.output_text_var.trace_add("read", self.on_change_output_text)
        #state.positioner_output_text.trace_add("write", self.on_change_output_text)

        # self.output_entry = customtkinter.CTkEntry(self, textvariable=self.output_text_var, bg_color="red")
        # #self.output_entry.grid(column=0, row=0, sticky="nsew")
        # self.output_entry.pack(side=tk.LEFT, expand=True, fill="both")

        self.output_entry = customtkinter.CTkTextbox(self)
        self.output_entry.pack(side=tk.LEFT, expand=True, fill="both")
        self.output_entry.configure(font=("Arial", 14),state="disabled")

    def on_change_output_text(self, *args):
        self.output_entry.configure(state="normal")
        self.output_text_var.set(state.positioner_output_text.get())
        self.output_entry.delete("1.0", tk.END)
        self.output_entry.insert("1.0", self.output_text_var.get())
        self.output_entry.configure(state="disabled")

class InputFrame(customtkinter.CTkFrame):
    def __init__(self, parent,):
        super().__init__(parent)
        self.columnconfigure(list(range(0,8)), weight=1)
        self.grid_propagate(False)

        self.start_azimuth_var = tk.StringVar()
        self.start_azimuth_var.trace_add("write", self.on_change_start_az)
        self.end_azimuth_var = tk.StringVar()
        self.end_azimuth_var.trace_add("write", self.on_change_end_az)
        self.start_elbeam_var = tk.StringVar()
        self.start_elbeam_var.trace_add("write", self.on_change_start_elbeam)
        self.end_elbeam_var = tk.StringVar()
        self.end_elbeam_var.trace_add("write", self.on_change_end_elbeam)
        self.speed_var = tk.StringVar()
        self.speed_var.trace_add("write", self.on_change_speed)
        self.increment_var = tk.StringVar()
        self.increment_var.trace_add("write", self.on_change_increment)
        self.repeat_var = tk.StringVar()
        self.repeat_var.trace_add("write", self.on_change_repeat)
        self.slip_detect_var = tk.StringVar()
        self.slip_detect_var.trace_add("write", self.on_change_slip_detect)


        self.radio_button_mode_var = tk.StringVar(value=None)
        self.radio_button_mode_var.trace_add("write", self.on_change_radio_button_mode)

        self.start_az_entry = customtkinter.CTkEntry(self, placeholder_text="Start Az", textvariable=self.start_azimuth_var, justify="center")
        self.start_az_entry.grid(column=1, row=0, sticky="w")
        self.start_az_entry.insert(0, "Start Az")
        self.start_az_label = customtkinter.CTkLabel(self, text="Start Az")
        self.start_az_label.grid(column=0, row=0, sticky="nes", padx=10, pady=5)


        self.end_az_entry = customtkinter.CTkEntry(self, placeholder_text="End Az", textvariable=self.end_azimuth_var, justify="center")
        self.end_az_entry.grid(column=1, row=1, sticky="w")
        self.end_az_entry.insert(0, "End Az")
        self.end_az_label = customtkinter.CTkLabel(self, text="End Az")
        self.end_az_label.grid(column=0, row=1, sticky="nes", padx=10, pady=5)

        self.start_elbeam_entry = customtkinter.CTkEntry(self, placeholder_text="Start ElBeam", textvariable=self.start_elbeam_var, justify="center")
        self.start_elbeam_entry.grid(column=1, row=2, sticky="w")
        self.start_elbeam_entry.insert(0, "Start ElBeam")
        self.start_elbeam_label = customtkinter.CTkLabel(self, text="Start ElBeam")
        self.start_elbeam_label.grid(column=0, row=2, sticky="nes", padx=10, pady=5)

        self.end_elbeam_entry = customtkinter.CTkEntry(self, placeholder_text="End ElBeam", textvariable=self.end_elbeam_var, justify="center")
        self.end_elbeam_entry.grid(column=1, row=3, sticky="w")
        self.end_elbeam_entry.insert(0, "End ElBeam")
        self.end_elbeam_label = customtkinter.CTkLabel(self, text="End ElBeam")
        self.end_elbeam_label.grid(column=0, row=3, sticky="nes", padx=10, pady=5)

        self.speed_entry = customtkinter.CTkEntry(self, placeholder_text="Speed", textvariable=self.speed_var, justify="center")
        self.speed_entry.grid(column=1, row=4, sticky="w")
        self.speed_entry.insert(0, "60")
        self.speed_label = customtkinter.CTkLabel(self, text="Speed")
        self.speed_label.grid(column=0, row=4, sticky="nes", padx=10, pady=5)

        self.increment_entry = customtkinter.CTkEntry(self, placeholder_text="Increment", textvariable=self.increment_var, justify="center")
        self.increment_entry.grid(column=1, row=5, sticky="w")
        self.increment_entry.insert(0, "0.25")
        self.increment_label = customtkinter.CTkLabel(self, text="Increment")
        self.increment_label.grid(column=0, row=5, sticky="nes", padx=10, pady=5)

        self.repeat_entry = customtkinter.CTkEntry(self, placeholder_text="Repeat", textvariable=self.repeat_var, justify="center")
        self.repeat_entry.grid(column=1, row=6, sticky="w")
        self.repeat_entry.insert(0, "1")
        self.repeat_label = customtkinter.CTkLabel(self, text="Repeat")
        self.repeat_label.grid(column=0, row=6, sticky="nes", padx=10, pady=5)

        self.slip_detect_entry = customtkinter.CTkEntry(self, placeholder_text="Slip Detect", textvariable=self.slip_detect_var, justify="center")
        self.slip_detect_entry.grid(column=1, row=7, sticky="w")
        self.slip_detect_entry.insert(0, "1")
        self.slip_detect_label = customtkinter.CTkLabel(self, text="Slip Detect")
        self.slip_detect_label.grid(column=0, row=7, sticky="nes", padx=10, pady=5)

        self.positioner_status_label = customtkinter.CTkLabel(self, text="Positioner Not Connected", fg_color="gray", text_color ="white", justify="center", corner_radius=6)
        self.positioner_status_label.grid(column=4, row=0, columnspan=2, sticky="ew")

        self.mode_label = customtkinter.CTkLabel(self, text="Mode", fg_color="gray", text_color="white", corner_radius=5)
        self.mode_label.grid(column=4, row=3, sticky="NEW", pady=10)

        self.ppi_mode_radio_button = customtkinter.CTkRadioButton(self, text="PPI", variable = self.radio_button_mode_var, value="ppi")
        self.ppi_mode_radio_button.grid(column=4, row=4, sticky="new")

        self.rhi_mode_radio_button = customtkinter.CTkRadioButton(self, text="RHI", variable = self.radio_button_mode_var, value="rhi")
        self.rhi_mode_radio_button.grid(column=4, row=5, sticky="new")

        self.sector_mode_radio_button = customtkinter.CTkRadioButton(self, text="Sector", variable = self.radio_button_mode_var, value="sector")
        self.sector_mode_radio_button.grid(column=4, row=6, sticky="new")

        self.rhi_square_mode_radio_button = customtkinter.CTkRadioButton(self, text="RHI-Square", variable = self.radio_button_mode_var, value="rhisquare")
        self.rhi_square_mode_radio_button.grid(column=5, row=4, sticky="new")

        self.spot_mode_radio_button = customtkinter.CTkRadioButton(self, text="Spot", variable = self.radio_button_mode_var, value="spot")
        self.spot_mode_radio_button.grid(column=5, row=5, sticky="new")

    def on_change_radio_button_mode(self, *argz):
        radio_button_mode_trace = self.radio_button_mode_var.get()
        state.positioner_mode_value = radio_button_mode_trace

    def on_change_start_az(self, *args):
        start_azimuth_value_trace = self.start_azimuth_var.get()
        state.starting_azimuth_value = start_azimuth_value_trace

    def on_change_end_az(self, *argz):
        end_azimuth_value_trace = self.end_azimuth_var.get()
        state.ending_azimuth_value = end_azimuth_value_trace

    def on_change_start_elbeam(self, *args):
        start_elbeam_value_trace = self.start_elbeam_var.get()
        state.starting_el_value = start_elbeam_value_trace

    def on_change_end_elbeam(self, *args):
        end_elbeam_value_trace = self.end_elbeam_var.get()
        state.ending_el_value = end_elbeam_value_trace

    def on_change_slip_detect(self, *args):
        slip_detect_value_trace = self.slip_detect_var.get()
        state.slip_detect_value = slip_detect_value_trace

    def on_change_increment(self, *args):
        increment_value_trace = self.increment_var.get()
        state.increment_value = increment_value_trace

    def on_change_repeat(self, *args):
        repeat_value_trace = self.repeat_var.get()
        state.repeat_value = repeat_value_trace

    def on_change_speed(self, *args):
        speed_value_trace = self.speed_var.get()
        state.speed_value = speed_value_trace







class CommandFrame(customtkinter.CTkFrame):
    def __init__(self, parent, input_frame, output_frame):
        super().__init__(parent)
        # self.continuous_output_list = None

        self.output_queue = queue.Queue()
        self.after(20, self.update_output_fields)

        self.input_frame = input_frame
        self.output_frame = output_frame
        self.columnconfigure(list(range(0,8)), weight=1)
        self.rowconfigure(list(range(0,8)), weight=1)
        self.grid_propagate(False)
        self.current_radar = None
        self.qualifier_values = ["5.0/1.0 Deg", "0.5/0.25 Deg", "0.1/0.05 Deg", "0.01/0.01 Deg"]
        self.keys_to_bind = [
            '<Key-I>', '<Key-i>',
            '<Key-J>', '<Key-j>',
            '<Key-K>', '<Key-k>',
            '<Key-L>', '<Key-l>',
            '<Key-W>', '<Key-w>',
            '<Key-A>', '<Key-a>',
            '<Key-S>', '<Key-s>',
            '<Key-D>', '<Key-d>',
        ]




        self.button_label = customtkinter.CTkLabel(self, text="Positioner Commands", fg_color="gray", text_color="white", corner_radius=5)
        self.button_label.pack(side=tk.TOP, pady=10)

        self.connect_positioner_button = customtkinter.CTkButton(self, text="Positioner Status", command=lambda: self.start_thread(self.get_positioner_status))
        self.connect_positioner_button.pack(side=tk.TOP, pady=10)

        self.start_scan_button = customtkinter.CTkButton(self, text="Start Scan", command=lambda: self.start_thread(self.start_scan))
        self.start_scan_button.pack(side=tk.TOP, pady=10)

        self.stop_scan_button = customtkinter.CTkButton(self, text="Stop Scan", command=lambda: self.start_thread(self.stop_scan))
        self.stop_scan_button.pack(side=tk.TOP, pady=10)

        self.go_home_button = customtkinter.CTkButton(self, text="Go to Home", command= lambda: self.start_thread(self.go_home))
        self.go_home_button.pack(side=tk.TOP, pady=10)

        self.homing_mode_button = customtkinter.CTkButton(self, text="Homing Mode", command = lambda: self.homing_mode_interface("no"))
        self.homing_mode_button.pack(side=tk.TOP, pady=10)

        self.reset_button = customtkinter.CTkButton(self, text="Reset", command=lambda: self.start_thread(self.reset_positioner))
        self.reset_button.pack(side=tk.TOP, pady=10)

        self.update_output_fields()

    def create_ssh_client(self):
        client = paramiko.client.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())

        return client

    def fl_network_mode(self):
        self.current_radar_key = state.radar_choice.get()
        for key, value in state.radars_found.get_dict().items():
            if key == self.current_radar_key:
                self.current_radar_value = value
        print(f"INSIDE FLORIDA {self.current_radar_value}")
        try:
            state.positioner_output_text.set("Attempting Connection to Network...")

            self.input_frame.positioner_status_label.configure(text="Connecting...", fg_color="gray")
            client = self.create_ssh_client()
            client.connect(hostname=f"{self.current_radar_value}", username=f"{os.environ.get('CONNECTION_USERNAME')}",
                               password=f"{os.environ.get('CONNECTION_PASSWORD')}", look_for_keys=False, allow_agent=False, timeout=5)
            transport = client.get_transport()
            channel = transport.open_session()
            channel.get_pty()
            channel = client.invoke_shell()
            time.sleep(.1)
            output = channel.recv(1024).decode()

            self.output_frame.output_entry.configure(state="normal")
            return client, channel
        except:
            state.positioner_output_text.set("Network Error")
            self.input_frame.positioner_status_label.configure(text="Connection Error", fg_color="yellow", text_color="black")
            self.button_mode("normal")
            return False

    def button_mode(self, state_variable):
        self.connect_positioner_button.configure(state=state_variable)
        self.start_scan_button.configure(state=state_variable)
        self.go_home_button.configure(state=state_variable)
        self.homing_mode_button.configure(state=state_variable)
        self.reset_button.configure(state=state_variable)


    def input_check(self):
        self.output_frame.output_entry.configure(state = "normal")
        self.output_frame.output_entry.delete("0.0", "end")
        self.current_radar_key = state.radar_choice.get()
        try:
            start_azimuth_input_check = float(state.starting_azimuth_value)
            ending_azimuth_input_check = float(state.ending_azimuth_value)
            starting_el_input_check = float(state.starting_el_value)
            ending_el_input_check = float(state.ending_el_value)
            speed_input_check = float(state.speed_value)
            increment_input_check = float(state.increment_value)
            self.input_frame.positioner_status_label.configure(text="Check inputs", fg_color="yellow",
                                                               text_color="black")

        except ValueError:
            #state.positioner_output_text.set("ERROR: Please check inputs")
            self.output_frame.output_entry.insert("0.0", "ERROR: Please check inputs")
            return 1
        if self.current_radar_key == "Select A Radar":
            self.output_frame.output_entry.insert("0.0", "ERROR: Please Select A Radar")
            self.input_frame.positioner_status_label.configure(text="Select A Radar", fg_color="yellow", text_color="black")
            return 1
        if state.positioner_mode_value is None:
            self.output_frame.output_entry.insert("0.0", "ERROR: Please select a scan mode")
            #state.positioner_output_text.set("ERROR: Please select a scan mode")
            return 1
        if start_azimuth_input_check > 360 or start_azimuth_input_check < 0:
            self.output_frame.output_entry.insert("0.0", "ERROR: Please check Starting AZ input")
            #state.positioner_output_text.set("ERROR: Please check Starting AZ input")
            return 1
        if ending_azimuth_input_check > 360 or ending_azimuth_input_check < 0:
            self.output_frame.output_entry.insert("0.0", "ERROR: Please check Ending Azimuth input")
            #state.positioner_output_text.set("ERROR: Please check Ending Azimuth input")
            return 1
        if starting_el_input_check > 45 or starting_el_input_check < (-6):
            self.output_frame.output_entry.insert("0.0", "ERROR: Please check Starting Elbeam input")
            #state.positioner_output_text.set("ERROR: Please check Starting Elbeam input")
            return 1
        if ending_el_input_check > 45 or ending_el_input_check < (-6):
            self.output_frame.output_entry.insert("0.0", "ERROR: Please check Ending Elbeam input")
            #state.positioner_output_text.set("ERROR: Please check Ending Elbeam input")
            return 1
        if speed_input_check > 300 or speed_input_check < 2:
            self.output_frame.output_entry.insert("ERROR: Please check speed input")
            return 1
        self.output_frame.output_entry.configure(state ="disabled")
        return 0

    def start_thread(self, func):
        thread = threading.Thread(
            target=func,
            args=(),
            daemon=True
        )
        thread.start()


    def set_home(self, key_stroke):
        #OK status\r\r\n
        # open connection - clear connection - cat - get info
        print(f"{type(key_stroke)} {key_stroke} in set home")
        try:
            client, channel = self.fl_network_mode()
        except:
            self.input_frame.positioner_status_label.configure(text="Network Error")
            return 1

        #channel = self.alex_home_network_mode()
        ttyf="/dev/ttyUSB1"
        channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo cbreak\n")
        time.sleep(0.1)
        #no keystrokes
        print("BACKGROUNDING INITIAL CAT IN SET HOME")
        channel.send(f"cat {ttyf} &\n")
        #channel.send(f"echo -n {key_stroke} > {ttyf}\n")
        print(f"SENDING {key_stroke}")
        channel.send(f"echo -n {key_stroke} > {ttyf}\n")
        time.sleep(0.1)
        print("FOREGROUNDING CAT IN SET HOME")
        channel.send("fg\n")
        time.sleep(0.1)

        if key_stroke == "X" or key_stroke == "/":
            self.normal_mode_interface()
            output = ""
            kill_switch = True
            while True and kill_switch:
                data = channel.recv(1048).decode("iso-8859-1")
                output = output + data
                print(output)
                if "POS>" in output:
                    kill_switch = False
                    print("POS> DETECTED")
                    print("SUSPENDING CAT BECAUSE AN X OR / IS RECIEVED")
                    channel.send(f"\x1a")
                    time.sleep(0.1)
                    print("BACKGROUNDING CAT IN SET HOME BECAUSE AN X OR / IS RECIEVED")
                    channel.send("bg\n")
                    time.sleep(0.1)
                    channel.close()
                    client.close()
                    self.get_positioner_status()
                    return 0
        output = channel.recv(2048).decode("iso-8859-1")
        print("FOREGROUNDING CAT IN SET HOME AFTER REGULAR KEY STROKE")

        #self.output_frame.output_entry.insert("end", output)
        print(f"OUTPUT 1 IN SET_HOME: {output}")


        #self.output_frame.output_entry.insert("end", output)
        # print(f"OUTPUT 2 IN SET_HOME: {output}")
        for line in output.split("\n"):
            if "AZ Target:" in line or "EL Target:" in line:
                #STRIP NEW whitespace/newline/carriage return
                self.output_frame.output_entry.insert("end", f"AZ Target: {(line.split('AZ Target:')[1]).strip()}")
                #TODO THIS SHOULD AUTOSCROLL DOWN
                self.output_frame.output_entry.see("end")
        # self.output_frame.output_entry.delete("0.0", "end")
        # for line in output.split("\n"):
        #     self.output_frame.output_entry.insert("end", line)
        # time.sleep(0.1)
        print("SUSPENDING AND BACKGROUNDING IN SET HOME AFTER REGULAR KEY STROKE")
        channel.send(f"\x1a")
        channel.send("bg\n")

        channel.close()
        client.close()

# cat backgrounded, - >
    #or read/write simultaneously two seperate reading

    def start_scan(self):
        #TODO IF START SCAN FAILS, reenable buttons
        #TRACKING ERROR WARNING
        #FAILING DUE TO TRACKING ERROR! Run 'scan rehome'
        if self.input_check() == 1:
            return 1

        try:
            client, channel = self.fl_network_mode()
        except:
            self.input_frame.positioner_status_label.configure(text="Network Error")
            return 1
        # NEW TRY
        ttyf = "/dev/ttyUSB1"
        # channel.send(f"cat {ttyf} &\n")
        # time.sleep(0.1)





        channel.send(f"""
                    stty -F {ttyf} 115200 raw -hupcl -onlcr -echo
                    echo scan mode {state.positioner_mode_value} > {ttyf}
                    echo scan set startaz {state.starting_azimuth_value} > {ttyf}
                    echo scan set endaz {state.ending_azimuth_value} > {ttyf}
                    echo scan set startelbeam {state.starting_el_value} > {ttyf}
                    echo scan set endelbeam {state.ending_el_value} > {ttyf}
                    echo scan set speed {state.speed_value} > {ttyf}
                    echo scan set inc {state.increment_value} > {ttyf}
                    echo scan set repeat {state.repeat_value} > {ttyf}
                    echo scan set slipdetect {state.slip_detect_value} > {ttyf}
                    echo scan start > {ttyf}\n
        #             """)

        # channel.send(f"fg\n")
        # output = ""
        # while channel.recv_ready():
        #     data = channel.recv(8192).decode("iso-8859-1")
        #     output += data


        # channel.send("fg\n")
        # print("FOREGROUNDING CAT")
        time.sleep(.1)
        # print("FOREGROUNDING CAT IN SET HOME")
        # channel.send("fg\n")
        #CHECK THIS FOR INPUT CHECK CONFUSION
        self.start_thread(self.continuous_output)

        #TODO ERROR CHECK NOT WORKING
        # output = ""
        # while not channel.exit_status_ready() or channel.recv_ready():
        #     if channel.recv_ready():
        #         data = channel.recv(8192).decode("iso-8859-1")
        #         time.sleep(.1)
        #         channel.send("fg\n")
        #         time.sleep(.1)
        #         output += data
        #         print(f"INSIDE START: {repr(output)}")
        #         if "MUST HOME" in data or "homed?" in output:
        #             self.output_frame.output_entry.insert("end", "Use Homing Mode")
        #             self.input_frame.positioner_status_label.configure(text="Radar must be Homed", fg_color="orange")
        #             print("SUSPEND/BACKGROUNDING CAT AT HOMING MODE CHECK IN START SCAN")
        #             channel.send(f"\x1a")
        #             channel.send("bg\n")
        #             channel.close()
        #             client.close()
        #             return 1
        #     else:
        #         time.sleep(0.01)
        self.button_mode("disabled")
        self.input_frame.positioner_status_label.configure(text=f"Running {state.positioner_mode_value} on {state.radar_choice.get()}", fg_color="green", text_color="white")

        # run_status = self.get_positioner_status()
        # if run_status != 1:
        #     self.input_frame.positioner_status_label.configure(text="Error: Start Scan Failed", fg_color="yellow", text_color="black")
        #     self.button_mode("normal")
        # print("SUSPEND/BACKGROUNDING CAT AT END OF START SCAN")
        # channel.send(f"\x1a")
        # time.sleep(.1)
        # channel.send("bg\n")
        # time.sleep(.1)
        channel.close()
        client.close()
        #run_status = self.get_positioner_status()
        return

    def continuous_output(self):
        self.continuous_output_list = []
        client, channel = self.fl_network_mode()

        buffer = ""
        ttyf = "/dev/ttyUSB1"
        channel.send(f"cat {ttyf} &\n")
        time.sleep(.1)
        channel.send("fg\n")
        time.sleep(.1)
        marker_found = False
        self.output_queue.put("STARTING OUTPUT FROM RADAR\n")
        while not KILL_RUN or channel.exit_status_ready() or channel.recv_ready():
            if channel.recv_ready():
                print(
                    f"KILL_RUN={KILL_RUN}, "
                    f"exit_ready={channel.exit_status_ready()}, "
                    f"recv_ready={channel.recv_ready()}",
                    flush=True
                )
                data = channel.recv(1024).decode("iso-8859-1")
                print(f"DATA AFTER FRESH RECEIVE: {repr(data)}")
                buffer += data
                output = buffer.split("\r\r\n")
                buffer = output.pop()

                for line in output:
                    print(f"LINE IN OUTPUT: {line}")

                    self.clean_output_data(line)

                print(f"INSIDE START: {repr(buffer)}")
                if "MUST HOME" in buffer or "homed?" in buffer or "TRACKING ERROR WARNING" in buffer:
                    self.output_frame.output_entry.insert("end", "Use Homing Mode")
                    self.input_frame.positioner_status_label.configure(text="Radar must be Homed", fg_color="orange")
                    print("SUSPEND/BACKGROUNDING CAT AT HOMING MODE CHECK IN START SCAN")
                    channel.send(f"\x1a")
                    channel.send("bg\n")
                    channel.close()
                    client.close()
                    return 1
            elif channel.exit_status_ready():
                print(f"EXIT STATUS READY = {channel.exit_status_ready()} ")
            else:
                time.sleep(0.01)
        self.output_frame.output_entry.insert("end", "Channel Closed")
        print("ENDING CONTINUOUS OUTPUT")
        time.sleep(0.01)
        channel.send(f"\x1a")
        time.sleep(0.01)
        channel.send("bg\n")
        time.sleep(0.01)
        channel.close()
        client.close()

    def clean_output_data(self, data):
        line = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', data)
        print(f"LINE IN CLEAN OUTPUT DATA OUTPUT: {line}")
        self.output_queue.put(f"{line.strip()}\n")

        #TODO CAN ATTEMPT THIS AFTER SEEING HOW RHI RHISQUARE ARE PRINTED...
        # if re.match(r'^\d+\s+\[SCAN (?:PPI|COM)\]', message):
        #     cleaned_messages.append(message)


    def update_output_fields(self):
        current_tag = "default"
        batch = []
        max_items = 500

        for _ in range(max_items):
            try:
                batch.append(self.output_queue.get_nowait())
            except queue.Empty:
                break
        if batch:
            output = "".join(batch)

            self.output_frame.output_entry.insert("end", output)
            self.output_frame.output_entry.see("end")

        # if self.continuous_output_list is not None:
        #     output = self.continuous_output_list
        #     self.output_frame.output_entry.insert("end", output)
        #     self.output_frame.output_entry.see("end")
        self.after(20, self.update_output_fields)



    def stop_scan(self):
        '''
        issue scan stop
        set up scan progress
        instead of putting up another status, put up a stopping alert
        :return:
        '''
        global KILL_RUN
        KILL_RUN = True
        self.continuous_output_list = None

        print("STOPPING SCAN")
        self.output_frame.output_entry.delete("0.0", "end")
        self.output_frame.output_entry.insert("end", "Executing Stop Command\nPlease Standby for positioner\nto finish rotation\n")
        try:
            client, channel = self.fl_network_mode()
        except:
            self.input_frame.positioner_status_label.configure(text="Network Error")
            return 1
        #channel = self.alex_home_network_mode()
        time.sleep(0.1)
        ttyf="/dev/ttyUSB1"
        channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
        channel.send(f"echo scan stop > {ttyf}\n")
        time.sleep(0.1)

        for i in range(1, 301):
            run_status_variable = self.get_positioner_status()
            if run_status_variable == 0:
                print("WITHIN IF CONDITION OF STOP SCAN")
                break
            else:
                print("WITHIN ELSE CONDITION OF STOP SCAN")

                state.positioner_output_text.set(f"Executing Stop Command Attempt #{i}\n Please Standby for positioner\nto finish rotation\n")
                channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
                channel.send(f"echo scan stop > {ttyf}\n")
                time.sleep(.5)

        run_status_variable = self.get_positioner_status()
        if run_status_variable == 1:
            state.positioner_output_text.set(f"Stop Command fail, retry")
        else:
            self.input_frame.positioner_status_label.configure(text="Stopped", fg_color="red", text_color="white")
            state.positioner_output_text.set("Scan stopped\n")

        self.button_mode("normal")
        channel.close()
        client.close()

    # def get_positioner_status(self):
    #     '''
    #     starting cat in background for first long running cat
    #     /x1a print issuing suspend
    #     print before bg for backgrounding cat
    #     print before fg for foregrounding
    #     :return:
    #     '''
    #     scan_mode_variable = ""
    #     run_status_variable = ""
    #     self.output_frame.output_entry.configure(state="normal")
    #     self.input_frame.positioner_status_label.configure(text="Checking status")
    #     try:
    #         client, channel = self.fl_network_mode()
    #     except:
    #         self.input_frame.positioner_status_label.configure(text="Network Error")
    #         return 1
    #     # # channel = self.alex_home_network_mode()
    #     self.input_frame.positioner_status_label.configure(text="Checking status")
    #     # HOMING MODE CHECK
    #     ttyf = "/dev/ttyUSB1"
    #     channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
    #     #START CAT IN BACKROUND
    #     channel.send(f"cat {ttyf} &\n")
    #     time.sleep(.2)
    #
    #     channel.send(f"echo \r")
    #     print("FOREGROUNDING CAT")
    #     channel.send("fg\n")
    #     output = ""
    #     output_check = ""
    #     try:
    #         output_check = channel.recv(1024).decode("iso-8859-1")
    #         print("H-mode MODE CHECK INPUT")
    #         print(repr(output_check))
    #     except:
    #         print("h-mode MODE AFTER TRY")
    #
    #     time.sleep(2)
    #
    #     time.sleep(.1)
    #     print("SUSPEND AND BACKGROUND CAT")
    #     channel.send(f"\x1a")
    #     channel.send("bg\n")
    #     #End Homing mode check
    #     if "[HOME    ]" in output_check or "home" in output_check:
    #         self.input_frame.positioner_status_label.configure(text="Homing mode")
    #         self.homing_mode_interface("yes")
    #         return 1
    #
    #     time.sleep(2)
    #     print("FOREGROUNDING CAT")
    #     channel.send("fg\n")
    #     channel.send(f"echo scan status > {ttyf}\n")
    #     time.sleep(.1)
    #
    #     time.sleep(0.1)
    #
    #     time.sleep(.1)
    #
    #     if "[HOME    ]" in output_check or "home" in output_check:
    #         self.input_frame.positioner_status_label.configure(text="Homing mode")
    #         self.homing_mode_interface("yes")
    #         return 1
    #
    #     start_az_variable = ""
    #     end_az_variable = ""
    #     el_axis_start_end_variable = []
    #     el_beam_start_end_variable = []
    #
    #     #NORMAL STATUS CHECK
    #     try:
    #         print("IN INITIAL TRY")
    #         output = channel.recv(8192).decode("iso-8859-1")
    #         if "[HOME    ]" in output or "home" in output:
    #             self.input_frame.positioner_status_label.configure(text="Homing mode")
    #             self.homing_mode_interface("yes")
    #             return 1
    #         #print(output)
    #         if "MUST HOME" in output or "homed?" in output:
    #             run_status_variable = 2
    #         time.sleep(.1)
    #         output_status = output.split(":~$ scan status", 1)
    #         output_lines = output_status[1].split("\r")
    #         for index, line in enumerate(output_lines):
    #             if "Mode: " in line:
    #                 scan_mode_variable = line.split("Mode:")[1]
    #             if "Run:" in line:
    #                 run_status_variable = line.split("Run:")[1]
    #             if "Start Az:" in line:
    #                 start_az_variable = line.split("Start Az:")[1]
    #             if "End Az:" in line:
    #                 end_az_variable = line.split("End Az:")[1]
    #             if "El (axis) Start:" in line:
    #                 el_axis_start_end_variable = line.split("El (axis)")[1]
    #             if "El (beam) Start:" in line:
    #                 el_beam_start_end_variable = line.split("El (beam)")[1]
    #             self.output_frame.output_entry.insert("end", line)
    #             if "Attenuations:" in line:
    #                 # self.status_text_box.insert(tk.END, "\r")
    #                 channel.close()
    #                 break
    #     except:
    #         print("IN EXCEPTION")
    #         self.output_frame.output_entry.delete("0.0", "end")
    #         channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
    #         channel.send(f"cat {ttyf} &\n")
    #         time.sleep(.1)
    #         channel.send(f"echo scan status > {ttyf}\n")
    #         time.sleep(.1)
    #         print("FOREGROUNDING CAT")
    #         channel.send("fg\n")
    #         time.sleep(0.1)
    #
    #
    #         time.sleep(.1)
    #
    #         output = channel.recv(8192).decode("iso-8859-1")
    #         print(output)
    #         if "MUST HOME" in output or "homed?" in output:
    #             run_status_variable = 2
    #         output_status = output.split("scan status", 1)
    #         output_lines = output_status[1].split("\r")
    #         for index, line in enumerate(output_lines):
    #             if "Mode: " in line:
    #                 scan_mode_variable = line.split("Mode:")[1]
    #             if "Run:" in line:
    #                 run_status_variable = line.split("Run:")[1]
    #             if "Start Az:" in line:
    #                 start_az_variable = line.split("Start Az: ")[1]
    #             if "End Az:" in line:
    #                 end_az_variable = line.split("End Az: ")[1]
    #                 # self.input_frame.end_entry.delete("0.0", "end")
    #                 # self.input_frame.end_az_entry.insert(0, end_az_variable)
    #             if "El (axis) Start:" in line:
    #                 el_axis_start_end_variable = line.split("El (axis)")[1]
    #             if "El (beam) Start:" in line:
    #                 el_beam_start_end_variable = line.split("El (beam)")[1]
    #             self.output_frame.output_entry.insert(tk.END, line)
    #             if "Attenuations:" in line:
    #                 # self.status_text_box.insert(tk.END, "\r")
    #                 break
    #     try:
    #         scan_mode_variable = scan_mode_variable.strip().split(", ")[1]
    #
    #         # start_az_variable = f"Start Az: {float(start_az_variable.strip()):.2f}"
    #         # end_az_variable = f"End Az: {float(end_az_variable.strip()):.2f}"
    #         # el_axis_start_end_variable = el_axis_start_end_variable.strip().split(" ")
    #         # el_axis_start = f"El (axis) Start: {float(el_axis_start_end_variable[1].split(',')[0]):.2f}"
    #         # el_axis_end = f"El (axis) End: {float(el_axis_start_end_variable[3]):.2f}"
    #         # el_beam_start_end_variable = el_beam_start_end_variable.strip().split(" ")
    #         # el_beam_start = f"El (beam) Start: {float(el_beam_start_end_variable[1].split(',')[0]):.2f}"
    #         # el_beam_end = f"El (beam) End: {float(el_beam_start_end_variable[3]):.2f}"
    #         run_status_variable = int(run_status_variable.strip())
    #
    #         print("RUN STATUS VARIABLE: ", run_status_variable)
    #         if run_status_variable == 1:
    #             self.input_frame.positioner_status_label.configure(
    #                 text=f"Running {scan_mode_variable} on {state.radar_choice.get()}", fg_color="green4")
    #         elif run_status_variable == 0:
    #             self.input_frame.positioner_status_label.configure(text="Stopped", fg_color="red")
    #         elif run_status_variable == 2:
    #             self.input_frame.positioner_status_label.configure(text="Please Home", fg_color="orange")
    #         else:
    #             self.input_frame.positioner_status_label.configure(text="Error", fg_color="yellow")
    #
    #     except:
    #         self.output_frame.output_entry.delete("0.0", "end")
    #         self.output_frame.output_entry.insert("0.0", "Connection Error, please try again")
    #     finally:
    #         print("SUSPENDING AND BACKGROUNDING CAT")
    #         channel.send(f"\x1a")
    #         channel.send("bg\n")
    #         channel.close()
    #         client.close()
    #         self.output_frame.output_entry.configure(state="disabled")
    #         print("RUN STATUS VARIABLE: ", run_status_variable)
    #         return run_status_variable


        #return run_status_variable

    def reset_positioner(self, var):
        answer = messagebox.askyesno("Reset Positioner", "Do you want to reset positioner?")
        print(answer)
        if answer:
            print("reset positioner")
            try:
                client, channel = self.fl_network_mode()
            except:
                self.input_frame.positioner_status_label.configure(text="Network Error")
                return 1
            #channel = self.alex_home_network_mode()
            ttyf = "/dev/ttyUSB1"
            channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")

            time.sleep(0.1)
            channel.send(f"echo reset > {ttyf}\n")
            #no output
            time.sleep(0.1)
            channel.close()
            client.close()
            self.input_frame.positioner_status_label.configure(text="Homing mode")
        else:
            print("dont reset positioner")

    def re_home(self):
        try:
            client, channel = self.fl_network_mode()
        except:
            self.input_frame.positioner_status_label.configure(text="Network Error")
            return 1
        #channel =self.alex_home_network_mode()
        ttyf = "/dev/ttyUSB1"
        channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
        channel.send(f"echo rehome > {ttyf}\n")
        time.sleep(0.5)
        self.get_positioner_status()
        channel.close()
        client.close()


    def go_home(self):
        try:
            client, channel = self.fl_network_mode()
        except:
            self.input_frame.positioner_status_label.configure(text="Network Error")
            return 1
        #channel =self.alex_home_network_mode()
        ttyf = "/dev/ttyUSB1"
        channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
        channel.send(f"echo gohome > {ttyf}\n")
        time.sleep(0.5)
        self.get_positioner_status()
        channel.close()
        client.close()

    def movement_output(self, key_press, movement):
        print(f"keystroke: '{movement} {key_press}'")
        movement_dict = {"5.0/1.0 Deg up": 'W',
                        "5.0/1.0 Deg down": 'S',
                        "5.0/1.0 Deg left": 'A',
                        "5.0/1.0 Deg right": 'D',
                        "0.5/0.25 Deg up": 'w',
                        "0.5/0.25 Deg down": 's',
                        "0.5/0.25 Deg left": 'a',
                        "0.5/0.25 Deg right": 'd',
                        "0.1/0.05 Deg up": 'i',
                        "0.1/0.05 Deg down": 'k',
                        "0.1/0.05 Deg left": 'j',
                        "0.1/0.05 Deg right": 'l',
                        "0.01/0.01 Deg up": 'I',
                        "0.01/0.01 Deg down": 'K',
                        "0.01/0.01 Deg left": 'J',
                        "0.01/0.01 Deg right": 'L',
                        "coarse left": 'A',
                         "coarse right": 'D',
                         "coarse up": 'W',
                         "coarse down": 'S',
                         "fine left": 'a',
                         "fine right": 'd',
                         "fine up": 'w',
                         "fine down": 's',
                         'extra fine left': 'j',
                         'extra fine right': 'l',
                         'extra fine up': 'i',
                         'extra fine down': 'k',
                         'extra extra fine left': 'J',
                         'extra extra fine right': 'L',
                         'extra extra fine up': 'I',
                         'extra extra fine down': 'K',}

        for key, value in movement_dict.items():
            if key == f'{movement} {key_press}':
                try:
                    print(f"value for set home {value}")
                    self.set_home(value)
                except Exception as e:
                    print(f"{e}")

    def homing_mode_interface(self, var):
        # REMOVE CHECK FOR RESET, ONLY ISSUE RESET
        """hit enter, get pos for normal mode or get home  [HOME some spaces] for the mode \n or maybe \r and read output"""
        self.input_frame.positioner_status_label.configure(text="Homing Mode")
        self.output_frame.output_entry.configure(state="normal")
        self.output_frame.output_entry.delete("0.0", "end")
        #TODO I DONT THINK THIS IS FOCUSING WHERE I WANT IT TO
        #self.focus_set()
        self.reset_positioner("yes")
        #REMOVE NORMAL MODE INTERFACE BUTTONS
        self.input_frame.start_az_entry.grid_remove()
        self.input_frame.start_az_label.grid_remove()
        self.input_frame.end_az_entry.grid_remove()
        self.input_frame.end_az_label.grid_remove()
        self.input_frame.start_elbeam_entry.grid_remove()
        self.input_frame.start_elbeam_label.grid_remove()
        self.input_frame.end_elbeam_entry.grid_remove()
        self.input_frame.end_elbeam_label.grid_remove()
        self.input_frame.speed_entry.grid_remove()
        self.input_frame.speed_label.grid_remove()
        self.input_frame.increment_entry.grid_remove()
        self.input_frame.increment_label.grid_remove()
        self.input_frame.repeat_entry.grid_remove()
        self.input_frame.repeat_label.grid_remove()
        self.input_frame.slip_detect_entry.grid_remove()
        self.input_frame.slip_detect_label.grid_remove()
        self.input_frame.mode_label.grid_remove()
        self.input_frame.ppi_mode_radio_button.grid_remove()
        self.input_frame.rhi_mode_radio_button.grid_remove()
        self.input_frame.sector_mode_radio_button.grid_remove()
        self.input_frame.rhi_square_mode_radio_button.grid_remove()
        self.input_frame.spot_mode_radio_button.grid_remove()
        #DEAL WITH BUTTONS
        self.button_mode("disabled")
        self.stop_scan_button.configure(state = "disabled")
        #call interface
        self.homing_mode_buttons()
        #KEY BINDINGS DO NOT WORK
        for key in self.keys_to_bind:
            #self.bind_all(key, lambda event, k=key: self.input_frame.set_home(k[-2]))
            self.bind(key, lambda event, k=key: self.input_frame.set_home(k[-2]))


    def normal_mode_interface(self):

        #ADD NORMAL MODE INTERFACE BUTTONS
        self.input_frame.start_az_entry.grid()
        self.input_frame.start_az_label.grid()
        self.input_frame.end_az_entry.grid()
        self.input_frame.end_az_label.grid()
        self.input_frame.start_elbeam_entry.grid()
        self.input_frame.start_elbeam_label.grid()
        self.input_frame.end_elbeam_entry.grid()
        self.input_frame.end_elbeam_label.grid()
        self.input_frame.speed_entry.grid()
        self.input_frame.speed_label.grid()
        self.input_frame.increment_entry.grid()
        self.input_frame.increment_label.grid()
        self.input_frame.repeat_entry.grid()
        self.input_frame.repeat_label.grid()
        self.input_frame.slip_detect_entry.grid()
        self.input_frame.slip_detect_label.grid()
        self.input_frame.mode_label.grid()
        self.input_frame.ppi_mode_radio_button.grid()
        self.input_frame.rhi_mode_radio_button.grid()
        self.input_frame.sector_mode_radio_button.grid()
        self.input_frame.rhi_square_mode_radio_button.grid()
        self.input_frame.spot_mode_radio_button.grid()
        #remove homing_mode_buttons
        self.exit_homing_mode.grid_remove()
        self.set_home_button.grid_remove()
        self.last_saved_button.grid_remove()
        self.left_button.grid_remove()
        self.right_button.grid_remove()
        self.up_button.grid_remove()
        self.down_button.grid_remove()
        self.qualifier_box.grid_remove()
        #DEAL WITH BUTTONS

        self.button_mode("normal")
        self.stop_scan_button.configure(state = "normal")



    def homing_mode_buttons(self):
        self.exit_homing_mode = customtkinter.CTkButton(self.input_frame, text= "Exit", command = lambda: self.set_home("X"))
        self.exit_homing_mode.grid(column = 0, row = 3, sticky="nes", padx=10, pady=5)

        self.set_home_button = customtkinter.CTkButton(self.input_frame, text= "Set Home '/'", command = lambda: self.set_home("/"))
        self.set_home_button.grid(column = 0, row = 4, sticky="nes", padx=10, pady=5)

        self.last_saved_button = customtkinter.CTkButton(self.input_frame, text= "Last Saved ' '", command = lambda: self.set_home(" "))
        self.last_saved_button.grid(column = 0, row = 5, sticky="nes", padx=10, pady=5)



        self.qualifier_box = customtkinter.CTkComboBox(self.input_frame, values = self.qualifier_values, state="readonly")
        self.qualifier_box.set(self.qualifier_values[0])
        self.qualifier_box.grid(column = 2, row = 3, sticky="w")

        self.left_button = customtkinter.CTkButton(self.input_frame, text="Left", width=30, command = lambda: self.movement_output("left", self.qualifier_box.get()))
        self.left_button.grid(column=4, row=5, sticky="ew")


        self.right_button = customtkinter.CTkButton(self.input_frame, text="Right", width=30, command = lambda: self.movement_output("right", self.qualifier_box.get()))
        self.right_button.grid(column =6, row=5, sticky="ew")


        self.up_button = customtkinter.CTkButton(self.input_frame, text="Up", width=30, command = lambda: self.movement_output("up", self.qualifier_box.get()))
        self.up_button.grid(column =5, row=4, sticky="ew")


        self.down_button = customtkinter.CTkButton(self.input_frame, text="Down", width=30, command = lambda: self.movement_output("down", self.qualifier_box.get()))
        self.down_button.grid(column =5, row=6, sticky="ew")

    def get_positioner_status(self):
        '''
        starting cat in background for first long running cat
        /x1a print issuing suspend
        print before bg for backgrounding cat
        print before fg for foregrounding
        :return:
        '''
        got_output = False
        scan_mode_variable = ""
        run_status_variable = ""
        self.output_frame.output_entry.configure(state="normal")
        self.input_frame.positioner_status_label.configure(text="Checking status")
        try:
            client, channel = self.fl_network_mode()
        except:
            self.input_frame.positioner_status_label.configure(text="Network Error")
            return 1
        # # channel = self.alex_home_network_mode()
        self.input_frame.positioner_status_label.configure(text="Checking status")
        # HOMING MODE CHECK
        ttyf = "/dev/ttyUSB1"
        print("STARTING CAT IN BACKGROUND OF GET POSITIONER STATUS")
        channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
        # START CAT IN BACKROUND
        channel.send(f"cat {ttyf} &\n")
        time.sleep(.1)
        channel.send(f"echo \r")
        print("FOREGROUNDING CAT IN POSITIONER STATUS #1")
        channel.send("fg\n")
        output = ""
        output_check = ""
        try:
            output_check = channel.recv(4096).decode("iso-8859-1")
            print("H-mode MODE CHECK INPUT")
            print(repr(output_check))
        except:
            print("h-mode MODE AFTER TRY")

        #CHECK THIS SLEEP TIME, WAS 2
        time.sleep(.1)

        time.sleep(.1)
        print("SUSPEND AND BACKGROUND CAT IN POSITIONER STATUS #1")
        channel.send(f"\x1a")
        time.sleep(.1)
        channel.send("bg\n")
        # End Homing mode check
        if "[HOME    ]" in output_check or "home" in output_check:
            self.input_frame.positioner_status_label.configure(text="Homing mode")
            self.homing_mode_interface("yes")
            return 1

        time.sleep(.1)
        print("FOREGROUNDING CAT TO IN POSITIONER STATUS #2 - SENDING SCAN STATUS")

        channel.send(f"echo scan status > {ttyf}\n")
        channel.send("fg\n")
        time.sleep(.1)
        print("SUSPEND AND BACKGROUND CAT IN POSITIONER STATUS #2")
        channel.send("bg\n")
        time.sleep(0.1)
        channel.send(f"\x1a")
        time.sleep(.1)

        if "[HOME    ]" in output_check or "home" in output_check:
            self.input_frame.positioner_status_label.configure(text="Homing mode")
            self.homing_mode_interface("yes")
            return 1

        start_az_variable = ""
        end_az_variable = ""
        el_axis_start_end_variable = []
        el_beam_start_end_variable = []

        # NORMAL STATUS CHECK
        try:
            print("IN INITIAL TRY")
            output = channel.recv(8192).decode("iso-8859-1")
            print(repr(output))
            if "[HOME    ]" in output or "home" in output:
                self.input_frame.positioner_status_label.configure(text="Homing mode")
                self.homing_mode_interface("yes")
                return 1
            # print(output)
            if "MUST HOME" in output or "homed?" in output:
                run_status_variable = 2
            time.sleep(.1)
            output_status = output.split(":~$ scan status", 1)
            output_lines = output_status[1].split("\r")
            got_output = True
            for index, line in enumerate(output_lines):
                if "Mode: " in line:
                    scan_mode_variable = line.split("Mode:")[1]
                if "Run:" in line:
                    run_status_variable = line.split("Run:")[1]
                    run_status_variable = int(run_status_variable.strip())
                if "Start Az:" in line:
                    start_az_variable = line.split("Start Az:")[1]
                if "End Az:" in line:
                    end_az_variable = line.split("End Az:")[1]
                if "El (axis) Start:" in line:
                    el_axis_start_end_variable = line.split("El (axis)")[1]
                if "El (beam) Start:" in line:
                    el_beam_start_end_variable = line.split("El (beam)")[1]
                self.output_frame.output_entry.insert("end", line)
                if "Attenuations:" in line:
                    # self.status_text_box.insert(tk.END, "\r")
                    channel.close()
                    break
        except:
            self.output_frame.output_entry.delete("0.0", "end")
            # channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
            # channel.send(f"cat {ttyf} &\n")
            print('SENDING ECHO SCAN STATUS IN EXCEPTION IF INITIAL COMMAND DID NOT WORK')
            channel.send(f"echo scan status > {ttyf}\n")
            time.sleep(.1)
            print("FOREGROUNDING CAT IN POSITIONER STATUS #3")
            channel.send("fg\n")
            time.sleep(0.1)
            print("BACKGROUNDING CAT IN POSITIONER STATUS #3")
            channel.send("bg\n")
            time.sleep(0.1)
            channel.send(f'x\x1a')
            output = channel.recv(8192).decode("iso-8859-1")
            #print(output)
            if "MUST HOME" in output_check or "homed?" in output_check:
                self.input_frame.positioner_status_label.configure(text="Homing mode")
                self.homing_mode_interface("yes")
                return 1
            output_status = output.split("scan status", 1)
            output_lines = output_status[1].split("\r")
            got_output = True
            for index, line in enumerate(output_lines):
                if "Mode: " in line:
                    scan_mode_variable = line.split("Mode:")[1]
                    scan_mode_variable = scan_mode_variable.strip().split(", ")[1]
                if "Run:" in line:
                    run_status_variable = line.split("Run:")[1]
                    run_status_variable = int(run_status_variable.strip())
                if "Start Az:" in line:
                    start_az_variable = line.split("Start Az: ")[1]
                if "End Az:" in line:
                    end_az_variable = line.split("End Az: ")[1]
                    # self.input_frame.end_entry.delete("0.0", "end")
                    # self.input_frame.end_az_entry.insert(0, end_az_variable)
                if "El (axis) Start:" in line:
                    el_axis_start_end_variable = line.split("El (axis)")[1]
                if "El (beam) Start:" in line:
                    el_beam_start_end_variable = line.split("El (beam)")[1]
                self.output_frame.output_entry.insert(tk.END, line)
                if "Attenuations:" in line:
                    # self.status_text_box.insert(tk.END, "\r")
                    break
        try:
            if not run_status_variable and not got_output:
                for line in output.split("\n"):
                    self.output_frame.output_entry.insert("end", line)
            # if scan_mode_variable:
            #     scan_mode_variable = scan_mode_variable.strip().split(", ")[1]
            #     print(f"SCAN MODE VARIABLE {scan_mode_variable}")

            # start_az_variable = f"Start Az: {float(start_az_variable.strip()):.2f}"
            # end_az_variable = f"End Az: {float(end_az_variable.strip()):.2f}"
            # el_axis_start_end_variable = el_axis_start_end_variable.strip().split(" ")
            # el_axis_start = f"El (axis) Start: {float(el_axis_start_end_variable[1].split(',')[0]):.2f}"
            # el_axis_end = f"El (axis) End: {float(el_axis_start_end_variable[3]):.2f}"
            # el_beam_start_end_variable = el_beam_start_end_variable.strip().split(" ")
            # el_beam_start = f"El (beam) Start: {float(el_beam_start_end_variable[1].split(',')[0]):.2f}"
            # el_beam_end = f"El (beam) End: {float(el_beam_start_end_variable[3]):.2f}"

            # if run_status_variable:
            #     run_status_variable = int(run_status_variable.strip())
            #
            #     print("RUN STATUS VARIABLE: ", run_status_variable)
            if run_status_variable == 1:
                self.input_frame.positioner_status_label.configure(
                    text=f"Running {scan_mode_variable} on {state.radar_choice.get()}", fg_color="green4")
            elif run_status_variable == 0:
                self.input_frame.positioner_status_label.configure(text="Stopped", fg_color="red")
            elif run_status_variable == 2:
                self.input_frame.positioner_status_label.configure(text="Please Home", fg_color="orange")
            else:
                self.input_frame.positioner_status_label.configure(text="Error", fg_color="yellow", text_color = "black")

        except:
            self.output_frame.output_entry.delete("0.0", "end")
            self.output_frame.output_entry.insert("0.0", "Connection Error, please try again")
        finally:
            # print("SUSPENDING AND BACKGROUNDING CAT")
            # channel.send(f"\x1a")
            # channel.send("bg\n")
            channel.close()
            client.close()
            self.output_frame.output_entry.configure(state="disabled")
            print("RUN STATUS VARIABLE: ", run_status_variable)
            return run_status_variable
