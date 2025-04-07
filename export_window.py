import tkinter
import ttkbootstrap as ttk
from tkinter.scrolledtext import ScrolledText
from ttkbootstrap.tooltip import ToolTip
from tkinter import filedialog

import extract
import ordering
import daftmav
import scuffed

class ExportWindow(tkinter.Toplevel):
    def __init__(self, parent, extracted):
        super().__init__(parent)
        self.wm_title("EDCP Export")
        self.grab_set()
        self.extracted = extracted
        self.validate()
        self.create_layout()
        self.update_text()
        

    def validate(self):
        try:
            l = ordering.get_ordering_from_result(self.extracted, with_solution=False)
            self.initial_state_valid = True
        except RuntimeError:
            self.initial_state_valid = False

    def update_text(self, *args):
        not_mixed = self.not_mix_var.get()
        if not not_mixed:
            try:
                order = ordering.get_mixed_ordering_from_result(self.extracted)
            except RuntimeError:
                order = None
        else:
            include_initial_state = self.include_initial_state_var.get()
            order = ordering.get_ordering_from_result(self.extracted,
                                                           with_already_present=include_initial_state)
        if order is None:
            daftmav_str = ("Error! Export failed!\n"
                                "Did you 'Solve for a system'?\n"
                                "Please submit an issue\n"
                                "if you did, with a\n"
                                "screenshot of the app.")
            self.daftmav_text_entry.config(fg="red")
            scuffed_str = ""
        else:
            daftmav_str = daftmav.export_ordering(order)
            scuffed_str = scuffed.export_ordering(order)

        self.set_entry_text(self.daftmav_text_entry, daftmav_str)
        self.set_entry_text(self.scuffed_text_entry, scuffed_str)

    def set_entry_text(self, entry, text):
        entry.delete('1.0', 'end')
        entry.insert('1.0', text)
        entry.see('1.0')

    def export_daftmav(self):
        contents = self.daftmav_text_entry.get('1.0', 'end')
        self.clipboard_clear()
        self.clipboard_append(contents)
        self.destroy()

    def export_scuffed(self):
        contents = self.scuffed_text_entry.get('1.0', 'end')
        self.clipboard_clear()
        self.clipboard_append(contents)
        self.destroy()

    def export_scuffed_file(self):
        contents = self.scuffed_text_entry.get('1.0', 'end')
        dest = filedialog.asksaveasfile(mode='w', filetypes=[("Text files", "*.txt"), ("All files", "*")])
        if dest:
            dest.write(contents)
            dest.close()
            self.destroy()
        else:
            pass

    def create_layout(self):
        options_frame = ttk.LabelFrame(self, text="Options", padding=2)
        self.include_initial_state_var = ttk.BooleanVar()
        self.not_mix_var = ttk.BooleanVar(value=True)
        self.initial_checkbox = ttk.Checkbutton(options_frame, text="Include initial state",
                                                variable=self.include_initial_state_var)
        self.mixed_checkbox = ttk.Checkbutton(options_frame, text="But only at the start",
                                              variable=self.not_mix_var)
        ToolTip(self.mixed_checkbox, text="Useful if your initial state is not yet built")
        self.initial_checkbox.pack(padx=5, pady=2, side="left")
        self.mixed_checkbox.pack(padx=5, pady=2, side="left")
        options_frame.pack(padx=2, pady=5, fill="x")

        if not self.initial_state_valid:
            self.not_mix_var.set(False)
            self.include_initial_state_var.set(True)
            self.initial_checkbox.config(state="disabled")
            self.mixed_checkbox.config(state="disabled")
            ToolTip(self.mixed_checkbox, text="Locked because the initial state is infeasible")
            ToolTip(self.initial_checkbox, text="Locked because the initial state is infeasible")
        
        daftmav_frame = ttk.Frame(self, padding=2)
        label = ttk.Label(daftmav_frame, text="Colonization Construction v3 (By DaftMav)", wraplength=100, width=10)
        self.daftmav_text_entry = ScrolledText(daftmav_frame, width=22, height=5, wrap='none')
        daftmav_button = ttk.Button(daftmav_frame, text="To clipboard",
                                         command=self.export_daftmav, width=8)
        label.pack(padx=5, pady=2, side="left", anchor=ttk.N)
        self.daftmav_text_entry.pack(padx=5, pady=2, side="left")
        daftmav_button.pack(padx=5, pady=2, side="left", anchor=ttk.N)
        daftmav_frame.pack(padx=2, pady=5, fill="x")

        scuffed_frame = ttk.Frame(self, padding=2)
        label = ttk.Label(scuffed_frame, text="Scuffed (by CMDR Nowksi)", wraplength=100, width=10)
        self.scuffed_text_entry = ScrolledText(scuffed_frame, width=22, height=5, wrap='none')
        scuffed_button_frame = ttk.Frame(scuffed_frame, padding=2)
        scuffed_button_clipboard = ttk.Button(scuffed_button_frame, text="To clipboard",
                                              command=self.export_scuffed, width=8)
        scuffed_button_file = ttk.Button(scuffed_button_frame, text="To file",
                                         command=self.export_scuffed_file, width=8)
        scuffed_button_clipboard.pack(padx=2, pady=5, side="top")
        scuffed_button_file.pack(padx=2, pady=5, side="top")
        label.pack(padx=5, pady=2, side="left", anchor=ttk.N)
        self.scuffed_text_entry.pack(padx=5, pady=2, side="left")
        scuffed_button_frame.pack(padx=5, pady=2, side="left", anchor=ttk.N)
        scuffed_frame.pack(padx=2, pady=5, fill="x")

        self.include_initial_state_var.trace_add("write", self.update_text)
        self.not_mix_var.trace_add("write", self.update_text)

        ToolTip(daftmav_button, "Click me, then paste in column 'D' in a Colony tab.\n If you selected 'include initial state', paste in the row of the first station, otherwise in the first empty row.")
        ToolTip(scuffed_button_file, "Save in a file, then use the tool 'import' link at the top right to choose the saved file.")
