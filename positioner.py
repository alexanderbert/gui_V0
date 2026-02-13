import tkinter as tk
from tkinter import ttk, messagebox
import paramiko
import nmap
import os
import time
import queue
import threading

from numpy.ma.extras import row_stack
from tkterminal import Terminal

client = paramiko.client.SSHClient()
output_queue = queue.Queue()

class PositionerFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background = "Red")
        self.columnconfigure(0, weight=6)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.grid_propagate(False)

        self.io_frame = IOFrame(self)
        self.io_frame.grid(column=0, row = 0, sticky = "NSEW")

        self.control_frame = ControlFrame(self, self.io_frame)
        self.control_frame.grid(column=1, row = 0, sticky = "NSEW")

class IOFrame(tk.Frame):
    def __init__(self, parent, ):
        super().__init__(parent, background = "red")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.grid_propagate(False)

        self.input_frame = InputFrame(self)
        self.input_frame.grid(column=0, row = 0, sticky = "NSEW")


class TerminalFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background = "white")
        self.terminal = Terminal(self)
        self.terminal.grid(column=0, row=0, sticky="NSEW")
        self.terminal.config(height= 50)

    def terminal_command(self, cmd):
        # self.terminal.config(state="normal")
        self.terminal.run_command(cmd)
        # self.terminal.run_command("\n")
        # self.terminal.config(state="disabled")

class OutputFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent,background="gray7")

        self.output_text = tk.Label(self, text = "Position: ", font = ("Arial", 20), foreground = "white")
        self.output_text.grid(column=0, row=0, sticky="NSEW")


class InputFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background="gray7")
        self.rowconfigure(0, weight=10)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(list(range(2)), weight=1)
        self.tf_list = ["True", "False"]
        self.tf_selected = None
        # self.terminal = Terminal(self, font = ("Arial", 20), foreground="white")
        # self.terminal.basename = f"Radar Selected: "
        # self.terminal.grid(column=0, row = 0, sticky = "NSEW")
        # self.terminal.shell = True
        # self.terminal.grid(column=0, row = 0, sticky = "NSEW")
        self.terminal_frame = TerminalFrame(self)
        self.terminal_frame.grid(column=0, row = 0, sticky = "NSEW")
        self.output_frame = OutputFrame(self)
        self.output_frame.grid(column=1, row = 0, sticky = "NSEW")
        '''
        figure out how to get prompt back after entering command while using a disabled state
        self.terminal.config(state="disabled")
        '''

        #self.spot_scan = tk.Button(self, text = "Spot Scan", command= lambda: self.terminal.run_command("whoami"))
        self.spot_scan = tk.Button(self, text="Spot Scan", command=lambda: self.terminal_frame.terminal_command("whoami"))
        self.spot_scan.grid(column=0, row = 1, sticky = "NSEW")
        azimuth_entry = ttk.Entry(self, width=10, font = ("Arial", 20), textvariable="pass")
        elevation_entry = ttk.Entry(self, width=10, font = ("Arial", 20), textvariable="amaass")
        azimuth_entry.grid(column=1, row = 1, sticky = "NSEW")
        elevation_entry.grid(column=2, row = 1, sticky = "NSEW")

        self.rhi_scan = tk.Button(self, text = "RHI Scan", command= lambda: "pass")
        self.rhi_scan.grid(column=3, row = 1, sticky = "NSEW")

        self.rehome = tk.Button(self, text = "Re-Home", command= lambda: "pass")
        self.rehome.grid(column=4, row = 1, sticky = "NSEW")
        self.control_mode = tk.Button(self, text = "Control Mode", command= lambda: self.terminal.config(state="normal"))
        self.control_mode.grid(column=5, row = 1, sticky = "NSEW")



class ControlFrame(tk.Frame):
    def __init__(self, parent, io_frame):
        super().__init__(parent, background = "red")
        self.io_frame = io_frame
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.radars_available_frame = RadarsAvailableFrame(self)
        self.radars_available_frame.grid(column=0, row = 0, sticky = "NSEW")

        self.button_frame = ButtonFrame(self, self.radars_available_frame, self.io_frame)
        self.button_frame.grid(column=0, row = 1, sticky = "NSEW")


