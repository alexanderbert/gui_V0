import tkinter as tk
from tkinter import messagebox

import paramiko
from dotenv import load_dotenv
import nmap
import threading
import state
import os
import time
import customtkinter


#TODO PUT IN HEADER BAR
class HomeFrame(customtkinter.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        # self.columnconfigure(list(range(0,11)), weight=1)
        # self.rowconfigure(list(range(0,10)), weight=1)
        self.welcome_statement = None
        self.output_textbox = customtkinter.CTkTextbox(self, state = "normal")
        self.output_textbox.pack(side="top", fill="both", pady = 40, padx = 40)

        self.welcome_statement = '''Radar Calibration and Testing Tool (RCATT). Please search for radars on your network 
        with the button located in the top right of the header.
        Lorem ipsum dolor sit amet consectetur adipiscing elit. Quo duis eiusmod
            exercitation pariatur eos minim quos fugiat est quos ex. Esse magna
            excepturi voluptate deserunt esse. In ullamco mollit deserunt ut non
            qui dolor. Officia illum vel sit in cum et officia imperdiet qui
            expedita officia.

        Cillum soluta dolores excepturi non ea irure consequatur in. Distinctio
        ea minus laborum ullamco cumque voluptatum. Quo excepturi excepteur
        non temporibus labore sint rerum commodo cupidatat.

        Sunt iusto et eiusmod incididunt consequatur consequat. Est dolorem
        nostrud labore corrupti veniam consectetur quos reprehenderit veniam.
        Ad proident velit et do do optio qui aute quis. Soluta cum qui nulla
        fuga vero dolor corrupti. Cumque eu nulla qui aliqua dolor molestias.'''
        self.output_textbox.tag_config("center", justify="center")
        self.output_textbox.insert("0.0", self.welcome_statement, "center")


