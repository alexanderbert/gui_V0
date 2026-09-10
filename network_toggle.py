import tkinter as tk
import state


class NetworkSwitch(tk.Frame):
    def __init__(self, parent, label_a="Wifi", label_b="Ethernet", command=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.network_state = tk.StringVar()
        self.command = command
        if state.network_state == "Ethernet":
            self.state = True
        else:
            self.state = False # False = Position A, True = Position B



        # --- UI Styling Configuration ---
        self.width = 60
        self.height = 30
        self.bg_color_a = "#4CD964" # Green for state A
        self.bg_color_b = "#0000FF" # Blue for state B #0000FF
        self.circle_color = "#FFFFFF"

        # 1. Label for State A
        self.lbl_a = tk.Label(self, text=label_a, font=("Helvetica", 12, "bold"), fg="#333333")
        self.lbl_a.pack(side="left", padx=5)

        # 2. The Interactive Slider Canvas
        self.canvas = tk.Canvas(self, width=self.width, height=self.height,
            highlightthickness=0, cursor="hand2")
        self.canvas.pack(side="left", padx=5)

        # 3. Label for State B
        self.lbl_b = tk.Label(self, text=label_b, font=("Helvetica", 12), fg="#999999")
        self.lbl_b.pack(side="left", padx=5)

        # Bind click event to the canvas
        self.canvas.bind("<Button-1>", self.toggle)

        # Draw the initial "A" state
        self.draw_switch()

    def draw_switch(self):
        self.canvas.delete("all")

        # Determine background color based on state
        bg_color = self.bg_color_b if self.state else self.bg_color_a

        # Draw rounded background pill
        r = self.height
        self.canvas.create_oval(0, 0, r, r, fill=bg_color, outline="")
        self.canvas.create_oval(self.width - r, 0, self.width, r, fill=bg_color, outline="")
        self.canvas.create_rectangle(r/2, 0, self.width - r/2, self.height, fill=bg_color, outline="")

        # Draw the sliding circle (Thumb)
        padding = 3
        circle_diameter = self.height - (padding * 2)

        if self.state:
            # Position B (Right side)
            x0 = self.width - circle_diameter - padding

        else:
            # Position A (Left side)
            x0 = padding

        y0 = padding
        x1 = x0 + circle_diameter
        y1 = y0 + circle_diameter

        self.canvas.create_oval(x0, y0, x1, y1, fill=self.circle_color, outline="")

    def toggle(self, event=None):
        # Flip the state

        self.state = not self.state


        # Update text styles to highlight the active side
        if self.state:
            self.lbl_a.config(font=("Helvetica", 12), fg="#999999")
            self.lbl_b.config(font=("Helvetica", 12, "bold"), fg="#333333")
            state.network_state = "10.42.0"
            # self.network_state.set("Wifi")
            # state.network_state = "Wifi"
            # print(state.network_state)
        else:
            self.lbl_a.config(font=("Helvetica", 12, "bold"), fg="#333333")
            self.lbl_b.config(font=("Helvetica", 12), fg="#999999")
            state.network_state = "192.168.69.*"
            # self.network_state.set("Ethernet")
            # state.network_state = "Ethernet"
            # print(state.network_state)

        # Redraw the slider graphics
        self.draw_switch()

        # Trigger the callback function if one was provided
        # if self.command:
        #     self.command(self.state)