class RadarsAvailableFrame(tk.Frame):
    radar_dict = {"Select A Radar": "--------"}
    def __init__(self, parent):
        super().__init__(parent, background = "steel blue")
        self.network_check_button = None
        self.radar_selected = None
        self.radars_available = None
        self.columnconfigure(1, weight=1)
        self.rowconfigure(list(range(2)), weight=1)


        self.network_check_button = tk.Button(self, text="Network Check" , command= lambda: RadarsAvailableFrame.find_other_radars(self))
        self.network_check_button.grid(column=0, row=1, sticky="SEW")
        self.network_check_button.config(width=10, font=("Arial", 20))

    def radar_drop(self):
        self.radars_available = list(self.radar_dict.keys())
        self.radar_selected = tk.StringVar()
        self.radar_selected.set(self.radars_available[0])
        combo_drop = ttk.Combobox(self, textvariable=self.radar_selected, values = self.radars_available, state="readonly")
        combo_drop.grid(column=0, row=0, sticky="NEW")
        combo_drop.config(width=10)
        combo_drop.config(font = ("Arial", 20))
        return self.radar_selected


    def find_other_radars(self):
        nm = nmap.PortScanner()
        nm.scan(hosts = "192.168.0.*", arguments = "-sn")
        for host in nm.all_hosts():
            try:
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.load_system_host_keys()
                client.connect(hostname=f"{host}", username=f"{os.environ.get('CONNECTION_USERNAME')}", password=f"{os.environ.get('CONNECTION_PASSWORD')}", look_for_keys=False, allow_agent=False, timeout=3)
                stdin, stdout, stderr = client.exec_command("hostname")
                radar_hostname = stdout.read().decode("utf-8")
                client.close()
                self.update_radar_pulldown(host, radar_hostname.strip())
            except:
                print(f"No connection to {host}")

    def update_radar_pulldown(self, ip_address, hostname):
        try:
            if ip_address not in self.radar_dict.values():
                self.radar_dict[hostname] = ip_address
        except:
            print("ERROR")
        self.radar_drop()



class ButtonFrame(tk.Frame):
    def __init__(self, parent, radar_available_frame, io_frame):
        super().__init__(parent, background="gray20")
        self.radar_available_frame = radar_available_frame
        self.io_frame = io_frame
        self.columnconfigure(0, weight=1)
        self.rowconfigure(list(range(4)), weight=1)
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

        channel.send("^S\n")
        channel.send("^C\n")
        client.close()



    def create_buttons(self):
        self.button_end = tk.Button(self, text="Disconnect", command= lambda: self.stop_order())
        self.button_end.grid(column=0,  row=1)
        self.button_end.config(width=10, font=("Arial", 20))

        self.button_reset = tk.Button(self, text="Home", command = lambda: RadarsAvailableFrame.run_reset_radar(self.radar_available_frame,
                                      command = "-r; sudo rmmod xdma; sudo modprobe xdma",
                                      hostname = self.radar_available_frame.radar_dict.get(self.radar_available_frame.radar_selected.get())))
        self.button_reset.grid(column=0, row=2)
        self.button_reset.config(width=10, font=("Arial", 20))

        self.submit_button = SubmitButton(self, self.radar_available_frame, self.io_frame)
        self.submit_button.grid(column=0, row=0)
        self.submit_button.config(width=10, font=("Arial", 20))

        # self.network_check_button = tk.Button(self, text="Network Check" , command= lambda: RadarsAvailableFrame.find_other_radars(self.radar_available_frame))
        # self.network_check_button.grid(column=0, row=3)
        # self.network_check_button.config(width=10, font=("Arial", 20))


class Button(tk.Button):
    def __init__(self, parent):
        super().__init__(parent)


class SubmitButton(tk.Button):
    def __init__(self, parent, radar_available_frame, io_frame):
        super().__init__(parent, text="Connect", command=lambda: self.run_command())
        self.radar_available_frame = radar_available_frame
        self.io_frame = io_frame

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
