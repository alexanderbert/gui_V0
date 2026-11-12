import tkinter
import time
import ssh_helper

import customtkinter

class DDS_Frame(customtkinter.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)


        '''python3.6 pulseSandbox.py -a 58.0 -b 3.0e6 -c 4.25e6 -d 0 -D 0.025 -f 25.0 -n 1/2 -g 4.15e5 -G 15 -i 14 -k 2.0 -l 8.5e6 -r 25.0e6 -s 0 -t 8192
        SGTTY=/home/sq/sq/usbmap/siggen
        stty -F $SGTTY 115200 raw
        cd /home/sq/sq/stormquant-beta/engineering/python_toolkit/
        echo -ne ':A01='"$(cat pulse_compression_fullwave.csv)"'.\r\n' > $SGTTY; head -n 1 $SGTTY'''
        #-a -b -c -k -l (lowercase L) -x -X -K
        #basically if ‘disable chirp’ add ‘-x and -K’
        self.voltage_label = None
        self.voltage_entry = None
        self.voltage_var = tkinter.DoubleVar()
        self.dash_a_label = None
        self.dash_a_entry = None
        self.dash_a_var = tkinter.DoubleVar()
        self.dash_b_label = None
        self.dash_b_entry = None
        self.dash_b_var = tkinter.DoubleVar()
        self.dash_c_label = None
        self.dash_c_entry = None
        self.dash_c_var = tkinter.DoubleVar()
        self.dash_k_label = None
        self.dash_k_entry = None
        self.dash_k_var = tkinter.DoubleVar()
        self.dash_l_label = None
        self.dash_l_entry = None
        self.dash_l_var = tkinter.DoubleVar()
        self.dash_x_label = None
        self.dash_x_entry = None
        self.dash_x_var = tkinter.BooleanVar()
        self.dash_capital_X_label = None
        self.dash_capital_X_entry = None
        self.dash_capital_X_var = tkinter.BooleanVar()
        self.dash_capital_K_label = None
        self.dash_capital_K_entry = None
        self.dash_capital_K_var = tkinter.BooleanVar()


        self.columnconfigure(0, weight=10)
        self.columnconfigure(1, weight=10)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.output_frame = customtkinter.CTkFrame(self)
        self.output_frame.grid(column=0, row=0, rowspan=2, sticky="nsew")
        self.output_frame.grid_columnconfigure(list(range(0, 3)), weight=2)
        self.output_frame.rowconfigure(list(range(0, 19)), weight=1)

        self.dash_voltage_label = customtkinter.CTkLabel(self.output_frame, text="Voltage (mV):")
        self.dash_voltage_label.grid(column=0, row=0, sticky="e", padx=20)
        self.dash_voltage_label.configure(font=("Arial", 14))
        self.dash_voltage_entry = customtkinter.CTkEntry(self.output_frame, width=100, font=("Arial", 14), justify="center",
                                     textvariable=self.voltage_var)
        self.dash_voltage_entry.grid(column=1, row=0, sticky="w")
        self.voltage_var.set(2000)

        self.dash_a_label = customtkinter.CTkLabel(self.output_frame, text="a | Chirp Length(uSec):")
        self.dash_a_label.grid(column=0, row=3, sticky="e", padx=20)
        self.dash_a_label.configure(font=("Arial", 14))
        self.dash_a_entry = customtkinter.CTkEntry(self.output_frame, width=100, font=("Arial", 14), justify="center",
                                     textvariable=self.dash_a_var)
        self.dash_a_entry.grid(column=1, row=3, sticky="w")
        self.dash_a_var.set(58.0)

        self.dash_b_label = customtkinter.CTkLabel(self.output_frame, text="b | Chirp Bandwidth (freq):")
        self.dash_b_label.grid(column=0, row=4, sticky="e", padx=20)
        self.dash_b_label.configure(font=("Arial", 14))
        self.dash_b_entry = customtkinter.CTkEntry(self.output_frame, width=100, font=("Arial", 14), justify="center",
                                     textvariable=self.dash_b_var)
        self.dash_b_entry.grid(column=1, row=4, sticky="w")
        self.dash_b_var.set(3.0E6)

        self.dash_c_label = customtkinter.CTkLabel(self.output_frame, text="c | Chirp Center freq:")
        self.dash_c_label.grid(column=0, row=5, sticky="e", padx=20)
        self.dash_c_label.configure(font=("Arial", 14))
        self.dash_c_entry = customtkinter.CTkEntry(self.output_frame, width=100, font=("Arial", 14), justify="center",
                                     textvariable=self.dash_c_var)
        self.dash_c_entry.grid(column=1, row=5, sticky="w")
        self.dash_c_var.set(4.25e6)

        self.dash_k_label = customtkinter.CTkLabel(self.output_frame, text="k | Fill Pulse Length (uSec):")
        self.dash_k_label.grid(column=0, row=6, sticky="e", padx=20)
        self.dash_k_label.configure(font=("Arial", 14))
        self.dash_k_entry = customtkinter.CTkEntry(self.output_frame, width=100, font=("Arial", 14), justify="center",
                                     textvariable=self.dash_k_var)
        self.dash_k_entry.grid(column=1, row=6, sticky="w")
        self.dash_k_var.set(2.0)

        self.dash_l_label = customtkinter.CTkLabel(self.output_frame, text="l | Fill Pulse Center:")
        self.dash_l_label.grid(column=0, row=7, sticky="e", padx=20)
        self.dash_l_label.configure(font=("Arial", 14))
        self.dash_l_entry = customtkinter.CTkEntry(self.output_frame, width=100, font=("Arial", 14), justify="center",
                                     textvariable=self.dash_l_var)
        self.dash_l_entry.grid(column=1, row=7, sticky="w")
        self.dash_l_var.set(8.5e6)

        self.dash_x_label = customtkinter.CTkLabel(self.output_frame, text="x | Turn chirp off:")
        self.dash_x_label.grid(column=0, row=8, sticky="e", padx=20)
        self.dash_x_label.configure(font=("Arial", 14))
        self.dash_x_entry = customtkinter.CTkSwitch(self.output_frame, width=100, font=("Arial", 14),text="",
                                     command=self.dash_x_switch_event,variable=self.dash_x_var, onvalue=True, offvalue=False)
        self.dash_x_entry.grid(column=1, row=8, sticky="w")
        self.dash_x_var.set(False)

        self.dash_capital_X_label = customtkinter.CTkLabel(self.output_frame, text="X | Turn fill pulse off:")
        self.dash_capital_X_label.grid(column=0, row=9, sticky="e", padx=20)
        self.dash_capital_X_label.configure(font=("Arial", 14))
        self.dash_capital_X_entry = customtkinter.CTkSwitch(self.output_frame, width=100, font=("Arial", 14),text="",
                                     command=self.dash_capital_X_switch_event,variable=self.dash_capital_X_var, onvalue=True, offvalue=False)
        self.dash_capital_X_entry.grid(column=1, row=9, sticky="w")
        self.dash_capital_X_var.set(False)

        self.dash_capital_K_label = customtkinter.CTkLabel(self.output_frame, text="K | Disable Chirp:")
        self.dash_capital_K_label.grid(column=0, row=10, sticky="e", padx=20)
        self.dash_capital_K_label.configure(font=("Arial", 14))
        self.dash_capital_K_entry = customtkinter.CTkSwitch(self.output_frame, width=100, font=("Arial", 14),text="",
                                     command=self.dash_capital_K_switch_event,variable=self.dash_capital_K_var, onvalue=True, offvalue=False)
        self.dash_capital_K_entry.grid(column=1, row=10, sticky="w")
        self.dash_capital_K_var.set(False)

    def dash_x_switch_event(self):
        print(f"DASH x EVENT: {self.dash_x_var.get()}")

    def dash_capital_X_switch_event(self):
        print(f"DASH CAPITAL X EVENT: {self.dash_capital_X_var.get()}")

    def dash_capital_K_switch_event(self):
        print(f"DASH CAPITAL K EVENT: {self.dash_capital_K_var.get()}")
        if self.dash_capital_K_var.get():
            self.dash_x_var.set(True)
            self.dash_capital_X_var.set(True)
        else:
            self.dash_x_var.set(False)
            self.dash_capital_X_var.set(False)

    def pulse_gen_60_new_parts(self):
        client = None
        client, channel = ssh_helper.fl_network_mode(self)

        stdin, stdout, stderr = client.exec_command(
            f"bash cd /home/sq/sq/stormquant-beta/engineering/python_toolkit/python3.6 pulseSandbox.py -a {self.dash_a_var.get()} -b {self.dash_b_var.get()} -c {self.dash_c_var.get()} -d 0 -D 0.025 -f 25.0 -n 1/2 -g 4.15e5 -G 15 -i 14 -k {self.dash_k_var.get()} -l {self.dash_l_var.get()} -r 25.0e6 -s 0 -t 8192 \n")

        """SGTTY=/home/sq/sq/usbmap/siggen
            stty -F $SGTTY 115200 raw
            cd /home/sq/sq/stormquant-beta/engineering/python_toolkit/
            echo -ne ':A01='"$(cat pulse_compression_fullwave.csv)"'.\r\n' > $SGTTY;
            head -n 1 $SGTTY
            """
        time.sleep(0.1)
        stdin, stdout, stderr = client.exec_command("bash siggen-waveform101.sh")
        time.sleep(0.1)
        stdin, stdout, stderr = client.exec_command(f"bash siggen-outargmv.sh {self.voltage_var.get()}")
        time.sleep(0.1)
        stdin, stdout, stderr = client.exec_command("bash siggen-externalsignalsync.sh")
        time.sleep(0.1)
        stdin, stdout, stderr = client.exec_command("bash siggen-60microseconds.sh")
        time.sleep(0.1)
        stdin, stdout, stderr = client.exec_command("bash siggen-externaltrigger.sh")
        time.sleep(0.1)
        stdin, stdout, stderr = client.exec_command("bash siggen-modtypeburst.sh")
        time.sleep(0.1)
        stdin, stdout, stderr = client.exec_command("bash siggen-ch1out.sh")
        time.sleep(0.1)
        stdin, stdout, stderr = client.exec_command("bash siggen-defaultmodinterface.sh")
        time.sleep(0.1)
        stdin, stdout, stderr = client.exec_command("bash siggen-presetarbwave.sh")
        time.sleep(0.1)
        stdin, stdout, stderr = client.exec_command("bash siggen-save.sh")



