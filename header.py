import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage

class HeaderFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background="gray85")
        self.grid_propagate(False)

    def add_header_image(self):
        header_image = PhotoImage(file="images/logo.png")
        image_label = tk.Label(self, image=header_image)
        image_label.pack(fill="y", expand=True)
        image_label.image = header_image