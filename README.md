# StormQuant Radar Bringup Tool (SQRBT)

This tool enables unit and integration testing for the radar signal transmission and antenna operation via a Tkinter Gui


## Usages
The GUI opens to an S-Curve calibration page with a network check to find the necessary devices on the network. Once 
a device is chosen from the drop-down, enter the desired specifications for your calibration. Upon hitting the
Run FPGA page, the GUI will switch to a numerical output. In a later version, graphical output will be added.

The Positioner Tab allows the user to also check the network and connect to desired devices. Text output is displayed in
the three text boxes with relevant information. The user my choose their input for their desired scan pattern. If 
needed, homing mode is accessible through the Reset button, and if already in homing mode, choosing the Homing Mode 
button will take them to the homing mode interface



### Build Steps for a linux system
1. Set up a virtual environment using Python3
2. Ensure tkinter is installed with the command `python -m tkinter`
3. If Tkinter is installed, continue below. Otherwise, run `sudo apt-get install python3-tk`
4. Install Paramiko, python-dotenv, python-nmap, pyinstaller, numpy, pandas, matplotlib, and SCPClient with pip. This will be corrected to a requirements.txt file in a later version
5. Clone the repo
6. Set up your .env file
7. Run `pyinstaller --onefile --add-data ".env:." app.py`
8. Set up another .env file in the dist folder which should now contain an app.py program file and an images directory
9. Open the executable



