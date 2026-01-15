import tkinter as tk
from tkinter import ttk, messagebox
from settings import *
import threading
import queue
import paramiko
import time
from dotenv import load_dotenv
import os
import sys
import subprocess
import nmap

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
client = paramiko.client.SSHClient()
output_queue = queue.Queue()


class MainFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background = "Gray")
        self.command_dict = {}
        self.entry_dict = {}
        self.columnconfigure(0, weight=6)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.grid_propagate(False)

        self.io_frame = IOFrame(self, self.command_dict, self.entry_dict)
        self.io_frame.grid(column=0, row = 0, sticky = "NSEW")

        self.control_frame = ControlFrame(self, self.command_dict, self.entry_dict, self.io_frame)
        self.control_frame.grid(column=1, row = 0, sticky = "NSEW")


class IOFrame(tk.Frame):
    def __init__(self, parent, command_dict, entry_dict):
        super().__init__(parent, background = "red")
        self.command_dict = command_dict
        self.entry_dict = entry_dict
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.grid_propagate(False)

        self.input_frame = InputFrame(self, self.command_dict, self.entry_dict)
        self.input_frame.grid(column=0, row = 0, sticky = "NSEW")
        self.input_frame.create_entries()

        self.output_frame = OutputFrame(self)



    def show_input_frame_hide_output_frame(self):
        self.input_frame.grid(column=0, row = 0, sticky = "NSEW")
        self.output_frame.grid_forget()
    def hide_input_frame_show_output_frame(self):
        self.input_frame.grid_forget()
        self.output_frame.grid(column=0, row = 0, sticky = "NSEW")
        self.output_frame.create_output()


class InputFrame(tk.Frame):
    def __init__(self, parent, entry_dict, command_dict):
        super().__init__(parent, background="gray7")
        self.rowconfigure(list(range(11)), weight=1)
        self.entry_dict = entry_dict
        self.command_dict = command_dict
        self.tf_list = ["True", "False"]
        self.tf_selected = None


    def create_entries(self):
        for index, entry in enumerate(FPGA_COMMAND_ALPHA):
            labels = CommandLabels(parent = self,command_selected= entry, unit=COMMAND_UPDATE[entry]['unit'], text = COMMAND_UPDATE[entry]['title'], col=1, row = index)
            labels.insert(tk.END, COMMAND_UPDATE[entry]['title'])
            labels.config(state = "disabled")
            labels.config(font = ("Arial", 20))
            labels.config(wrap="word")
            self.entry_dict[f'entry_{[index]}'] = tk.StringVar()

            entry = ttk.Entry(self, width=10, font = ("Arial", 20), textvariable=self.entry_dict[f'entry_{[index]}'])
            if COMMAND_UPDATE[FPGA_COMMAND_ALPHA[index]]['default_value'] == 'True':
                entry.insert(15, f"{COMMAND_UPDATE[FPGA_COMMAND_ALPHA[index]]['default_value']}")
                entry.grid(column=0, row=index, sticky="NS")
                self.command_dict[FPGA_COMMAND_ALPHA[index]] = COMMAND_UPDATE[FPGA_COMMAND_ALPHA[index]][
                    'default_value']
                entry.config(state=tk.DISABLED)
            elif COMMAND_UPDATE[FPGA_COMMAND_ALPHA[index]]['default_value']:
                entry.insert(15, f"{COMMAND_UPDATE[FPGA_COMMAND_ALPHA[index]]['default_value']}")
                entry.grid(column = 0, row = index, sticky = "NS")
                self.command_dict[FPGA_COMMAND_ALPHA[index]] = COMMAND_UPDATE[FPGA_COMMAND_ALPHA[index]]['default_value']


class OutputFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background = "dark gray")
        # self.command_dict = parent.command_dict
        # self.entry_dict = parent.entry_dict
        self.rowconfigure(list(range(8)), weight=1)


    def update_all_textboxes(self, output_list):
        x_dc_offset_value = output_list[0].split("= ")
        self.x_dc_offset_textbox.replace("1.0", tk.END, x_dc_offset_value[1], "center")
        self.x_dc_offset_textbox.tag_configure("center", justify="center")
        y_dc_offset_value = output_list[1].split("= ")
        self.y_dc_offset_textbox.replace("1.0", tk.END, y_dc_offset_value[1], "center")
        self.y_dc_offset_textbox.tag_configure("center", justify="center")
        x_min_max_value = output_list[2].split("X  ")
        self.x_min_max_textbox.replace("1.0", tk.END, x_min_max_value[1], "center")
        self.x_min_max_textbox.tag_configure("center", justify="center")
        y_min_max_value = output_list[3].split("Y  ")
        self.y_min_max_textbox.replace("1.0", tk.END, y_min_max_value[1], "center")
        self.y_min_max_textbox.tag_configure("center", justify="center")
        x_power_value = output_list[4].split(": ")
        self.x_power_textbox.replace("1.0", tk.END, x_power_value[1], "center")
        self.x_power_textbox.tag_configure("center", justify="center")
        y_power_value = output_list[5].split(": ")
        self.y_power_textbox.replace("1.0", tk.END, y_power_value[1], "center")
        self.y_power_textbox.tag_configure("center", justify="center")
        rate_value = output_list[6].split(": ")
        final_rate = rate_value[1].split("=")
        self.rate_textbox.replace("1.0", tk.END, final_rate[0], "center")
        self.rate_textbox.tag_configure("center", justify="center")

    def create_output(self):
        for index, entry in enumerate(OUTPUT_FIELDS):
            output_labels = tk.Label(self, text=OUTPUT_FIELDS[index])
            output_labels.grid(column=0, row=index, sticky="NSEW")
            output_labels.config(font = ("Arial", 20))
        self.x_dc_offset_textbox = tk.Text(self, font=("Arial", 20))
        self.x_dc_offset_textbox.grid(column=1, row=0, sticky="NSEW")
        self.y_dc_offset_textbox = tk.Text(self, font=("Arial", 20))
        self.y_dc_offset_textbox.grid(column=1, row=1, sticky="NSEW")
        self.x_min_max_textbox = tk.Text(self, font=("Arial", 20))
        self.x_min_max_textbox.grid(column=1, row=2, sticky="NSEW")
        self.y_min_max_textbox = tk.Text(self, font=("Arial", 20))
        self.y_min_max_textbox.grid(column=1, row=3, sticky="NSEW")
        self.x_power_textbox = tk.Text(self, font=("Arial", 20))
        self.x_power_textbox.grid(column=1, row=4, sticky="NSEW")
        self.y_power_textbox = tk.Text(self, font=("Arial", 20))
        self.y_power_textbox.grid(column=1, row=5, sticky="NSEW")
        self.rate_textbox = tk.Text(self, font=("Arial", 20))
        self.rate_textbox.grid(column=1, row=6, sticky="NSEW")
        self.settings_label = tk.Label(self, text="Settings")
        self.settings_label.config(font = ("Arial", 20))
        self.settings_label.grid(column=0, row=7, sticky="NSEW")
        self.settings_textbox = tk.Text(self, wrap="word", font=("Arial", 20))
        self.settings_textbox.grid(column=1, row=7, sticky="NSEW")

    def display_settings(self, settings):
        commands = settings.split(" ")
        print(commands)
        output_string = ""
        for command in commands:
            if command == "-u":
                output_string += f"{COMMAND_UPDATE[command]['shorthand']}: True"
            elif command in COMMAND_UPDATE.keys():
                output_string += f"{COMMAND_UPDATE[command]['shorthand']}: "
            else:
                output_string += f"{command}, "

        self.settings_textbox.insert(tk.END, output_string)


