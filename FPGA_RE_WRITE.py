import logging
import tkinter as tk
import customtkinter
import socket
from tkinter import ttk, messagebox
from settings import *
import threading
import queue
import paramiko
#TODO NEED THIS LINE TO RUN
# from scp import SCPClient
import time
from dotenv import load_dotenv
import os
import sys
import subprocess
import nmap
from datetime import datetime
from pathlib import Path
from datetime import datetime
import glob
import shutil
import state

# Determine the correct path to the .env file
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    application_path = os.path.dirname(sys.executable)
else:
    # Running in a normal Python environment
    application_path = os.path.dirname(os.path.abspath(__file__))

dotenv_path = os.path.join(application_path, '.env')

# Load the .env file from the determined path
load_dotenv(dotenv_path=dotenv_path)
is_running = False
# client = paramiko.client.SSHClient()
output_queue = queue.Queue()


class MainFrame(customtkinter.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.columnconfigure(0, weight=10)
        self.columnconfigure(1, weight=10)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(list(range(0,20)), weight=1)
        self.grid_propagate(False)
        self.command_dict = {}
        self.entry_dict = {}
        self.status_var = tk.StringVar()
        self.current_radar_value = None
        self.CURRENT_FPGA_PID = None



        self.input_frame = customtkinter.CTkFrame(self)
        self.input_frame.grid(column=0, columnspan=2, row=0, rowspan=20, sticky="nsew")
        self.input_frame.grid_propagate(False)

        self.output_frame = customtkinter.CTkFrame(self)
        self.output_frame.grid_propagate(False)

        self.create_entries()

        self.status_entry = customtkinter.CTkEntry(self, textvariable=self.status_var, justify="center")
        self.status_entry.grid(column=2, row=5)
        self.status_var.set("Not connected")

        self.output_fpga_values = None
        self.update_all_textboxes()
        self.x_dc_offset_textbox_var = tk.StringVar()
        self.y_dc_offset_textbox_var = tk.StringVar()
        self.x_min_max_textbox_var = tk.StringVar()
        self.y_min_max_textbox_var = tk.StringVar()
        self.x_power_textbox_var = tk.StringVar()
        self.y_power_textbox_var = tk.StringVar()
        self.rate_textbox_var = tk.StringVar()

        self.commands_label = customtkinter.CTkLabel(master=self, text="Commands", text_color="#E5A93B", width=150)
        self.commands_label.grid(column=2, row=0)
        self.commands_label.configure(font=("Arial", 14, "underline"))

        self.button_end = customtkinter.CTkButton(self, text="End Run", command=lambda: self.start_threading(self.stop_order))
        self.button_end.grid(column=2, row=4)
        self.button_end.configure(width=150, font=("Arial", 14))

        self.button_reset = customtkinter.CTkButton(self, text="Reset", command=lambda: self.run_reset_radar())
        self.button_reset.grid(column=2, row=3)
        self.button_reset.configure(width=150, font=("Arial", 14))

        self.submit_button = customtkinter.CTkButton(self, text = "Run FPGA", command=lambda: self.start_threading(self.run_command_connect, False))
        self.submit_button.grid(column=2, row=1)
        self.submit_button.configure(width=150, font=("Arial", 14))

        self.capture_button = customtkinter.CTkButton(self, text = "Capture Run", command = lambda: self.start_threading(self.run_command_connect, True))
        self.capture_button.grid(column=2, row=2)
        self.capture_button.configure(text="Capture", width=150, font=("Arial", 14))

    def start_threading(self, func, *args):
        print("Starting Thread")
        self.status_var.set("Starting thread")

        thread = threading.Thread(
            target=func,
            args=args,
            daemon=True
        )
        thread.start()


    def create_entries(self):
        for index, entry in enumerate(FPGA_COMMAND_ALPHA):
            labels = CommandLabels(parent=self.input_frame, command_selected=entry, unit=COMMAND_UPDATE[entry]['unit'],
                                   text=COMMAND_UPDATE[entry]['title'], col=1, row=index)
            labels.insert(tk.END, COMMAND_UPDATE[entry]['title'])
            labels.configure(state="disabled")
            labels.configure(font=("Arial", 14))
            labels.configure(wrap="word")
            self.entry_dict[f'{entry }'] = tk.StringVar()

            entry = customtkinter.CTkEntry(self.input_frame, width=75, font=("Arial", 14),
                                           textvariable=self.entry_dict[f'{entry}'])
            if COMMAND_UPDATE[FPGA_COMMAND_ALPHA[index]]['default_value'] == 'True':
                entry.insert(15, f"{COMMAND_UPDATE[FPGA_COMMAND_ALPHA[index]]['default_value']}")
                entry.grid(column=0, row=index)
                self.command_dict[FPGA_COMMAND_ALPHA[index]] = COMMAND_UPDATE[FPGA_COMMAND_ALPHA[index]][
                    'default_value']
                entry.configure(state=tk.DISABLED)
            elif COMMAND_UPDATE[FPGA_COMMAND_ALPHA[index]]['default_value']:
                entry.insert(15, f"{COMMAND_UPDATE[FPGA_COMMAND_ALPHA[index]]['default_value']}")
                entry.grid(column=0, row=index)
                self.command_dict[FPGA_COMMAND_ALPHA[index]] = COMMAND_UPDATE[FPGA_COMMAND_ALPHA[index]][
                    'default_value']

    def update_all_textboxes(self):
        if self.output_fpga_values is not None:
            x_dc_offset, y_dc_offset, x_min_max, y_min_max, x_power, y_power, rate = self.output_fpga_values
            self.x_dc_offset_textbox_var.set(x_dc_offset)
            self.y_dc_offset_textbox_var.set(y_dc_offset)
            self.x_min_max_textbox_var.set(x_min_max)
            self.y_min_max_textbox_var.set(y_min_max)
            self.x_power_textbox_var.set(x_power)
            self.y_power_textbox_var.set(y_power)
            self.rate_textbox_var.set(rate)
        self.after(20, self.update_all_textboxes)

        # if output_queue.qsize() > 0:
        #     output_list = output_queue.get()
        #     x_dc_offset_value = output_list[0].split("= ")
        #     # self.x_dc_offset_textbox.delete("0.0", "end")
        #     # self.x_dc_offset_textbox.insert("0.0",x_dc_offset_value[1] )
        #     self.x_dc_offset_textbox_var.set(x_dc_offset_value[1])
        #     print(f"x_dc_offset_value: {x_dc_offset_value[1]}")
        #
        #     y_dc_offset_value = output_list[1].split("= ")
        #     # self.y_dc_offset_textbox.delete("0.0", "end")
        #     # self.y_dc_offset_textbox.insert("0.0", y_dc_offset_value[1] )
        #     self.y_dc_offset_textbox_var.set(y_dc_offset_value[1])
        #     print(f"y_dc_offset_value: {y_dc_offset_value[1]}")
        #
        #     x_min_max_value = output_list[2].split("X  ")
        #     # self.x_min_max_textbox.delete("0.0", "end")
        #     # self.x_min_max_textbox.insert("0.0", x_min_max_value[1] )
        #     self.x_min_max_textbox_var.set(x_min_max_value[1])
        #     print(f"x_min_max_value: {x_min_max_value[1]}")
        #
        #     y_min_max_value = output_list[3].split("Y  ")
        #     # self.y_min_max_textbox.delete("0.0", "end")
        #     # self.y_min_max_textbox.insert("0.0", y_min_max_value[1] )
        #     self.y_min_max_textbox_var.set(y_min_max_value[1] )
        #     print(f"y_min_max_value: {y_min_max_value[1]}")
        #
        #     x_power_value = output_list[4].split(": ")
        #     self.x_power_textbox_var.set(x_power_value[1])
        #     # self.x_power_textbox.delete("0.0", "end")
        #     # self.x_power_textbox.insert("0.0", x_power_value[1] )
        #
        #     y_power_value = output_list[5].split(": ")
        #     self.y_power_textbox_var.set(y_power_value[1])
        #     # self.y_power_textbox.delete("0.0", "end")
        #     # self.y_power_textbox.insert("0.0", y_power_value[1] )
        #     print(f"y_power_value: {y_power_value[1]}")
        #
        #     rate_value = output_list[6].split(": ")
        #     final_rate = rate_value[1].split("=")
        #     self.rate_textbox_var.set(final_rate[0])
        #     # self.rate_textbox.delete("0.0", "end")
        #     # self.rate_textbox.insert("0.0", final_rate[0] )
        #     print(f"final_rate: {final_rate[0]}")

    def create_output(self):
        self.output_frame.grid(column=0, row=0, columnspan=2, rowspan=20, sticky = "NSEW")
        self.output_frame.grid_columnconfigure(list(range(0,3)), weight=2)
        self.output_frame.rowconfigure(list(range(0,19)), weight=1)
        self.grid_propagate(False)
        for index, entry in enumerate(OUTPUT_FIELDS):
            output_labels = customtkinter.CTkLabel(self.output_frame, text=OUTPUT_FIELDS[index])
            output_labels.grid(column=0, row=index, sticky="e", padx=20)
            output_labels.configure(font=("Arial", 14), width = 100)
        self.x_dc_offset_textbox = customtkinter.CTkEntry(self.output_frame, justify="center", textvariable=self.x_dc_offset_textbox_var)
        self.x_dc_offset_textbox.configure(width = 100, height = 20)
        self.x_dc_offset_textbox.grid(column=1, row=0, pady=10, sticky="w")
        self.y_dc_offset_textbox = customtkinter.CTkEntry(self.output_frame, font=("Arial", 14), justify="center", textvariable=self.y_dc_offset_textbox_var)
        self.y_dc_offset_textbox.configure(width = 100, height = 20)
        self.y_dc_offset_textbox.grid(column=1, row=1, pady=10, sticky="w")
        self.x_min_max_textbox = customtkinter.CTkEntry(self.output_frame, font=("Arial", 14), justify="center", textvariable=self.x_min_max_textbox_var)
        self.x_min_max_textbox.configure(width = 100, height = 20)
        self.x_min_max_textbox.grid(column=1, row=2, pady=10, sticky="w")
        self.y_min_max_textbox = customtkinter.CTkEntry(self.output_frame, font=("Arial", 14), justify="center", textvariable=self.y_min_max_textbox_var)
        self.y_min_max_textbox.configure(width = 100, height = 20)
        self.y_min_max_textbox.grid(column=1, row=3, pady=10, sticky="w")
        self.x_power_textbox = customtkinter.CTkEntry(self.output_frame, font=("Arial", 14), justify="center", textvariable=self.x_power_textbox_var)
        self.x_power_textbox.configure(width = 100, height = 20)
        self.x_power_textbox.grid(column=1, row=4, pady=10, sticky="w")
        self.y_power_textbox = customtkinter.CTkEntry(self.output_frame, font=("Arial", 14), justify="center", textvariable=self.y_power_textbox_var)
        self.y_power_textbox.configure(width = 100, height = 20)
        self.y_power_textbox.grid(column=1, row=5, pady=10, sticky="w")
        self.rate_textbox = customtkinter.CTkEntry(self.output_frame, font=("Arial", 14), justify="center", textvariable =self.rate_textbox_var)
        self.rate_textbox.configure(width = 100, height = 20)
        self.rate_textbox.grid(column=1, row=6, pady=10, sticky="w")
        self.settings_label = customtkinter.CTkLabel(self.output_frame, text="Settings:")
        self.settings_label.configure(font=("Arial", 14))
        self.settings_label.grid(column=0, row=7, pady=10, padx=20, sticky="e")
        self.settings_textbox = customtkinter.CTkTextbox(self.output_frame, wrap="word", font=("Arial", 14))
        self.settings_textbox.configure(width = 200, height = 30)
        self.settings_textbox.grid(column=1, row=7, pady=10, sticky="ew")

    def display_settings(self):
        commands = ""
        for key, value in self.entry_dict.items():
            commands += f" {key} {value} "

        commands.strip()
        self.settings_textbox.delete("0.0", "end")
        self.settings_textbox.insert("0.0", commands)


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

    def stop_order(self):
        self.status_var.set("Stopping order...")


        client, channel = self.fl_network_mode()

        if self.CURRENT_FPGA_PID:
            stdin, stdout, stderr = client.exec_command(f"kill -9 {self.CURRENT_FPGA_PID}")
            print(f"STDOUT: {stdout.read().decode('utf-8')}")
            print(f"STDERR: {stderr.read().decode('utf-8')}")

            global is_running
            is_running = False
            self.status_var.set("Run Stopped")
        else:
            self.status_var.set("Stop order failed")

        channel.close()
        client.close()
        self.CURRENT_FPGA_PID = None


    def run_reset_radar(self):
        print(state.radar_choice.get())
        self.current_radar_key = state.radar_choice.get()
        for key, value in state.radars_found.get_dict().items():
            if key == self.current_radar_key:
                self.current_radar_value = value
        print(f"INSIDE FLORIDA {self.current_radar_value}")

        client, channel = self.fl_network_mode()

        self.status_var.set("Running Reset...")
        channel.send("ps auxfww | grep fpgaStream\n")
        time.sleep(1)
        while channel.recv_ready():
            chunk = channel.recv(1024).decode("iso-8859-1")

        grep_results = chunk.split("\n")
        open_pids = []
        for i, line in enumerate(grep_results):
            if i == 0:
                pass
            else:
                lister = line.split()
                if len(lister) > 5:
                    open_pids.append(lister[1])
        for pid in open_pids:
            channel.send(f"sudo kill -9 {pid}\n")
            time.sleep(1)
            while channel.recv_ready():
                chunk = channel.recv(1024).decode("iso-8859-1")
                if "password for sq:" in chunk:
                    channel.send(f"{os.environ.get('CONNECTION_PASSWORD')}\n")

        channel.send(f"cd {os.environ.get('FPGAPATH')}\n")
        time.sleep(1)
        channel.send(f"./fpgaStream -r; sudo rmmod xdma; sudo modprobe xdma \n")
        time.sleep(3)
        while channel.recv_ready():
            chunk = channel.recv(1024).decode("iso-8859-1")
            if "password for sq:" in chunk:
                channel.send(f"{os.environ.get('CONNECTION_PASSWORD')}\n")
        client.close()
        print("Reset FINISHED")
        self.status_var.set("Reset FINISHED")




    def run_command_connect(self, capture_check):
        global is_running
        is_running = True
        is_capture_run = False

        command = ""
        for key, value in self.entry_dict.items():
            if value.get() == "True":
                command += f" {key} "
                continue
            command += f" {key} {value.get()}"

        try:
            client, channel = self.fl_network_mode()
        except ValueError:
            print("Network Error")
            is_running = False
            return 1

        #HIDE INPUTS AND SHOW OUTPUTS
        self.hide_inputs()
        self.create_output()

        print(f"COMMAND:{command.strip()}")
        self.settings_textbox.tag_config("center", justify="center")
        self.settings_textbox.delete("0.0", "end")
        self.settings_textbox.insert("0.0", command.strip(), "center")

        if capture_check:
            #is_capture_run = True
            self.status_var.set("Capture Run Starting")
        else:
            self.status_var.set("Starting Stream")
        try:
            time.sleep(0.1)
            channel.send(f"cd {os.environ['FPGAPATH']}\n")
            time.sleep(.1)
            channel.send(f"./fpgaStream {command}\n")
            time.sleep(.1)

            max_duration = 2000
            start_time = time.time()
            output = ""

            # while channel.recv_ready() and is_running:
            print("IS RUNNING", is_running)
            print("IS CAPTURE", is_capture_run)
            channel.settimeout(5)
            stdin, stdout,stderr = client.exec_command("pgrep -n fpgaStream")
            self.CURRENT_FPGA_PID = stdout.read().decode('utf-8').strip()
            print(self.CURRENT_FPGA_PID)
            while channel.active and is_running:
                buffer = channel.recv(1024).decode("iso-8859-1")
                print(f"OUTPUT FROM RUN BUFFER: {repr(buffer)}")
                output += buffer

                #TODO CURRENT TRY
                if "Captured 10000 packets." in output:
                    is_capture_run = True
                    print("FINISHED GATHERING PACKETS")
                    break

                if "failed reading" in output or "FAILED READING" in output:
                    print("FAILED READING FOUND IN OUTPUT")
                    self.status_var.set("Failed Reading")
                    self.status_entry.configure(fg_color="red", text_color="white")
                    self.hide_outputs()
                    self.show_inputs()
                    client.close()
                    channel.close()
                    is_running = False
                    return 1
                if "\x1b[1;1H$<5>" in buffer:
                    try:
                        clean_buffer = buffer.replace("\x1b[1;1H$<5>", "")
                        fields = [field.strip() for field in clean_buffer.split(",")]
                        x_dc_offset_value = fields[0].split("=", 1)[1].strip()
                        y_dc_offset_value = fields[1].split("=", 1)[1].strip()
                        x_min_max_value = fields[2].split("X  ", 1)[1].strip()
                        y_min_max_value = fields[3].split("Y  ", 1)[1].strip()
                        x_power_value = fields[4].split(": ", 1)[1].strip()
                        y_power_value = fields[5].split(": ", 1)[1].strip()

                        rate_value = fields[9].split(":", 1)[1].strip()
                        final_rate = rate_value.split("=", 1)[0].strip()

                        self.output_fpga_values = (
                            x_dc_offset_value,
                            y_dc_offset_value,
                            x_min_max_value,
                            y_min_max_value,
                            x_power_value,
                            y_power_value,
                            final_rate,
                        )

                        #print("FPGA VALUES:", self.output_fpga_values)
                    except (ValueError, IndexError) as e:
                        print(e)
                        continue
                    except socket.timeout:
                        print("CHANNEL TIME OUT")
                        channel.close()
                        client.close()
                        self.status_var.set("Channel Timed out")
                        self.hide_outputs()
                        self.show_inputs()
                        return 1

                        #TODO PREVIOUS TRY
                        # if "[1;1H$<5>" in after[1]:
                        #     new_output = after[1].replace("[1;1H$<5>", "\n")
                        #     new_output = new_output.split("\n")
                        #     for line in new_output:
                        #         print("FOR LINE IN OUTPUT: ", line)
                        #         splits = line.split(",")
                        #         desired_fields = []
                        #         for index, split in enumerate(splits):
                        #             if len(splits) == 11:
                        #                 if index < 6 or index == 9:
                        #                     desired_fields.append(split)
                        #         print(desired_fields)
                        #         output_queue.put(desired_fields)
                        # else:
                        #     new_output = after[1].replace("[1;1H$<5>", "\n")
                        #     new_output = new_output.split("\n")
                        #     for line in new_output:
                        #         print("ELSE LINE IN OUTPUT: ", line)
                        #         splits = line.split(",")
                        #         desired_fields = []
                        #         for index, split in enumerate(splits):
                        #             if len(splits) == 11:
                        #                 if index < 6 or index == 9:
                        #                     desired_fields.append(split)
                        #         print(desired_fields)
                        #         output_queue.put(desired_fields)


        except:
            self.status_var.set("Run Error")
            self.status_entry.configure(fg_color="red", text_color="white")
            self.hide_outputs()
            self.show_inputs()
            client.close()
            channel.close()
            is_running = False
            return 1
        if is_capture_run:
            self.status_var.set("Gathering capture files")
            self.get_bin_files()

        channel.close()
        client.close()
        self.status_entry.configure(fg_color="green", text_color="black")
        self.status_var.set("Run Finished")
        self.hide_outputs()
        self.show_inputs()
        return 0



    def get_bin_files(self):

        ## GET ACTUAL LOCATIONS HERE
        print(f"Gathering capture files")
        client, channel = self.fl_network_mode()


        try:
            #TODO GET THE RADAR I DONT THINK I HAVE TO

            #channel.send(f"cd {os.environ.get('FPGAPATH')}\n")
            #channel.send(f"cd {os.environ['FPGAPATH']}\n")
            stdin, stdout, stderr = client.exec_command(f"cd {os.environ['FPGAPATH']} && pwd")
            print(stdout.read().decode())
            time.sleep(0.5)


            stdin, stdout, stderr = client.exec_command("pwd")
            print(f"{stdout.read().decode()}")
            now = datetime.now()
            formatted_time = now.strftime("%m-%d-%H-%M")
            bin_files = glob.glob(f"{os.environ['FPGAPATH']}/*.bin")
            print(f"{bin_files} BIN FILES")
            new_directory = f"raw-bin-{formatted_time}"
            stdin, stdout, stderr = client.exec_command(f"mkdir -p '{os.environ['FPGAPATH']}/{new_directory}/'")
            print(f"{new_directory} CREATED")
            stdin, stdout, stderr = client.exec_command(f"cp {os.environ['FPGAPATH']}/daq0080*.bin '{os.environ['FPGAPATH']}/{new_directory}/'")
            transfer_status = stdout.channel.recv_exit_status()
            print(f"{transfer_status} of bins")
            stdin, stdout, stderr = client.exec_command(
                f"cd {os.environ['FPGAPATH']} && tar -czvf '{new_directory}.tgz' '{new_directory}'"
                #f"tar -czvf '{os.environ['FPGAPATH']}/{new_directory}.tgz' '{os.environ['FPGAPATH']}/{new_directory}/'"
                )
            exit_status = stdout.channel.recv_exit_status()
            print(f"{exit_status}")


            stdin, stdout, stderr = client.exec_command(f"rm {os.environ['FPGAPATH']}/*.bin")
            exit_status = stdout.channel.recv_exit_status()
            print(f"{exit_status}")


            #TODO NEED THESE TWO LINES TO RUN
            # with SCPClient(client.get_transport()) as scp:
            #     scp.get(f"{os.environ['FPGAPATH']}/raw-bin-{formatted_time}.tgz", "./generatedBinFiles/")
                #todo unnecessary if exe exists on file
                #scp.get("/home/sq/sq/stormquant-beta/cmake-build-debug/common/raytestingutils/convertRawToCleartext", "../ClearText/")
                #os.chmod("../ClearText/convertRawToCleartext", 0o755)
        except Exception as e:
            print(f"An error has occurred: {e}")

        finally:
            #todo add threading if this works
            self.status_var.set("Capture Finished")
            client.close()

    def run_queue(self):

        print(output_queue.qsize())
        try:
            if not output_queue.empty():
                self.after(20, self.update_all_textboxes())
        except:
            print("Error occured")

    def hide_inputs(self):
        self.input_frame.grid_remove()

    def show_outputs(self):
        self.create_output()

    def show_inputs(self):
        self.input_frame.grid()

    def hide_outputs(self):
        self.output_frame.grid_remove()



class CommandLabels(customtkinter.CTkTextbox):
    def __init__(self, parent, unit, col, text, row, command_selected, wrap = tk.CHAR):
        super().__init__(master = parent, width = 150, height = 30)
        self.unit = unit
        self.text = text
        self.col = col
        self.row = row
        self.command_selected = command_selected
        self.wrap = wrap
        self.font = ("Times New Roman", 14)
        self.grid(column = col, row = row, sticky = "W")
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        self.configure(state = "normal")
        self.grid(column=self.col, row=self.row)
        self.delete("1.0", tk.END)
        self.insert(tk.END, COMMAND_UPDATE[self.command_selected]['text'])
        self.configure(width=450)
        self.configure(state = "disabled")

    def on_leave(self, event):
        self.configure(state="normal")
        self.grid(column = self.col, row = self.row)
        self.delete("1.0", tk.END)
        self.insert(tk.END, COMMAND_UPDATE[self.command_selected]['title'])
        self.configure(width=150)
        self.configure(state="disabled")

