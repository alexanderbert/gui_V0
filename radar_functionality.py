import tkinter as tk
from tkinter import ttk
import paramiko
from dotenv import load_dotenv
import nmap
import os
import sys
import logging
import time
import threading
import queue



if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    application_path = os.path.dirname(sys.executable)
else:
    # Running in a normal Python environment
    application_path = os.path.dirname(os.path.abspath(__file__))


dotenv_path = os.path.join(application_path, '.env')
load_dotenv(dotenv_path=dotenv_path)

client = paramiko.client.SSHClient()
output_queue = queue.Queue()
is_fpga_running = False


class RadarFunctionality(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background = "Gray63")
        self.current_radar = None
        self.columnconfigure(0, weight=10)
        self.columnconfigure(1, weight=10)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        #INNER FRAMES
        self.fpga_control_frame = tk.Frame(self)
        self.fpga_control_frame.grid(row=0, column=2, sticky="nsew")
        self.fpga_control_frame.grid_columnconfigure(0, weight=1)
        self.fpga_control_frame.grid_columnconfigure(1, weight=1)


        self.radar_control_frame = tk.Frame(self)
        self.radar_control_frame.grid(row=1, column=2, sticky="nsew")


        self.output_frame = tk.Frame(self)
        self.output_frame.grid(column=0, row=0, sticky="nsew")
        self.output_frame.grid_columnconfigure(0, weight=1)
        self.output_frame.grid_columnconfigure(1, weight=1)
        self.output_frame.rowconfigure(list(range(0,4)), weight=1)

        #Variables
        self.radar_dict = {"Select A Radar": "---------"}
        #self.radar_selected = None
        self.radars_available = None
        self.radar_drop()
        
        #infrastructure
        self.run_heatmap_fpga_button= tk.Button(self.fpga_control_frame, text="Heat Map FPGA", command=lambda:self.start_threading(self.heat_map_fpga()))
        self.run_heatmap_fpga_button.grid(row=0, column=2)
        self.run_heatmap_fpga_button.config(width=20, font=("Arial", 20))

        self.run_capture_fpga_button= tk.Button(self.fpga_control_frame, text="Capture FPGA", command=lambda:self.capture_fpga())
        self.run_capture_fpga_button.grid(row=1, column=2)
        self.run_capture_fpga_button.config(width=20, font=("Arial", 20))

        self.stop_fpga_button= tk.Button(self.fpga_control_frame, text="End FPGA", command=lambda:self.stop_fpga())
        self.stop_fpga_button.grid(row=2, column=2)
        self.stop_fpga_button.config(width=20, font=("Arial", 20))


        self.find_other_radars_button = tk.Button(self.radar_control_frame, text="Find other radars", command=lambda:self.start_network_scan())
        self.find_other_radars_button.grid(row=3, column=2)
        self.find_other_radars_button.config(width=20, font=("Arial", 20))
        # self.status_textbox = tk.Text(self.radar_control_frame)
        # self.status_textbox.grid(column=0, row=1, sticky="nesw")
        # self.status_textbox.config(font=("Arial", 20))
        # self.status_textbox.config(state="disabled")

        self.initial_output_frame()



    def initial_output_frame(self):
        self.az_label = tk.Label(self.output_frame, text="Az:")
        self.az_label.grid(column=0, row=0, sticky="nsew")
        self.az_label.config(font=("Arial", 20))
        self.az_entry = tk.Entry(self.output_frame)
        self.az_entry.grid(column=1, row=0, sticky="nsew")
        self.az_entry.config(font=("Arial", 20))
        self.el_label = tk.Label(self.output_frame, text= "El:")
        self.el_label.grid(column=0, row=1, sticky="nsew")
        self.el_label.config(font=("Arial", 20))
        self.el_entry = tk.Entry(self.output_frame)
        self.el_entry.grid(column=1, row=1, sticky="nsew")
        self.el_entry.config(font=("Arial", 20))
        self.x_power_label = tk.Label(self.output_frame, text="X Power:")
        self.x_power_label.grid(column=0, row=2, sticky="nsew")
        self.x_power_label.config(font=("Arial", 20))
        self.x_power_entry = tk.Entry(self.output_frame)
        self.x_power_entry.grid(column=1, row=2, sticky="nsew")
        self.x_power_entry.config(font=("Arial", 20))
        self.y_power_label = tk.Label(self.output_frame, text="Y Power:")
        self.y_power_label.grid(column=0, row=3, sticky="nsew")
        self.y_power_label.config(font=("Arial", 20))
        self.y_power_entry = tk.Entry(self.output_frame)
        self.y_power_entry.grid(column=1, row=3, sticky="nsew")
        self.y_power_entry.config(font=("Arial", 20))


    def heat_map_fpga(self):
        channel = self.fl_network_mode()
        print("After connection to fl network")
        global is_fpga_running
        is_fpga_running = True
        time.sleep(1)
        channel.send(f"cd {os.environ['FPGAPATH']}\n")
        print(f"sent: cd {os.environ['FPGAPATH']}")
        time.sleep(1)
        channel.send(f"./fpgaStream -w 0.96 -s 0.5 -e 0.5 -b 0.0 -g 0.0 -S 100 -8 144 -9 24 -X -D 10\n")
        print(f"SENT: ./fpgaStream -w 0.96 -s 0.5 -e 0.5 -b 0.0 -g 0.0 -S 100 -8 144 -9 24 -X -D 10\n")
        time.sleep(1)
        print(f"FPGA RUNNING STATE: {is_fpga_running}")
        output = ""
        try:
            while channel.active and is_fpga_running:
                chunk = channel.recv(1024).decode("iso-8859-1")
                print(chunk)
                output += chunk

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

            channel.send("^S\n")
            channel.send("^C\n")
            client.close()
        except:
            channel.send("^S\n")
            channel.send("^C\n")

    def stop_fpga(self):
        global is_fpga_running
        is_fpga_running = False

    def capture_fpga(self):
        pass

    def start_threading(self, funct, argus = None):
        thread = threading.Thread(
            target= funct,
            args= (argus,),
            daemon=True
        )
        thread.start()

    # def paramiko_connection(self, hostname, chosen_command):
    #     print("CONNECTING TO HOSTNAME", hostname)
    #     client.load_system_host_keys()
    #     client.connect(hostname=hostname, username=f"{os.environ.get('CONNECTION_USERNAME')}", password=f"{os.environ.get('CONNECTION_PASSWORD')}", look_for_keys=False, allow_agent=False)
    #     transport = client.get_transport()
    #     channel=transport.open_session()
    #     channel.get_pty()
    #     channel.invoke_shell()
    #     #channel.send(f"sudo -S systemctl {chosen_command} radar.service\n")
    #     # command = f"sudo -S systemctl {chosen_command} radar.service\n"
    #     # stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    #     #
    #     # stdin.write(f"{os.environ.get('CONNECTION_PASSWORD')} \n")
    #     # stdin.flush()
    #     # client.close()

    def fl_network_mode(self):
        self.current_radar = self.radar_dict[self.radar_selected.get()]
        print(self.current_radar)
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=f"{self.current_radar}", username=f"{os.environ.get('CONNECTION_USERNAME')}",
                       password=f"{os.environ.get('CONNECTION_PASSWORD')}", look_for_keys=False, allow_agent=False)
        # print(f"{self.positioner_selected_for_use} inside status")
        # print(f"{selected_positioner_global} GLOBAL status")
        transport = client.get_transport()
        channel = transport.open_session()
        channel.get_pty()
        channel = client.invoke_shell()
        time.sleep(.1)
        logging.info("CONNECTED TO FLORIDA NETWORK")
        return channel


    def radar_drop(self):
        self.radars_available = list(self.radar_dict.keys())
        self.radar_selected = tk.StringVar()
        self.radar_selected.set(self.radars_available[0])
        combo_drop = ttk.Combobox(self.radar_control_frame, textvariable=self.radar_selected, values = self.radars_available, state="readonly")
        combo_drop.grid(column=2, row=4)
        combo_drop.config(width=20)
        combo_drop.config(font = ("Arial", 20))
        return self.radar_selected.get()



    def find_other_radars(self):
        #self.status_textbox.config(state="normal")
        nm = nmap.PortScanner()
        host_ip = os.environ.get("HOST_IP")
        nm.scan(hosts=f"{os.environ.get('HOST_IP')}", arguments="-sn")
        logging.info(f"running on {host_ip}")
        for host in nm.all_hosts():
            try:
                logging.info(f"Scanning {host}")
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.load_system_host_keys()
                # self.io_frame.input_frame.output_frame.terminal_frame.pos_text_box.delete("1.0", tk.END)
                # self.io_frame.input_frame.output_frame.terminal_frame.pos_text_box.insert(tk.END, host)
                client.connect(hostname=f"{host}", username=f"{os.environ.get('CONNECTION_USERNAME')}", password=f"{os.environ.get('CONNECTION_PASSWORD')}", look_for_keys=False, allow_agent=False, timeout=3, auth_timeout=5)
                stdin, stdout, stderr = client.exec_command("hostname")
                radar_hostname = stdout.read().decode("utf-8")
                client.close()
                self.update_radar_pulldown(host, radar_hostname.strip())
            except:
                print(f"No connection to {host}")
        logging.info("RUNNING find_other_radars")
        # self.status_textbox.insert(tk.END, "FINISHED SCANNING")
        # self.status_textbox.config(state="disabled")


    def start_network_scan(self):
        thread = threading.Thread(
            target = self.find_other_radars,
            daemon = True
        )
        thread.start()

    def update_radar_pulldown(self, ip_address, hostname):
        try:
            if ip_address not in self.radar_dict.values():
                self.radar_dict[hostname] = ip_address
                # self.io_frame.input_frame.output_frame.terminal_frame.pos_text_box.delete("1.0", tk.END)
                # self.io_frame.input_frame.output_frame.terminal_frame.pos_text_box.insert(tk.END, f"Found: {ip_address}")
        except:
            print("ERROR")
        self.radar_drop()

    def run_queue(self):
        #print(f"OPQ: {output_queue.get()}")
        # while output_queue.qsize() > 10 and is_running:
        #     self.after(100, self.io_frame.output_frame.update_all_textboxes(output_queue.get()))
        print(output_queue.qsize())
        try:
            if not output_queue.empty():
                self.after(100, self.update_textboxes(output_queue.get()))
        except:
            print("Error occured")

    def update_textboxes(self, output_list):
        x_dc_offset_value = output_list[0].split("= ")
        # self.x_dc_offset_textbox.replace("1.0", tk.END, x_dc_offset_value[1], "center")
        # self.x_dc_offset_textbox.tag_configure("center", justify="center")
        y_dc_offset_value = output_list[1].split("= ")
        # self.y_dc_offset_textbox.replace("1.0", tk.END, y_dc_offset_value[1], "center")
        # self.y_dc_offset_textbox.tag_configure("center", justify="center")
        x_min_max_value = output_list[2].split("X  ")
        # self.x_min_max_textbox.replace("1.0", tk.END, x_min_max_value[1], "center")
        # self.x_min_max_textbox.tag_configure("center", justify="center")
        y_min_max_value = output_list[3].split("Y  ")
        # self.y_min_max_textbox.replace("1.0", tk.END, y_min_max_value[1], "center")
        # self.y_min_max_textbox.tag_configure("center", justify="center")
        x_power_value = output_list[4].split(": ")
        self.x_power_entry.delete(0, tk.END)
        self.x_power_entry.insert(0, x_power_value[0])
        # self.x_power_entry.replace("1.0", tk.END, x_power_value[1], "center")
        # self.x_power_entry.tag_configure("center", justify="center")
        y_power_value = output_list[5].split(": ")
        self.y_power_entry.delete(0, tk.END)
        self.y_power_entry.insert(0, y_power_value[0])
        # self.y_power_textbox.replace("1.0", tk.END, y_power_value[1], "center")
        # self.y_power_textbox.tag_configure("center", justify="center")
        rate_value = output_list[6].split(": ")
        final_rate = rate_value[1].split("=")
        # self.rate_textbox.replace("1.0", tk.END, final_rate[0], "center")
        # self.rate_textbox.tag_configure("center", justify="center")

    # class SSHWoker:
    #     def __init__(self):
    #         self.thread = threading.Thread(target=self._worker, daemon=True)
    #         self.thread.start()
    #
    #     def _worker(self):
    #         channel = self.fl_network_mode()
    #
    #         while True:
    #             try:
    #                 result =