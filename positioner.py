import tkinter as tk
from tkinter import ttk, messagebox
import paramiko
import nmap
import os
import time
import queue
import threading

from datetime import datetime

from tkterminal import Terminal

client = paramiko.client.SSHClient()
output_queue = queue.Queue()
selected_positioner_global = None
home_set = False


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
        self.positioner_selected = False
        self.current_position = None
        self.home_position = None
        self.scan_type_var = tk.StringVar()
        self.scan_type_var.set("Scan Type: ")
        self.positioner_selected_var = tk.StringVar()
        self.positioner_selected_var.set("Positioner: ")
        self.positioner_selected_for_use = None

        self.status_text_box = tk.Text(self, font=("Arial", 16), bg="gray7", fg="white")
        self.status_text_box.grid(column=0, row=0, sticky="NSEW")
        self.status_text_box.config(height=30, width = 60)

        self.pos_text_box = tk.Text(self, font=("Arial", 20), bg="gray7", fg="white")
        self.pos_text_box.grid(column=1, row=0, sticky="NSEW")


    def set_positioner(self, positioner):
        self.positioner_selected = positioner
        self.positioner_selected_var.set(f"Positioner: {positioner}")
        self.positioner_selected_for_use = positioner
        print(self.positioner_selected_for_use)
        global selected_positioner_global
        selected_positioner_global = self.positioner_selected
        self.get_positioner_status()
        return self.positioner_selected

    def fl_network_mode(self):
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=f"{self.positioner_selected}", username=f"{os.environ.get('CONNECTION_USERNAME')}",
                       password=f"{os.environ.get('CONNECTION_PASSWORD')}", look_for_keys=False, allow_agent=False)
        print(f"{self.positioner_selected_for_use} inside status")
        print(f"{selected_positioner_global} GLOBAL status")
        transport = client.get_transport()
        channel = transport.open_session()
        channel.get_pty()
        channel = client.invoke_shell()
        time.sleep(1)
        return channel

    def alex_home_network_mode(self):
        key_path = "/Users/alexanderbertotto/.ssh/id_ed25519"
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname="data.stormquant.com", username="alex", key_filename=key_path, look_for_keys=False,
                       allow_agent=False)
        time.sleep(1)
        transport = client.get_transport()
        channel = transport.open_session()
        channel.get_pty()
        channel = client.invoke_shell()
        time.sleep(.5)
        channel.send("sudo su - radaraccess\n")
        time.sleep(1)
        #USE -t or not?
        #channel.send("ssh -t Radar2-tunnel\n")
        channel.send("ssh Radar5-tunnel\n")
        output = channel.recv(4096).decode("iso-8859-1")
        # print(output)
        time.sleep(1)
        return channel

    def get_positioner_status(self):
        #channel = self.fl_network_mode()
        self.status_text_box.delete("1.0", tk.END)
        channel = self.alex_home_network_mode()
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
        run_status_variable = ""
        #output = channel.recv(4096).decode("iso-8859-1")
        #(\n\n)
        try:
            output = channel.recv(8192).decode("iso-8859-1")
            time.sleep(1)
            print(output)
            output_status = output.split("sq@sq-radar-5:~$ scan status", 1)
            output_lines = output_status[1].split("\r")
            for index, line in enumerate(output_lines):
                print(f"{index}: {line}")
                if "Run:" in line:
                    run_status_variable = line.split("Run:")[1]
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
            print(output)
            output_status = output.split("scan status", 1)
            output_lines = output_status[1].split("\r")
            for index, line in enumerate(output_lines):
                print(f"{index}: {line}")
                if "Run:" in line:
                    run_status_variable = line.split("Run:")[1]
                self.status_text_box.insert(tk.END, line)
                if "Attenuations:" in line:
                    # self.status_text_box.insert(tk.END, "\r")
                    break

        channel.close()
        client.close()
        run_status_variable = int(run_status_variable.strip())
        # print(f" RUN STATUS: {run_status_variable}")
        # print((run_status_variable == 1))
        print(f"RUN STATUS: {run_status_variable}")
        return run_status_variable




    def spot_scan(self, start_az, end_az, start_elbeam, end_elbeam, speed, inc, repeat, slipdetect):
        #channel = self.fl_network_mode()
        channel = self.alex_home_network_mode()
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
        #channel = self.fl_network_mode()
        channel = self.alex_home_network_mode()
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
        #channel = self.fl_network_mode()
        channel = self.alex_home_network_mode()
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
        #channel = self.fl_network_mode()
        channel = self.alex_home_network_mode()
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
        time.sleep(0.5)
        self.get_positioner_status()
        channel.close()
        client.close()

    def sector_scan(self, start_az, end_az, start_ele, end_ele, speed, inc, repeat, slipdetect):
        #channel = self.fl_network_mode()
        channel = self.alex_home_network_mode()
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
        #channel = self.fl_network_mode()
        channel = self.alex_home_network_mode()
        time.sleep(1)
        ttyf="/dev/ttyUSB1"
        channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
        channel.send(f"echo scan stop > {ttyf}\n")
        time.sleep(1)
        run_status_variable = self.get_positioner_status()

        for i in range(300):
            if run_status_variable != 1:
                print("SCAN STOPPED")
                break
            time.sleep(1)
            self.stop_scan()

        channel.close()
        client.close()

    #NEED TO CHECK
    def get_current_position(self):
        self.pos_text_box.delete("1.0", tk.END)
        #channel = self.fl_network_mode()
        channel = self.alex_home_network_mode()
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
        print(output)
        try:
            output_status = output.split("sq@sq-radar-5:~$ pos", 1)
            output_lines = output_status[1].split("\r")
            current_datetime = datetime.now()
            self.pos_text_box.insert(tk.END, f"Time of Position Check:\n")
            self.pos_text_box.insert(tk.END, current_datetime)
            for line in output_lines:
                print(line)
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
                print(line)
                self.pos_text_box.insert(tk.END, line)
                if "AZ/EL From Encoders:" in line:
                    # self.status_text_box.insert(tk.END, "\r")
                    break

        channel.close()
        client.close()


    def re_home(self):
        #channel = self.fl_network_mode()
        channel =self.alex_home_network_mode()
        ttyf = "/dev/ttyUSB1"
        channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
        channel.send(f"echo rehome  > {ttyf}\n")
        time.sleep(0.5)
        self.get_positioner_status()
        channel.close()
        client.close()


    def go_home(self):
        #channel = self.fl_network_mode()
        channel =self.alex_home_network_mode()
        ttyf = "/dev/ttyUSB1"
        channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
        channel.send(f"echo gohome  > {ttyf}\n")
        time.sleep(0.5)
        self.get_positioner_status()
        channel.close()
        client.close()

    def set_home(self, key_stroke):
        # self.scan_type_var.set(f"SET HOME")
        print(key_stroke)
        #channel = self.fl_network_mode()
        channel = self.alex_home_network_mode()
        ttyf="/dev/ttyUSB1"
        channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo")
        time.sleep(0.1)
        channel.send(f"echo {key_stroke} > {ttyf}\n")
        time.sleep(0.5)

        self.get_positioner_status()
        channel.close()
        client.close()

    def reset_positioner(self):
        print(self.positioner_selected)
        answer = messagebox.askyesno("Reset Positioner", "Do you want to reset positioner?")
        if answer:
            print("reset positioner")
            #channel = self.fl_network_mode()
            channel = self.alex_home_network_mode()
            ttyf = "/dev/ttyUSB1"
            channel.send(f"stty -F {ttyf} 115200 raw -hupcl -onlcr -echo\n")
            time.sleep(0.5)
            channel.send(f"echo reset > {ttyf}\n")
            time.sleep(0.5)
            self.get_positioner_status()
            channel.close()
            client.close()
        else:
            print("dont reset positioner")

    def start_threading(self):
        thread = threading.Thread(target=self.get_positioner_status())
        thread.start()

