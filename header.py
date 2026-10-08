import os
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage
import os
import paramiko
import threading
import time
import nmap

import customtkinter

import state
from network_toggle import NetworkSwitch

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS2
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class HeaderFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background="gray85")
        self.header_image = None
        self.grid_propagate(False)


        self.popup = None

        self.radars_available = list(state.radars_found.get_dict())
        self.connection_button = None
        self.radar_dropdown = None



        self.connection_button = customtkinter.CTkButton(self, text="Find Radars", fg_color = "red",
                                                         command=lambda: self.start_thread(self.find_other_radars))

        self.connection_button.configure(font=("Arial", 20))

        self.combo_drop = customtkinter.CTkComboBox(self, values=self.radars_available, state="readonly", command=self.update_radar_state)
        self.combo_drop.set(self.radars_available[0])
        #self.combo_drop.grid(column=5, row=4)
        self.combo_drop.configure(width = 200, font=("Arial", 20), dropdown_font=("Arial", 20), justify="center")

        self.connection_button.pack(side="right", padx=50)
        self.combo_drop.pack(side="right", padx=50)

        self.network_switch = NetworkSwitch(self, label_a="Wifi", label_b="Ethernet", command=self.on_switch_toggle)
        self.network_switch.pack(side="right", padx=50, pady=10, anchor="s")


    def create_ssh_client(self):
        client = paramiko.client.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())

        return client

    def start_thread(self, func, *args):
        thread = threading.Thread(
            target=func,
            args=args,
            daemon=True
        )
        thread.start()


    def on_change_radar_choice(self, *args):

        self.radar_choice_var = state.radar_choice.get()


    def create_popup(self):
        #
        window_width = self.master.winfo_screenwidth()
        window_height = self.master.winfo_screenheight()
        window_x = self.master.winfo_rootx()
        window_y = self.master.winfo_rooty()

        center_x = (window_x + window_width) / 4
        center_y = (window_y + window_height) / 4
        self.popup = tk.Toplevel(self)
        self.popup.title("Status")
        self.popup.geometry(f"200x75+{int(center_x)}+{int(center_y)}")

        label = customtkinter.CTkLabel(self.popup, text="Searching Network", font=("Arial", 20), justify="center")
        label.grid(row=0, column=0, pady=10, padx=10)

        self.popup.transient()
        self.popup.grab_set()

    def update_radar_pulldown(self):
        radars_available = []
        for name, address in state.radars_found.get_dict().items():
                radars_available.append(name)
        self.combo_drop.configure(values=radars_available)

    def update_radar_state(self, choice):

        for key, value in state.radars_found.get_dict().items():
            if key == choice:
                # state.radar_choice = value
                state.radar_choice.set(key)
        state.radar_choice.get()




    def find_other_radars(self):
        #TODO remove okay, re
        self.create_popup()
        state.radars_found.update_dict({"DUMMY1": 111111111})

        nm = nmap.PortScanner()
        # host_ip = os.environ.get("HOST_IP")
        # nm.scan(hosts=f"{os.environ.get('HOST_IP')}", arguments="-sn")
        #CHANGE NMAP SCAN BASED ON NETWORK STATE
        try:
            nm.scan(hosts=state.network_state, arguments="-sn", timeout=20)
        except:
            print("NETWORK ERROR")
            return
        host_ip = state.network_state

        print(f"running on {host_ip}")
        for host in nm.all_hosts():
            client = self.create_ssh_client()
            try:

                client.connect(hostname=f"{host}", username=f"{os.environ.get('CONNECTION_USERNAME')}", password=f"{os.environ.get('CONNECTION_PASSWORD')}", look_for_keys=False, allow_agent=False, timeout=3, auth_timeout=5)
                stdin, stdout, stderr = client.exec_command("hostname")
                radar_hostname = stdout.read().decode("utf-8")
                client.close()
                #self.update_radar_pulldown(host, radar_hostname.strip())
                state.radars_found.update_dict({radar_hostname.strip(): host})
            except:
                print(f"No connection to {host}")
        self.update_radar_pulldown()
        self.connection_button.configure(fg_color="green")
        self.popup.destroy()
        #input_warning = messagebox.showwarning("Warning", "Finished Searching Network")



    def on_switch_toggle(self, is_on):
        if is_on:

            print(state.network_state)

        else:

            print(state.network_state)




    def add_header_image(self):
        self.header_image = PhotoImage(file=resource_path("images/logoresize3.png"))
        image_label = tk.Label(self, image=self.header_image, borderwidth=0)
        image_label.pack(side="left", padx=50)
        image_label.image = self.header_image


