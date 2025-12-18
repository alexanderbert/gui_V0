import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage

class HeaderFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background="gray85")
        self.grid_propagate(False)

    def add_header_image(self):
        header_image = PhotoImage(file="images/logoresize3.png")
        image_label = tk.Label(self, image=header_image, borderwidth=0)
        image_label.pack(side="left", padx=50)
        image_label.image = header_image
        title_text = tk.Label(self, text = "Calibration Tool", font=("Arial", 20, 'bold'))
        title_text.pack(side="right", padx=50)