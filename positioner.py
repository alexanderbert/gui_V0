import tkinter as tk
from tkinter import ttk, messagebox
import paramiko
import nmap
import os
import time
import queue
import threading
import sys
import logging
import subprocess
from settings import *

from datetime import datetime
is_fpga_running = False
logging.basicConfig(filename="log.txt", filemode='a', level=logging.INFO, format="%(asctime)s - %(message)s")
output_queue = queue.Queue()

client = paramiko.client.SSHClient()

selected_positioner_global = None
home_set = False

#todo Check for tracking error
#todo check for USB0/1/2 initially
#todo tty to global
'''
save home / - to set valid home
scan rehome -puts you in homing mode
then moved 22.5 S to spin properly
save home / 
contact it
'''

run_status_global = False

if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    application_path = os.path.dirname(sys.executable)
else:
    # Running in a normal Python environment
    application_path = os.path.dirname(os.path.abspath(__file__))

dotenv_path = os.path.join(application_path, '.env')


class PositionerFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background = "Red")
        self.columnconfigure(0, weight=6)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.grid_propagate(False)

        self.io_frame = IOFrame(self)
        self.io_frame.grid(column=0, row = 0, sticky = "NSEW")

        self.control_frame = ControlFrame(self, self.io_frame)
        self.control_frame.grid(column=1, row = 0, sticky = "NSEW")

class IOFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background = "red")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.grid_propagate(False)

        self.input_frame = InputFrame(self)
        self.input_frame.grid(column=0, row = 0, sticky = "NSEW")


class TerminalFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background = "gold")
        # self.columnconfigure(0, weight=1)
        # self.columnconfigure(1, weight=1)
        # self.rowconfigure(0, weight=1)
        # self.rowconfigure(1, weight=1)
        # self.grid_propagate(False)
        self.positioner_selected = False
        self.current_position = None
        self.home_position = None
        self.scan_type_var = tk.StringVar()
        self.scan_type_var.set("Scan Type: ")
        self.positioner_selected_var = tk.StringVar()
        self.positioner_selected_var.set("Positioner: ")
        self.positioner_selected_for_use = None

        self.status_text_box = tk.Text(self, font=("Arial", 16), bg="gray7", fg="white")
        self.status_text_box.grid(column=0, row=0, rowspan=2, sticky="NSEW")
        self.status_text_box.config(height=30, width = 60)

        self.pos_text_box = tk.Text(self, font=("Arial", 20), bg="gray7", fg="white")
        self.pos_text_box.grid(column=1, row=0, sticky="NEW")
        self.pos_text_box.config(height=13, width = 60)
        self.pos_text_box.insert(tk.END, "Not Connected")

        self.simplified_status = tk.Text(self, font=("Arial", 20), bg="gray7", fg="white", borderwidth=2)
        self.simplified_status.grid(column=1, row=1, sticky="SEW")
        self.simplified_status.config(height=10, width = 10)
        self.simplified_status.insert(tk.END, "Not Connected")


    def set_positioner(self, positioner):
        self.positioner_selected = positioner
        self.positioner_selected_var.set(f"Positioner: {positioner}")
        self.positioner_selected_for_use = positioner
        print(self.positioner_selected_for_use)
        global selected_positioner_global
        selected_positioner_global = self.positioner_selected
        initial_status = self.initial_positioner_status()
        logging.info(f"positioner_selected within set_positioner: {self.positioner_selected}")
        print(self.positioner_selected)
        return initial_status

    def initial_positioner_status(self):
        channel = self.fl_network_mode()
        logging.info("within initial_positioner_status")
        #channel = self.alex_home_network_mode()
        ttyf = "/dev/ttyUSB1"
        channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo \n")
        logging.info('channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo \n")')
        #testing time
        channel.settimeout(1)
        output = channel.recv(1024).decode("iso-8859-1")
        time.sleep(.1)
        channel.send(f"echo > {ttyf}\n")
        logging.info('channel.send(f"echo > {ttyf}\n")')
        self.get_positioner_status()
        #todo make sure initial check reads correctly 8/21/26
        logging.info(f"output from initial_positioner_status: {output}")
        # if "POS>" in output:
        #     logging.info("POS> IN output")
        #     self.get_positioner_status()
        #     return True
        # else:
        #     logging.info("NO 'POS>' in output")
        #     return False



    def fl_network_mode(self):
        print(self.positioner_selected)
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=f"{self.positioner_selected}", username=f"{os.environ.get('CONNECTION_USERNAME')}",
                       password=f"{os.environ.get('CONNECTION_PASSWORD')}", look_for_keys=False, allow_agent=False)
        # print(f"{self.positioner_selected_for_use} inside status")
        # print(f"{selected_positioner_global} GLOBAL status")
        transport = client.get_transport()
        channel = transport.open_session()
        channel.get_pty()
        channel = client.invoke_shell()
        time.sleep(1)
        logging.info("CONNECTED TO FLORIDA NETWORK")
        return channel

    # def alex_home_network_mode(self):
        #moved to test file


    def get_positioner_status(self):
        channel = self.fl_network_mode()
        self.status_text_box.delete("1.0", tk.END)
        #channel = self.alex_home_network_mode()
        logging.info("within get_positioner_status")
        ttyf="/dev/ttyUSB1"
        channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
        channel.send(f"cat {ttyf} &\n")
        time.sleep(.5)
        channel.send(f"echo scan status > {ttyf}\n")
        time.sleep(.5)
        channel.send("fg\n")
        time.sleep(0.5)
        channel.send(f"\x1a")
        time.sleep(.5)
        scan_mode_variable = ""
        run_status_variable = ""
        start_az_variable = ""
        end_az_variable = ""
        el_axis_start_end_variable = []
        el_beam_start_end_variable = []

        try:
            output = channel.recv(8192).decode("iso-8859-1")

            time.sleep(1)
            output_status = output.split(":~$ scan status", 1)
            output_lines = output_status[1].split("\r")
            for index, line in enumerate(output_lines):
                if "Mode: " in line:
                    scan_mode_variable = line.split("Mode:")[1]
                if "Run:" in line:
                    run_status_variable = line.split("Run:")[1]
                if "Start Az:" in line:
                    start_az_variable = line.split("Start Az:")[1]
                if "End Az:" in line:
                    end_az_variable = line.split("End Az:")[1]
                if "El (axis) Start:" in line:
                    el_axis_start_end_variable = line.split("El (axis)")[1]
                if "El (beam) Start:" in line:
                    el_beam_start_end_variable = line.split("El (beam)")[1]
                self.status_text_box.insert(tk.END, line)
                if "Attenuations:" in line:
                    #self.status_text_box.insert(tk.END, "\r")
                    break
        except:
            channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
            channel.send(f"cat {ttyf} &\n")
            time.sleep(.5)
            channel.send(f"echo scan status > {ttyf}\n")
            time.sleep(.5)
            channel.send("fg\n")
            time.sleep(0.5)
            channel.send(f"\x1a")
            time.sleep(.5)
            output = channel.recv(8192).decode("iso-8859-1")
            time.sleep(1)
            output_status = output.split("scan status", 1)
            output_lines = output_status[1].split("\r")
            for index, line in enumerate(output_lines):
                if "Mode: " in line:
                    scan_mode_variable = line.split("Mode:")[1]
                if "Run:" in line:
                    run_status_variable = line.split("Run:")[1]
                if "Start Az:" in line:
                    start_az_variable = line.split("Start Az: ")[1]
                if "End Az:" in line:
                    end_az_variable = line.split("End Az: ")[1]
                if "El (axis) Start:" in line:
                    el_axis_start_end_variable = line.split("El (axis)")[1]
                if "El (beam) Start:" in line:
                    el_beam_start_end_variable = line.split("El (beam)")[1]
                self.status_text_box.insert(tk.END, line)
                if "Attenuations:" in line:
                    # self.status_text_box.insert(tk.END, "\r")
                    break

        scan_mode_variable = scan_mode_variable.strip().split(", ")[1]

        start_az_variable = f"Start Az: {float(start_az_variable.strip()):.2f}"
        end_az_variable = f"End Az: {float(end_az_variable.strip()):.2f}"
        el_axis_start_end_variable = el_axis_start_end_variable.strip().split(" ")
        el_axis_start = f"El (axis) Start: {float(el_axis_start_end_variable[1].split(',')[0]):.2f}"
        el_axis_end = f"El (axis) End: {float(el_axis_start_end_variable[3]):.2f}"
        el_beam_start_end_variable = el_beam_start_end_variable.strip().split(" ")
        el_beam_start = f"El (beam) Start: {float(el_beam_start_end_variable[1].split(',')[0]):.2f}"
        el_beam_end = f"El (beam) End: {float(el_beam_start_end_variable[3]):.2f}"

        channel.close()
        client.close()

        run_status_variable = int(run_status_variable.strip())
        simplified_variables_list = [scan_mode_variable, start_az_variable, end_az_variable, el_axis_start, el_axis_end, el_beam_start, el_beam_end]
        self.simplified_status.delete("1.0", tk.END)
        if run_status_variable == 1:
            self.simplified_status.insert(tk.END, "Running\n")
            self.pos_text_box.delete("1.0", tk.END)
            self.pos_text_box.insert("1.0", "Scanning\n")
        elif run_status_variable == 0:
            self.simplified_status.insert(tk.END, "Stopped\n")
            self.pos_text_box.delete("1.0", tk.END)
            self.pos_text_box.insert("1.0", "Scan Stopped\n")
        else:
            self.simplified_status.insert(tk.END, "Status Issue\n")
        for varies in simplified_variables_list:
            self.simplified_status.insert(tk.END, f"{varies}\n")
        if run_status_variable == 1:
            self.simplified_status.config(background="green4")
            self.simplified_status.config(foreground="black")
        else:
            self.simplified_status.config(background="firebrick3")
            self.simplified_status.config(foreground="black")
        global run_status_global
        run_status_global = run_status_variable
        return run_status_variable




    def spot_scan(self, start_az, end_az, start_elbeam, end_elbeam, speed, inc, repeat, slipdetect):
        self.pos_text_box.delete("1.0", tk.END)
        self.pos_text_box.config(font=("Arial", 16), foreground="white")
        self.pos_text_box.insert("1.0", "Starting Spot Scan")
        channel = self.fl_network_mode()
        #channel = self.alex_home_network_mode()
        ttyf = "/dev/ttyUSB1"
        channel.send(f"""
                    stty -F {ttyf} 115200 raw -hupcl -onlcr -echo
                    echo scan mode spot > {ttyf}
                    echo scan set startaz {start_az} > {ttyf}
                    echo scan set endaz {end_az} > {ttyf}
                    echo scan set startelbeam {start_elbeam} > {ttyf}
                    echo scan set endelbeam {end_elbeam} > {ttyf}
                    echo scan set speed {speed} > {ttyf}
                    echo scan set inc {inc} > {ttyf}
                    echo scan set repeat {repeat} > {ttyf}
                    echo scan set slipdetect {slipdetect} > {ttyf}
                    echo scan start > {ttyf}\n
                    """)
        time.sleep(0.5)
        self.get_positioner_status()
        channel.close()
        client.close()



    def rhi_scan(self, start_az, end_az, start_ele, end_ele, speed, inc, repeat, slipdetect):
        self.pos_text_box.delete("1.0", tk.END)
        self.pos_text_box.config(font=("Arial", 16), foreground="white")
        self.pos_text_box.insert("1.0", "Starting RHI Scan")
        channel = self.fl_network_mode()
        #channel = self.alex_home_network_mode()
        ttyf="/dev/ttyUSB1"
        channel.send(f"""
                    stty -F {ttyf} 115200 raw -hupcl -onlcr -echo
                    echo scan mode rhi > {ttyf}
                    echo scan set startaz {start_az} > {ttyf}
                    echo scan set endaz {end_az} > {ttyf}
                    echo scan set startelbeam {start_ele} > {ttyf}
                    echo scan set endelbeam {end_ele} > {ttyf}
                    echo scan set speed {speed} > {ttyf}
                    echo scan set inc {inc} > {ttyf}
                    echo scan set repeat {repeat} > {ttyf}
                    echo scan set slipdetect {slipdetect} > {ttyf}
                    echo scan start > {ttyf}\n
                    """)
        time.sleep(0.5)
        self.get_positioner_status()
        channel.close()
        client.close()

    def rhi_square_scan(self, start_az, end_az, start_ele, end_ele, speed, inc, repeat, slipdetect):
        self.pos_text_box.delete("1.0", tk.END)
        self.pos_text_box.config(font=("Arial", 16), foreground="white")
        self.pos_text_box.insert("1.0", "Starting RHI Square Scan")
        channel = self.fl_network_mode()
        #channel = self.alex_home_network_mode()
        ttyf="/dev/ttyUSB1"
        channel.send(f"""
                    stty -F {ttyf} 115200 raw -hupcl -onlcr -echo
                    echo scan mode rhisquare > {ttyf}
                    echo scan set startaz {start_az} > {ttyf}
                    echo scan set endaz {end_az} > {ttyf}
                    echo scan set startelbeam {start_ele} > {ttyf}
                    echo scan set endelbeam {end_ele} > {ttyf}
                    echo scan set speed {speed} > {ttyf}
                    echo scan set inc {inc} > {ttyf}
                    echo scan set repeat {repeat} > {ttyf}
                    echo scan set slipdetect {slipdetect} > {ttyf}
                    echo scan start > {ttyf}\n
                    """)
        time.sleep(1)
        self.get_positioner_status()
        channel.close()
        client.close()

        #channel.send(f"echo scan status > {ttyf}\n")

    def ppi_scan(self, start_az, end_az, start_ele, end_ele, speed, inc, repeat, slipdetect):
        self.pos_text_box.delete("1.0", tk.END)
        self.pos_text_box.config(font=("Arial", 16), foreground="white")
        self.pos_text_box.insert("1.0", "Starting PPI Scan")
        channel = self.fl_network_mode()
        #channel = self.alex_home_network_mode()
        ttyf="/dev/ttyUSB1"
        channel.send(f"""
                    stty -F {ttyf} 115200 raw -hupcl -onlcr -echo
                    echo scan mode ppi > {ttyf}
                    echo scan set startaz {start_az} > {ttyf}
                    echo scan set endaz {end_az} > {ttyf}
                    echo scan set startelbeam {start_ele} > {ttyf}
                    echo scan set endelbeam {end_ele} > {ttyf}
                    echo scan set speed {speed} > {ttyf}
                    echo scan set inc {inc} > {ttyf}
                    echo scan set repeat {repeat} > {ttyf}
                    echo scan set slipdetect {slipdetect} > {ttyf}
                    echo scan start > {ttyf}\n
                    """)
        logging.info(f'stty -F {ttyf} 115200 raw -hupcl -onlcr -echo')
        logging.info(f'echo scan mode ppi > {ttyf}')
        logging.info(f'echo scan set startaz {start_az} > {ttyf}')
        logging.info(f'echo scan set endaz {end_az} > {ttyf}')
        logging.info(f'echo scan set startelbeam {start_ele} > {ttyf}')
        logging.info(f'echo scan set endelbeam {end_ele} > {ttyf}')
        logging.info(f'echo scan set speed {speed} > {ttyf}')
        logging.info(f'echo scan set inc {inc} > {ttyf}')
        logging.info(f'echo scan set repeat {repeat} > {ttyf}')
        logging.info(f'echo scan set slipdetect {slipdetect} > {ttyf}')
        logging.info(f'echo scan start > {ttyf}')
        time.sleep(0.5)
        self.get_positioner_status()
        channel.close()
        client.close()

    def sector_scan(self, start_az, end_az, start_ele, end_ele, speed, inc, repeat, slipdetect):
        self.pos_text_box.delete("1.0", tk.END)
        self.pos_text_box.config(font=("Arial", 16), foreground="white")
        self.pos_text_box.insert("1.0", "Starting Sector Scan")
        channel = self.fl_network_mode()
        #channel = self.alex_home_network_mode()
        ttyf="/dev/ttyUSB1"
        channel.send(f"""
                    stty -F {ttyf} 115200 raw -hupcl -onlcr -echo
                    echo scan mode sector > {ttyf}
                    echo scan set startaz {start_az} > {ttyf}
                    echo scan set endaz {end_az} > {ttyf}
                    echo scan set startelbeam {start_ele} > {ttyf}
                    echo scan set endelbeam {end_ele} > {ttyf}
                    echo scan set speed {speed} > {ttyf}
                    echo scan set inc {inc} > {ttyf}
                    echo scan set repeat {repeat} > {ttyf}
                    echo scan set slipdetect {slipdetect} > {ttyf}
                    echo scan start > {ttyf}\n
                    """)
        time.sleep(0.5)
        # output = channel.recv(4096).decode("iso-8859-1")
        # print(output)
        self.get_positioner_status()
        channel.close()
        client.close()

    def stop_scan(self):
        logging.info("STOPPING SCAN")
        print("STOPPING SCAN")
        self.pos_text_box.delete("1.0", tk.END)
        self.pos_text_box.config(font=("Arial", 16), foreground="white")
        self.pos_text_box.insert("1.0", "Executing Stop Command\nPlease Standby for positioner\nto finish rotation\n")
        channel = self.fl_network_mode()
        #channel = self.alex_home_network_mode()
        time.sleep(1)
        ttyf="/dev/ttyUSB1"
        channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
        channel.send(f"echo scan stop > {ttyf}\n")
        time.sleep(1)

        for i in range(1, 301):
            run_status_variable = self.get_positioner_status()
            if run_status_variable != 1:
                print("WITHIN IF CONDITION OF STOP SCAN")
                break
            else:
                print("WITHIN ELSE CONDITION OF STOP SCAN")
                self.pos_text_box.delete("1.0", tk.END)
                self.pos_text_box.insert("1.0", f"Executing Stop Command Attempt #{i}\n Please Standby for positioner\nto finish rotation\n")
                channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
                channel.send(f"echo scan stop > {ttyf}\n")
                time.sleep(.5)



        run_status_variable = self.get_positioner_status()
        if run_status_variable == 1:
            self.pos_text_box.delete("1.0", tk.END)
            self.pos_text_box.insert(tk.END, f"Stop Command fail, retry")
            self.pos_text_box.config(font=("Arial", 24), foreground="red")
        else:
            self.pos_text_box.delete("1.0", tk.END)
            self.pos_text_box.config(font=("Arial", 16), foreground="white")
            self.pos_text_box.insert("1.0", "Scan stopped\n")


        channel.close()
        client.close()

    #NEED TO CHECK
    def get_current_position(self):
        self.pos_text_box.delete("1.0", tk.END)
        logging.info("Getting Current Position")
        channel = self.fl_network_mode()
        #channel = self.alex_home_network_mode()
        ttyf = "/dev/ttyUSB1"
        channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
        channel.send(f"cat {ttyf} &\n")
        time.sleep(0.5)
        channel.send(f"echo pos > {ttyf}\n")
        time.sleep(0.5)
        channel.send("fg \n")
        time.sleep(0.5)
        channel.send(f"\x1a")
        output = channel.recv(8192).decode("iso-8859-1")
        time.sleep(1)
        try:
            output_status = output.split(":~$ pos", 1)
            output_lines = output_status[1].split("\r")
            current_datetime = datetime.now()
            self.pos_text_box.insert(tk.END, f"Time of Position Check:\n")
            self.pos_text_box.insert(tk.END, current_datetime)
            for line in output_lines:
                self.pos_text_box.insert(tk.END, line)
                if "AZ/EL From Encoders:" in line:
                    #self.status_text_box.insert(tk.END, "\r")
                    break
        except:
            output_status = output.split("pos", 1)
            output_lines = output_status[1].split("\r")
            current_datetime = datetime.now()
            self.pos_text_box.insert(tk.END, f"Time of Position Check:\r {current_datetime}\r")
            for line in output_lines:
                self.pos_text_box.insert(tk.END, line)
                if "AZ/EL From Encoders:" in line:
                    # self.status_text_box.insert(tk.END, "\r")
                    break

        channel.close()
        client.close()


    def re_home(self):
        channel = self.fl_network_mode()
        #channel =self.alex_home_network_mode()
        ttyf = "/dev/ttyUSB1"
        channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
        channel.send(f"echo rehome > {ttyf}\n")
        time.sleep(0.5)
        self.get_positioner_status()
        channel.close()
        client.close()


    def go_home(self):
        channel = self.fl_network_mode()
        #channel =self.alex_home_network_mode()
        ttyf = "/dev/ttyUSB1"
        channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
        channel.send(f"echo gohome > {ttyf}\n")
        time.sleep(0.5)
        self.get_positioner_status()
        channel.close()
        client.close()

    def set_home(self, key_stroke):
        logging.info(f"key stroke pressed: {key_stroke}")
        print(f"{type(key_stroke)} in set home")
        channel = self.fl_network_mode()
        #channel = self.alex_home_network_mode()
        ttyf="/dev/ttyUSB1"
        channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo cbreak\n")
        time.sleep(0.1)
        #no keystrokes
        channel.send(f"echo -n {key_stroke} > {ttyf}\n")
        logging.info(f'channel.send(f"echo -n {key_stroke} > {ttyf}\n")')
        channel.settimeout(2)
        output = channel.recv(12288).decode("iso-8859-1")
        for line in output.split("\n"):
            logging.info(line)
            self.status_text_box.insert(tk.END, line)
        time.sleep(0.1)
        channel.close()
        client.close()


    def reset_positioner(self):
        print(f"positioner selected: {self.positioner_selected}")
        logging.info("RESET POSITIONER CALLED")
        answer = messagebox.askyesno("Reset Positioner", "Do you want to reset positioner?")
        print(answer)
        if answer:
            print("reset positioner")
            channel = self.fl_network_mode()
            #channel = self.alex_home_network_mode()
            ttyf = "/dev/ttyUSB1"
            channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
            logging.info(f'channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")')
            time.sleep(0.5)
            channel.send(f"echo reset > {ttyf}\n")
            logging.info(f'channel.send(f"echo reset > {ttyf}\n")')
            channel.settimeout(2)
            output = channel.recv(12288).decode("iso-8859-1")
            for line in output.split("\n"):
                logging.info(line)
                self.status_text_box.insert(tk.END, line)
            channel.close()
            client.close()
        else:
            print("dont reset positioner")

    def fpga_stream(self, command_string):
        global is_fpga_running
        is_fpga_running = True
        #Set up to capture packets
        #set up directory
        try:
            subprocess.run(['socat','tcp-l:7777,reuseaddr,fork','system:\'cpio -i\''], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with exit code {e.returncode}")

        print(f"positioner selected: {self.positioner_selected}")
        print(f"INSIDE FPGA STREAM{command_string}")
        #todo Setup Output of x y power and command path
        channel = self.fl_network_mode()
        channel.get_pty()
        channel.invoke_shell()
        channel.send(f"cd {os.environ['FPGAPATH']}\n")
        time.sleep(.1)
        #sent to reroute capture packets
        channel.send("./fpgaStream -q -c | socat - tcp:10.42.0.1:7777")
        #TODO SET COMMAND PATH
        channel.send(f"./fpgaStream {command_string}\n")
        time.sleep(2)
        while channel.active and is_fpga_running:
            chunk = channel.recv(1024).decode("iso-8859-1")
            output += chunk
            current_time = time.time()
            if "<5>" in output:
                after = output.split("<5>", 1)
                if "[1;1H$<5>" in after[1]:
                    new_output = after[1].replace("[1;1H$<5>", "\n")
                    new_output = new_output.split("\n")
                    for line in new_output:
                        print(line)
                        splits = line.split(",")
                        desired_fields = []
                        for index, split in enumerate(splits):
                            if len(splits) == 11:
                                if index < 6 or index == 9:
                                    desired_fields.append(split)
                        print(desired_fields)
                        output_queue.put(desired_fields)
                        self.run_queue()
            output = ""
            time.sleep(.5)
        channel.send("^S\n")
        channel.send("^C\n")
        client.close()

    def run_queue(self):
        # print(f"OPQ: {output_queue.get()}")
        # while output_queue.qsize() > 10 and is_running:
        #     self.after(100, self.io_frame.output_frame.update_all_textboxes(output_queue.get()))
        print(output_queue.qsize())
        try:
            if not output_queue.empty():
                self.after(10, self.update_pos_textbox_fpga(output_queue.get()))
        except:
            print("Error occured")

    def update_pos_textbox_fpga(self, output_list):
        #TODO clean this up
        x_dc_offset_value = output_list[0].split("= ")
        y_dc_offset_value = output_list[1].split("= ")
        x_min_max_value = output_list[2].split("X  ")
        y_min_max_value = output_list[3].split("Y  ")
        x_power_value = output_list[4].split(": ")
        # self.x_power_textbox.replace("1.0", tk.END, x_power_value[1], "center")
        # self.x_power_textbox.tag_configure("center", justify="center")
        y_power_value = output_list[5].split(": ")
        rate_value = output_list[6].split(": ")
        # self.y_power_textbox.replace("1.0", tk.END, y_power_value[1], "center")
        # self.y_power_textbox.tag_configure("center", justify="center")

        self.pos_text_box.insert("1.0", tk.END, x_power_value[1], "center")
        self.pos_text_box.replace("1.0", tk.END, y_power_value[1], "center")

    def end_fpga_running(self):
        global is_fpga_running
        is_fpga_running = False


class OutputFrame(tk.Frame):
    def __init__(self, parent, terminal_frame):
        super().__init__(parent,background="gray7")
        self.rowconfigure(list(range(6)), weight=1)
        self.columnconfigure(0, weight=1)
        self.grid_propagate(False)
        self.terminal_frame = terminal_frame

        #self.pos_text_box = tk.Text(self, height=1, width=20, background="gray7")
        # self.pos_text_box = tk.Text(self, font=("Arial", 20), background="orange", fg="white")
        # self.pos_text_box.grid(column=0, row=0, sticky="NEW")
        # self.pos_text_box.config(height=30, width = 30, bg="orange")


class ScanFrame(tk.Frame):
    def __init__(self, parent, terminal_frame):
        super().__init__(parent, background='gray7')
        self.columnconfigure(list(range(7)), weight=1)
        self.rowconfigure(list(range(4)), weight=1)
        self.terminal_frame = terminal_frame

        self.start_azimuth_var = tk.StringVar()
        self.end_azimuth_var = tk.StringVar()
        self.start_elbeam_var = tk.StringVar()
        self.end_elbeam_var = tk.StringVar()
        self.speed_var = tk.StringVar()
        self.increment_var = tk.StringVar()
        self.repeat_var = tk.StringVar()
        self.slipdetect_var = tk.StringVar()
        self.create_layout()
        self.homing_fpga_commands = {}
        self.qualifier_values = ["5.0/1.0 Deg", "0.5/0.25 Deg", "0.1/0.05 Deg", "0.01/0.01 Deg"]
        self.movement_selected = tk.StringVar()
        self.movement_selected.set(self.qualifier_values[0])

        #TODO ADD / and SPACEBAR
        self.keys_to_bind = [
            '<Key-I>', '<Key-i>',
            '<Key-J>', '<Key-j>',
            '<Key-K>', '<Key-k>',
            '<Key-L>', '<Key-l>',
            '<Key-W>', '<Key-w>',
            '<Key-A>', '<Key-a>',
            '<Key-S>', '<Key-s>',
            '<Key-D>', '<Key-d>',
        ]

    def run_fpga(self, one, two, three, four, five, six, seven):
        self.popup.destroy()
        command_string = f" -w {one} -s {two} -e {three} -g {four} -S {five} -8 {six} -9 {seven}"
        print(command_string)

        thread = threading.Thread(
            target=self.terminal_frame.fpga_stream,
            args= (command_string,),
            daemon=True
        )
        thread.start()

        #self.terminal_frame.fpga_stream(command_list)

    def open_fpga_popup(self):
        self.popup = tk.Toplevel()
        self.popup.title("FPGA")
        self.popup.geometry("500x500")
        self.popup.grab_set()

        #TODO AUTOMATE FIELD POPULATION
        # for index, entry in enumerate(FPGA_COMMAND_ALPHA):
        #     labels = CommandLabels(parent=self, command_selected=entry, unit=COMMAND_UPDATE[entry]['unit'],
        #                            text=COMMAND_UPDATE[entry]['title'], col=1, row=index)
        #     labels.insert(tk.END, COMMAND_UPDATE[entry]['title'])
        #     labels.config(state="disabled")
        #     labels.config(font=("Arial", 20))
        #     labels.config(wrap="word")
        #     self.entry_dict[f'entry_{[index]}'] = tk.StringVar()
        #
        #     entry = ttk.Entry(self, width=10, font=("Arial", 20), textvariable=self.entry_dict[f'entry_{[index]}'])
        #     if COMMAND_UPDATE[FPGA_COMMAND_ALPHA[index]]['default_value'] == 'True':
        #         entry.insert(15, f"{COMMAND_UPDATE[FPGA_COMMAND_ALPHA[index]]['default_value']}")
        #         entry.grid(column=0, row=index, sticky="NS")
        #         self.command_dict[FPGA_COMMAND_ALPHA[index]] = COMMAND_UPDATE[FPGA_COMMAND_ALPHA[index]][
        #             'default_value']
        #         entry.config(state=tk.DISABLED)
        #     elif COMMAND_UPDATE[FPGA_COMMAND_ALPHA[index]]['default_value']:
        #         entry.insert(15, f"{COMMAND_UPDATE[FPGA_COMMAND_ALPHA[index]]['default_value']}")
        #         entry.grid(column=0, row=index, sticky="NS")
        #         self.command_dict[FPGA_COMMAND_ALPHA[index]] = COMMAND_UPDATE[FPGA_COMMAND_ALPHA[index]][
        #             'default_value']




        entry_1 = tk.StringVar(value="0.96")
        entry_2 = tk.StringVar(value="0.5")
        entry_3 = tk.StringVar(value="0.5")
        entry_4 = tk.StringVar(value="0.0")
        entry_5 = tk.StringVar(value="1000")
        entry_6 = tk.StringVar(value="144")
        entry_7 = tk.StringVar(value="24")

        label_1= tk.Label(self.popup, text="-w")
        label_1.grid(column=0, row=0, sticky="NSW")
        label_2 = tk.Label(self.popup, text="-s")
        label_2.grid(column=0, row=1, sticky="NSW")
        label_3=tk.Label(self.popup, text="-e")
        label_3.grid(column=0, row=2, sticky="NSW")
        label_4=tk.Label(self.popup, text="-g")
        label_4.grid(column=0, row=3, sticky="NSW")
        label_5=tk.Label(self.popup, text="-S")
        label_5.grid(column=0, row=4, sticky="NSW")
        label_6=tk.Label(self.popup, text="-8")
        label_6.grid(column=0, row=5, sticky="NSW")
        label_7=tk.Label(self.popup, text="-9")
        label_7.grid(column=0, row=6, sticky="NSW")

        entry_1=tk.Entry(self.popup, width=10, textvariable=entry_1)
        entry_1.grid(column=1, row=0, sticky="NSW")

        entry_2 = tk.Entry(self.popup, width=10, textvariable=entry_2)
        entry_2.grid(column=1, row=1, sticky="NSW")

        entry_3 = tk.Entry(self.popup, width=10, textvariable=entry_3)
        entry_3.grid(column=1, row=2, sticky="NSW")

        entry_4 = tk.Entry(self.popup, width=10, textvariable=entry_4)
        entry_4.grid(column=1, row=3, sticky="NSW")

        entry_5 = tk.Entry(self.popup, width=10, textvariable=entry_5)
        entry_5.grid(column=1, row=4, sticky="NSW")

        entry_6 = tk.Entry(self.popup, width=10, textvariable=entry_6)
        entry_6.grid(column=1, row=5, sticky="NSW")

        entry_7 = tk.Entry(self.popup, width=10, textvariable=entry_7)
        entry_7.grid(column=1, row=6, sticky="NSW")

        fpga_button = tk.Button(self.popup, text="Run FPGA", command= lambda: self.run_fpga(entry_1.get(), entry_2.get(), entry_3.get(), entry_4.get(), entry_5.get(), entry_6.get(), entry_7.get()))
        fpga_button.grid(column=4, row=0, sticky="NSE")

        self.homing_fpga_commands = {f" -w {entry_1} -s {entry_2} -e {entry_3} -g {entry_4} -S {entry_5} -8 {entry_6} -9 {entry_7}"}

        close_btn = tk.Button(self.popup, text="close", command=self.popup.destroy)
        close_btn.grid(column=4, row=1, sticky="NSE")

    def create_layout(self):

        self.start_azimuth_label = tk.Label(self, text="Start Azimuth", font = ("Arial", 20), foreground="white", background="gray7")
        self.start_azimuth_label.grid(column=0, row=0, sticky="NSW")

        self.start_azimuth_entry = ttk.Entry(self, width=10, font = ("Arial", 20), textvariable=self.start_azimuth_var)
        self.start_azimuth_entry.delete(0, tk.END)
        self.start_azimuth_entry.insert(0, "startaz")
        self.start_azimuth_entry.grid(column=1, row=0, sticky="NSEW")
        self.start_azimuth_entry.bind("<Button-1>", self.on_click_clear)

        self.end_azimuth_label = tk.Label(self, text="End Azimuth", font = ("Arial", 20), foreground="white", background="gray7")
        self.end_azimuth_label.grid(column=0, row=1, sticky="NSW")

        self.end_azimuth_entry = ttk.Entry(self, width=10, font = ("Arial", 20), textvariable=self.end_azimuth_var)
        self.end_azimuth_entry.delete(0, tk.END)
        self.end_azimuth_entry.insert(0, "endaz")
        self.end_azimuth_entry.grid(column=1, row=1, sticky="NSEW")
        self.end_azimuth_entry.bind("<Button-1>", self.on_click_clear)

        self.start_elbeam_label = tk.Label(self, text="Start Elbeam", font = ("Arial", 20), foreground="white", background="gray7")
        self.start_elbeam_label.grid(column=0, row=2, sticky="NSW")
        self.start_elbeam_entry = ttk.Entry(self, width=10, font = ("Arial", 20), textvariable=self.start_elbeam_var)
        self.start_elbeam_entry.delete(0, tk.END)
        self.start_elbeam_entry.insert(0, "start elbeam")
        self.start_elbeam_entry.grid(column=1, row = 2, sticky = "NSEW")
        self.start_elbeam_entry.bind("<Button-1>", self.on_click_clear)

        self.end_elbeam_label=tk.Label(self, text="End Elbeam", font=("Arial", 20), foreground="white", background="gray7")
        self.end_elbeam_label.grid(column=0, row=3, sticky="NSW")

        self.end_elbeam_entry = ttk.Entry(self, width=10, font = ("Arial", 20), textvariable=self.end_elbeam_var)
        self.end_elbeam_entry.delete(0, tk.END)
        self.end_elbeam_entry.insert(0, "end elbeam")
        self.end_elbeam_entry.grid(column=1, row = 3, sticky = "NSEW")
        self.end_elbeam_entry.bind("<Button-1>", self.on_click_clear)

        self.speed_label = tk.Label(self, text="Speed", font=("Arial", 20), foreground="white", background="gray7")
        self.speed_label.grid(column=2, row=0, sticky="NSW")

        self.speed_entry = ttk.Entry(self, width=10, font = ("Arial", 20), textvariable=self.speed_var)
        self.speed_entry.delete(0, tk.END)
        self.speed_entry.insert(0, "20")
        self.speed_entry.grid(column=3, row=0, sticky="NSEW")

        self.increment_label = tk.Label(self, text="Increment", font=("Arial", 20), foreground="white", background="gray7")
        self.increment_label.grid(column=2, row=1, sticky="NSW")

        self.increment_entry = ttk.Entry(self, width=10, font = ("Arial", 20), textvariable=self.increment_var)
        self.increment_entry.delete(0, tk.END)
        self.increment_entry.insert(0, "1.5")
        self.increment_entry.grid(column=3, row=1, sticky="NSEW")

        self.repeat_label = tk.Label(self, text="Repeat", font=("Arial", 20), foreground="white", background="gray7")
        self.repeat_label.grid(column=2, row=2, sticky="NSW")

        self.repeat_entry = ttk.Entry(self, width=10, font = ("Arial", 20), textvariable=self.repeat_var)
        self.repeat_entry.delete(0, tk.END)
        self.repeat_entry.insert(0, "1")
        self.repeat_entry.grid(column=3, row=2, sticky="NSEW")

        self.slipdetect_label = tk.Label(self, text="Slip Detect", font=("Arial", 20), foreground="white", background="gray7")
        self.slipdetect_label.grid(column=2, row=3, sticky="NSW")

        self.slipdetect_entry = ttk.Entry(self, width=10, font = ("Arial", 20), textvariable=self.slipdetect_var)
        self.slipdetect_entry.delete(0, tk.END)
        self.slipdetect_entry.insert(0, "1")
        self.slipdetect_entry.grid(column=3, row=3, sticky="NSEW")

        self.rhi_scan = tk.Button(self, text = "RHI", command= lambda: self.start_threading("RHI"))
        self.rhi_scan.grid(column=4, row = 0, sticky = "NSEW")
        self.rhi_scan.config(font = ("Arial", 20))

        self.rhi_squared_scan = tk.Button(self, text="RHI Square", command=lambda: self.start_threading("RHI SQUARE"))
        self.rhi_squared_scan.grid(column=4, row=1, sticky="NSEW")
        self.rhi_squared_scan.config(font=("Arial", 20))

        self.ppi_scan = tk.Button(self, text="PPI", command=lambda: self.start_threading("PPI"))
        self.ppi_scan.grid(column=4, row = 2, sticky="NSEW")
        self.ppi_scan.config(font=("Arial", 20))

        self.sector_scan = tk.Button(self, text="Sector", command=lambda: self.start_threading("SECTOR"))
        self.sector_scan.grid(column=4, row = 3, sticky="NSEW")
        self.sector_scan.config(font=("Arial", 20))


        self.spot_scan = tk.Button(self, text="Spot Scan", command=lambda: self.start_threading("SPOT"))
        self.spot_scan.grid(column=5, row = 0, sticky="NSEW")
        self.spot_scan.config(font=("Arial", 20))

        self.homing_mode = tk.Button(self, text="Homing mode", command=lambda: self.homing_mode_interface())
        self.homing_mode.grid(column=5, row = 1, sticky="NSEW")
        self.homing_mode.config(font=("Arial", 20))

        self.go_home = tk.Button(self, text = "GO HOME", command=lambda: self.terminal_frame.go_home())
        self.go_home.grid(column=5, row = 2, sticky="NSEW")
        self.go_home.config(font=("Arial", 20))

        self.re_home = tk.Button(self, text = "RE HOME", command=lambda: self.terminal_frame.re_home())
        self.re_home.grid(column=5, row = 3, sticky="NSEW")
        self.re_home.config(font=("Arial", 20))


    def set_home_finished(self, cmd):
        for key in self.keys_to_bind:
            self.unbind_all(key)
        try:
            self.terminal_frame.set_home(cmd)

        except:
            pass
        self.left_button.destroy()
        self.right_button.destroy()
        self.up_button.destroy()
        self.down_button.destroy()
        self.qualifier_box.destroy()
        #self.fpgastream.destroy()
        #self.stop_fpgastream.destroy()
        self.set_home_button.destroy()
        self.create_layout()
        logging.info("NORMAL MODE ACTIVATED")

    def movement_output(self, key_press, movement):
        print(f"keystroke: '{movement} {key_press}'")
        #"5.0/1.0 Deg", "0.5/0.25 Deg", "0.1/0.05 Deg", "0.01/0.01 Deg"
        # key_pad_dict = {"5.0/1.0 Deg up": 'W',
        #                 "5.0/1.0 Deg down": 'S',
        #                 "5.0/1.0 Deg left": 'A',
        #                 "5.0/1.0 Deg right": 'D',
        #                 "0.5/0.25 Deg up": 'w',
        #                 "0.5/0.25 Deg down": 's',
        #                 "0.5/0.25 Deg left": 'a',
        #                 "0.5/0.25 Deg right": 'd',
        #                 "0.1/0.05 Deg up": 'i',
        #                 "0.1/0.05 Deg down": 'k',
        #                 "0.1/0.05 Deg left": 'j',
        #                 "0.1/0.05 Deg right": 'l',
        #                 "0.01/0.01 Deg up": 'I',
        #                 "0.01/0.01 Deg down": 'K',
        #                 "0.01/0.01 Deg left": 'J',
        #                 "0.01/0.01 Deg right": 'L',
        #                 }
        movement_dict = {"5.0/1.0 Deg up": 'W',
                        "5.0/1.0 Deg down": 'S',
                        "5.0/1.0 Deg left": 'A',
                        "5.0/1.0 Deg right": 'D',
                        "0.5/0.25 Deg up": 'w',
                        "0.5/0.25 Deg down": 's',
                        "0.5/0.25 Deg left": 'a',
                        "0.5/0.25 Deg right": 'd',
                        "0.1/0.05 Deg up": 'i',
                        "0.1/0.05 Deg down": 'k',
                        "0.1/0.05 Deg left": 'j',
                        "0.1/0.05 Deg right": 'l',
                        "0.01/0.01 Deg up": 'I',
                        "0.01/0.01 Deg down": 'K',
                        "0.01/0.01 Deg left": 'J',
                        "0.01/0.01 Deg right": 'L',
                        "coarse left": 'A',
                         "coarse right": 'D',
                         "coarse up": 'W',
                         "coarse down": 'S',
                         "fine left": 'a',
                         "fine right": 'd',
                         "fine up": 'w',
                         "fine down": 's',
                         'extra fine left': 'j',
                         'extra fine right': 'l',
                         'extra fine up': 'i',
                         'extra fine down': 'k',
                         'extra extra fine left': 'J',
                         'extra extra fine right': 'L',
                         'extra extra fine up': 'I',
                         'extra extra fine down': 'K',}

        for key, value in movement_dict.items():
            if key == f'{movement} {key_press}':
                try:
                    print(f"value for set home {value}")
                    self.terminal_frame.set_home(value)
                except Exception as e:
                    print(f"{e}")



    def homing_mode_interface(self):
        #Clear or reset default values
        #Todo Open connection here and keep homing mode connection until done? Can this occur with the fpga stream?
        logging.info("HOMING MODE ACTIVATED")
        self.focus_set()
        self.terminal_frame.pos_text_box.config(state="disabled")
        self.terminal_frame.status_text_box.config(state="disabled")
        self.terminal_frame.simplified_status.config(state="disabled")

        self.start_azimuth_label.destroy()
        self.start_azimuth_entry.destroy()
        self.end_azimuth_label.destroy()
        self.end_azimuth_entry.destroy()
        self.start_elbeam_label.destroy()
        self.start_elbeam_entry.destroy()
        self.end_elbeam_label.destroy()
        self.end_elbeam_entry.destroy()
        self.speed_label.destroy()
        self.speed_entry.destroy()
        self.increment_label.destroy()
        self.increment_entry.destroy()
        self.repeat_label.destroy()
        self.repeat_entry.destroy()
        self.slipdetect_label.destroy()
        self.slipdetect_entry.destroy()
        self.rhi_scan.destroy()
        self.rhi_squared_scan.destroy()
        self.ppi_scan.destroy()
        self.sector_scan.destroy()
        self.spot_scan.destroy()
        self.homing_mode.destroy()
        self.go_home.destroy()
        self.re_home.destroy()

        self.exit_homing_mode = tk.Button(self, text="Exit", command=lambda: self.set_home_finished("x"))
        self.exit_homing_mode.grid(column = 5, row = 1, sticky="NSEW")
        self.exit_homing_mode.config(font=("Arial", 20))
        self.exit_homing_mode.config(width=10)

        #self.left_button = tk.Button(self, text="Left", command= lambda: self.terminal_frame.set_home("left"))
        self.left_button = tk.Button(self, text="Left", command=lambda: self.movement_output("left", self.movement_selected.get()))
        self.left_button.grid(column = 1, row = 1, sticky="NSEW")
        self.left_button.config(font=("Arial", 20))
        self.left_button.config(width=10)

        # self.right_button = tk.Button(self, text="Right", command=lambda: self.terminal_frame.set_home("right"))
        self.right_button = tk.Button(self, text="Right", command=lambda: self.movement_output("right", self.movement_selected.get()))
        self.right_button.grid(column = 3, row = 1, sticky="NSEW")
        self.right_button.config(font=("Arial", 20))
        self.right_button.config(width=10)

        # self.up_button = tk.Button(self, text="Up", command=lambda: self.terminal_frame.set_home("up"))
        self.up_button = tk.Button(self, text="Up", command=lambda: self.movement_output("up", self.movement_selected.get()))
        self.up_button.grid(column = 2, row = 0, sticky="NSEW")
        self.up_button.config(font=("Arial", 20))
        self.up_button.config(width=10)

        #self.down_button = tk.Button(self, text="Down", command=lambda: self.terminal_frame.set_home("down"))
        self.down_button = tk.Button(self, text="Down", command=lambda: self.movement_output("down", self.movement_selected.get()))
        self.down_button.grid(column = 2, row = 2, sticky="NSEW")
        self.down_button.config(font=("Arial", 20))
        self.down_button.config(width=10)


        self.qualifier_box= ttk.Combobox(self, textvariable=self.movement_selected, values=self.qualifier_values, state="readonly")
        self.qualifier_box.grid(column=0, row=0, sticky="NSEW")
        self.qualifier_box.config(font=("Arial", 20))
        self.qualifier_box.config(width=10)




        self.set_home_button = tk.Button(self, text="Save Home-'/'", command=lambda: self.set_home_finished("/"))
        self.set_home_button.grid(column=4, row=2, sticky="NSEW")
        self.set_home_button.config(font=("Arial", 20))


        # self.space_bar_button = tk.Button(self, text="Space Bar", command=lambda: self.terminal_frame.set_home("space_bar"))
        # self.set_home_button.grid(column=4, row=3, sticky="NSEW")
        # self.set_home_button.config(font=("Arial", 20))
        self.space_bar_button = tk.Button(self, text="Last Saved-' '", command=lambda: self.terminal_frame.set_home(" "))
        self.space_bar_button.grid(column=4, row=3, sticky="NSEW")
        self.space_bar_button.config(font=("Arial", 20))

        #TODO FPGA STREAM WITHIN BUT NOT FOR NOW
        # self.fpgastream = tk.Button(self, text="FPGA", command=lambda: self.open_fpga_popup())
        # self.fpgastream.grid(column=5, row=2, sticky="NSEW")
        # self.fpgastream.config(font=("Arial", 20))
        # self.fpgastream.config(width=10)
        #
        # self.stop_fpgastream = tk.Button(self, text="Stop FPGA", command=lambda: self.terminal_frame.end_fpga_running())
        # self.stop_fpgastream.grid(column=5, row=3, sticky="NSEW")
        # self.stop_fpgastream.config(font=("Arial", 20))
        # self.stop_fpgastream.config(width=10)

        #Bound Keys for Use as well as buttons
        for key in self.keys_to_bind:
            self.bind_all(key, lambda event, k=key: self.terminal_frame.set_home(k[-2]))



    def on_click_clear(self, event):
        event.widget.delete(0, "end")

    def input_checker(self, start_azimuth_var, end_azimuth_var, start_elbeam_var, end_elbeam_var, speed_var, increment_var, repeat_var, slipdetect_var):

        try:
            start_az = float(start_azimuth_var.get())
        except:
            self.start_azimuth_entry.delete(0, "end")
            return messagebox.showerror("Error", "Starting Azimuth must be between 0 and 360")

        try:
            end_az = float(end_azimuth_var.get())
        except:
            self.end_azimuth_entry.delete(0, "end")
            return messagebox.showerror("Error", "Ending Azimuth must be between 0 and 360")

        try:
            start_elbeam = float(start_elbeam_var.get())
        except:
            self.start_elbeam_entry.delete(0, "end")
            return messagebox.showerror("Error", "Starting Elbeam must be between -6 and 45")

        try:
            end_elbeam = float(end_elbeam_var.get())
        except:
            self.end_elbeam_entry.delete(0, "end")
            return messagebox.showerror("Error", "Ending Elbeam must be between -6 and 45")

        try:
            speed = float(speed_var.get())
        except:
            self.speed_entry.delete(0, "end")
            return messagebox.showerror("Error", "Speed must be between 2 and 300")

        try:
            increment = float(increment_var.get())
        except:
            self.increment_entry.delete(0, "end")
            return messagebox.showerror("Error", "Increment must be between 1.5 and 5")

        try:
            repeat = int(repeat_var.get())
        except:
            self.repeat_entry.delete(0, "end")
            return messagebox.showerror("Error", "Repeat: 1 for yes, 0 for no")

        try:
            slipdetect = int(slipdetect_var.get())
        except:
            self.slipdetect_entry.delete(0, "end")
            return messagebox.showerror("Error", "Slip detect: 1 for yes, 0 for no")


        if start_az < 0 or start_az >= end_az or start_az > 360:
            self.start_azimuth_entry.delete(0, "end")
            return messagebox.showerror("Error", "Starting Azimuth must be between 0 and 360")
        if end_az < 0 or end_az > 360:
            self.end_azimuth_entry.delete(0, "end")
            return messagebox.showerror("Error", "Ending Azimuth must be between 0 and 360")
        if start_elbeam < -7 or start_elbeam > 45 or start_elbeam >= end_elbeam:
            self.start_elbeam_entry.delete(0, "end")
            return messagebox.showerror("Error", "Starting Elbeam must be between -6 and 45")
        if end_elbeam < -5 or end_elbeam > 45:
            self.end_elbeam_entry.delete(0, "end")
            return messagebox.showerror("Error", "Ending Elbeam must be between -6 and 45")
        if speed < 2 or speed > 300:
            self.speed_entry.delete(0, "end")
            self.speed_entry.insert("0", "20.0")
            return messagebox.showerror("Error", "Speed must be between 2 and 300")
        if increment < 1.5 or increment > 5:
            self.increment_entry.delete(0, "end")
            self.increment_entry.insert("0", "1.5")
            return messagebox.showerror("Error", "Increment must be between 1.5 and 5")
        if repeat not in [0, 1]:
            self.repeat_entry.delete(0, "end")
            self.repeat_entry.insert("0", "1")
            return messagebox.showerror("Error", "Repeat: 1 for yes, 0 for no")
        if slipdetect not in [0, 1]:
            self.slipdetect_entry.delete(0, "end")
            self.slipdetect_entry.insert("0", "1")
            return messagebox.showerror("Error", "Slip detect: 1 for yes, 0 for no")
        return start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat, slipdetect

    def start_threading(self, scan_type):
        start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat, slipdetect = self.input_checker(
            self.start_azimuth_var, self.end_azimuth_var, self.start_elbeam_var, self.end_elbeam_var, self.speed_var,
            self.increment_var, self.repeat_var, self.slipdetect_var)
        #todo match not available in this version of python
        # match scan_type:
        #     case "RHI":
        #         self.terminal_frame.rhi_scan(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat, slipdetect)
        #         return None
        #     case "RHI SQUARE":
        #         self.terminal_frame.rhi_square_scan(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat, slipdetect)
        #         return None
        #     case "PPI":
        #         self.terminal_frame.ppi_scan(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat, slipdetect)
        #         return None
        #     case "SECTOR":
        #         self.terminal_frame.sector_scan(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat, slipdetect)
        #         return None
        #     case "SPOT":
        #         self.terminal_frame.spot_scan(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat, slipdetect)
        #         return None
        #     case "SET HOME":
        #         self.terminal_frame.set_home()
        #         return None
        #     case _:
        #         return print("unknown")

        if scan_type == "RHI":
            # self.terminal_frame.rhi_scan(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat,
            #                              slipdetect)

            thread = threading.Thread(
                target=self.terminal_frame.rhi_scan,
                args= (start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat,
                                         slipdetect),
                daemon=True
            )
            thread.start()

        elif scan_type == "RHI SQUARE":
            #self.terminal_frame.rhi_square_scan(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat, slipdetect)

            thread = threading.Thread(
                target=self.terminal_frame.rhi_square_scan,
                args=(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat,
                      slipdetect),
                daemon=True
            )
            thread.start()
        elif scan_type == "PPI":
            # self.terminal_frame.ppi_scan(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat,
            #                              slipdetect)
            thread = threading.Thread(
                target=self.terminal_frame.ppi_scan,
                args=(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat,
                      slipdetect),
                daemon=True
            )
            thread.start()
        elif scan_type == "SECTOR":
            # self.terminal_frame.sector_scan(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat,
            #                                 slipdetect)
            thread = threading.Thread(
                target=self.terminal_frame.sector_scan,
                args=(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat,
                      slipdetect),
                daemon=True
            )
            thread.start()
        elif scan_type == "SPOT":
            # self.terminal_frame.spot_scan(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat,
            #                               slipdetect)
            thread = threading.Thread(
                target=self.terminal_frame.spot_scan,
                args=(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat,
                      slipdetect),
                daemon=True
            )
            thread.start()

        elif scan_type == "SET HOME":
            self.terminal_frame.set_home()
        else:
            print("Unknown scan type")



class InputFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background="gray7")
        self.rowconfigure(0, weight=4)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(list(range(2)), weight=1)
        self.tf_list = ["True", "False"]
        self.tf_selected = None

        self.terminal_frame = TerminalFrame(self)
        self.terminal_frame.grid(column=0, row = 0, sticky = "NSEW")
        self.output_frame = OutputFrame(self, self.terminal_frame)
        self.output_frame.grid(column=1, row = 0, sticky = "NSEW")
        self.scan_frame = ScanFrame(self, self.terminal_frame)
        self.scan_frame.grid(column=0, columnspan= 2, row = 1, rowspan=2, sticky = "NSEW")