class OutputFrame(tk.Frame):
    def __init__(self, parent, terminal_frame):
        super().__init__(parent,background="gray7")
        self.rowconfigure(list(range(6)), weight=1)
        self.columnconfigure(0, weight=1)
        self.grid_propagate(False)
        self.terminal_frame = terminal_frame

        #self.pos_text_box = tk.Text(self, height=1, width=20, background="gray7")
        self.pos_text_box = tk.Text(self, font=("Arial", 20), bg="gray7", fg="white")
        self.pos_text_box.grid(column=0, row=0, sticky="NSEW")
        self.pos_text_box.config(height=30, width = 70)


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


    def set_home_finished(self):

        self.fine_w_key.destroy()
        self.fine_a_key.destroy()
        self.fine_s_key.destroy()
        self.fine_d_key.destroy()
        self.coarse_w_key.destroy()
        self.coarse_a_key.destroy()
        self.coarse_s_key.destroy()
        self.coarse_d_key.destroy()
        self.set_home_button.destroy()
        self.create_layout()
        self.terminal_frame.set_home("/")

    def homing_mode_interface(self):
        #Clear or reset default values
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

        self.fine_w_key = tk.Button(self, text="Fine W", command=lambda: self.terminal_frame.set_home("w"))
        self.fine_w_key.grid(column=1, row=0, sticky="NSEW")
        self.fine_w_key.config(font=("Arial", 20))
        self.fine_w_key.config(width=10)

        self.fine_s_key = tk.Button(self, text="Fine S", command=lambda: self.terminal_frame.set_home("s"))
        self.fine_s_key.grid(column=1, row=2, sticky="NSEW")
        self.fine_s_key.config(font=("Arial", 20))
        self.fine_s_key.config(width=10)

        self.fine_a_key = tk.Button(self, text="Fine A", command=lambda: self.terminal_frame.set_home("a"))
        self.fine_a_key.grid(column=0, row=1, sticky="NSEW")
        self.fine_a_key.config(font=("Arial", 20))
        self.fine_a_key.config(width=10)

        self.fine_d_key = tk.Button(self, text="Fine D", command=lambda: self.terminal_frame.set_home("d"))
        self.fine_d_key.grid(column=2, row=1, sticky="NSEW")
        self.fine_d_key.config(font=("Arial", 20))
        self.fine_d_key.config(width=10)

        self.set_home_button = tk.Button(self, text="Save Home Position", command=lambda: self.set_home_finished())
        self.set_home_button.grid(column=2, row=3, sticky="NSEW")
        self.set_home_button.config(font=("Arial", 20))


        # self.space_bar_button = tk.Button(self, text="Space Bar", command=lambda: self.terminal_frame.set_home("space_bar"))
        # self.set_home_button.grid(column=4, row=3, sticky="NSEW")
        # self.set_home_button.config(font=("Arial", 20))
        self.space_bar_button = tk.Button(self, text="Last Saved Position", command=lambda: self.terminal_frame.set_home(" "))
        self.space_bar_button.grid(column=3, row=3, sticky="NSEW")
        self.space_bar_button.config(font=("Arial", 20))

        self.coarse_w_key = tk.Button(self, text="Coarse W", command=lambda: self.terminal_frame.set_home("W"))
        self.coarse_w_key.grid(column=4, row=0, sticky="NSEW")
        self.coarse_w_key.config(font=("Arial", 20))
        self.coarse_w_key.config(width=10)

        self.coarse_s_key = tk.Button(self, text="Coarse S", command=lambda: self.terminal_frame.set_home("S"))
        self.coarse_s_key.grid(column=4, row=2, sticky="NSEW")
        self.coarse_s_key.config(font=("Arial", 20))
        self.coarse_s_key.config(width=10)

        self.coarse_a_key = tk.Button(self, text="Coarse A", command=lambda: self.terminal_frame.set_home("A"))
        self.coarse_a_key.grid(column=3, row=1, sticky="NSEW")
        self.coarse_a_key.config(font=("Arial", 20))
        self.coarse_a_key.config(width=10)

        self.coarse_d_key = tk.Button(self, text="Coarse D", command=lambda: self.terminal_frame.set_home("D"))
        self.coarse_d_key.grid(column=5, row=1, sticky="NSEW")
        self.coarse_d_key.config(font=("Arial", 20))
        self.coarse_d_key.config(width=10)


    def on_click_clear(self, event):
        event.widget.delete(0, "end")

    def input_checker(self, start_azimuth_var, end_azimuth_var, start_elbeam_var, end_elbeam_var, speed_var, increment_var, repeat_var, slipdetect_var):
        try:
            start_az = float(start_azimuth_var.get())
            end_az = float(end_azimuth_var.get())
            start_elbeam = float(start_elbeam_var.get())
            end_elbeam = float(end_elbeam_var.get())
            speed = float(speed_var.get())
            increment = float(increment_var.get())
            repeat = int(repeat_var.get())
            slipdetect = int(slipdetect_var.get())
        except:
            return messagebox.showerror("Error", "Entry Error")

        if start_az < 0 or start_az >= end_az or start_az > 360:
            self.start_azimuth_entry.delete(0, "end")
            return messagebox.showerror("Error", "Starting Azimuth entry incorrect")
        if end_az < 0 or end_az > 360:
            self.end_azimuth_entry.delete(0, "end")
            return messagebox.showerror("Error", "Ending Azimuth entry incorrect")
        if start_elbeam < -7 or start_elbeam > 45 or start_elbeam >= end_elbeam:
            self.start_elbeam_entry.delete(0, "end")
            return messagebox.showerror("Error", "Starting Elbeam entry incorrect")
        if end_elbeam < -5 or end_elbeam > 45:
            self.end_elbeam_entry.delete(0, "end")
            return messagebox.showerror("Error", "Ending Elbeam entry incorrect")
        if speed < 2 or speed > 300:
            self.speed_entry.delete(0, "end")
            self.speed_entry.insert("0", "20.0")
            return messagebox.showerror("Error", "Speed entry incorrect")
        if increment < 1.5 or increment > 5:
            self.increment_entry.delete(0, "end")
            self.increment_entry.insert("0", "1.5")
            return messagebox.showerror("Error", "Increment entry incorrect")
        if repeat not in [0, 1]:
            self.repeat_entry.delete(0, "end")
            self.repeat_entry.insert("0", "1")
            return messagebox.showerror("Error", "Repeat entry incorrect")
        if slipdetect not in [0, 1]:
            self.slipdetect_entry.delete(0, "end")
            self.slipdetect_entry.insert("0", "1")
            return messagebox.showerror("Error", "Slip detect entry incorrect")
        return start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat, slipdetect

    def start_threading(self, scan_type):
        #DO I NEED THREADING?
        if not self.input_checker:
            return print("failed")
        else:
            try:
                start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat, slipdetect = self.input_checker(self.start_azimuth_var, self.end_azimuth_var, self.start_elbeam_var, self.end_elbeam_var, self.speed_var, self.increment_var, self.repeat_var, self.slipdetect_var)
                print(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat, slipdetect)
            except:
                return print("failed")

        match scan_type:
            case "RHI":
                self.terminal_frame.rhi_scan(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat, slipdetect)
                return None
            case "RHI SQUARE":
                self.terminal_frame.rhi_square_scan(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat, slipdetect)
                return None
            case "PPI":
                self.terminal_frame.ppi_scan(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat, slipdetect)
                return None
            case "SECTOR":
                self.terminal_frame.sector_scan(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat, slipdetect)
                return None
            case "SPOT":
                self.terminal_frame.spot_scan(start_az, end_az, start_elbeam, end_elbeam, speed, increment, repeat, slipdetect)
                return None
            case "SET HOME":
                self.terminal_frame.set_home()
                return None
            case _:
                return print("unknown")




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
        '''
        hide until connected but still running?
        fpga click to hide or side by side to fit graphs
        '''

        #self.spot_scan = tk.Button(self, text = "Spot Scan", command= lambda: self.terminal.run_command("whoami"))
        # self.spot_scan = tk.Button(self, text="Spot Scan", command=lambda: self.terminal_frame.start_threading("ping 8.8.8.8"))
        # self.spot_scan.grid(column=0, row = 1, sticky = "NSEW")
        # azimuth_entry = ttk.Entry(self, width=10, font = ("Arial", 20), textvariable="pass")
        # elevation_entry = ttk.Entry(self, width=10, font = ("Arial", 20), textvariable="amaass")
        # azimuth_entry.grid(column=1, row = 1, sticky = "NSEW")
        # elevation_entry.grid(column=2, row = 1, sticky = "NSEW")
        #
        # self.rhi_scan = tk.Button(self, text = "RHI Scan", command= lambda: "pass")
        # self.rhi_scan.grid(column=3, row = 1, sticky = "NSEW")
        #
        # self.rehome = tk.Button(self, text = "Re-Home", command= lambda: "pass")
        # self.rehome.grid(column=4, row = 1, sticky = "NSEW")
        # self.control_mode = tk.Button(self, text = "Control Mode", command= lambda: self.terminal_frame.terminal.config(state="normal"))
        # self.control_mode.grid(column=5, row = 1, sticky = "NSEW")