class ControlFrame(tk.Frame):
    def __init__(self, parent, command_dict, entry_dict, io_frame):
        super().__init__(parent, background = "red")
        self.io_frame = io_frame
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.radars_available_frame = RadarsAvailableFrame(self)
        self.radars_available_frame.grid(column=0, row = 0, sticky = "NSEW")

        self.button_frame = ButtonFrame(self, command_dict, entry_dict, self.radars_available_frame, self.io_frame)
        self.button_frame.grid(column=0, row = 1, sticky = "NSEW")


class RadarsAvailableFrame(tk.Frame):
    radar_dict = {"sq-radar-1-DUMMY": "192.168.0.120", "sq-radar-2": "192.168.0.136"}
    def __init__(self, parent):
        super().__init__(parent, background = "steel blue")
        self.radar_selected = None
        self.radars_available = None
        self.columnconfigure(list(range(3)), weight=1)


    def radar_drop(self):
        self.radars_available = list(self.radar_dict.keys())
        self.radar_selected = tk.StringVar()
        self.radar_selected.set(self.radars_available[0])
        combo_drop = ttk.Combobox(self, textvariable=self.radar_selected, values = self.radars_available, state="readonly")
        combo_drop.grid(column=1, row=0, sticky="EW")
        combo_drop.config(width=10)
        combo_drop.config(font = ("Arial", 20))
        return self.radar_selected


    def find_other_radars(self):
        # client.load_system_host_keys()
        # client.connect(hostname="192.168.0.136", username=f"{os.environ.get('CONNECTION_USERNAME')}", password=f"{os.environ.get('CONNECTION_PASSWORD')}", look_for_keys=False, allow_agent=False)
        # transport = client.get_transport()
        # channel = transport.open_session()
        # channel.get_pty()
        # channel.invoke_shell()
        #
        # channel.send("nmap -sL 192.168.0.*\n")
        # time.sleep(2)
        # output = ""
        # while channel.recv_ready():
        #     chunk = channel.recv(1024).decode("iso-8859-1")
        #     output += chunk
        #     time.sleep(2)
        # self.update_radar_pulldown(output)
        # client.close()

        nm = nmap.PortScanner()
        nm.scan(hosts = "192.168.0.0/255", arguments = "-sL")
        for host in nm.all_hosts():
            self.update_radar_pulldown(host)

        # try:
        #     result = subprocess.run(["nmap", "-sL", "192.168.0.*\n"], capture_output=True)
        #     print(result.stdout)
        # except subprocess.CalledProcessError as e:
        #     print(f"Command Failed: {e.stderr}")


    def update_radar_pulldown(self, output):
        data = output.split("\n")
        for line in data:
            if "Nmap scan report for sq-radar-" in line:
                radar_key = line[21:31]
                radar_address = line[33:46]
                try:
                    if radar_key not in self.radar_dict:
                        self.radar_dict[radar_key] = radar_address
                        self.radar_drop()
                except:
                    print("ERROR")


    def run_reset_radar(self, command, hostname, username=f"{os.environ.get('CONNECTION_USERNAME')}", password=f"{os.environ.get('CONNECTION_PASSWORD')}"):
        client.load_system_host_keys()
        client.connect(hostname=hostname, username=username, password=password, look_for_keys=False, allow_agent=False)
        transport = client.get_transport()
        channel = transport.open_session()
        channel.get_pty()
        channel.invoke_shell()

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
                    channel.send(f"{password}\n")

        channel.send(f"cd {os.environ.get('FPGAPATH')}\n")
        time.sleep(1)
        channel.send(f"./fpgaStream {command}\n")
        time.sleep(3)
        while channel.recv_ready():
            chunk = channel.recv(1024).decode("iso-8859-1")
            if "password for sq:" in chunk:
                channel.send(f"{password}\n")
        client.close()

