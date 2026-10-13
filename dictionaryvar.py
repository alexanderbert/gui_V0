import tkinter as tk
import json

class DictVar:
    def __init__(self, master=None, initial_dict=None):
        self._var = tk.StringVar(master=master)
        self.set_dict(initial_dict or {})

    def set_dict(self, dictionary):
        if not isinstance(dictionary, dict):
            raise TypeError("Value must be a dictionary")
        self._var.set(json.dumps(dictionary))

    def get_dict(self):
        """Retrieves the dictionary snapshot."""
        return json.loads(self._var.get())

    def update_key(self, key, value):
        """Updates or adds a single key-value pair."""
        current = self.get_dict()
        current[key] = value
        self.set_dict(current)

    def update_dict(self, new_data):
        """Merges multiple key-value pairs."""
        if not isinstance(new_data, dict):
            raise TypeError("Value must be a dictionary")
        current = self.get_dict()
        current.update(new_data)
        self.set_dict(current)
    def trace_add(self, mode, callback):
        # Allow widgets or functions to "listen" to dictionary changes
        return self._var.trace_add(mode, callback)