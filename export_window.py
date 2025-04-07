import tkinter
import ttkbootstrap as ttk
from tkinter.scrolledtext import ScrolledText
from ttkbootstrap.tooltip import ToolTip

import extract
import ordering
import daftmav

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
            self.daftmav_str = ("Error! Export failed!\n"
                                "Did you 'Solve for a system'?\n"
                                "Please submit an issue\n"
                                "if you did, with a\n"
                                "screenshot of the app.")
            self.text_entry.config(fg="red")
        else:
            self.daftmav_str = daftmav.export_ordering(order)
        self.text_entry.delete('1.0', 'end')
        self.text_entry.insert('1.0', self.daftmav_str)
        self.text_entry.see('1.0')

    def export(self):
        contents = self.text_entry.get('1.0', 'end')
        self.clipboard_clear()
        self.clipboard_append(contents)
        self.daftmav_button.config(text="Done!", bootstyle="success")
        self.destroy()

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
        label = ttk.Label(daftmav_frame, text="Colonization Construction v3 (By DaftMav)", wraplength=100)
        self.text_entry = ScrolledText(daftmav_frame, width=22, height=5, wrap='none')
        self.daftmav_button = ttk.Button(daftmav_frame, text="To clipboard",
                                         command=self.export, width=8)
        label.pack(padx=5, pady=2, side="left", anchor=ttk.N)
        self.text_entry.pack(padx=5, pady=2, side="left")
        self.daftmav_button.pack(padx=5, pady=2, side="left", anchor=ttk.N)
        daftmav_frame.pack(padx=2, pady=5, fill="x")

        self.include_initial_state_var.trace_add("write", self.update_text)
        self.not_mix_var.trace_add("write", self.update_text)