class ControlFrame(tk.Frame):
    def __init__(self, parent, io_frame):
        super().__init__(parent, background = "red")
        self.io_frame = io_frame
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.radars_available_frame = RadarsAvailableFrame(self)
        self.radars_available_frame.grid(column=0, row = 0, sticky = "NSEW")

        self.button_frame = ButtonFrame(self, self.radars_available_frame, self.io_frame)
        self.button_frame.grid(column=0, row = 1, sticky = "NSEW")


class RadarsAvailableFrame(tk.Frame):
    radar_dict = {"Select A Radar": "--------", "sq-radar-2": "192.192.192.192"}
    def __init__(self, parent):
        super().__init__(parent, background = "steel blue")
        self.network_check_button = None
        self.radar_selected = None
        self.radars_available = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(list(range(2)), weight=1)


        self.network_check_button = tk.Button(self, text="Network Check" , command= lambda: RadarsAvailableFrame.find_other_radars(self))
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



class ButtonFrame(tk.Frame):
    def __init__(self, parent, radar_available_frame, io_frame):
        super().__init__(parent, background="firebrick3")
        self.radar_available_frame = radar_available_frame
        self.io_frame = io_frame
        self.columnconfigure(0, weight=1)
        self.rowconfigure(list(range(4)), weight=1)
        self.button_end = None
        self.button_reset = None
        self.network_check_button = None
        self.create_buttons()

    # def stop_order(self):
    #     global is_running
    #     is_running = False
    #     self.io_frame.show_input_frame_hide_output_frame()
    #
    # def run_command_connect(self, command, hostname, username=f"{os.environ.get('CONNECTION_USERNAME')}", password=f"{os.environ.get('CONNECTION_PASSWORD')}"):
    #     global is_running
    #     is_running = True
    #     self.io_frame.hide_input_frame_show_output_frame()
    #     self.io_frame.output_frame.display_settings(command)
    #     client.load_system_host_keys()
    #     client.connect(hostname=hostname, username=username, password=password, look_for_keys=False, allow_agent=False)
    #     print("connected")
    #     transport = client.get_transport()
    #     channel = transport.open_session()
    #     channel.get_pty()
    #     channel.invoke_shell()
    #     channel.send(f"cd {os.environ['FPGAPATH']}\n")
    #     time.sleep(1)
    #     channel.send(f"./fpgaStream {command}\n")
    #     time.sleep(2)
    #
    #     max_duration = 2000
    #     start_time = time.time()
    #     output = ""
    #     # while channel.recv_ready() and is_running:
    #     while channel.active and is_running:
    #         chunk = channel.recv(1024).decode("iso-8859-1")
    #         output += chunk
    #
    #     channel.send("^S\n")
    #     channel.send("^C\n")
    #     client.close()



    def create_buttons(self):
        self.button_end = tk.Button(self, text="Connect Positioner", command=lambda: self.io_frame.input_frame.output_frame.terminal_frame.set_positioner(self.radar_available_frame.radar_dict.get(self.radar_available_frame.radar_selected.get())))
        self.button_end.grid(column=0,  row=0)
        self.button_end.config(width=15, font=("Arial", 20))

        # self.button_reset = tk.Button(self, text="Home", command = lambda: RadarsAvailableFrame.run_reset_radar(self.radar_available_frame,
        #                               command = "-r; sudo rmmod xdma; sudo modprobe xdma",
        #                               hostname = self.radar_available_frame.radar_dict.get(self.radar_available_frame.radar_selected.get())))
        # self.button_reset.grid(column=0, row=2)
        # self.button_reset.config(width=10, font=("Arial", 20))
        self.stop_scan_button = tk.Button(self, text="Stop Scan", command= lambda: self.io_frame.input_frame.output_frame.terminal_frame.stop_scan())
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

        self.reset_positioner = tk.Button(self, text="Reset Positioner",command=lambda: self.io_frame.input_frame.output_frame.terminal_frame.reset_positioner())
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
        super().__init__(parent, text="Connectfix", command=lambda: self.run_command())
        self.radar_available_frame = radar_available_frame
        self.io_frame = io_frame

    def run_queue(self):
        #print(f"OPQ: {output_queue.get()}")
        # while output_queue.qsize() > 10 and is_running:
        #     self.after(100, self.io_frame.output_frame.update_all_textboxes(output_queue.get()))
        print(output_queue.qsize())
        try:
            if not output_queue.empty():
                self.after(100, self.io_frame.output_frame.update_all_textboxes(output_queue.get()))
        except:
            print("Error occured")

    def run_command(self, received_commands, received_units):
        cmd_str = ""
        unit_list = []

        for unit in self.received_units:
            unit_list.append(unit)

        for i, value in enumerate(self.received_commands.values()):
            if value.get() == "True":
                cmd_str += f"{unit_list[i]} "
            else:
                cmd_str += f"{unit_list[i]} {value.get()} "

        input_check_return = self.input_check(cmd_str)
        if input_check_return == False:
            self.io_frame.input_frame.create_entries()
            return

        radar_key = self.radar_available_frame.radar_selected.get()
        radar_value = RadarsAvailableFrame.radar_dict.get(radar_key)
        thread = threading.Thread(target=ButtonFrame.run_command_connect, args=(self, cmd_str.strip(), radar_value))
        thread.start()
