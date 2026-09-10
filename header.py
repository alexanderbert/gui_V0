import os
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage
import os
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

        self.network_switch = NetworkSwitch(self, label_a="Wifi", label_b="Ethernet", command=self.on_switch_toggle)
        self.network_switch.pack(side="right", padx=50, anchor="s")

    def on_switch_toggle(self, is_on):
        if is_on:
            # print("Switch is at Position B")
            # print(f"on: {self.network_state.get()}")
            # state.network_state = "Ethernet"
            print(state.network_state)
            # return state.network_state
        else:
            # print("Switch is at Position A")
            # print(f"off: {self.network_state.get()}")
            # state.network_state = "Wifi"
            print(state.network_state)
            # return state.network_state


    def add_header_image(self):
        self.header_image = PhotoImage(file=resource_path("images/logoresize3.png"))
        image_label = tk.Label(self, image=self.header_image, borderwidth=0)
        image_label.pack(side="left", padx=50)
        image_label.image = self.header_image
        title_text = tk.Label(self, text = "Calibration Tool", font=("Arial", 20, 'bold'))
        title_text.pack(side="right", padx=50)

