import tkinter as tk
import paramiko
import nmap

class RadarFunctionality(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background = "aqua")