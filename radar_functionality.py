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
import re
from datetime import datetime
import csv



if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    application_path = os.path.dirname(sys.executable)
else:
    # Running in a normal Python environment
    application_path = os.path.dirname(os.path.abspath(__file__))


dotenv_path = os.path.join(application_path, '.env')
load_dotenv(dotenv_path=dotenv_path)



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
        self.run_heatmap_fpga_button= tk.Button(self.fpga_control_frame, text="Heat Map FPGA", command=lambda:self.start_threading(self.heat_map_fpga))
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


        #self.power_queue = queue.Queue()
        self.latest_values = None
        self.values_lock = threading.Lock()

        self.csv_queue= queue.Queue()
        #
        # self.csv_file = None
        # self.csv_writer = None

        self.initial_output_frame()

        self.update_textboxes()

        self.csv_thread = threading.Thread(
            target=self.csv_writer_worker,
            daemon=True
        )
        self.csv_thread.start()


    def create_ssh_client(self):
        client = paramiko.client.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())

        return client

    def create_values_csv(self):
        timestamp = datetime.now().strftime("%y%m%d_%H%M")
        filename = os.path.join(
            application_path,
            f"heatmap_{timestamp}.csv"
        )

        self.csv_file = open(
            filename,
            "w",
            newline="",
            buffering=1
        )

        self.csv_writer = csv.writer(self.csv_file)

        self.csv_writer.writerow([
            "X Power",
            "Y Power"
        ])

    def csv_writer_worker(self):
        csv_file = None
        csv_writer = None

        while True:
            item = self.csv_queue.get()
            if item is None:
                break
            if csv_file is None:
                timestamp = datetime.now().strftime("%y%m%d_%H%M")

                filename=os.path.join(
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
                    "X Power",
                    "Y Power"
                ])
            csv_writer.writerow(item)
        if csv_file is not None:
            csv_file.close()


    def close_values_csv(self):
        if self.csv_file is not None:
            self.csv_file.close()
        self.csv_file = None
        self.csv_writer = None


    def initial_output_frame(self):

        self.x_power_var = tk.StringVar(value="0")
        self.y_power_var = tk.StringVar(value="0")


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
        self.x_power_entry = tk.Entry(self.output_frame, textvariable=self.x_power_var)
        self.x_power_entry.grid(column=1, row=2, sticky="nsew")
        self.x_power_entry.config(font=("Arial", 20))
        self.y_power_label = tk.Label(self.output_frame, text="Y Power:")
        self.y_power_label.grid(column=0, row=3, sticky="nsew")
        self.y_power_label.config(font=("Arial", 20))
        self.y_power_entry = tk.Entry(self.output_frame, textvariable=self.y_power_var)
        self.y_power_entry.grid(column=1, row=3, sticky="nsew")
        self.y_power_entry.config(font=("Arial", 20))


    def heat_map_fpga(self):
        client, channel = self.fl_network_mode()
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
        buffer = ""
        pattern = re.compile(
            r"X power:\s*([+-]?\d+\.\d+),\s*"
            r"Y power:\s*([+-]?\d+\.\d+)"
            )
        try:

            self.create_values_csv()

            while channel.active and is_fpga_running:
                if channel.recv_ready():
                    data = channel.recv(1024).decode("iso-8859-1")
                #print(data)
                    buffer += data

                    matches = list(pattern.finditer(buffer))

                    for match in matches:
                        x_power = float(match.group(1))
                        y_power = float(match.group(2))

                        # try to output only the latest values for the gui for performance
                        with self.values_lock:
                            self.latest_values = (x_power, y_power)
                        #self.power_queue.put((x_power, y_power))

                        #queue values
                        self.csv_queue.put((x_power, y_power))
                        #self.csv_writer.writerow([x_power, y_power])

                        #try to new buffer tech
                        buffer = buffer[match.end():]
                    # if len(buffer) > 4096:
                    #     buffer = buffer[-4096]
        finally:
            is_fpga_running = False
            if channel is not None:
                try:
                    channel.send("\x03")
                    time.sleep(0.2)
                except Exception as e:
                    pass
            if client is not None:
                client.close()

    def stop_fpga(self):
        global is_fpga_running
        is_fpga_running = False

    def capture_fpga(self):
        pass

    def start_threading(self, funct, *args):
        thread = threading.Thread(
            target= funct,
            args= args,
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
        client = self.create_ssh_client()
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
        return client, channel


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
            client = self.create_ssh_client()
            try:
                logging.info(f"Scanning {host}")
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

    # def run_queue(self):
    #     #print(f"OPQ: {output_queue.get()}")
    #     # while output_queue.qsize() > 10 and is_running:
    #     #     self.after(100, self.io_frame.output_frame.update_all_textboxes(output_queue.get()))
    #     print(output_queue.qsize())
    #     try:
    #         if not output_queue.empty():
    #             self.after(100, self.update_textboxes(output_queue.get()))
    #     except:
    #         print("Error occured")

    def update_textboxes(self):
        with self.values_lock:
            data = self.latest_values
        if data is not None:
            x_power, y_power = data

            self.x_power_var.set(f"{x_power}")
            self.y_power_var.set(f"{y_power}")

        self.after(30, self.update_textboxes)
        # try:
        #     data = self.power_queue.get_nowait()
        #
        #     x_power, y_power = data
        #
        #     self.x_power_entry.delete(0, tk.END)
        #     self.x_power_entry.insert(tk.END, str(x_power))
        #     self.y_power_entry.delete(0, tk.END)
        #     self.y_power_entry.insert(tk.END, str(y_power))
        # except queue.Empty:
        #     pass
        #
        # self.after(50, self.update_textboxes)
