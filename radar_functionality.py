import tkinter as tk
from tkinter import ttk
import paramiko
from dotenv import load_dotenv
import nmap
import os
import sys


if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    application_path = os.path.dirname(sys.executable)
else:
    # Running in a normal Python environment
    application_path = os.path.dirname(os.path.abspath(__file__))


dotenv_path = os.path.join(application_path, '.env')
load_dotenv(dotenv_path=dotenv_path)

client = paramiko.client.SSHClient()


class RadarFunctionality(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background = "Gray63")
        self.columnconfigure(list(range(4)), weight=1)
        self.rowconfigure(list(range(4)), weight=1)
        self.radar_dict = {"Select A Radar": "---------", "Dummy Radar": "123123123123"}
        #self.radar_selected = None
        self.radars_available = None
        self.radar_drop()


        self.enable_autostart_button = tk.Button(self, text="Enable Autostart", command=lambda:self.enable_autostart())
        self.enable_autostart_button.grid(row=0, column=0)
        self.enable_autostart_button.config(width=20, font=("Arial", 20))

        self.disable_autostart_button = tk.Button(self, text="Disable Autostart", command=lambda:self.disable_autostart())
        self.disable_autostart_button.grid(row=1, column=0)
        self.disable_autostart_button.config(width=20, font=("Arial", 20))


        self.find_other_radars_button = tk.Button(self, text="Find other radars", command=lambda:self.find_other_radars())
        self.find_other_radars_button.grid(row=0, column=1)
        self.find_other_radars_button.config(width=20, font=("Arial", 20))

    def enable_autostart(self):
        print("ENABLE AUTOSTART")
        radar_key = self.radar_selected.get()
        radar_value = self.radar_dict.get(radar_key)
        self.paramiko_connection(radar_value, "enable")


    def disable_autostart(self):
        print("DISABLE AUTOSTART")
        radar_key = self.radar_selected.get()
        radar_value = self.radar_dict.get(radar_key)
        self.paramiko_connection(radar_value, "disable")

    def paramiko_connection(self, hostname, chosen_command):
        print("CONNECTING TO HOSTNAME", hostname)
        # client.load_system_host_keys()
        # client.connect(hostname=hostname, username=f"{os.environ.get('CONNECTION_USERNAME')}", password=f"{os.environ.get('CONNECTION_PASSWORD')}", look_for_keys=False, allow_agent=False)
        # transport = client.get_transport()
        # channel=transport.open_session()
        # channel.get_pty()
        # channel.invoke_shell()
        # #channel.send(f"sudo -S systemctl {chosen_command} radar.service\n")
        # command = f"sudo -S systemctl {chosen_command} radar.service\n"
        # stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        #
        # stdin.write(f"{os.environ.get('CONNECTION_PASSWORD')} \n")
        # stdin.flush()
        # client.close()


    def radar_drop(self):
        self.radars_available = list(self.radar_dict.keys())
        self.radar_selected = tk.StringVar()
        self.radar_selected.set(self.radars_available[0])
        combo_drop = ttk.Combobox(self, textvariable=self.radar_selected, values = self.radars_available, state="readonly")
        combo_drop.grid(column=2, row=0, sticky="EW")
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