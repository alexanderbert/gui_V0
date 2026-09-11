import tkinter as tk
from tkinter import ttk, filedialog
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
        # self.radar_control_frame.grid_rowconfigure(list(range(0,3)), weight=1)


        self.output_frame = tk.Frame(self)
        self.output_frame.grid(column=0, row=0, sticky="nsew")
        self.output_frame.grid_columnconfigure(0, weight=1)
        self.output_frame.grid_columnconfigure(1, weight=1)
        self.output_frame.rowconfigure(list(range(0,4)), weight=1)
        #self.output_frame.grid_propagate(False)

        self.toolbar_frame= tk.Frame(self.output_frame)
        self.toolbar_frame.grid_propagate(False)
        # self.network_state = "Wifi"


        #Variables
        self.radar_dict = {"Select A Radar": "---------"}
        #self.radar_selected = None
        self.radars_available = None
        self.radar_drop()
        
        #infrastructure
        self.run_heatmap_fpga_button= tk.Button(self.fpga_control_frame, text="RUN", command=lambda:self.start_threading(self.heat_map_fpga))
        self.run_heatmap_fpga_button.grid(row=0, column=2)
        self.run_heatmap_fpga_button.config(width=20, font=("Arial", 20))
        #
        # self.run_capture_fpga_button= tk.Button(self.fpga_control_frame, text="Capture FPGA", command=lambda:self.capture_fpga())
        # self.run_capture_fpga_button.grid(row=1, column=2)
        # self.run_capture_fpga_button.config(width=20, font=("Arial", 20))

        self.stop_fpga_button= tk.Button(self.fpga_control_frame, text="End RUN", command=lambda:self.stop_fpga())
        self.stop_fpga_button.grid(row=2, column=2)
        self.stop_fpga_button.config(width=20, font=("Arial", 20))

        self.create_heatmap_button= tk.Button(self.fpga_control_frame, text="Create Heatmap", command=lambda:self.create_heatmap())
        self.create_heatmap_button.grid(row=1, column=2)
        self.create_heatmap_button.config(width=20, font=("Arial", 20))

        self.capture_packets_button = tk.Button(self.fpga_control_frame, text="CAPTURE ONLY", command=lambda:self.start_threading(self.capture_packets_run))
        self.capture_packets_button.grid(column=2, row =4)
        self.capture_packets_button.config(width=20, font=("Arial", 20))

        self.close_heatmap_button = None


        self.find_other_radars_button = tk.Button(self.radar_control_frame, text="Check Network", command=lambda:self.start_network_scan())
        self.find_other_radars_button.grid(row=3, column=2)
        self.find_other_radars_button.config(width=20, font=("Arial", 20))

        self.canvas = None


        #self.power_queue = queue.Queue()
        self.latest_values = None
        #self.values_lock = threading.Lock()

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

    # def create_values_csv(self):
    #     timestamp = datetime.now().strftime("%m%d_%H%M%S")
    #     filename = os.path.join(
    #         application_path,
    #         f"heatmap_{timestamp}.csv"
    #     )
    #
    #     self.csv_file = open(
    #         filename,
    #         "w",
    #         newline="",
    #         buffering=1
    #     )
    #
    #     self.csv_writer = csv.writer(self.csv_file)
    #
    #     self.csv_writer.writerow([
    #         "X Power",
    #         "Y Power"
    #     ])

    def csv_writer_worker(self):
        csv_file = None
        csv_writer = None

        while True:
            item = self.csv_queue.get()
            if item is None:
                break
            if csv_file is None:
                timestamp = datetime.now().strftime("%m%d_%H%M%S")

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
                    "Azimuth",
                    "Elevation",
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

        self.az_var = tk.StringVar(value="0")
        self.el_var = tk.StringVar(value="0")
        self.x_power_var = tk.StringVar(value="0")
        self.y_power_var = tk.StringVar(value="0")


        self.az_label = tk.Label(self.output_frame, text="Az:")
        self.az_label.grid(column=0, row=0, sticky="nsew")
        self.az_label.config(font=("Arial", 20))
        self.az_entry = tk.Entry(self.output_frame, textvariable=self.az_var)
        self.az_entry.grid(column=1, row=0, sticky="nsew")
        self.az_entry.config(font=("Arial", 20))

        self.el_label = tk.Label(self.output_frame, text= "El:")
        self.el_label.grid(column=0, row=1, sticky="nsew")
        self.el_label.config(font=("Arial", 20))
        self.el_entry = tk.Entry(self.output_frame, textvariable=self.el_var)
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

        # calculate speed in seconds - degrees 20 seconds 360/20 = 18 degrees a second
        # 10 degrees azimuth 10/18 degrees
        # total elevation size /increment *2 (-3 to 5) is 8 incremnts
        # mulitiply 8, add 20% as a safety
    def heat_map_fpga(self):
        S_FLAG_VALUE = 300
        print(f"LOOK at me StartAZ:{state.starting_azimuth_value}, ENDAZ{state.ending_azimuth_value}, STARTEL{state.starting_el_value} END EL{state.ending_el_value} speed{state.speed_value} inc{state.increment_value}")
        try:
            #THE JAKE EQUATION
            expected_Q_Value = (float(state.ending_azimuth_value) - float(state.starting_azimuth_value) / (360 / float(state.speed_value))) * ((float(state.ending_el_value) - float(state.starting_el_value)) / (float(state.increment_value) * 2)) * 2 * S_FLAG_VALUE * 1.2
            print(expected_Q_Value)
        except:
            pass
        client, channel = self.fl_network_mode()
        print("After connection to fl network")
        global is_fpga_running
        is_fpga_running = True
        time.sleep(1)
        try:
            channel.send(f"cd {os.environ['FPGAPATH']}\n")
            print(f"sent: cd {os.environ['FPGAPATH']}")
            time.sleep(1)
            channel.send(f"./fpgaStream -w 0.96 -s 0.5 -e 0.5 -b 0.0 -g 0.0 -S {S_FLAG_VALUE} -Q {expected_Q_Value} -8 2000 -9 4000 -X -D 10\n")
            print(f"SENT: ./fpgaStream -w 0.96 -s 0.5 -e 0.5 -b 0.0 -g 0.0 -S {S_FLAG_VALUE} -Q {int(expected_Q_Value)} -8 2000 -9 4000 -X -D 10\n")
            time.sleep(1)
            print(f"FPGA RUNNING STATE: {is_fpga_running}")
            buffer = ""
        except:
            pass

        # Grabs the line with Power and the line above it for azimuth and altitude
        position_pattern = re.compile(
            r"position:\s*(?P<az>[+-]?\d+\.\d+)\s+azimuth,\s*"
            r"[+-]?\d+\.\d+,\s*plate,\s*"
            r"(?P<el>[+-]?\d+\.\d+)\s+altitude"
        )

        power_pattern = re.compile(
            r"X power:\s*(?P<xPow>[+-]?\d+\.\d+).*?"
            r"Y power:\s*(?P<yPow>[+-]?\d+\.\d+)"
        )

        try:
            last_position = None
            # self.create_values_csv()

            while channel.active and is_fpga_running:
                if channel.recv_ready():
                    data = channel.recv(1024).decode("iso-8859-1")
                #print(data)
                    buffer += data
                    while True:
                        position_match = position_pattern.search(buffer)
                        power_match = power_pattern.search(buffer)

                        if position_match is None and power_match is None:
                            break

                        if position_match is not None and (power_match is None or position_match.start() < power_match.start()):
                            last_position = position_match

                            buffer = buffer[position_match.end():]
                            continue

                        if power_match is not None:
                            if last_position is not None:
                                az = float(last_position.group("az"))
                                el = float(last_position.group("el"))
                                x_power = float(power_match.group("xPow"))
                                y_power = float(power_match.group("yPow"))

                                self.latest_values = (az, el, x_power, y_power)
                                self.csv_queue.put((az, el, x_power, y_power))

                                last_position = None
                            buffer = buffer[power_match.end():]
                            continue


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


    def capture_packets_run(self):
        #Todo run this from wherever the files will be stored
        try:
            target_directory = "/captureMode"
            subprocess.run(['socat','tcp-l:7777,reuseaddr,fork','system:\'cpio -i\''],cwd=target_directory, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with exit code {e.returncode}")

        client, channel = self.fl_network_mode()
        print("After connection to fl network")
        global is_fpga_running
        is_fpga_running = True
        time.sleep(1)
        channel.send(f"cd {os.environ['FPGAPATH']}\n")
        print(f"sent: cd {os.environ['FPGAPATH']}")
        #Need a total -Q number for pulses to be read i think
        channel.send(f"./fpgaStream -w 0.96 -s 0.5 -e 0.5 -b 0.0 -g 0.0 -S 1000 -k 8000 -Q 10000 -q -c | socat - tcp:10.42.0.1:7777\n")
        time.sleep(.5)
        channel.close()
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
        print(f"insid eother radars {state.network_state}")
        self.find_other_radars_button.config(text="Searching for radars")
        self.find_other_radars_button.config(state="disabled")
        nm = nmap.PortScanner()
        # host_ip = os.environ.get("HOST_IP")
        # nm.scan(hosts=f"{os.environ.get('HOST_IP')}", arguments="-sn")
        #CHANGE NMAP SCAN BASED ON NETWORK STATE
        nm.scan(hosts=state.network_state, arguments="-sn")
        host_ip = state.network_state
        logging.info(f"running on {host_ip}")
        print(f"running on {host_ip}")
        for host in nm.all_hosts():
            client = self.create_ssh_client()
            try:
                logging.info(f"Scanning {host}")
                client.connect(hostname=f"{host}", username=f"{os.environ.get('CONNECTION_USERNAME')}", password=f"{os.environ.get('CONNECTION_PASSWORD')}", look_for_keys=False, allow_agent=False, timeout=3, auth_timeout=5)
                stdin, stdout, stderr = client.exec_command("hostname")
                radar_hostname = stdout.read().decode("utf-8")
                client.close()
                self.update_radar_pulldown(host, radar_hostname.strip())
            except:
                print(f"No connection to {host}")
        logging.info("RUNNING find_other_radars")
        self.find_other_radars_button.config(state="normal")
        self.find_other_radars_button.config(text="Find Radars")


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
        if self.latest_values is not None:
            #az, el, absAz, absEl, xPower, yPower = self.latest_values
            az, el, xPower, yPower = self.latest_values
            self.az_var.set(f"{az}")
            self.el_var.set(f"{el}")
            self.x_power_var.set(f"{xPower}")
            self.y_power_var.set(f"{yPower}")
        self.after(20, self.update_textboxes)
        #2nd try
        # with self.values_lock:
        #     data = self.latest_values
        # if data is not None:
        #     x_power, y_power = data
        #
        #     self.x_power_var.set(f"{x_power}")
        #     self.y_power_var.set(f"{y_power}")
        #
        # self.after(30, self.update_textboxes)
        #1st try
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

    def create_heatmap(self):


        self.az_entry.grid_remove()
        self.az_label.grid_remove()
        self.el_entry.grid_remove()
        self.el_label.grid_remove()
        self.x_power_entry.grid_remove()
        self.x_power_label.grid_remove()
        self.y_power_entry.grid_remove()
        self.y_power_label.grid_remove()

        self.find_other_radars_button.grid_remove()



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

        if not csv_file:
            self.az_entry.grid()
            self.az_label.grid()
            self.el_entry.grid()
            self.el_label.grid()
            self.x_power_entry.grid()
            self.x_power_label.grid()
            self.y_power_entry.grid()
            self.y_power_label.grid()
            self.find_other_radars_button.grid()
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
        if not azimuth_raw:
            raise ValueError("No valid data")
        azimuth = np.array(azimuth_raw)
        elevation = np.array(elevation_raw)
        x_power = np.array(x_power_raw)
        # TODO OLD EQUATION
        # y_power = np.array(y_power_raw)
        #
        # x_linear = 10 ** (x_power / 10)
        # y_linear = 10 ** (y_power / 10)
        #
        # total_linear = x_linear + y_linear
        #
        # power = 10 * np.log10(total_linear)


        #NEW HEATMAP CREATION
        fig, ax = plt.subplots(figsize=(4, 6))
        az_grid = np.linspace(azimuth.min(), azimuth.max(), 500)
        el_grid = np.linspace(elevation.min(), elevation.max(), 500)

        AZ, EL = np.meshgrid(az_grid, el_grid)

        POWER = griddata(
            (azimuth,elevation),
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
            xytext=(10,10),
            textcoords="offset points",
            color="black",


        )
        heatmap = ax.pcolormesh(
            AZ,
            EL,
            POWER,
            shading="auto",
            cmap="inferno"
            #cmap="gray
        )



        #plt.fig(4, 6)


        fig.colorbar(heatmap, ax=ax, label="X Power (dB)")
        ax.set_xlabel("Azimuth (degrees)")
        ax.set_ylabel("Elevation (degrees)")
        ax.set_title("X Power Heatmap")
        plt.tight_layout()


        #TODO Hide this initial version of HEATMAP FOR NOW
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

        #CREATE JPG IF IT DOESNT EXIT
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

        # fig.set_size_inches(3.5, 6)
        # self.plot_frame = tk.Frame(self)
        # self.plot_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

        # self.plot_frame.grid_columnconfigure(0, weight=1)
        # self.plot_frame.grid_rowconfigure(0, weight=1)
        #canvas = FigureCanvasTkAgg(fig, plot_frame)
        self.canvas = FigureCanvasTkAgg(fig, self.output_frame)
        self.canvas.draw()
        #self.canvas.get_tk_widget().grid(column=0, columnspan=2, row=0, rowspan=4, sticky="nsew")
        self.canvas.get_tk_widget().grid(column=0, row=0, columnspan=2, rowspan=3, sticky="nsew")
        #canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        self.toolbar_frame = tk.Frame(self.output_frame, width=100, height=40)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()
        self.toolbar_frame.grid(column=0, row=4, sticky="w")

        self.toolbar_frame.grid_propagate(False)


        # toolbar = NavigationToolbar2Tk(canvas, plot_frame)
        # toolbar.update()
        # toolbar.pack(side="left")

        # PREVENTS RESIZING
        # self.plot_frame.pack_propagate(False)

        # fig.tight_layout()
        #
        # canvas = FigureCanvasTkAgg(fig, master=self.initial_output_frame)
        # canvas.draw()

        self.canvas.get_tk_widget().grid(column=0, row=0, sticky="nsew")

        self.close_heatmap_button= tk.Button(self.fpga_control_frame, text="Close Heatmap", command=lambda:self.close_heatmap())
        self.close_heatmap_button.grid(column=2, row=4)
        self.close_heatmap_button.config(width=20, font=("Arial", 20))
        return self.canvas

    def close_heatmap(self):
        if self.canvas is not None:
            plt.close(self.canvas.figure)
            self.canvas.get_tk_widget().destroy()

            self.canvas = None
            # self.heatmap_fig = None
            # self.heatmap_ax = None
        if self.toolbar_frame is not None:
            self.toolbar_frame.grid_remove()

        # Remove close button
        if self.close_heatmap_button is not None:
            self.close_heatmap_button.destroy()

            self.close_heatmap_button = None
        self.az_entry.grid()
        self.az_label.grid()
        self.el_entry.grid()
        self.el_label.grid()
        self.x_power_entry.grid()
        self.x_power_label.grid()
        self.y_power_entry.grid()
        self.y_power_label.grid()
        self.find_other_radars_button.grid()
        # self.canvas.get_tk_widget().grid_remove()
        # self.close_heatmap_button.grid_remove()
        # self.columnconfigure(0, weight=10)
        # self.columnconfigure(1, weight=10)
        # self.columnconfigure(2, weight=1)
        # self.rowconfigure(0, weight=1)
        # self.rowconfigure(1, weight=1)

        #INNER FRAMES

        #
        #
        # self.output_frame = tk.Frame(self)
        # self.output_frame.grid(column=0, row=0, sticky="nsew")
        # self.output_frame.grid_columnconfigure(0, weight=1)
        # self.output_frame.grid_columnconfigure(1, weight=1)
        # self.output_frame.rowconfigure(list(range(0,4)), weight=1)
        self.initial_output_frame()


