import tkinter
import ttkbootstrap as ttk
from tkinter.scrolledtext import ScrolledText
from ttkbootstrap.tooltip import ToolTip

import extract
import ordering
import daftmav
import scuffed

class ImportWindow(tkinter.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.wm_title("EDCP Import")
        self.grab_set()
        self.create_layout()

    def on_daftmav_import(self):
        contents = self.daftmav_text_entry.get('1.0', 'end')
        result = daftmav.import_state(self.parent, contents, with_system_name=self.set_system_name_var.get())
        if result:
            self.set_error_message(result)
        else:
            self.destroy()

    def on_scuffed_import(self):
        contents = self.scuffed_text_entry.get('1.0', 'end')
        result = scuffed.import_state(self.parent, contents, with_system_name=self.set_system_name_var.get())
        if result:
            self.set_error_message(result)
        else:
            self.destroy()

    def set_error_message(self, msg):
        self.message_label.config(text=msg)

    def create_layout(self):
        options_frame = ttk.LabelFrame(self, text="Options", padding=2)
        self.set_system_name_var = ttk.BooleanVar()
        self.set_system_checkbox = ttk.Checkbutton(options_frame, text="Set system name if found",
                                                   variable=self.set_system_name_var)
        self.set_system_checkbox.pack(padx=5, pady=2, side="left")
        options_frame.pack(padx=2, pady=5, fill="x", side="top")

        daftmav_frame = ttk.Frame(self, padding=2)
        label = ttk.Label(daftmav_frame, text="Colonization Construction v3 (By DaftMav)", wraplength=100, width=10)
        self.daftmav_text_entry = ScrolledText(daftmav_frame, width=20, height=5, wrap='none')
        self.daftmav_button = ttk.Button(daftmav_frame, text="Import",
                                         command=self.on_daftmav_import, width=8)
        label.pack(padx=5, pady=2, side="left", anchor=ttk.N)
        self.daftmav_text_entry.pack(padx=5, pady=2, side="left")
        self.daftmav_button.pack(padx=5, pady=2, side="left", anchor=ttk.N)
        daftmav_frame.pack(padx=2, pady=5, fill="x", side="top")

        scuffed_frame = ttk.Frame(self, padding=2)
        label = ttk.Label(scuffed_frame, text="Scuffed (by CMDR Nowksi)", wraplength=100, width=10)
        self.scuffed_text_entry = ScrolledText(scuffed_frame, width=20, height=5, wrap='none')
        self.scuffed_button = ttk.Button(scuffed_frame, text="Import",
                                         command=self.on_scuffed_import, width=8)
        label.pack(padx=5, pady=2, side="left", anchor=ttk.N)
        self.scuffed_text_entry.pack(padx=5, pady=2, side="left")
        self.scuffed_button.pack(padx=5, pady=2, side="left", anchor=ttk.N)
        scuffed_frame.pack(padx=2, pady=5, fill="x", side="top")

        self.message_label = ttk.Label(self, text="", bootstyle="danger")
        self.message_label.pack(padx=2, pady=5, side="top")