class ControlFrame(tk.Frame):
    def __init__(self, parent, io_frame):
        super().__init__(parent, background = "red")
        self.io_frame = io_frame
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.radars_available_frame = RadarsAvailableFrame(self, io_frame)
        self.radars_available_frame.grid(column=0, row = 0, sticky = "NSEW")

        self.button_frame = ButtonFrame(self, self.radars_available_frame, self.io_frame)
        self.button_frame.grid(column=0, row = 1, sticky = "NSEW")


class RadarsAvailableFrame(tk.Frame):
    radar_dict = {"Select A Radar": "--------"}
    def __init__(self, parent, io_frame):
        super().__init__(parent, background = "steel blue")
        self.network_check_button = None
        self.radar_selected = None
        self.radars_available = None
        self.io_frame = io_frame
        self.columnconfigure(0, weight=1)
        self.rowconfigure(list(range(2)), weight=1)


        self.network_check_button = tk.Button(self, text="Network Check" , command= lambda: RadarsAvailableFrame.start_network_scan(self))
        self.network_check_button.grid(column=0, row=1, sticky="SEW")
        self.network_check_button.config(width=10, font=("Arial", 20))

    def radar_drop(self):
        self.radars_available = list(self.radar_dict.keys())
        self.radar_selected = tk.StringVar()
        self.radar_selected.set(self.radars_available[0])
        combo_drop = ttk.Combobox(self, textvariable=self.radar_selected, values = self.radars_available, state="readonly")
        combo_drop.grid(column=0, row=0, sticky="NEW")
        combo_drop.config(width=10)
        combo_drop.config(font = ("Arial", 20))
        return self.radar_selected


    def find_other_radars(self):
        nm = nmap.PortScanner()
        host_ip = os.environ.get("HOST_IP")
        nm.scan(hosts=f"{os.environ.get('HOST_IP')}", arguments="-sn")
        logging.info(f"running on {host_ip}")
        for host in nm.all_hosts():
            try:
                logging.info(f"Scanning {host}")
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.load_system_host_keys()
                self.io_frame.input_frame.output_frame.terminal_frame.pos_text_box.delete("1.0", tk.END)
                self.io_frame.input_frame.output_frame.terminal_frame.pos_text_box.insert(tk.END, host)
                client.connect(hostname=f"{host}", username=f"{os.environ.get('CONNECTION_USERNAME')}", password=f"{os.environ.get('CONNECTION_PASSWORD')}", look_for_keys=False, allow_agent=False, timeout=3, auth_timeout=5)
                stdin, stdout, stderr = client.exec_command("hostname")
                radar_hostname = stdout.read().decode("utf-8")
                client.close()
                self.update_radar_pulldown(host, radar_hostname.strip())
            except:
                print(f"No connection to {host}")
        logging.info("RUNNING find_other_radars")
        self.io_frame.input_frame.output_frame.terminal_frame.pos_text_box.delete("1.0", tk.END)
        self.io_frame.input_frame.output_frame.terminal_frame.pos_text_box.insert(tk.END, "Finished Scanning")

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
                self.io_frame.input_frame.output_frame.terminal_frame.pos_text_box.delete("1.0", tk.END)
                self.io_frame.input_frame.output_frame.terminal_frame.pos_text_box.insert(tk.END, f"Found: {ip_address}")
        except:
            print("ERROR")
        self.radar_drop()



