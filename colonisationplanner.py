import os
from platformdirs import user_data_dir
import sys
import tkinter

import pyglet
import ttkbootstrap as ttk
from ttkbootstrap.tooltip import ToolTip

import data
from data import all_buildings, all_scores, all_categories, all_slots
from building_row import BuildingRow
from scrollable_frame import ScrollableFrame
from tksetup import register_validate_commands, get_vcmd, on_focus_out, set_style_if_negative, get_int_var_value
import solver
import export

#TODO
#   Add port economy (once Fdev fixes it)
#   Add custom maximum e.g. maximize wealth^2*techlevel (will need to switch to minlp)

# Main window
class MainWindow(ttk.Window):
    def __init__(self, savefile):
        super().__init__(themename="darkly")
        self.style.configure('.', font=("Eurostile", 12))
        register_validate_commands(self)
        self.title("Elite Dangerous colonisation planner")
        self.geometry("1000x1000")
        self.building_input = []
        self.port_order = None
        self.save_file = export.SaveFile(savefile)
        w = self.save_file.get_warnings()
        if w:
            print("Warning:", w)
        self.create_widgets_and_layout()

    def create_widgets_and_layout(self):
        self.create_import_export_panel()
        self.create_dark_mode()
        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True)
        self.create_optimization_criterion_choice()
        self.create_main_panel()
        self.create_result_panel()
        self.create_action_buttons()


    # Dropdown menu at the top for choosing what to optimize
    def create_optimization_criterion_choice(self):
        self.maximizeinput = ttk.StringVar()
        frame = ttk.Frame(self.scroll_frame.scrollable_frame)
        frame.pack(pady=5)
        label = ttk.Label(frame, text="Select what you are trying to maximize (except for construction cost which is minimized):")
        label.pack(side="left", padx=4, pady=5)
        dropdown = tkinter.OptionMenu(frame, self.maximizeinput, *data.to_printable_list(all_scores))
        dropdown.pack(side="left", padx=4, pady=5)
        frame = ttk.Frame(self.scroll_frame.scrollable_frame)
        frame.pack(pady=5)
        self.advancedobjective = ttk.BooleanVar()
        frame2 = ttk.Frame(self.scroll_frame.scrollable_frame)
        frame2.pack()
        advancedframe = ttk.LabelFrame(frame2, text="", padding=2)
        canvas = tkinter.Canvas(frame2, width=33, height=33, bg='darkgrey')
        canvas.pack(side="right", padx=4, pady=5)
        canvas.create_oval(10, 10, 30, 30, fill="lightblue")
        canvas.create_text(20, 20, text="?", font=("arial", 8, "bold"))
        directionframe = ttk.Frame(advancedframe)
        self.direction_input = ttk.BooleanVar()
        directionswitch = ttk.Checkbutton(directionframe, text="", variable=self.direction_input, bootstyle="round-toggle", state='disabled')
        self.objectiveinput = ttk.StringVar()
        entry = ttk.Entry(advancedframe, textvariable=self.objectiveinput, width=40)
        pretext = "Enter your custom objective function here..."
        entry.insert(0, pretext)
        entry.bind("<FocusIn>", lambda event: entry.delete(0, "end") if entry.get() == pretext else None)
        entry.bind("<FocusOut>", lambda event: entry.insert(0, pretext) if not entry.get() else None)
        entry.config(state='disabled')
        ToolTip(canvas, text="Set your own custom objective function.\nThe objective function is what the program tries to maximize/minimize (depending on what you select).\nSupported operators:\n+, -, /, *, ^, ln() (natural logarithm), abs() (absolute value)\n(abs(x) = x if x >= 0, -x if x < 0)\n\nIf brackets are not present, standard order of operations will be followed.\nBrackets after the ln/sgn are required, for the program to recognize what to take the logarithm or sign of.\nSpaces can be placed anywhere.\nType numbers normally.\n\nUse letters to represent the system scores:\ni: Initial population increase\nm: Maximum population increase\ne: Security\nt: Tech level\nw: Wealth\nn: Standard of living\nd: Development level\nc: Construction cost\n\nExample inputs:\nw*t^2 maximizes/minimizes wealth * (tech level squared)\n(-15*d + ln(n^ w))/c maximizes/minimizes (-15 * development level + ln(standard of living ^ wealth)) / construction cost")
        checkbox = ttk.Checkbutton(frame2, text="Advanced objective", variable=self.advancedobjective, command=lambda: (dropdown.config(state='disabled'), directionswitch.config(state='normal'), entry.config(state='normal')) if self.advancedobjective.get() else (dropdown.config(state='normal'), directionswitch.config(state='disabled'), entry.config(state='disabled')))
        advancedframe.config(labelwidget=checkbox)
        advancedframe.pack(side="left", padx=4, pady=5)
        self.scroll_frame.scrollable_frame.update_idletasks()
        directionframe.pack()
        label = ttk.Label(directionframe, text="Minimize")
        label.pack(side="left", padx=3, pady=5)
        ToolTip(directionswitch, text="Turn on to maximize the objective function and turn off to minimize it")
        directionswitch.pack(side="left", padx=3, pady=5)
        label = ttk.Label(directionframe, text="Maximize")
        label.pack(side="left", pady=5)
        entry.pack(padx=4, pady=5)

    # Main panel in the middle
    def create_main_panel(self):
        self.mixed_frame = ttk.Frame(self.scroll_frame.scrollable_frame)
        self.mixed_frame.pack()
        self.create_stats_panel()

        self.right_frame = ttk.Frame(self.mixed_frame)
        self.right_frame.pack(side="left", expand=True, fill="both")
        self.create_slots_panel()
        self.create_choose_first_station_panel()
        self.create_construction_points_panel()

    def print_result(self, text):
        current_text = self.resultlabel.cget("text")
        new_text = current_text + "\n" + text
        self.resultlabel.config(text=new_text)

    def set_port_ordering(self, order):
        self.port_order = order
        port_ordering_string = "Suggested port build order: "
        port_ordering_string += " --> ".join(f"{port_index+1}: {data.to_printable(port_name)}"
                                             for port_index, port_name in enumerate(order))
        self.print_result(port_ordering_string)
        ToolTip(self.resultlabel, text="If you want to force a different ordering, you can set ports as 'already built' in your favorite order.\nThe system will build facilities to provide the required construction points.\nRemember to update the number of available slots accordingly.")


    # Dark-mode toggle button at the top left
    def create_dark_mode(self):
        self.dark_mode_var = ttk.BooleanVar(value=True)
        self.dark_mode_button = ttk.Checkbutton(self, text="Dark mode",
                                                variable=self.dark_mode_var, bootstyle="round-toggle")
        self.dark_mode_var.trace_add("write", self.on_dark_mode_change)
        self.dark_mode_button.place(x=5, y=5)

    # Handler for dark mode
    def on_dark_mode_change(self, *args):
        if self.dark_mode_var.get():
            self.style.theme_use("darkly")
        else:
            self.style.theme_use("litera")


    # Leftmost panel for system stats
    def create_stats_panel(self):
        self.minvars = {}
        self.maxvars = {}
        self.resultvars = {}

        constraint_frame = ttk.LabelFrame(self.mixed_frame, text="System Stats", padding=2)
        constraint_frame.pack(padx=10, pady=5, side="left", fill="y")
        ttk.Label(constraint_frame, text="min. value").grid(column=1, row=1)
        ttk.Label(constraint_frame, text="max. value").grid(column=2, row=1)
        ttk.Label(constraint_frame, text="solution value").grid(column=3, row=1)
        for i, name in enumerate(all_scores):
            self.minvars[name] = ttk.StringVar(value="")
            self.maxvars[name] = ttk.StringVar(value="")
            self.resultvars[name] = ttk.IntVar()

            display_name = data.to_printable(name)
            label = ttk.Label(constraint_frame, text=display_name)
            label.grid(column=0, row=2+i, pady=2, padx=2)
            entry_min = ttk.Entry(constraint_frame, textvariable=self.minvars[name],
                                  validate="key", validatecommand=get_vcmd(), width=7, justify=ttk.RIGHT)
            entry_max = ttk.Entry(constraint_frame, textvariable=self.maxvars[name],
                                  validate="key", validatecommand=get_vcmd(), width=7, justify=ttk.RIGHT)
            entry_min.grid(column=1, row=2+i, pady=2, padx=2)
            entry_max.grid(column=2, row=2+i, pady=2, padx=2)
            entry_min.bind("<FocusOut>", lambda event, var=self.minvars[name]: on_focus_out(event, var))
            entry_max.bind("<FocusOut>", lambda event, var=self.maxvars[name]: on_focus_out(event, var))

            result = ttk.Entry(constraint_frame, textvariable=self.resultvars[name], width=7, justify=ttk.RIGHT)
            result.grid(column=3, row=2+i, padx=5, pady=2)
            result.config(state="readonly")
            set_style_if_negative(self.resultvars[name], result)


    # Panel for available construction slots in the system
    def create_slots_panel(self):
        self.available_slots_currently_vars = {}
        self.total_slots_currently_vars = {}
        self.available_slots_currently_entries = {}
        self.total_slots_currently_entries = {}
        self.available_slots_after_vars = {}
        self.used_slots_after_vars = {}
        self.slot_behavior = "fix_available"

        slots_frame = ttk.LabelFrame(self.right_frame, text="System slots", padding=2)
        slots_frame.pack(padx=10, pady=5, side="top", fill="y")
        ttk.Label(slots_frame, text="currently").grid(column=1, row=0, columnspan=2)
        ttk.Label(slots_frame, text="in solution").grid(column=3, row=0, columnspan=2)
        slots_available_button = ttk.Button(slots_frame, text="available", bootstyle="link",
                                            command=lambda: self.on_toggle_slot_input("fix_available"))
        slots_available_button.grid(column=1, row=1)
        slots_total_button = ttk.Button(slots_frame, text="total", bootstyle="link",
                                        command=lambda: self.on_toggle_slot_input("fix_total"))
        slots_total_button.grid(column=2, row=1)
        ToolTip(slots_available_button, "Click to toggle between providing the available or total number of slots")
        ToolTip(slots_total_button, "Click to toggle between providing the available or total number of slots")
        ttk.Label(slots_frame, text="used").grid(column=3, row=1)
        ttk.Label(slots_frame, text="available").grid(column=4, row=1)

        for idx, (slot, slot_name) in enumerate(all_slots.items()):

            self.available_slots_currently_vars[slot] = ttk.IntVar()
            self.total_slots_currently_vars[slot] = ttk.IntVar()
            self.available_slots_after_vars[slot] = ttk.IntVar()
            self.used_slots_after_vars[slot] = ttk.IntVar()

            label = ttk.Label(slots_frame, text=slot_name)
            if slot_name == "Orbital":
                ToolTip(label, "Including asteroid bases (not first station) but excluding first station")
            if slot_name == "Asteroid":
                ToolTip(label, "Excluding first station")
            available = ttk.Entry(slots_frame, textvariable=self.available_slots_currently_vars[slot],
                                  validate="key", validatecommand=get_vcmd(), width=7, justify=ttk.RIGHT)
            total = ttk.Entry(slots_frame, textvariable=self.total_slots_currently_vars[slot],
                             width=7, state="readonly", justify=ttk.RIGHT)
            used_after = ttk.Entry(slots_frame, textvariable=self.used_slots_after_vars[slot],
                                   width=7, state="readonly", justify=ttk.RIGHT)
            available_after = ttk.Entry(slots_frame, textvariable=self.available_slots_after_vars[slot],
                                        width=7, state="readonly", justify=ttk.RIGHT)

            label.grid(row=2+idx, column=0, padx=2)
            available.grid(row=2+idx, column=1, padx=2, pady=2)
            total.grid(row=2+idx, column=2, padx=2, pady=2)
            used_after.grid(row=2+idx, column=3, padx=2, pady=2)
            available_after.grid(row=2+idx, column=4, padx=2, pady=2)

            available.bind("<FocusOut>", lambda event, var=self.available_slots_currently_vars[slot]: on_focus_out(event, var))
            available.config(bootstyle="primary")
            self.available_slots_after_vars[slot].trace_add("write", lambda *args, slot=slot: self.on_write_to_used_slots_after(slot))
            self.available_slots_currently_entries[slot] = available
            self.total_slots_currently_entries[slot] = total

            self.available_slots_currently_vars[slot].trace_add("write", self.update_values_from_building_input)

        self.criminalinput = ttk.BooleanVar()
        checkbox = ttk.Checkbutton(slots_frame, text="Allow contraband stations (pirate base, criminal outpost)",
                                   variable=self.criminalinput)
        checkbox.grid(row=3+len(all_slots), column=0, columnspan=5, padx=10, pady=10)

    # Handler for automatically setting "in solution used" when there is a change to "in solution available"
    def on_write_to_used_slots_after(self, slot):
        value = self.total_slots_currently_vars[slot].get() - self.available_slots_after_vars[slot].get()
        self.used_slots_after_vars[slot].set(value)

    # Handler for "available" and "total" column headers
    def on_toggle_slot_input(self, button_name):
        self.slot_behavior = button_name
        if button_name == "fix_available":
            for slot in all_slots.keys():
                self.available_slots_currently_entries[slot].config(state="normal")
                self.total_slots_currently_entries[slot].config(state="readonly")
        else:
            for slot in all_slots.keys():
                self.available_slots_currently_entries[slot].config(state="readonly")
                self.total_slots_currently_entries[slot].config(state="normal")


    # Panel for letting the program choose the First Station
    def create_choose_first_station_panel(self):
        self.choose_first_station_var = ttk.BooleanVar(value=False)
        self.first_station_cb_coriolis_var = ttk.BooleanVar(value=True)
        self.first_station_cb_asteroid_var = ttk.BooleanVar(value=True)
        self.first_station_cb_orbis_var = ttk.BooleanVar(value=True)
        first_station_checkbox = ttk.Checkbutton(self.right_frame, text="Let the program choose the first station",
                                                 variable=self.choose_first_station_var)
        first_station_frame = ttk.LabelFrame(self.right_frame, text="Test",
                                             labelwidget=first_station_checkbox, padding=2)
        first_station_frame.pack(side="top", padx=10, pady=5, fill="both")
        self.first_station_cbc_check = ttk.Checkbutton(first_station_frame, text="Allow Coriolis",
                                                  variable=self.first_station_cb_coriolis_var, state="disabled")
        self.first_station_cbab_check = ttk.Checkbutton(first_station_frame, text="Allow Asteroid Base",
                                                   variable=self.first_station_cb_asteroid_var, state="disabled")
        self.first_station_cbo_check = ttk.Checkbutton(first_station_frame, text="Allow Orbis",
                                                  variable=self.first_station_cb_orbis_var, state="disabled")
        self.first_station_cbc_check.pack(side="left", padx=4, pady=2)
        self.first_station_cbab_check.pack(side="left", padx=4, pady=2)
        self.first_station_cbo_check.pack(side="left", padx=4, pady=2)
        self.choose_first_station_var.trace_add("write", self.on_first_station_box)

    def on_first_station_box(self, *args):
        checkbox_state = "normal" if self.choose_first_station_var.get() else "disabled"
        for w in [self.first_station_cbc_check, self.first_station_cbab_check, self.first_station_cbo_check]:
            w.config(state=checkbox_state)
        if self.choose_first_station_var.get():
            self.building_input[0].building_choice.config(state="disabled")
            self.building_input[0].name_var.set("Let the program choose for me")
            self.building_input[0].already_present_var.set(0)
            if len(self.building_input) == 1:
                self.add_empty_building_row()
            for row in self.building_input[1:]:
                row.already_present_entry.config(state="readonly")
                row.already_present_var.set(0)
        else:
            self.building_input[0].building_choice.config(state="readonly")
            if self.building_input[0].valid:
                self.building_input[0].already_present_var.set(1)
            for row in self.building_input[1:]:
                row.already_present_entry.config(state="normal")


    # Panel for construction points
    def create_construction_points_panel(self):
        construction_points_frame = ttk.LabelFrame(self.right_frame, text="Construction points", padding=2)
        construction_points_frame.pack(side="top", padx=10, pady=5, fill="both")
        ttk.Label(construction_points_frame, text="currently").grid(row=0, column=1)
        ttk.Label(construction_points_frame, text="in solution").grid(row=0, column=2)

        self.T2points_variable = ttk.IntVar()
        self.T2points_variable_after = ttk.IntVar()
        label = ttk.Label(construction_points_frame, text="T2 points")
        self.T2points_entry = ttk.Entry(construction_points_frame, textvariable=self.T2points_variable,
                                        validate="key", validatecommand=get_vcmd(),
                                        width=10, justify=ttk.RIGHT, state="readonly")
        self.T2points_entry_after = ttk.Entry(construction_points_frame, textvariable=self.T2points_variable_after,
                                         width=10, justify=ttk.RIGHT, state="readonly")
        label.grid(row=1, column=0, padx=2, pady=2)
        self.T2points_entry.grid(row=1, column=1, padx=2, pady=2)
        self.T2points_entry_after.grid(row=1, column=2, padx=2, pady=2)

        self.T3points_variable = ttk.IntVar()
        self.T3points_variable_after = ttk.IntVar()
        label = ttk.Label(construction_points_frame, text="T3 points")
        self.T3points_entry = ttk.Entry(construction_points_frame, textvariable=self.T3points_variable,
                                        validate="key", validatecommand=get_vcmd(),
                                        width=10, justify=ttk.RIGHT, state="readonly")
        self.T3points_entry_after = ttk.Entry(construction_points_frame, textvariable=self.T3points_variable_after,
                                              width=10, justify=ttk.RIGHT, state="readonly")
        label.grid(row=2, column=0, padx=2, pady=2)
        self.T3points_entry.grid(row=2, column=1, padx=2, pady=2)
        self.T3points_entry_after.grid(row=2, column=2, padx=2, pady=2)

        self.auto_construction_points = ttk.BooleanVar(value=True)
        construction_points_checkbox = ttk.Checkbutton(construction_points_frame, text="Compute automatically from already built facilities", variable=self.auto_construction_points)
        construction_points_checkbox.grid(row=3, column=0, columnspan=3, pady=5, padx=10)
        self.auto_construction_points.trace_add("write", self.on_auto_construction_points)

    # Handler for the "compute automatically" checkbox
    def on_auto_construction_points(self, *args):
        if self.auto_construction_points.get():
            self.update_values_from_building_input()
            self.T2points_entry.config(state="readonly")
            self.T3points_entry.config(state="readonly")
        else:
            self.T2points_entry.config(state=ttk.NORMAL)
            self.T3points_entry.config(state=ttk.NORMAL)


    # Action buttons in the middle of the window
    def create_action_buttons(self):
        button_frame = ttk.Frame(self)
        solve_button = ttk.Button(button_frame, text="Solve for a system", command=self.on_solve)
        solve_button.pack(padx=5, side="left")
        clear_button = ttk.Button(button_frame, text="Clear Result", command=self.on_clear_button)
        clear_button.pack(padx=5, side="left")
        clear_all_button = ttk.Button(button_frame, text="Clear All Values", command=self.on_clear_all_button, bootstyle="danger")
        clear_all_button.pack(padx=5, side="left")
        button_frame.pack(pady=7)

    def create_import_export_panel(self):
        frame = ttk.Frame(self)
        self.system_name_var = ttk.StringVar()
        self.plan_name_var = ttk.StringVar()
        ttk.Label(frame, text="System Name:").pack(padx=5, pady=5, side="left")
        self.system_name_entry = ttk.Combobox(frame, textvariable=self.system_name_var, width=20,
                                         values=self.save_file.get_system_list())
        self.system_name_entry.pack(padx=5, pady=5, side="left")
        ttk.Label(frame, text="Plan name").pack(padx=5, pady=5, side="left")
        self.plan_name_entry = ttk.Combobox(frame, textvariable=self.plan_name_var, width=20, values=[])
        self.plan_name_entry.pack(padx=5, pady=5, side="left")

        self.system_name_var.trace_add("write", self.on_select_system)
        self.plan_name_var.trace_add("write", self.on_select_plan)

        save_button = ttk.Button(frame, text="Save", command=self.on_save_button)
        save_button.pack(padx=5, side="left")
        reload_button = ttk.Button(frame, text="Reload", command=self.on_select_plan)
        reload_button.pack(padx=5, side="left")
        frame.pack(pady=7)

    # Handlers for action buttons: "solve" and "clear result"
    def on_solve(self):
        res = solver.solve(self)
        if res and self.building_input[-1].valid:
            self.add_empty_building_row()

    def on_clear_button(self):
        self.clear_result()
        if self.building_input[0].valid:
            self.add_empty_building_row()

    def on_clear_all_button(self):
        self.clear_all()

    def on_save_button(self):
        system = self.system_name_var.get()
        plan = self.plan_name_var.get()
        if system and plan:
            self.save_file.save_plan(system, plan, self)
            w = self.save_file.get_warnings()
            if w:
                print("Warning:", w)
        self.system_name_entry.config(values=self.save_file.get_system_list())
        self.plan_name_entry.config(values=self.save_file.get_plan_list(system))

    def on_select_system(self, *args):
        system = self.system_name_var.get()
        plans = self.save_file.get_plan_list(system)
        self.plan_name_entry.config(values=plans)
        if plans:
            self.plan_name_var.set(plans[0])
        else:
            self.plan_name_var.set("")

    def on_select_plan(self, *args):
        system = self.system_name_var.get()
        plan = self.plan_name_var.get()
        if system and plan and plan in self.save_file.get_plan_list(system):
            self.save_file.load_plan(system, plan, self, with_solution=True)


    # Bottom-most panel: several rows for different building types. Also where the result is displayed
    def create_result_panel(self):
        self.building_frame = ttk.Frame(self.scroll_frame.scrollable_frame)
        self.building_frame.pack(padx=10, pady=5)

        header = [ ttk.Label(self.building_frame, text="Category", wraplength=150, anchor=ttk.N),
                   ttk.Label(self.building_frame, text="Building", wraplength=250, anchor=ttk.N),
                   ttk.Label(self.building_frame, text="Already built", wraplength=70, anchor=ttk.N),
                   ttk.Label(self.building_frame, text="Total at least", wraplength=70, anchor=ttk.N),
                   ttk.Label(self.building_frame, text="Total at most", wraplength=70, anchor=ttk.N),
                   ttk.Label(self.building_frame, text="To build", wraplength=70, anchor=ttk.N),
                   ttk.Label(self.building_frame, text="Total", wraplength=70, anchor=ttk.N)
                  ]
        for i, label in enumerate(header):
            label.grid(row=0, column=i)

        self.add_empty_building_row(firststation=True)

        self.resultlabel = ttk.Label(self.scroll_frame.scrollable_frame, text="")
        self.resultlabel.pack(pady=10)

    def add_empty_building_row(self, **kwargs):
        row = BuildingRow(self.building_frame, self, **kwargs)
        if self.choose_first_station_var.get():
            row.already_present_entry.config(state="readonly")
        self.building_input.append(row)
        row.pack(len(self.building_input) + 1)
        return row

    def get_row_for_building(self, building_name, include_first_station=True):
        result_row = None
        for row in reversed(self.building_input): # Makes sure I finish with the First Station
            if row.building_name == building_name:
                result_row = row
                break
        if result_row is None or (result_row.first_station and not include_first_station):
            result_row = self.add_empty_building_row(result_building=data.to_printable(building_name))
        return result_row

    def clear_result(self):
        self.resultlabel.config(text="")
        self.port_order = None
        for var in self.available_slots_after_vars.values():
            var.set(0)
        for var in self.used_slots_after_vars.values():
            var.set(0)
        self.T2points_variable_after.set(0)
        self.T3points_variable_after.set(0)
        for score in all_scores:
            self.resultvars[score].set(0)

        if self.choose_first_station_var.get():
            self.building_input[0].name_var.set("Let the program choose for me")
        for row in self.building_input:
            if row.is_result:
                row.delete()
            else:
                row.remove_result()
        self.building_input = [ row for row in self.building_input if not row.is_result ]
        for i, row in enumerate(self.building_input):
            row.pack(i+1)

    def clear_all(self):
        self.clear_result()
        self.maximizeinput.set("")
        for score in all_scores:
            self.minvars[score].set("")
            self.maxvars[score].set("")
        self.choose_first_station_var.set(False)
        self.auto_construction_points.set(True)
        for row in self.building_input:
            row.delete()
        self.building_input = []
        self.add_empty_building_row(firststation=True)

    def update_values_from_building_input(self, *args):
        construction_points = data.ConstructionPointsCounter()
        slots = {name: 0 for name in self.available_slots_currently_vars.keys() }
        for row in self.building_input:
            if row.valid:
                building = all_buildings[row.building_name]
                nb_present = row.already_present

                slots[building.slot] += nb_present
                if row.building_name == "Asteroid_Base":
                    slots["asteroid"] += nb_present

                construction_points.add_building(building, nb_present, row.first_station)

        for slot, nb_used in slots.items():
            if self.slot_behavior == "fix_available":
                avail = get_int_var_value(self.available_slots_currently_vars[slot])
                self.total_slots_currently_vars[slot].set(avail + nb_used)
            else:
                total = get_int_var_value(self.total_slots_currently_vars[slot])
                self.available_slots_currently_vars[slot].set(total - nb_used)

        if self.auto_construction_points.get():
            self.T2points_variable.set(construction_points.T2points)
            self.T3points_variable.set(construction_points.T3points)


if __name__ == "__main__":
    pyglet.options['win32_gdi_font'] = True
    if getattr(sys, "frozen", False) and hasattr(sys, '_MEIPASS'):
        data_dir = user_data_dir("edcolonisationplanner", "")
        os.makedirs(data_dir, exist_ok=True)
        savefile = os.path.join(data_dir, "saved_data.json")
        font_path = os.path.join(sys._MEIPASS, "eurostile.TTF")
        pyglet.font.add_file(font_path)
    else:
        savefile = "./saved_data.json"
        pyglet.font.add_file('eurostile.TTF')

    root = MainWindow(savefile)
    root.mainloop()