class ButtonFrame(tk.Frame):
    def __init__(self, parent, command_dict, entry_dict, radar_available_frame, io_frame):
        super().__init__(parent, background="gray20")
        self.radar_available_frame = radar_available_frame
        self.io_frame = io_frame
        self.columnconfigure(0, weight=1)
        self.rowconfigure(list(range(4)), weight=1)
        self.command_dict = command_dict
        self.entry_dict = entry_dict
        self.button_end = None
        self.button_reset = None
        self.network_check_button = None
        self.create_buttons()

    def stop_order(self):
        global is_running
        is_running = False
        self.io_frame.show_input_frame_hide_output_frame()

    def run_command_connect(self, command, hostname, username=f"{os.environ.get('CONNECTION_USERNAME')}", password=f"{os.environ.get('CONNECTION_PASSWORD')}"):
        global is_running
        is_running = True
        self.io_frame.hide_input_frame_show_output_frame()
        self.io_frame.output_frame.display_settings(command)
        client.load_system_host_keys()
        client.connect(hostname=hostname, username=username, password=password, look_for_keys=False, allow_agent=False)
        print("connected")
        transport = client.get_transport()
        channel = transport.open_session()
        channel.get_pty()
        channel.invoke_shell()
        channel.send(f"cd {os.environ['FPGAPATH']}\n")
        time.sleep(1)
        channel.send(f"./fpgaStream {command}\n")
        time.sleep(2)

        max_duration = 2000
        start_time = time.time()
        output = ""
        # while channel.recv_ready() and is_running:
        while channel.active and is_running:
            chunk = channel.recv(1024).decode("iso-8859-1")
            output += chunk
            current_time = time.time()
            if current_time - start_time < 2:
                time.sleep(3)
            if "<5>" in output:
                after = output.split("<5>", 1)
                if "[1;1H$<5>" in after[1]:
                    new_output = after[1].replace("[1;1H$<5>", "\n")
                    new_output = new_output.split("\n")
                    for line in new_output:
                        print(line)
                        splits = line.split(",")
                        desired_fields = []
                        for index, split in enumerate(splits):
                            if len(splits) == 11:
                                if index < 6 or index == 9:
                                    desired_fields.append(split)
                        print(desired_fields)
                        output_queue.put(desired_fields)
                        self.run_queue()
            output = ""
            time.sleep(.5)
            if current_time - start_time > max_duration:
                break

        channel.send("^S\n")
        channel.send("^C\n")
        client.close()



    def create_buttons(self):
        self.button_end = tk.Button(self, text="End Run", command= lambda: self.stop_order())
        self.button_end.grid(column=0,  row=1)
        self.button_end.config(width=10, font=("Arial", 20))

        self.button_reset = tk.Button(self, text="Reset", command = lambda: RadarsAvailableFrame.run_reset_radar(self.radar_available_frame,
                                      command = "-r; sudo rmmod xdma; sudo modprobe xdma",
                                      hostname = self.radar_available_frame.radar_dict.get(self.radar_available_frame.radar_selected.get())))
        self.button_reset.grid(column=0, row=2)
        self.button_reset.config(width=10, font=("Arial", 20))

        self.submit_button = SubmitButton(self, self.command_dict, self.entry_dict, self.radar_available_frame, self.io_frame)
        self.submit_button.grid(column=0, row=0)
        self.submit_button.config(width=10, font=("Arial", 20))

        self.network_check_button = tk.Button(self, text="Network Check" , command= lambda: RadarsAvailableFrame.find_other_radars(self.radar_available_frame))
        self.network_check_button.grid(column=0, row=3)
        self.network_check_button.config(width=10, font=("Arial", 20))


class CommandLabels(tk.Text):
    def __init__(self, parent, unit, col, text, row, command_selected, wrap = tk.CHAR):
        super().__init__(master = parent, width = 18)
        self.unit = unit
        self.text = text
        self.col = col
        self.row = row
        self.command_selected = command_selected
        self.wrap = wrap
        self.font = ("Times New Roman", 18)
        self.grid(column = col, row = row, sticky = "W")
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        self.config(state = "normal")
        event.widget.grid(column=self.col, row=self.row)
        event.widget.delete("1.0", tk.END)
        event.widget.insert(tk.END, COMMAND_UPDATE[self.command_selected]['text'])
        event.widget.configure(width=45)
        event.widget.config(state = "disabled")

    def on_leave(self, event):
        self.config(state="normal")
        event.widget.grid(column = self.col, row = self.row)
        event.widget.delete("1.0", tk.END)
        event.widget.insert(tk.END, COMMAND_UPDATE[self.command_selected]['title'])
        event.widget.configure(width=18)
        self.config(state="disabled")

