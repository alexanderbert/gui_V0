from home import *
#from fpga_layout import *
from header import *
#from positioner import PositionerFrame
#from radar_functionality import RadarFunctionality
#from visualization import *
from v2_positioner import *
from v2_radar_functionality import *
from v2_visualization import *
from v2_fpga_layout import *
import customtkinter
import tkinter.font as tkFont


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1480x900")
        self.title("Radar Control")

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=7)
        self.columnconfigure(0, weight=1)
        self.grid_propagate(False)

        state.init_state(self)

        self.header_frame = HeaderFrame(self)
        self.header_frame.grid(column=0, row = 0, sticky = "EW")
        self.header_frame.add_header_image()
        self.notebook_style = ttk.Style()
        self.notebook_style.theme_use("classic")
        self.my_notebook = ttk.Notebook()
        self.my_notebook.grid(row=1, column=0, sticky="nsew")
        self.my_notebook.grid_propagate(False)
        self.notebook_style = ttk.Style()
        self.main_frame = MainFrame(self.my_notebook)

        # self.positioner_frame = PositionerFrame(self.my_notebook)
        # self.positioner_frame.control_frame.radars_available_frame.radar_drop()
        self.positioner_frame = Positioner2Frame(self.my_notebook)


        self.connection_frame = HomeFrame(self.my_notebook)


        self.visualization_frame = MainFrameV(self.my_notebook)

        #self.radar_functionality_frame = RadarFunctionality(self.my_notebook)
        self.radar_functionality = RadarFunctionality2(self.my_notebook)

        self.my_notebook.add(self.connection_frame, text = "Home")
        ### seperate tab for home
        self.my_notebook.add(self.main_frame, text = "Generate Radar Data")
        self.my_notebook.add(self.positioner_frame, text = "Positioner Control")
        self.my_notebook.add(self.visualization_frame, text = "Visualize Radar Output")
        self.my_notebook.add(self.radar_functionality, text = "Collect Calibration Data")



        self.option_add("*TCombobox*Listbox.font", ("Arial", 20))

        style = ttk.Style()
        style.theme_use(
            'clam'
        )
        style.configure("blue.Horizontal.TProgressbar", foreground="red", background="blue")
        style.configure("green.Horizontal.TProgressbar", foreground="red", background="green")
        style.configure("yellow.Horizontal.TProgressbar", foreground="red", background="yellow")
        style.configure("red.Horizontal.TProgressbar", foreground="red", background="red")

        # default_font = tkFont.nametofont("TkDefaultFont")
        # default_font.configure(family="Arial", size=20)


        self.mainloop()

App()