class ButtonFrame(tk.Frame):
    def __init__(self, parent, radar_available_frame, io_frame):
        super().__init__(parent, background="firebrick3", borderwidth=5, highlightbackground="black")
        self.radar_available_frame = radar_available_frame
        self.io_frame = io_frame
        self.columnconfigure(0, weight=1)
        self.rowconfigure(list(range(4)), weight=1)
        self.button_end = None
        self.button_reset = None
        self.network_check_button = None
        self.create_buttons()

    def update_status(self, message):
        self.io_frame.input_frame.output_frame.terminal_frame.pos_text_box.config(font=("Arial", 16),
                                                                                  foreground="white")
        self.io_frame.input_frame.output_frame.terminal_frame.pos_text_box.config(state="normal")
        self.io_frame.input_frame.output_frame.terminal_frame.pos_text_box.delete("1.0", tk.END)
        self.io_frame.input_frame.output_frame.terminal_frame.pos_text_box.insert(tk.END, message)

    def stop_scan_all(self):
        # self.io_frame.input_frame.output_frame.terminal_frame.pos_text_box.delete("1.0", tk.END)
        # self.io_frame.input_frame.output_frame.terminal_frame.pos_text_box.config(font=("Arial", 16), foreground="white")
        # self.io_frame.input_frame.output_frame.terminal_frame.pos_text_box.insert(tk.END, f"Stopping Scan.\nPlease standby as the positioner \ncompletes the rotation.")

        #self.io_frame.input_frame.output_frame.terminal_frame.pos_text_box.after(0, self.update_status, f"Stopping Scan.\nPlease standby as the positioner \ncompletes the rotation." )

        thread = threading.Thread(
            target = self.io_frame.input_frame.output_frame.terminal_frame.stop_scan,
            daemon = True
        )
        thread.start()


    def start_homing_mode_and_reset(self):
        logging.info(f"STARTING HOMING MODE AND RESET")
        self.io_frame.input_frame.output_frame.terminal_frame.reset_positioner()
        self.io_frame.input_frame.scan_frame.homing_mode_interface()

    def connect_positioner_initial_state(self):
        #Todo kill this behavior for now and go right into normal mode
        logging.info(f"running connect_positioner_initial_state")
        initial_state = self.io_frame.input_frame.output_frame.terminal_frame.set_positioner(self.radar_available_frame.radar_dict.get(self.radar_available_frame.radar_selected.get()))
        logging.info(f"CONNECT POSITIONER INITIAL STATE: {initial_state}, false should activate homing mode interface")
        #self.io_frame.input_frame.scan_frame.homing_mode_interface()
        # if not initial_state:
        #     logging.info("INITIAL STATE WAS FALSEY")
        #     self.io_frame.input_frame.scan_frame.homing_mode_interface()
        # else:
        #     logging.info("INITIAL STATE: NORMAL MODE")



    def create_buttons(self):
        #self.connect_positioner_button = tk.Button(self, text="Connect Positioner", command=lambda: self.io_frame.input_frame.output_frame.terminal_frame.set_positioner(self.radar_available_frame.radar_dict.get(self.radar_available_frame.radar_selected.get())))
        self.connect_positioner_button = tk.Button(self, text="Connect Positioner", command = lambda: self.connect_positioner_initial_state())
        self.connect_positioner_button.grid(column=0,  row=0)
        self.connect_positioner_button.config(width=15, font=("Arial", 20))

        # self.button_reset = tk.Button(self, text="Home", command = lambda: RadarsAvailableFrame.run_reset_radar(self.radar_available_frame,
        #                               command = "-r; sudo rmmod xdma; sudo modprobe xdma",
        #                               hostname = self.radar_available_frame.radar_dict.get(self.radar_available_frame.radar_selected.get())))
        # self.button_reset.grid(column=0, row=2)
        # self.button_reset.config(width=10, font=("Arial", 20))

        #self.stop_scan_button = tk.Button(self, text="Stop Scan", command=lambda: self.io_frame.input_frame.output_frame.terminal_frame.stop_scan())
        self.stop_scan_button = tk.Button(self, text="Stop Scan", command= lambda: self.stop_scan_all())
        self.stop_scan_button.grid(column=0, row=3)
        self.stop_scan_button.config(width=15, font=("Arial", 20))


        #self.get_status = tk.Button(self, text = "Positioner Status", command = lambda: self.io_frame.input_frame.output_frame.terminal_frame.get_positioner_status())
        self.get_status = tk.Button(self, text="Positioner Status",
                                    command=lambda: self.io_frame.input_frame.output_frame.terminal_frame.get_positioner_status())
        self.get_status.grid(column=0, row=1)
        self.get_status.config(width=15, font=("Arial", 20))

        self.get_position = tk.Button(self, text="Current Position", command=lambda: self.io_frame.input_frame.output_frame.terminal_frame.get_current_position())
        self.get_position.grid(column=0, row=2)
        self.get_position.config(width=15, font=("Arial", 20))

        #self.reset_positioner = tk.Button(self, text="Reset Positioner",command=lambda: self.io_frame.input_frame.output_frame.terminal_frame.reset_positioner())
        #CHANGE RESET BUTTON TO ALSO CHANGE BUTTON LAYOUT
        self.reset_positioner = tk.Button(self, text="Reset Positioner",
                                          command=lambda: self.start_homing_mode_and_reset())
        self.reset_positioner.grid(column=0, row=4)
        self.reset_positioner.config(width=15, font=("Arial", 20))


        self.submit_button = SubmitButton(self, self.radar_available_frame, self.io_frame)
        #self.submit_button.grid(column=0, row=0)
        self.submit_button.config(width=10, font=("Arial", 20))


        # self.network_check_button = tk.Button(self, text="Network Check" , command= lambda: RadarsAvailableFrame.find_other_radars(self.radar_available_frame))
        # self.network_check_button.grid(column=0, row=3)
        # self.network_check_button.config(width=10, font=("Arial", 20))


class Button(tk.Button):
    def __init__(self, parent):
        super().__init__(parent)


class SubmitButton(tk.Button):
    def __init__(self, parent, radar_available_frame, io_frame):
        super().__init__(parent)
        self.radar_available_frame = radar_available_frame
        self.io_frame = io_frame