class Button(tk.Button):
    def __init__(self, parent):
        super().__init__(parent)

class SubmitButton(tk.Button):
    def __init__(self, parent, received_commands, received_units, radar_available_frame, io_frame):
        super().__init__(parent, text="Run FPGA", command=lambda: self.run_command(self.received_commands, self.received_units))
        self.radar_available_frame = radar_available_frame
        self.io_frame = io_frame
        self.received_commands = received_commands
        self.received_units = received_units

    def run_queue(self):
        #print(f"OPQ: {output_queue.get()}")
        # while output_queue.qsize() > 10 and is_running:
        #     self.after(100, self.io_frame.output_frame.update_all_textboxes(output_queue.get()))
        print(output_queue.qsize())
        try:
            if not output_queue.empty():
                self.after(100, self.io_frame.output_frame.update_all_textboxes(output_queue.get()))
        except:
            print("Error occured")

    def run_command(self, received_commands, received_units):
        cmd_str = ""
        unit_list = []

        for unit in self.received_units:
            unit_list.append(unit)

        for i, value in enumerate(self.received_commands.values()):
            if value.get() == "True":
                cmd_str += f"{unit_list[i]} "
            else:
                cmd_str += f"{unit_list[i]} {value.get()} "

        input_check_return = self.input_check(cmd_str)
        if input_check_return == False:
            self.io_frame.input_frame.create_entries()
            return

        radar_key = self.radar_available_frame.radar_selected.get()
        radar_value = RadarsAvailableFrame.radar_dict.get(radar_key)
        thread = threading.Thread(target=ButtonFrame.run_command_connect, args=(self, cmd_str.strip(), radar_value))
        thread.start()

    def input_check(self, cmd_str):
        cmd_list = cmd_str.split(" ")
        for i, cmd_flag in enumerate(cmd_list):
            #if cmd_flag in COMMAND_UPDATE and cmd_flag != '-u' and cmd_flag != "-y" and cmd_flag != "-C" and cmd_flag != "-V":
            if cmd_flag in COMMAND_UPDATE and cmd_flag != '-u':
                if cmd_flag == "-y" or cmd_flag == "-C" or cmd_flag == "-V":
                    cmd_num  = cmd_list[i+1]
                    try:
                        float(cmd_num)
                    except ValueError:
                        return False
                elif cmd_flag == "-D":
                    cmd_num = cmd_list[i+1]
                    try:
                        num_cmd_num = float(cmd_num)
                    except ValueError:
                        return False
                    if 0 <= num_cmd_num <= float(cmd_list[1]):
                        continue
                    else:
                        input_warning = messagebox.showwarning("Warning", f"{COMMAND_UPDATE[cmd_flag]['title']} ratio must be between 0 and 1.0")
                        if input_warning == 'ok':
                            return False
                else:
                    cmd_num = cmd_list[i+1]
                    try:
                        num_cmd_num = float(cmd_num)
                    except ValueError:
                        return False
                    if COMMAND_UPDATE[cmd_flag]['lowerbound'] <= num_cmd_num <= COMMAND_UPDATE[cmd_flag]['upperbound']:
                        continue
                    else:
                        input_warning = messagebox.showwarning("Warning", f"{COMMAND_UPDATE[cmd_flag]['title']} must be betweeen {COMMAND_UPDATE[cmd_flag]['lowerbound']} and {COMMAND_UPDATE[cmd_flag]['upperbound']}")
                        if input_warning == 'ok':
                            return False