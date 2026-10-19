import re
import tkinter as tk
import customtkinter
import state
import time
import os
import paramiko


class Initial_Check(customtkinter.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.columnconfigure(list(range(0,5)), weight=1)
        self.rowconfigure(list(range(0,5)), weight=1)
        self.usb_check_output_var = tk.StringVar()
        self.radar_chosen = None


        self.usb_check_output_textbox = customtkinter.CTkTextbox(self)
        self.usb_check_output_textbox.grid(column=0, columnspan=4, row=0, sticky="nsew")
        self.usb_check_output_textbox.configure(font=("Arial", 14),state="normal")
        self.usb_check_output_textbox.tag_config("cyan", foreground="cyan")
        self.usb_check_output_textbox.tag_config("red", foreground="red")
        self.usb_check_output_textbox.tag_config("yellow", foreground="yellow")
        self.usb_check_output_textbox.tag_config("default", foreground="white")

        self.usb_check_button = customtkinter.CTkButton(self, width=100, text="USB Check", command = lambda: self.run_usb_check())
        self.usb_check_button.grid(column=5, row=0, sticky="ew")
        # self.yellow_example = "lrwxrwxrwx 1 sq sq 61 Sep 23 09:36 \x1b[0m\x1b[01;36mgpsdo\x1b[0m -> \x1b[40;33;01m/dev/serial/by-path/platform-3530000.xhci-usb-0:3.1:1.2-port0\x1b[0m\x1b[K\r\n"
        # self.red_example = "lrwxrwxrwx 1 sq sq 61 Sep 23 09:36 \x1b[40;31;01mmonitor\x1b[0m -> \x1b[40;31;01m/dev/serial/by-path/platform-3530000.xhci-usb-0:3.4.4.2.2:1.0\x1b[0m\x1b[K\r\n"
        # self.ansi_color_checker(self.red_example)

    def run_usb_check(self):
        self.current_radar_key = state.radar_choice.get()
        for key, value in state.radars_found.get_dict().items():
            if key == self.current_radar_key:
                self.current_radar_value = value
        self.usb_check_output_textbox.configure(state="normal")
        self.usb_check_output_textbox.delete("0.0", "end")
        message = f"RUNNING USB CHECK on {self.current_radar_value}"
        try:
            client, channel = self.fl_network_mode()
        except:
            print("CONNECTION ERROR")
            self.usb_check_output_textbox.configure(state="normal")
            self.usb_check_output_textbox.delete("0.0", "end")
            self.usb_check_output_textbox.insert("0.0", "CONNECTION ERROR: Check Radar selection")
            self.usb_check_output_textbox.configure(state="disabled")
            return 1

        #TODO SIMPLIFIED OUTPUT --- IS WORKING
        # command = 'for i in /home/sq/sq/usbmap/*; do echo -n "${i%%*/} "; readlink > /dev/null 2> /dev/null "$i" && echo plugged || echo unplugged; done'
        # stdin, stdout, stderr = client.exec_command(command)
        # message = stdout.read().decode("utf-8")
        # self.usb_check_output_textbox.insert("0.0", f"USB REPORT FOR {state.radar_choice.get()}\n")
        # for line in message.splitlines():
        #     line = line.split("usbmap/")[1] + "\n"
        #     self.usb_check_output_textbox.insert("end", line)

        command = 'ls -l --color=always /home/sq/sq/usbmap\n'
        # stdin, stdout, stderr = client.exec_command(command)
        # message = stdout.read()
        # self.usb_check_output_textbox.insert("0.0",f"USB REPORT FOR {state.radar_choice.get()}\n")
        #
        # for line in message.splitlines():
        #     self.usb_check_output_textbox.insert("end", line)

        channel.send(command)
        output = ""
        while True:
            if channel.recv_ready():
                data = channel.recv(2048).decode()
                output += data
                print(repr(data))
                if ("ttyUSB2") in output:
                    break
            time.sleep(.1)
        if "/home/sq/sq/usbmap" in output:
            output = output.split("/home/sq/sq/usbmap\r")[1]
            for line in output.split("\r"):
                #self.usb_check_output_textbox.insert("end", line)
                print("PUT COLOR CHECKER HEREE")
                #TODO THIS CALLS THE COLOR CHECKER
                self.ansi_color_checker(line)
        self.usb_check_output_textbox.configure(state="disabled")

    def create_ssh_client(self):
        client = paramiko.client.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
        return client

    def fl_network_mode(self):
        self.current_radar_key = state.radar_choice.get()
        for key, value in state.radars_found.get_dict().items():
            if key == self.current_radar_key:
                self.current_radar_value = value
        print(f"INSIDE FLORIDA {self.current_radar_value}")
        try:
            client = self.create_ssh_client()
            client.connect(hostname=f"{self.current_radar_value}", username=f"{os.environ.get('CONNECTION_USERNAME')}",
                           password=f"{os.environ.get('CONNECTION_PASSWORD')}", look_for_keys=False, allow_agent=False, timeout=10)
            # print(f"{self.positioner_selected_for_use} inside status")
            # print(f"{selected_positioner_global} GLOBAL status")
            transport = client.get_transport()
            channel = transport.open_session()
            channel.get_pty()
            channel = client.invoke_shell()
            time.sleep(.1)
            return client, channel
        except:
            print("ERROR CHECKING USB MAP")


    # yellow_example = ['\nlrwxrwxrwx 1 sq sq 61 Sep 23 09:36 ', '\x1b[01;36m', 'posctl', '\x1b[0m', ' -> ', '\x1b[40;33;01m', '/dev/serial/by-path/platform-3530000.xhci-usb-0:3.1:1.1-port0', '\x1b[0m', '\x1b[K']
    # red_example = ['\nlrwxrwxrwx 1 sq sq 61 Sep 23 09:36 ', '\x1b[40;31;01m', 'monitor-stlink', '\x1b[0m', ' -> ', '\x1b[40;31;01m', '/dev/serial/by-path/platform-3530000.xhci-usb-0:3.4.4.2.3:1.2', '\x1b[0m', '\x1b[K']
    def ansi_color_checker(self, text):
        ansi_regex = r'(\x1b\[[0-9;]*m)'
        if re.search(ansi_regex, text):
            pieces = re.split(ansi_regex, text)
            self.usb_check_output_textbox.insert("end", pieces[0], "default")
            for index, piece in enumerate(pieces):
                print(f"PIECE AND INDEX IN QUESTION: index: {index}, piece: {piece}")
                if "\x1b[K" in piece:
                    self.usb_check_output_textbox.insert("end", " ", "default")
                    break
                elif "" == piece:
                    continue
                elif "\x1b[01;36m" in piece:
                    self.usb_check_output_textbox.insert("end", pieces[index + 1], "cyan")
                elif "\x1b[0m" in piece:
                    if "\x1b[K" in pieces[index + 1]:
                        self.usb_check_output_textbox.insert("end", "", "default")
                        break
                    else:
                        self.usb_check_output_textbox.insert("end", pieces[index + 1], "default")
                elif "\x1b[40;33;01m" in piece:
                    self.usb_check_output_textbox.insert("end", pieces[index + 1], "yellow")
                elif "\x1b[40;31;01m" in piece:
                    self.usb_check_output_textbox.insert("end", pieces[index + 1], "red")
                else:
                    continue
            # else:
            #     self.usb_check_output_textbox.insert("end", text, "default")



        #TODO THIS DOES WORK BUT HIGHLIGHTS THE WHOLE LINE
        # if "[40;31;01" in text:
        #     self.usb_check_output_textbox.insert("end", text, "red")
        # elif "[40;33;01" in text:
        #     self.usb_check_output_textbox.insert("end", text, "yellow")
        # else:
        #     self.usb_check_output_textbox.insert("end", text, "default")

