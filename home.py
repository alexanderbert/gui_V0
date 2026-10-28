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
        self.welcome_statement_2 = None
        self.output_textbox = customtkinter.CTkTextbox(self, state = "normal")
        self.output_textbox.pack(side="top", fill="both",expand=True, pady = 40, padx = 40)

        self.welcome_statement = f'''
        
        
        
        Radar Calibration and Testing Tool (RCATT) Version {state.current_version_number}. Please search for radars on your network 
        with the button located in the top right of the header.
        
        When first choosing the radar, make sure it is stopped via 'sudo service radar stop' or 'sudo sytemctl stop radar'
        
        
        # The initial checklist tab consists of a usb check that displays the color coded usbmap'
        # 
        # Lorem ipsum dolor sit amet consectetur adipiscing elit. Quo duis eiusmod
        #     exercitation pariatur eos minim quos fugiat est quos ex. Esse magna
        #     excepturi voluptate deserunt esse. In ullamco mollit deserunt ut non
        #     qui dolor. Officia illum vel sit in cum et officia imperdiet qui
        #     expedita officia.
        # 
        # Cillum soluta dolores excepturi non ea irure consequatur in. Distinctio
        # ea minus laborum ullamco cumque voluptatum. Quo excepturi excepteur
        # non temporibus labore sint rerum commodo cupidatat.
        # 
        # Sunt iusto et eiusmod incididunt consequatur consequat. Est dolorem
        # nostrud labore corrupti veniam consectetur quos reprehenderit veniam.
        # Ad proident velit et do do optio qui aute quis. Soluta cum qui nulla
        # fuga vero dolor corrupti. Cumque eu nulla qui aliqua dolor molestias.'''
        self.output_textbox.tag_config("center", justify="center")

        self.welcome_statement_2 = f'''Radar Calibration and Testing Tool (RCATT) Version {state.current_version_number}. The application has tabs for different 
functionality. The dropdown menu in the header will populate after the 'Find Radars' button is pushed. Make sure to 
select either Wi-Fi or Ethernet depending on the appropriate connection to the radar. A pop-up will display on the screen
while the network is being searched. Use the dropdown to select the radar you wish to work on.


The 'Initial Checklist' tab allows the user to print a usbmap of the radar with color coded information.

The 'Generate Radar Data' tab opens to an S-Curve calibration page. Enter the desired specifications for your 
calibration and select Run FPGA. The data will but output numerically. Capture will run 10000 packets worth of data, 
capture bin files from the radar, zip them, and pull the zip down locally in the generatedBinFiles. The reset button 
will reset the radar and clear any extraneous fpgaStreams.

The 'Positioner Control' tab will allow the user to start and stop the positioner in both normal and homing modes. If the
radar must be put in homing mode, hit the 'Homing Mode Button' and click yes on the popup. Scan data will be output to 
the GUI as well as status information.

The 'Visualize Radar Output' tab will take the data generated from the capture runs in the 'Generate Radar Data' and
display them in the gui.

the 'Collect Calibration Data' runs a specific fpgaStream based on the positioner. The inputs on the 'Positioner Control'
tab must be input correctly as the fpgaStream bases certain information on the inputs. When your positioner is running,
hit the 'Collect Heatmap Data' button. This will generate a csv file and display some numerical data. When the run is 
finished, use the 'Draw Heatmap' button to select your timestamped csv file and create a Heatmap that is both shown
on the GUI and created as a jpg. When you are satisfied with the position of the positioner, use the 'Capture Raw Packets'
button to generate packet data that is stored locally.
'''

        self.output_textbox.insert("0.0", self.welcome_statement_2, "center")
        self.output_textbox.configure(state="disabled")


