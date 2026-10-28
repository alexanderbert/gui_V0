# StormQuant Radar Bringup Tool (SQRBT)

This tool enables unit and integration testing for the radar signal transmission and antenna operation via a Tkinter Gui


## Usages
The GUI opens to a home page detailing a brief description of the app. The application has tabs for different 
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



### Build Steps for a linux system
1. Set up a virtual environment using Python3
2. Ensure tkinter is installed with the command `python -m tkinter`
3. If Tkinter is installed, continue below. Otherwise, run `sudo apt-get install python3-tk`
4. Install Paramiko, python-dotenv, python-nmap, pyinstaller, numpy, pandas, matplotlib, and scp with pip. This will be corrected to a requirements.txt file in a later version
5. Clone the repo
6. Set up your .env file
7. Run `pyinstaller --onefile --add-data ".env:." app.py`
8. Set up another .env file in the dist folder which should now contain an app.py program file and an images directory
9. Open the executable



