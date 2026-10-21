import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import paramiko
from dotenv import load_dotenv
import nmap
import os
import sys
import logging
import time
import threading
import queue
import re
from datetime import datetime
import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
import subprocess
from pathlib import Path
from scipy.interpolate import griddata
import customtkinter

from network_toggle import NetworkSwitch
import state

dir_path = Path("./captureMode")
dir_path.mkdir(parents=True, exist_ok=True)

dir_path = Path("./generatedHeatmaps")
dir_path.mkdir(parents=True, exist_ok=True)

if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    application_path = os.path.dirname(sys.executable)
else:
    # Running in a normal Python environment
    application_path = os.path.dirname(os.path.abspath(__file__))

dotenv_path = os.path.join(application_path, '.env')
load_dotenv(dotenv_path=dotenv_path)

is_fpga_running = False


class RadarFunctionality2(customtkinter.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.command_list_label = None
        self.dash_w_label = None
        self.dash_w_entry = None
        self.dash_s_label = None
        self.dash_s_entry = None
        self.dash_e_label = None
        self.dash_e_entry = None
        self.dash_b_label = None
        self.dash_b_entry = None
        self.dash_g_label = None
        self.dash_g_entry = None
        self.dash_capital_S_label = None
        self.dash_capital_S_entry = None
        self.dash_capital_D_label = None
        self.dash_capital_D_entry = None
        self.az_label = None
        self.az_entry = None
        self.el_label = None
        self.el_entry = None
        self.x_power_label = None
        self.x_power_entry = None
        self.y_power_label = None
        self.y_power_entry = None
        self.status_label = None
        self.status_entry = None

        self.timestamp = None
        self.current_radar = None

        self.dash_w_var = tk.DoubleVar()
        self.dash_s_var = tk.DoubleVar()
        self.dash_e_var = tk.DoubleVar()
        self.dash_b_var = tk.DoubleVar()
        self.dash_g_var = tk.DoubleVar()
        self.dash_capital_S_var = tk.IntVar()
        self.dash_eight_var = tk.IntVar()
        self.dash_nine_var = tk.IntVar()
        self.dash_capital_D_var = tk.IntVar()
        self.dash_y_var = tk.DoubleVar()
        self.dash_capital_V_var = tk.DoubleVar()
        self.dash_capital_C_var = tk.DoubleVar()

        self.columnconfigure(0, weight=10)
        self.columnconfigure(1, weight=10)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # INNER FRAMES
        self.fpga_control_frame = customtkinter.CTkFrame(self)
        self.fpga_control_frame.grid(row=0, column=2, sticky="nsew")
        self.fpga_control_frame.grid_columnconfigure(0, weight=1)
        self.fpga_control_frame.grid_rowconfigure(list(range(0, 7)), weight=1)
        # self.fpga_control_frame.grid_columnconfigure(1, weight=1)

        self.radar_control_frame = customtkinter.CTkFrame(self)
        self.radar_control_frame.grid(row=1, column=2, sticky="nsew")
        self.radar_control_frame.grid_columnconfigure(0, weight=1)
        self.radar_control_frame.grid_rowconfigure(list(range(0, 4)), weight=1)

        self.output_frame = customtkinter.CTkFrame(self)
        self.output_frame.grid(column=0, row=0, rowspan=2, sticky="nsew")
        self.output_frame.grid_columnconfigure(list(range(0, 3)), weight=2)
        # self.output_frame.grid_columnconfigure(4, weight=1)
        # self.output_frame.grid_columnconfigure(1, weight=1)
        self.output_frame.rowconfigure(list(range(0, 19)), weight=1)
        # self.output_frame.grid_propagate(False)

        self.toolbar_frame = customtkinter.CTkFrame(self.output_frame, height=20)
        self.toolbar_frame.grid_propagate(False)
        # self.network_state = "Wifi"


        # infrastructure
        self.run_heatmap_fpga_button = customtkinter.CTkButton(self.fpga_control_frame, text="Collect Heatmap Data",
                                                               command=lambda: self.start_threading(self.heat_map_fpga))
        self.run_heatmap_fpga_button.grid(row=0, column=0)
        self.run_heatmap_fpga_button.configure(width=200, font=("Arial", 14))
        #
        # self.run_capture_fpga_button= tk.Button(self.fpga_control_frame, text="Capture FPGA", command=lambda:self.capture_fpga())
        # self.run_capture_fpga_button.grid(row=1, column=2)
        # self.run_capture_fpga_button.config(width=20, font=("Arial", 20))

        # Dont need a stop button because the runs with self terminate
        self.abort_fpga_button = customtkinter.CTkButton(self.fpga_control_frame, text="Abort FPGA",
                                                         command=lambda: self.start_threading(self.kill_fpga))
        self.abort_fpga_button.grid(column=0, row=2)
        self.abort_fpga_button.configure(width=200, font=("Arial", 14))

        self.create_heatmap_button = customtkinter.CTkButton(self.fpga_control_frame, text="Draw Heatmap",
                                                             command=lambda: self.create_heatmap())
        self.create_heatmap_button.grid(column=0, row=1)
        self.create_heatmap_button.configure(width=200, font=("Arial", 14))

        self.capture_packets_button = customtkinter.CTkButton(self.fpga_control_frame, text="Capture Raw Packets",
                                                              command=lambda: self.start_threading(
                                                                  self.capture_packets_run))
        self.capture_packets_button.grid(column=0, row=3)
        self.capture_packets_button.configure(width=200, font=("Arial", 14))

        self.close_heatmap_button = None

        self.canvas = None
        self.progress_bar = None
        self.progress_bar_stage = 0

        # self.power_queue = queue.Queue()
        self.latest_values = None
        # self.values_lock = threading.Lock()

        self.csv_queue = queue.Queue()
        self.raw_csv_queue = queue.Queue()
        #
        # self.csv_file = None
        # self.csv_writer = None

        self.initial_output_frame()

        self.update_textboxes()

    def create_ssh_client(self):
        client = paramiko.client.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())

        return client

    def csv_writer_worker(self, timestamp):
        csv_file = None
        csv_writer = None
        try:
            while True:
                item = self.csv_queue.get()

                try:
                    if item is None:
                        break
                    if csv_file is None:
                        # timestamp = datetime.now().strftime("%m%d_%H%M%S")

                        filename = os.path.join(
                            application_path,
                            f"heatmap_{timestamp}.csv"
                        )

                        csv_file = open(
                            filename,
                            "w",
                            newline="",
                            buffering=1
                        )

                        csv_writer = csv.writer(csv_file)

                        csv_writer.writerow([
                            "Azimuth",
                            "Elevation",
                            "X Power",
                            "Y Power"
                        ])

                    csv_writer.writerow(item)
                finally:
                    self.csv_queue.task_done()
        finally:
            if csv_file is not None:
                csv_file.close()

    def raw_csv_writer_worker(self, timestamp):
        # timestamp = datetime.now().strftime("%m%d_%H%M%S")

        filename = os.path.join(
            application_path,
            f"RAW_OUTPUT_{timestamp}.csv"
        )
        with open(
                filename,
                'w',
                newline='',
                encoding='utf-8',
        ) as f:
            writer = csv.writer(f)
            writer.writerow(['raw_data'])

            while True:
                data = self.raw_csv_queue.get()
                try:
                    if data is None:
                        break
                    writer.writerow([data])
                finally:
                    self.raw_csv_queue.task_done()

    # def close_values_csv(self):
    #     if self.csv_file is not None:
    #         self.csv_file.close()
    #     self.csv_file = None
    #     self.csv_writer = None

    def initial_output_frame(self):
        self.az_var = tk.StringVar(value="0")
        self.el_var = tk.StringVar(value="0")
        self.x_power_var = tk.StringVar(value="0")
        self.y_power_var = tk.StringVar(value="0")
        self.status_var = tk.StringVar(value="Not Running")

        self.setup_initial_input_outputs()

        self.status_label = customtkinter.CTkLabel(self.output_frame, text="Status:", justify="center")
        self.status_label.grid(column=0, row=15, sticky="e", pady=10, padx=20)
        self.status_label.configure(font=("Arial", 14))
        self.status_entry = customtkinter.CTkEntry(self.output_frame, width = 200, textvariable=self.status_var, justify="center")
        self.status_entry.grid(column=1, row=15, pady=10, sticky="w")
        self.status_entry.configure(font=("Arial", 14))

    def heat_map_fpga(self):
        self.timestamp = datetime.now().strftime("%m%d_%H%M%S")

        self.csv_thread = threading.Thread(
            target=self.csv_writer_worker,
            args=(self.timestamp,),
            daemon=True
        )
        self.raw_csv_thread = threading.Thread(
            target=self.raw_csv_writer_worker,
            args=(self.timestamp,),
            daemon=True
        )

        self.csv_thread.start()
        self.raw_csv_thread.start()
        #self.raw_csv_queue.put((0, 0, 0, 0))
        # try:
        #     print(f"-w {self.dash_w_var.get()} -s {self.dash_s_var.get()} -e {self.dash_e_var.get()} -b {self.dash_b_var.get()} -g {self.dash_g_var.get()} -S {self.dash_capital_S_var.get()} -8 {int(self.dash_eight_var.get())} -9 {int(self.dash_nine_var.get())} -X -D {self.dash_capital_D_var.get()}")
        # except:
        #     input_warning = messagebox.showwarning("Warning", "Inputs entered incorrectly.")
        #     return 1
        # if not self.dash_eight_var.get() or not self.dash_nine_var.get():
        #     input_warning = messagebox.showwarning("warning", "input values")
        #     return 1
        #
        # if state.starting_azimuth_value == "startaz" or state.ending_azimuth_value == "endaz" or state.starting_el_value == "start elbeam" or state.ending_el_value == "end elbeam":
        #     input_warning = messagebox.showwarning("Warning",
        #                                            f"Please enter values in the Positioner tab first.")
        # else:


        # self.csv_queue.put((0, 0, 0, 0))
        try:
            azDelta = float(state.ending_azimuth_value) - float(state.starting_azimuth_value)
            elDelta = float(state.ending_el_value) - float(state.starting_el_value)
            azDeegPerS = 360.0 / float(state.speed_value)
            elDegPerStep = float(state.increment_value) * 2.0
            expected_Q_Value = int((azDelta / azDeegPerS) * (elDelta / elDegPerStep) * 2.0 * self.dash_capital_S_var.get() * 1.2)
            state.expected_Q_VALUE_VALUE = expected_Q_Value

            print(self.dash_capital_S_var.get(), elDelta, azDeegPerS, elDegPerStep, expected_Q_Value)
        except:
            pass
        print(f"EXPECTED Q VALUE: {state.expected_Q_VALUE_VALUE}")
        client, channel = self.fl_network_mode()
        # client, channel = self.alex_network_mode()
        # stdin, stdout, stderr = client.exec_command("ls")
        # print(stdout.read().decode('utf-8'))

        # HIDE INPUT / OUTPUTS
        self.hide_initial_i_o()
        self.create_heatmap_button.grid_remove()
        self.display_fpga_output()

        self.status_var.set("Starting FPGA")
        self.status_entry.configure(fg_color="green", text_color = "black")



        print("After connection to fl network")
        global is_fpga_running
        is_fpga_running = True
        time.sleep(.2)
        self.progress_bar_label = customtkinter.CTkLabel(self.output_frame, text="Progress: ", justify="center")
        self.progress_bar_label.grid(column=0, row=5, sticky="e", padx=20)
        self.progress_bar = ttk.Progressbar(self.output_frame, orient="horizontal", mode="determinate",
                                            style="yellow.Horizontal.TProgressbar", length=400,
                                            maximum=state.expected_Q_VALUE_VALUE)
        self.progress_bar.grid(column=1, row=5, sticky="w")
        self.progress_bar['value'] = 0

        try:
            channel.send(f"cd {os.environ['FPGAPATH']}\n")
            print(f"sent: cd {os.environ['FPGAPATH']}")
            time.sleep(.2)
            # 10/2
            channel.send(
                f"""./fpgaStream -w {self.dash_w_var.get()} -s {self.dash_s_var.get()} -e {self.dash_e_var.get()} -b {self.dash_b_var.get()} -g {self.dash_g_var.get()} -S {self.dash_capital_S_var.get()} -Q {state.expected_Q_VALUE_VALUE} -8 {int(self.dash_eight_var.get())} -9 {int(self.dash_nine_var.get())} -X -D {self.dash_capital_D_var.get()} -y {self.dash_y_var.get()} -V {self.dash_capital_V_var.get()} -C {self.dash_capital_C_var.get()} -u\n""")
            time.sleep(.2)
            print(f"FPGA RUNNING STATE: {is_fpga_running}")


        except:
            pass
        buffer = ""

        # regex accounts for zeros
        position_pattern = re.compile(
            r"position:\s*(?P<az>[+-]?\d+(?:\.\d+)?)\s+azimuth,\s*"
            r"[+-]?\d+(?:\.\d+)?,\s*plate,\s*"
            r"(?P<el>[+-]?\d+(?:\.\d+)?)\s+altitude"
        )

        # power_pattern = re.compile(
        #     r"X power:\s*(?P<xPow>[+-]?\d+\.\d+).*?"
        #     r"Y power:\s*(?P<yPow>[+-]?\d+\.\d+)"
        #     r"num:\s*(?P<num>\d+),"
        # )
        power_pattern = re.compile(
            r"X power:\s*(?P<xPow>[+-]?\d+\.\d+).*?"
            r"Y power:\s*(?P<yPow>[+-]?\d+\.\d+).*?"
            r"num:\s*(?P<num>\d+),"
        )

        failure_pattern = re.compile(
            r"failure", re.IGNORECASE
        )

        max_buffer_length = 0

        try:
            last_position = None

            self.status_var.set("RUNNING")
            while channel.active and is_fpga_running:

                if channel.recv_ready():
                    data = channel.recv(1024).decode("iso-8859-1")
                    # TODO PRINT COMMAND TO VIEW DATA
                    # print(repr(data))

                    # PUTTING RAW DATA INTO RAW CSV
                    self.raw_csv_queue.put(data)
                    buffer += data

                    if len(buffer) > max_buffer_length:
                        max_buffer_length = len(buffer)
                        print(f"New max buffer size: {max_buffer_length:,} characters")

                    # print(repr(buffer))
                    captured_match = re.search(r"Captured\s+(\d+)\s+packets\.", buffer)
                    if captured_match:
                        captured_count = int(captured_match.group(1))
                        print(f"FPGA FINISHED: captured {captured_count} packets")
                        is_fpga_running = False
                        break

                    failure_match = failure_pattern.search(buffer)
                    if failure_match:
                        print("FPGA FAILURE")
                        is_fpga_running = False
                        break

                    while True:
                        position_match = position_pattern.search(buffer)
                        power_match = power_pattern.search(buffer)

                        if position_match is None and power_match is None:
                            break

                        if position_match is not None and (
                                power_match is None or position_match.start() < power_match.start()):
                            last_position = position_match

                            buffer = buffer[position_match.end():]
                            continue

                        if power_match is not None:
                            if last_position is not None:
                                az = float(last_position.group("az"))
                                el = float(last_position.group("el"))
                                x_power = float(power_match.group("xPow"))
                                y_power = float(power_match.group("yPow"))
                                num_value = int(power_match.group('num'))
                                # THIS WILL UPDATE PROGRESS BAR
                                # self.update_progressbar(num_value, expected_Q_Value)
                                self.update_progressbar(num_value)

                                self.latest_values = (az, el, x_power, y_power)
                                self.csv_queue.put((az, el, x_power, y_power))

                                last_position = None
                            buffer = buffer[power_match.end():]
                            continue
                elif channel.recv_stderr_ready():
                    print("FPGA FAILURE")
                    err = channel.recv_stderr(1024).decode("iso-8859-1")
                    print("STDERR:", err)
                elif channel.exit_status_ready():
                    print("Exit status:", channel.recv_exit_status())


        except Exception as e:
            import traceback
            print(f"ERROR DURING FPGASTREAM PROCESSING FOR HEATMAP: {e}")
            traceback.print_exc()

        finally:
            is_fpga_running = False
            if channel is not None:
                try:
                    channel.send("^S\n")
                    channel.send("^C\n")
                    channel.send("\x03")
                    time.sleep(0.2)
                except Exception as e:
                    pass
            if client is not None:
                client.close()
            self.csv_queue.put(None)
            self.raw_csv_queue.put(None)
            if self.csv_thread is not None:
                self.csv_thread.join()
            if self.raw_csv_thread is not None:
                self.raw_csv_thread.join()
            print("RUN FINISHED")
            self.status_var.set("FINISHED")
            self.status_entry.configure(fg_color="white", text_color="black")
            self.progress_bar_stage = 0
            self.progress_bar.destroy()
            self.progress_bar_label.destroy()
            # print(f"Maximum buffer size: {max_buffer_length:,} characters")
            self.hide_fpga_output()
            self.replace_initial_i_o()
            self.create_heatmap_button.grid()

    def capture_packets_run(self):
        Q_VALUE = 10000
        self.hide_initial_i_o()
        self.progress_bar_label = customtkinter.CTkLabel(self.output_frame, text="Progress: ", justify="center")
        self.progress_bar_label.grid(column=0, row=5, sticky="e", padx=20)

        self.progress_bar = ttk.Progressbar(self.output_frame, orient="horizontal", mode="determinate",
                                            style="yellow.Horizontal.TProgressbar", length=400,
                                            maximum=Q_VALUE)
        self.progress_bar.grid(column=1, row=5, sticky="w",padx=50)
        self.progress_bar['value'] = 0
        #TODO SEE IF THIS EXECUTES CORRECTLY
        self.command_list_label = customtkinter.CTkLabel(self.output_frame,
                                                         text=f"""Command String: -w {self.dash_w_var.get()} -s {self.dash_s_var.get()} -e {self.dash_e_var.get()} -b {self.dash_b_var.get()} -g {self.dash_g_var.get()} 
        -S {self.dash_capital_S_var.get()} -Q {state.expected_Q_VALUE_VALUE} -8 {int(self.dash_eight_var.get())} -9 {int(self.dash_nine_var.get())} 
        -X -D {self.dash_capital_D_var.get()} -y {self.dash_y_var.get()} -V {self.dash_capital_V_var.get()} -C {self.dash_capital_C_var.get()} -u""")
        self.command_list_label.grid(column=0, columnspan=2, row=12)
        self.command_list_label.configure(font=("Arial", 14), justify="center")

        self.status_var.set("Capture Run Started")
        self.status_entry.configure(fg_color="green", text_color="white")
        global is_fpga_running
        is_fpga_running = True
        # Todo make sure this works correctly. No cues but based off of -Q 10000
        try:
            target_directory = "./captureMode"
            subprocess.run(['socat', 'tcp-l:7777,reuseaddr,fork', 'system:\'cpio -i\''], cwd=target_directory,
                           check=True)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with exit code {e.returncode}")

        client, channel = self.fl_network_mode()
        print("After connection to fl network")
        time.sleep(.2)
        channel.send(f"cd {os.environ['FPGAPATH']}\n")
        print(f"sent: cd {os.environ['FPGAPATH']}")

        # CMD LINE 10/2
        #TODO NEED NEW COMMAND LAPTOP
        channel.send(
            #f"""./fpgaStream -w {self.dash_w_var.get()} -s {self.dash_s_var.get()} -e {self.dash_e_var.get()} -b {self.dash_b_var.get()} -g {self.dash_g_var.get()} -S {self.dash_capital_S_var.get()} -k 8000 -Q 10000 -q -c -y 6.25 -V {1 / self.dash_w_var.get()} -C 0.05 -u | socat - tcp:10.42.0.1:7777\n""")
        # EXAMPLE STREAM'./fpgaStream -S 300 -D 10 -u -w 0.96 -s 2.0 -e 2.0 -b 0.0 -g -1.0 -y 5.8 -V 6.3 -C 0.1 -k 8000 -q -Q 3000 -n'
            f'./fpgaStream -S {self.dash_capital_S_var.get()} -D {self.dash_capital_D_var.get()} -u -w {self.dash_w_var.get()} -s {self.dash_s_var.get()} -e {self.dash_e_var.get()} -b {self.dash_b_var.get()} -g {self.dash_g_var.get()} -y {self.dash_y_var.get()} -V {self.dash_capital_V_var.get()} -C {self.dash_capital_C_var.get()} -k 10000 -q -Q {10 * self.dash_capital_S_var.get()} -n | socat - tcp:10.42.0.1:7777\n '
        )
        time.sleep(.1)

        num_pattern = re.compile(
            r"num:\s*(?P<num>\d+),\s*"
        )

        buffer = ''
        while channel.active and is_fpga_running:
            if channel.recv_ready():
                data = channel.recv(1024).decode("iso-8859-1")
                buffer += data
                num_match = num_pattern.search(buffer)

                captured_match = re.search(r"Captured\s+(\d+)\s+packets\.", buffer)
                if captured_match:
                    captured_count = int(captured_match.group(1))
                    print(f"FPGA FINISHED: captured {captured_count} packets")
                    is_fpga_running = False
                    break

                if num_match:
                    num_value = int(num_match.group("num"))
                    self.update_progressbar(num_value)

        channel.close()
        client.close()
        self.create_heatmap_button.grid()
        self.status_var.set("Capture Run Finished")
        self.status_entry.configure(fg_color="white", text_color="black")
        self.progress_bar_stage = 0
        self.progress_bar_label.destroy()
        self.progress_bar.destroy()
        self.replace_initial_i_o()
        self.command_list_label.grid_remove()

    def update_progressbar(self, value):
        '''
        Updates the progress bar, update_idletasks forces a gui refresh so this might not be optimal but
        I won't know until testing. The other option would be to create a .after(x, update_progressbar) function
        INCLUDE MAx num for color change?
        '''
        # twenty_five = int(max_num * .25)
        # fifty = int(max_num * .5)
        # seventy_five = int(max_num * .75)
        self.progress_bar['value'] = value
        # if self.progress_bar_stage == 0 and value > twenty_five:
        #     self.progress_bar.config(style="red.Horizontal.TProgressbar")
        #     self.progress_bar_stage = 1
        # if self.progress_bar_stage == 1 and value > fifty:
        #     self.progress_bar.config(style="blue.Horizontal.TProgressbar")
        #     self.progress_bar_stage = 2
        # if self.progress_bar_stage == 2 and value > seventy_five:
        #     self.progress_bar.config(style="green.Horizontal.TProgressbar")
        #     self.progress_bar_stage = 3

        # self.update_idletasks()

    def kill_fpga(self):
        if self.az_label is not None:
            self.hide_fpga_output()
            self.create_heatmap_button.grid()
        if self.progress_bar is not None:
            self.progress_bar.destroy()
        if self.command_list_label is not None:
            self.command_list_label.grid_remove()
        self.replace_initial_i_o()
        global is_fpga_running
        is_fpga_running = False
        self.status_var.set("Running Abort")
        self.status_entry.configure(fg_color="orange")
        password = f"{os.environ.get('CONNECTION_PASSWORD')}"
        client, channel = self.fl_network_mode()
        try:
            channel.send("ps auxfww | grep '[f]pgaStream'\n")

            output = ""
            time.sleep(.1)
            while channel.recv_ready():
                output += channel.recv(4096).decode("iso-8859-1")

            open_pids = []

            for line in output.splitlines():
                parts = line.split()
                if len(parts) > 1:
                    pid = parts[1]
                    if pid.isdigit():
                        open_pids.append(pid)

            for pid in open_pids:
                stdin, stdout, stderr = client.exec_command(f"sudo -S -p '' kill -9 {pid}\n")
                stdin.write(f"{password}\n")
                stdin.flush()

                exit_status = stdout.channel.recv_exit_status()
                error = stderr.read().decode("utf-8", errors="replace")

                if exit_status != 0:
                    print(f"Failed to kill process: {error}")

                # channel.send(f"sudo kill -9 {pid}\n")
                # time.sleep(.1)
                #
                # while channel.recv_ready():
                #     chunk = channel.recv(4096).decode("iso-8859-1")
                #     if "password for sq:" in chunk and password:
                #         channel.send(f"{password}\n")
        finally:
            client.close()
            self.status_var.set("Abort Finished")
            self.csv_queue.put(None)
            self.raw_csv_queue.put(None)
            if self.csv_thread is not None:
                self.csv_thread.join()
            if self.raw_csv_thread is not None:
                self.raw_csv_thread.join()
            print("RUN FINISHED")
            self.status_var.set("FINISHED")
            self.status_entry.configure(fg_color="white", text_color="black")

            self.progress_bar_stage = 0

    def start_threading(self, funct, *args):
        # TODO THE FOLLOWING GETS THE RADAR SELECTED IN THE HEADER
        radar_choice = state.radar_choice.get()
        radar_dict = state.radars_found.get_dict()
        print(f"INSIDE HEATMAP FPGA {radar_dict[radar_choice]}")

        # check for fpga_heat_map vs abort and capture
        self.current_radar_key = state.radar_choice.get()
        for key, value in state.radars_found.get_dict().items():
            if key == self.current_radar_key:
                self.current_radar_value = value
        print(f"INSIDE FLORIDA {self.current_radar_value}")
        print(funct.__name__)
        if self.current_radar_value == "--------" or self.current_radar_value is None:
            self.status_var.set("Please Select A Radar")
            self.status_entry.configure(fg_color="yellow", text_color="Black")
            return
        else:
            if funct.__name__ == "continuous_waveform" or funct.__name__ == "standard_60_waveform":
                thread = threading.Thread(
                    target=funct,
                    args=args,
                    daemon=True
                )
                thread.start()
            else:
                error_code = self.check_inputs(funct.__name__)
                if error_code == 0:
                    thread = threading.Thread(
                        target=funct,
                        args=args,
                        daemon=True
                    )
                    thread.start()
                else:
                    self.status_var.set("Check Inputs")

    # def alex_network_mode(self):
    #     self.curent_radar = self.radar_dict[self.radar_selected.get()]
    #     print(self.current_radar)
    #     try:
    #         client = self.create_ssh_client()
    #         client.connect(hostname=f"{self.current_radar}", username=f"{os.environ.get('CONNECTION_USERNAME')}",
    #                    password=f"{os.environ.get('CONNECTION_PASSWORD')}", look_for_keys=False, allow_agent=False)
    #         transport = client.get_transport()
    #         channel = transport.open_session()
    #         channel.get_pty()
    #         channel = client.invoke_shell()
    #         time.sleep(.1)
    #         logging.info("CONNECTED TO ALEX")
    #         return client, channel
    #     except:
    #         self.status_var.set("Network Error")
    #         self.status_entry.config(background="red")

    def fl_network_mode(self):
        self.current_radar_key = state.radar_choice.get()
        for key, value in state.radars_found.get_dict().items():
            if key == self.current_radar_key:
                self.current_radar_value = value
        print(f"INSIDE FLORIDA {self.current_radar_value}")
        self.status_var.set("Connecting to radar...")
        self.status_entry.configure(fg_color="yellow green", text_color="black")
        try:
            client = self.create_ssh_client()
            client.connect(hostname=f"{self.current_radar_value}", username=f"{os.environ.get('CONNECTION_USERNAME')}",
                           password=f"{os.environ.get('CONNECTION_PASSWORD')}", look_for_keys=False, allow_agent=False, timeout=10)
            # print(f"{self.positioner_selected_for_use} inside status")
            # print(f"{selected_positioner_global} GLOBAL status")
            transport = client.get_transport()
            channel = transport.open_session()
            channel.get_pty()
            channel = client.invoke_shell()
            time.sleep(.1)
            logging.info("CONNECTED TO FLORIDA NETWORK")
            return client, channel
        except:
            self.status_var.set("Network Error")
            self.status_entry.configure(fg_color="red", text_color="white")


    def update_textboxes(self):
        if self.latest_values is not None:
            # az, el, absAz, absEl, xPower, yPower = self.latest_values
            az, el, xPower, yPower = self.latest_values
            self.az_var.set(f"{az}")
            self.el_var.set(f"{el}")
            self.x_power_var.set(f"{xPower}")
            self.y_power_var.set(f"{yPower}")
        self.after(20, self.update_textboxes)

    def create_heatmap(self):
        # self.current_radar = self.radar_dict[self.radar_selected.get()]
        print(self.current_radar)
        '''
        Will Create a heatmap based on data accumulated by heat_map_fpga.
        Does not have protections against faulty data.
        calculation is currently based off of X POWER.
        :return:
        '''
        if self.az_label is not None:
            self.remove_output_network_widgets()
            self.heat_map_specific_hide()
        else:
            self.hide_initial_i_o()
            self.heat_map_specific_show()
        self.hide_initial_i_o()
        self.heat_map_specific_hide()
        self.status_label.grid_remove()
        self.status_entry.grid_remove()
        azimuth_raw = []
        elevation_raw = []
        x_power_raw = []
        y_power_raw = []

        csv_file = filedialog.askopenfilename(
            initialdir=".",
            title="Choose a folder",
            filetypes=[
                ("csv files", "*.csv"),
                ("All Files", "*.*")
            ]
        )
        print(f"CHOSEN CSV{csv_file}")
        #TODO DOES NOT WORK IF THE FILE IS CHOSEN IN A DIFFERENT DIRECTORY
        if not csv_file:
            self.replace_initial_i_o()
            self.heat_map_specific_show()
            return

        with open(csv_file, "r", newline="") as file:
            reader = csv.reader(file)

            next(reader, None)
            for row in reader:
                if len(row) < 4:
                    continue
                try:
                    azimuth_raw.append(float(row[0]))
                    elevation_raw.append(float(row[1]))
                    x_power_raw.append(float(row[2]))
                    y_power_raw.append(float(row[3]))
                except ValueError:
                    continue
        if not azimuth_raw or not elevation_raw or not x_power_raw or not y_power_raw:
            raise ValueError("No valid data")
        azimuth = np.array(azimuth_raw)
        elevation = np.array(elevation_raw)
        x_power = np.array(x_power_raw)

        # NEW HEATMAP CREATION
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            az_grid = np.linspace(azimuth.min(), azimuth.max(), 500)
            el_grid = np.linspace(elevation.min(), elevation.max(), 500)

            AZ, EL = np.meshgrid(az_grid, el_grid)

            POWER = griddata(
                (azimuth, elevation),
                x_power,
                (AZ, EL),
                method="linear",
            )

            peak_index = np.nanargmax(POWER)

            peak_el, peak_az = np.unravel_index(
                peak_index,
                POWER.shape
            )

            peak_azimuth = AZ[peak_el, peak_az]
            peak_elevation = EL[peak_el, peak_az]
            peak_power = POWER[peak_el, peak_az]
            ax.plot(
                peak_azimuth,
                peak_elevation,
                marker="x",
                markersize=12,
                markeredgewidth=3,
                color="black"
            )

            ax.annotate(
                f"{peak_azimuth:.2f}, {peak_elevation:.2f}",
                (peak_azimuth, peak_elevation),
                xytext=(-10, -20),
                textcoords="offset points",
                color="black",

            )
            heatmap = ax.pcolormesh(
                AZ,
                EL,
                POWER,
                shading="auto",
                cmap="inferno",
            )

            heatmap = ax.contour(
                AZ,
                EL,
                POWER,
                shading="auto",
                cmap="inferno"
                # cmap="gray
            )

            # plt.fig(4, 6)

            fig.colorbar(heatmap, ax=ax, label="X Power (dB)")
            ax.set_xlabel("Azimuth (degrees)")
            ax.set_ylabel("Elevation (degrees)")
            ax.set_title("X Power Heatmap")
            plt.tight_layout()
        except:
            self.replace_initial_i_o()
            self.heat_map_specific_show()
            return

        # TODO Hide this initial version of HEATMAP FOR NOW
        # heatmap = np.full(
        #     (len(elevation), len(azimuth)),np.nan
        # )
        # for az, el, p in zip(azimuth, elevation, x_power):
        #     az_index = np.where(azimuth == az)[0][0]
        #     el_index = np.where(elevation == el)[0][0]
        #
        #     heatmap[el_index, az_index] = p
        #
        # fig, ax = plt.subplots(figsize=(3.5,6))
        #
        # print("Number of oints:", len(azimuth))
        # print("Non-Nan heatmap values:", np.count_nonzero(~np.isnan(heatmap)))
        # print("Power min", np.nanmin(heatmap))
        # print("Power max", np.nanmax(heatmap))
        #
        # im = ax.imshow(
        #     heatmap,
        #     origin="lower",
        #     aspect="auto",
        #     extent =[
        #         azimuth.min(),
        #         azimuth.max(),
        #         elevation.min(),
        #         elevation.max()
        #     ],
        #     cmap="inferno",
        #     interpolation="nearest"
        #     #cmap=gray
        # )
        #
        # ax.set_xlabel("Azimuth")
        # ax.set_ylabel("Elevation")
        # ax.set_title("Linear X/Y Power")
        #
        # fig.colorbar(
        #     im,
        #     ax=ax,
        #     label="Power (dB)"
        # )

        # CREATE JPG IF IT DOESNT EXIT
        csv_path = Path(csv_file)
        output_dir = csv_path.parent / "generatedHeatmaps"
        current_heatmap_output = output_dir / (csv_path.stem + ".jpg")
        if not current_heatmap_output.exists():
            fig.savefig(
                current_heatmap_output,
                format="jpg",
                dpi=300,
                bbox_inches="tight"
            )

        def fixed_width_coord(x,y):
            return f'x={x:8.2f}, y={y:8.2f}'
        ax.format_coord = fixed_width_coord
        ax.fmt_xdata = lambda x: f"{x:8.2f}"
        ax.fmt_ydata = lambda y: f"{y:8.2f}"
        self.output_frame.grid(columnspan=2)
        self.canvas = FigureCanvasTkAgg(fig, self.output_frame)
        self.canvas.draw()
        # self.canvas.get_tk_widget().grid(column=0, columnspan=2, row=0, rowspan=4, sticky="nsew")
        self.canvas.get_tk_widget().grid(column=0, row=0, columnspan=2, rowspan=4, sticky="nsew")
        # canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        self.toolbar_frame = customtkinter.CTkFrame(self.output_frame, width=100, height=40)



        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()
        self.toolbar_frame.grid(column=0, row=4, sticky="sw")

        self.toolbar_frame.grid_propagate(False)

        #self.canvas.get_tk_widget().grid(column=0, columnspan=2, row=0, sticky="nsew")

        self.close_heatmap_button = customtkinter.CTkButton(self.fpga_control_frame, text="Close Heatmap",
                                                            command=lambda: self.close_heatmap())
        self.close_heatmap_button.grid(column=0, row=2)
        self.close_heatmap_button.configure(width=200, font=("Arial", 14))
        return self.canvas

    def close_heatmap(self):
        if self.canvas is not None:
            self.output_frame.grid(columnspan=1)
            plt.close(self.canvas.figure)
            self.canvas.get_tk_widget().destroy()

            self.canvas = None
            # self.heatmap_fig = None
            # self.heatmap_ax = None
        if self.toolbar_frame is not None:
            self.toolbar_frame.grid_remove()

        # Remove close button
        if self.close_heatmap_button is not None:
            self.close_heatmap_button.grid_remove()
            self.create_heatmap_button.grid()

            self.close_heatmap_button = None

        self.replace_initial_i_o()
        self.heat_map_specific_show()

        # self.initial_output_frame()

    def remove_output_network_widgets(self):
        self.az_entry.grid_remove()
        self.az_label.grid_remove()
        self.el_entry.grid_remove()
        self.el_label.grid_remove()
        self.x_power_entry.grid_remove()
        self.x_power_label.grid_remove()
        self.y_power_entry.grid_remove()
        self.y_power_label.grid_remove()
        #TODO JUST DID THIS
        # self.status_entry.grid_remove()
        # self.status_label.grid_remove()
        # self.dash_eight_entry.grid_remove()
        # self.dash_eight_label.grid_remove()
        # self.dash_nine_entry.grid_remove()
        # self.dash_nine_label.grid_remove()
        # self.create_heatmap_button.grid_remove()


    def replace_output_network_widgets(self):
        self.az_entry.grid()
        self.az_label.grid()
        self.el_entry.grid()
        self.el_label.grid()
        self.x_power_entry.grid()
        self.x_power_label.grid()
        self.y_power_entry.grid()
        self.y_power_label.grid()
        self.status_entry.grid()
        self.status_label.grid()
        self.dash_eight_entry.grid()
        self.dash_eight_label.grid()
        self.dash_nine_entry.grid()
        self.dash_nine_label.grid()
        self.close_heatmap_button.grid_remove()
        self.command_list_label.grid()


    def setup_initial_input_outputs(self):
        self.dash_w_label = customtkinter.CTkLabel(self.output_frame, text="w | Pulse width(ms):")
        self.dash_w_label.grid(column=0, row=0, sticky="e", padx=20)
        self.dash_w_label.configure(font=("Arial", 14))
        self.dash_w_entry = customtkinter.CTkEntry(self.output_frame, width=100, font=("Arial", 14), justify="center",
                                     textvariable=self.dash_w_var)
        self.dash_w_entry.grid(column=1, row=0, sticky="w")
        self.dash_w_var.set(0.96)

        self.dash_s_label = customtkinter.CTkLabel(self.output_frame, text="s | Pulse setup(ms):")
        self.dash_s_label.grid(column=0, row=1, sticky="e", padx=20)
        self.dash_s_label.configure(font=("Arial", 14))
        self.dash_s_entry = customtkinter.CTkEntry(self.output_frame, width=100, font=("Arial", 14), justify="center",
                                     textvariable=self.dash_s_var)
        self.dash_s_entry.grid(column=1, row=1, sticky="w")
        self.dash_s_var.set(2.0)

        self.dash_e_label = customtkinter.CTkLabel(self.output_frame, text="e | Pulse Holdover(ms):")
        self.dash_e_label.grid(column=0, row=2, sticky="e", padx=20)
        self.dash_e_label.configure(font=("Arial", 14))
        self.dash_e_entry = customtkinter.CTkEntry(self.output_frame, width=100, font=("Arial", 14), justify="center",
                                     textvariable=self.dash_e_var)
        self.dash_e_entry.grid(column=1, row=2, sticky="w")
        self.dash_e_var.set(2.0)

        self.dash_b_label = customtkinter.CTkLabel(self.output_frame, text="b | Rx Start:")
        self.dash_b_label.grid(column=0, row=3, sticky="e", padx=20)
        self.dash_b_label.configure(font=("Arial", 14))
        self.dash_b_entry = customtkinter.CTkEntry(self.output_frame,width=100, font=("Arial", 14), justify="center",
                                     textvariable=self.dash_b_var)
        self.dash_b_entry.grid(column=1, row=3, sticky="w")
        self.dash_b_var.set(0.0)

        self.dash_g_label = customtkinter.CTkLabel(self.output_frame, text="g | Rx stop:")
        self.dash_g_label.grid(column=0, row=4, sticky="e",padx=20)
        self.dash_g_label.configure(font=("Arial", 14))
        self.dash_g_entry = customtkinter.CTkEntry(self.output_frame, width=100,font=("Arial", 14), justify="center",
                                     textvariable=self.dash_g_var)
        self.dash_g_entry.grid(column=1, row=4, sticky="w")
        self.dash_g_var.set(-1.0)

        self.dash_capital_S_label = customtkinter.CTkLabel(self.output_frame, text="S | Pulse per s:")
        self.dash_capital_S_label.grid(column=0, row=5, sticky="e",padx=20)
        self.dash_capital_S_label.configure(font=("Arial", 14))
        self.dash_capital_S_entry = customtkinter.CTkEntry(self.output_frame, width=100,font=("Arial", 14), justify="center",
                                             textvariable=self.dash_capital_S_var)
        self.dash_capital_S_entry.grid(column=1, row=5, sticky="w")
        self.dash_capital_S_var.set(300)

        self.dash_capital_D_label = customtkinter.CTkLabel(self.output_frame, text="D | Read Before:")
        self.dash_capital_D_label.grid(column=0, row=6, sticky="e", padx=20)
        self.dash_capital_D_label.configure(font=("Arial", 14))
        self.dash_capital_D_entry = customtkinter.CTkEntry(self.output_frame, width=100,font=("Arial", 14), justify="center",
                                             textvariable=self.dash_capital_D_var)
        self.dash_capital_D_entry.grid(column=1, row=6, sticky="w")
        self.dash_capital_D_var.set(10)

        self.dash_eight_label = customtkinter.CTkLabel(self.output_frame, text="8 | Sample Start Offset:")
        self.dash_eight_label.grid(column=0, row=7, sticky="e", padx=20)
        self.dash_eight_label.configure(font=("Arial", 14))
        self.dash_eight_entry = customtkinter.CTkEntry(self.output_frame,width=100, font=("Arial", 14), justify="center",
                                         textvariable=self.dash_eight_var)
        self.dash_eight_entry.grid(column=1, row=7, sticky="w")
        self.dash_eight_var.set(0)

        self.dash_nine_label = customtkinter.CTkLabel(self.output_frame, text="9 | Sampling Length:")
        self.dash_nine_label.grid(column=0, row=8, sticky="e", padx=20)
        self.dash_nine_label.configure(font=("Arial", 14))
        self.dash_nine_entry = customtkinter.CTkEntry(self.output_frame,width=100, font=("Arial", 14), justify="center",
                                        textvariable=self.dash_nine_var)
        self.dash_nine_entry.grid(column=1, row=8, sticky="w")
        self.dash_nine_var.set(24)

        self.dash_y_label = customtkinter.CTkLabel(self.output_frame, text="y | FIR center frequency:")
        self.dash_y_label.grid(column=0, row=9, sticky="e", padx=20)
        self.dash_y_label.configure(font=("Arial", 14))
        self.dash_y_entry = customtkinter.CTkEntry(self.output_frame, width=100, font=("Arial", 14), justify="center", textvariable=self.dash_y_var)
        self.dash_y_entry.grid(column=1, row=9, sticky="w")
        self.dash_y_var.set(5.8)

        self.dash_capital_V_label = customtkinter.CTkLabel(self.output_frame, text="V | FIR Override:")
        self.dash_capital_V_label.grid(column=0, row=10, sticky="e", padx=20)
        self.dash_capital_V_label.configure(font=("Arial", 14))
        self.dash_capital_V_entry = customtkinter.CTkEntry(self.output_frame, width=100, font=("Arial", 14), justify="center",textvariable=self.dash_capital_V_var)
        self.dash_capital_V_entry.grid(column=1, row=10, sticky="w")
        self.dash_capital_V_var.set(6.3)

        self.dash_capital_C_label = customtkinter.CTkLabel(self.output_frame, text="C | FIR Parks width:")
        self.dash_capital_C_label.grid(column=0, row=11, sticky="e", padx=20)
        self.dash_capital_C_label.configure(font=("Arial", 14))
        self.dash_capital_C_entry = customtkinter.CTkEntry(self.output_frame, width=100, font=("Arial", 14), justify="center",textvariable=self.dash_capital_C_var)
        self.dash_capital_C_entry.grid(column=1, row=11, sticky="w")
        self.dash_capital_C_var.set(0.1)

        self.wave_form_label = customtkinter.CTkLabel(self.fpga_control_frame, text="Wave Form Commands", fg_color = "#2B2B2B", text_color = "#E5A93B")
        self.wave_form_label.grid(column=0, row=5, sticky='ew')
        self.wave_form_label.configure(font=("Arial", 14, "underline"))

        self.continuous_waveform_button = customtkinter.CTkButton(self.fpga_control_frame, width=10,
                                                                  text="Set Continuous Wave form",
                                                                  command=lambda: self.start_threading(
                                                                      self.continuous_waveform))
        self.continuous_waveform_button.grid(column=0, row=6)
        self.continuous_waveform_button.configure(width=200, font=("Arial", 14))

        self.standard_60_waveform_button = customtkinter.CTkButton(self.fpga_control_frame, width=10,
                                                                   text="Set 60 Wave form",
                                                                   command=lambda: self.start_threading(
                                                                       self.standard_60_waveform))
        self.standard_60_waveform_button.grid(column=0, row=7)
        self.standard_60_waveform_button.configure(width=200, font=("Arial", 14))

    def continuous_waveform(self):
        try:
            w_var = str(self.dash_w_var.get())
        except:
            input_warning = messagebox.showwarning("Warning", "Please enter valid Pulse Width")
            return 1

        client, channel = self.fl_network_mode()
        # client.exec_command(f"bash /home/sq/sq/stormquant-beta/scripts/siggen-program-cw-variable.sh {w_var}\n")
        stdin, stdout, stderr = client.exec_command(
            f"bash /home/sq/sq/stormquant-beta/scripts/siggen-program-cw-variable.sh {w_var}\n")
        print("STDOUT:")
        print(stdout.read().decode())
        print("STDERR:")
        print(stderr.read().decode())
        channel.close()
        client.close()
        self.continuous_waveform_button.configure(fg_color="green")
        self.standard_60_waveform_button.configure(fg_color="#1F6AA5")

    def standard_60_waveform(self):

        client, channel = self.fl_network_mode()
        stdin, stdout, stderr = client.exec_command(f"bash /home/sq/sq/stormquant-beta/scripts/siggen-program-60.sh\n")
        print("STDOUT:")
        print(stdout.read().decode())

        print("STDERR:")
        print(stderr.read().decode())
        channel.close()
        client.close()
        self.continuous_waveform_button.configure(fg_color="#1F6AA5")
        self.standard_60_waveform_button.configure(fg_color="green")

    def hide_initial_i_o(self):
        self.dash_w_label.grid_remove()
        self.dash_w_entry.grid_remove()
        self.dash_s_label.grid_remove()
        self.dash_s_entry.grid_remove()
        self.dash_e_label.grid_remove()
        self.dash_e_entry.grid_remove()
        self.dash_b_label.grid_remove()
        self.dash_b_entry.grid_remove()
        self.dash_g_label.grid_remove()
        self.dash_g_entry.grid_remove()
        self.dash_capital_S_label.grid_remove()
        self.dash_capital_S_entry.grid_remove()
        self.dash_capital_D_label.grid_remove()
        self.dash_capital_D_entry.grid_remove()
        self.dash_eight_label.grid_remove()
        self.dash_eight_entry.grid_remove()
        self.dash_nine_label.grid_remove()
        self.dash_nine_entry.grid_remove()
        self.dash_y_label.grid_remove()
        self.dash_y_entry.grid_remove()
        self.dash_capital_C_label.grid_remove()
        self.dash_capital_C_entry.grid_remove()
        self.dash_capital_V_label.grid_remove()
        self.dash_capital_V_entry.grid_remove()



    def heat_map_specific_hide(self):
        # TODO DOUBLE CHECK IF WORKING CORRECTLY
        self.abort_fpga_button.grid_remove()
        self.create_heatmap_button.grid_remove()
        self.status_label.grid_remove()
        self.status_entry.grid_remove()

    def heat_map_specific_show(self):
        self.status_label.grid()
        self.status_entry.grid()
        self.abort_fpga_button.grid()
        self.create_heatmap_button.grid()

    def replace_initial_i_o(self):
        self.dash_w_label.grid()
        self.dash_w_entry.grid()
        self.dash_s_label.grid()
        self.dash_s_entry.grid()
        self.dash_e_label.grid()
        self.dash_e_entry.grid()
        self.dash_b_label.grid()
        self.dash_b_entry.grid()
        self.dash_g_label.grid()
        self.dash_g_entry.grid()
        self.dash_capital_S_label.grid()
        self.dash_capital_S_entry.grid()
        self.dash_capital_D_label.grid()
        self.dash_capital_D_entry.grid()
        self.dash_eight_label.grid()
        self.dash_eight_entry.grid()
        self.dash_nine_label.grid()
        self.dash_nine_entry.grid()
        self.dash_y_label.grid()
        self.dash_y_entry.grid()
        self.dash_capital_C_label.grid()
        self.dash_capital_C_entry.grid()
        self.dash_capital_V_label.grid()
        self.dash_capital_V_entry.grid()


    def display_fpga_output(self):
        self.az_label = customtkinter.CTkLabel(self.output_frame, text="Az:")
        self.az_label.grid(column=0, row=0, sticky="E", padx=20)
        self.az_label.configure(font=("Arial", 14))
        self.az_entry = customtkinter.CTkEntry(self.output_frame, textvariable=self.az_var)
        self.az_entry.grid(column=1, row=0, sticky="W")
        self.az_entry.configure(font=("Arial", 14), justify="center")

        self.el_label = customtkinter.CTkLabel(self.output_frame, text="El:")
        self.el_label.grid(column=0, row=1, sticky="E", padx=20)
        self.el_label.configure(font=("Arial", 14))
        self.el_entry = customtkinter.CTkEntry(self.output_frame, textvariable=self.el_var)
        self.el_entry.grid(column=1, row=1, sticky="W")
        self.el_entry.configure(font=("Arial", 14), justify="center")

        self.x_power_label = customtkinter.CTkLabel(self.output_frame, text="X Power:")
        self.x_power_label.grid(column=0, row=2, sticky="E", padx=20)
        self.x_power_label.configure(font=("Arial", 14))
        self.x_power_entry = customtkinter.CTkEntry(self.output_frame, textvariable=self.x_power_var)
        self.x_power_entry.grid(column=1, row=2, sticky="W")
        self.x_power_entry.configure(font=("Arial", 14), justify="center")

        self.y_power_label = customtkinter.CTkLabel(self.output_frame, text="Y Power:")
        self.y_power_label.grid(column=0, row=3, sticky="E", padx=20)
        self.y_power_label.configure(font=("Arial", 14))
        self.y_power_entry = customtkinter.CTkEntry(self.output_frame, textvariable=self.y_power_var)
        self.y_power_entry.grid(column=1, row=3, sticky="W")
        self.y_power_entry.configure(font=("Arial", 14), justify="center")

        self.command_list_label = customtkinter.CTkLabel(self.output_frame, text=f"""Command String: \t-w {self.dash_w_var.get()} \t-s {self.dash_s_var.get()} \t-e {self.dash_e_var.get()} \t-b {self.dash_b_var.get()} \t-g {self.dash_g_var.get()} 
        \t-S {self.dash_capital_S_var.get()} \t-Q {state.expected_Q_VALUE_VALUE} \t-8 {int(self.dash_eight_var.get())} \t-9 {int(self.dash_nine_var.get())} 
        \t\t-X \t-D {self.dash_capital_D_var.get()} \t-y {self.dash_y_var.get()} \t-V {self.dash_capital_V_var.get()} \t-C {self.dash_capital_C_var.get()} -u""")
        self.command_list_label.grid(column=0,columnspan=2, row=12)
        self.command_list_label.configure(font=("Arial", 14), justify="center")

    def hide_fpga_output(self):
        self.az_label.grid_remove()
        self.az_entry.grid_remove()
        self.el_label.grid_remove()
        self.el_entry.grid_remove()
        self.x_power_label.grid_remove()
        self.x_power_entry.grid_remove()
        self.y_power_label.grid_remove()
        self.y_power_entry.grid_remove()
        self.command_list_label.grid_remove()

    def check_inputs(self, mode):
        print(state.starting_azimuth_value)
        try:
            print(
                f"-w {self.dash_w_var.get()} -s {self.dash_s_var.get()} -e {self.dash_e_var.get()} -b {self.dash_b_var.get()} -g {self.dash_g_var.get()} -S {self.dash_capital_S_var.get()} -8 {int(self.dash_eight_var.get())} -9 {int(self.dash_nine_var.get())} -X -D {self.dash_capital_D_var.get()}")
        except:
            input_warning = messagebox.showwarning("Warning", "Inputs entered incorrectly.")
            return 1
        if not self.dash_eight_var.get() or not self.dash_nine_var.get():
            input_warning = messagebox.showwarning("warning", "input values")
            return 1
        if mode == "heat_map_fpga":
            if state.starting_azimuth_value == "Start Az" or state.ending_azimuth_value == "End Az" or state.starting_el_value == "Start ElBeam" or state.ending_el_value == "End ElBeam":
                input_warning = messagebox.showwarning("Warning",
                                                       f"Please enter values in the Positioner tab first.")
                return 1
        return 0
