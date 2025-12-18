from fpga_layout import *
from header import *

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("1480x900")
        self.title("Radar Control")

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=7)
        self.columnconfigure(0, weight=1)
        self.grid_propagate(False)

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
        self.main_frame.control_frame.radars_available_frame.radar_drop()

        self.frame2 = tk.Frame(self.my_notebook, bg="blue")

        self.my_notebook.add(self.main_frame, text = "FPGA")
        self.my_notebook.add(self.frame2, text = "Blue")

        self.mainloop()
App()
