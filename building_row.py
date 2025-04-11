import ttkbootstrap as ttk
from ttkbootstrap.tooltip import ToolTip

import data
from data import all_buildings, all_scores, all_categories, all_slots
from tksetup import get_vcmd, get_vcmd_positive, on_focus_out, on_focus_out_integer, get_int_var_value, Combobox

class BuildingRow:
    def __init__(self, parent, main_frame, firststation=False, result_building=None):
        self.parent = parent
        self.main_frame = main_frame
        values = all_buildings.keys()
        init_text = "Pick a facility"
        if firststation:
            values = all_categories["First Station"]
            init_text = "Pick your first station"

        values = data.to_printable_list(values)
        self.name_var = ttk.StringVar(value=init_text)
        self.valid = False
        self.first_station = firststation
        if firststation:
            self.category_choice = ttk.Label(self.parent, text="First Station", width=15)
            values.append("Let the program choose for me")
        else:
            self.category_var = ttk.StringVar(value="All")
            self.category_choice = Combobox(self.parent, textvariable=self.category_var,
                                            width=15, state="readonly", values=list(all_categories.keys()))
            self.category_var.trace_add("write", self.on_category_choice)

        self.building_choice = Combobox(self.parent, textvariable=self.name_var, width=25, state="readonly",
                                        values=values)
        self.already_present_var, self.already_present_entry = self.make_int_var_and_entry()
        self.at_least_var, self.at_least_entry = self.make_var_and_entry()
        self.at_most_var, self.at_most_entry = self.make_var_and_entry()
        self.to_build_var, self.to_build_entry = self.make_int_var_and_entry(modifiable=False)
        self.total_var, self.total_entry = self.make_int_var_and_entry(modifiable=False)
        self.delete_button = None
        self.widgets = [ self.category_choice,
                    self.building_choice,
                    self.already_present_entry,
                    self.at_least_entry,
                    self.at_most_entry,
                    self.to_build_entry,
                    self.total_entry ]
        if result_building or firststation:
            self.create_delete_button()

        self.to_build_var.trace_add("write", self.update_total)
        self.name_var.trace_add("write", self.on_choice)
        self.already_present_var.trace_add("write", self.on_set_already_built)
        self.total_var.trace_add("write", self.set_or_clear_tooltip)

        if firststation:
            self.already_present_entry.config(state="readonly")
            self.delete_button.config(state="disabled")

        if result_building:
            self.name_var.set(result_building)
            self.valid = True
            # self.building_choice.config(state="disabled")
            # self.already_present_entry.config(state="readonly")

    @property
    def is_result(self):
        return (not self.first_station and self.already_present == 0
                and self.at_least_var.get() == "" and self.at_most_var.get() == "")
    @property
    def is_port(self):
        building_name = data.from_printable(self.name_var.get())
        return not self.first_station and self.valid and data.is_port(all_buildings[building_name])
    @property
    def building_name(self):
        return data.from_printable(self.name_var.get())
    @property
    def already_present(self):
        return get_int_var_value(self.already_present_var)

    def pack(self, index=None):
        if index is None:
            index = self.index
        else:
            self.index = index
        for column, w in enumerate(self.widgets):
            w.grid(row=index, column=column, padx=2, pady=2)

    def set_build_result(self, value):
        self.to_build_var.set(value)
        if value > 0:
            self.to_build_entry.config(bootstyle="success")

    def set_or_clear_tooltip(self, *args):
        nb_total = self.total_var.get()
        if self.valid and nb_total > 0:
            building = all_buildings[self.building_name]
            state = data.SystemState({"already_present": {self.building_name: nb_total}})
            score_text = ", ".join(f"{data.to_printable(score)}: {state.scores[score]}" for score in data.base_scores
                                   if state.scores[score] != 0)
            self.tooltip = ToolTip(self.total_entry, score_text)
        else:
            if getattr(self, "tooltip", None):
                # No way to delete a tooltip, so we just replace the total entry with a new one that has no tooltip
                idx_in_widgets = self.widgets.index(self.total_entry)
                self.total_entry.destroy()
                _, self.total_entry = self.make_int_var_and_entry(modifiable=False, use_variable=self.total_var)
                self.widgets[idx_in_widgets] = self.total_entry
                self.pack()
                self.tooltip = None

    def remove_result(self):
        self.to_build_var.set(0)
        self.to_build_entry.config(bootstyle="default")

    def on_category_choice(self, var, index, mode):
        category = self.category_var.get()
        self.building_choice.config(values=data.to_printable_list(all_categories[category]))
        self.name_var.set("Pick a facility")
        self.valid = False

    def on_choice(self, var, index, mode):
        if self.name_var.get() in self.building_choice.cget("values"):
            self.valid = (self.name_var.get() != "Let the program choose for me")
            if self.name_var.get() == "Let the program choose for me":
                self.main_frame.choose_first_station_var.set(True)
                self.already_present_var.set(0)
            if self.first_station and not self.main_frame.choose_first_station_var.get():
                self.already_present_var.set(1)
            if self is self.main_frame.building_input[-1]:
                self.main_frame.add_empty_building_row()
                if self.delete_button is None and not self.first_station:
                    self.create_delete_button()
                    self.delete_button.grid(row=self.index, column=7)

    def on_set_already_built(self, *_args):
        self.main_frame.update_values_from_building_input()
        self.update_total()

    def update_total(self, *args):
        self.total_var.set(self.to_build_var.get() + self.already_present)

    def delete(self):
        for w in self.widgets:
            w.destroy()

    def create_delete_button(self):
        self.delete_button = ttk.Button(self.parent, text="X",
                                        width=1, command=self.on_delete, bootstyle=("outline", "secondary"))
        self.widgets.append(self.delete_button)

    def on_delete(self):
        idx = self.main_frame.building_input.index(self)
        self.delete()
        del self.main_frame.building_input[idx]
        self.main_frame.update_values_from_building_input()
        for i, row in enumerate(self.main_frame.building_input):
            row.pack(i+1)

    def make_var_and_entry(self, modifiable=True, width=7, **kwargs):
        variable = ttk.StringVar()
        entry = ttk.Entry(self.parent, textvariable=variable,
                          validate="key", validatecommand=get_vcmd(),
                          width=width, justify=ttk.RIGHT, **kwargs)
        if modifiable:
            entry.bind("<FocusOut>", lambda event, var=variable: on_focus_out(event, var))
        else:
            entry.config(state="readonly")
        return (variable, entry)

    def make_int_var_and_entry(self, modifiable=True, width=7, use_variable=None, **kwargs):
        variable = use_variable or ttk.IntVar()
        entry = ttk.Entry(self.parent, textvariable=variable,
                          validate="key", validatecommand=get_vcmd_positive(),
                          width=width, justify=ttk.RIGHT, **kwargs)
        if modifiable:
            entry.bind("<FocusOut>", lambda event, var=variable: on_focus_out_integer(event, var))
        else:
            entry.config(state="readonly")
        return (variable, entry)
