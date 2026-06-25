import tkinter as tk
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
        super().__init__(parent, background = "Gray3")
        self.columnconfigure(list(range(4)), weight=1)
        self.rowconfigure(list(range(4)), weight=1)


        self.enable_autostart_button = tk.Button(self, text="Enable Autostart", command=lambda:self.enable_autostart())
        self.enable_autostart_button.grid(row=0, column=0)
        self.enable_autostart_button.config(width=20, font=("Arial", 20))

        self.disable_autostart_button = tk.Button(self, text="Disable Autostart", command=lambda:self.disable_autostart())
        self.disable_autostart_button.grid(row=0, column=1)
        self.disable_autostart_button.config(width=20, font=("Arial", 20))

    def enable_autostart(self):
        print("ENABLE AUTOSTART")
        self.paramiko_connection("DUMMY HOSTNAME", "enable")


    def disable_autostart(self):
        print("DISABLE AUTOSTART")
        self.paramiko_connection("DUMMY HOSTNAME", "disable")

    def paramiko_connection(self, hostname, chosen_command):
        client.load_system_host_keys()
        client.connect(hostname=hostname, username=f"{os.environ.get('CONNECTION_USERNAME')}", password=f"{os.environ.get('CONNECTION_PASSWORD')}", look_for_keys=False, allow_agent=False)
        transport = client.get_transport()
        channel=transport.open_session()
        channel.get_pty()
        channel.invoke_shell()
        channel.send(f"sudo systemctl {chosen_command} radar.service\n")
