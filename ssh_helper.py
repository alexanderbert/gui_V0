import os
import state

def fl_network_mode(self):
    self.current_radar_key = state.radar_choice.get()
    for key, value in state.radars_found.get_dict().items():
        if key == self.current_radar_key:
            self.current_radar_value = value
    print(f"INSIDE FLORIDA {self.current_radar_value}")
    self.status_var.set("Connecting to radar...")
    self.status_entry.configure(fg_color="yellow green", text_color="black")
    try:
        client = self.create_ssh_client()
        client.connect(hostname=f"{self.current_radar_value}", username=f"{os.environ.get('CONNECTION_USERNAME')}",
                       password=f"{os.environ.get('CONNECTION_PASSWORD')}", look_for_keys=False, allow_agent=False,
                       timeout=10)
        # print(f"{self.positioner_selected_for_use} inside status")
        # print(f"{selected_positioner_global} GLOBAL status")
        transport = client.get_transport()
        channel = transport.open_session()
        channel.get_pty()
        channel = client.invoke_shell()
        return client, channel
    except Exception as e:
        print(f"WITHIN FL_NETWORK_MODE{e}")
        return False
