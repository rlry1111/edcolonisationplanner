import re
import os
import sys
from collections import defaultdict

import pulp

import tkinter
import ttkbootstrap as ttk
from ttkbootstrap.tooltip import ToolTip
import pyglet

from data import all_buildings, all_scores, all_categories
import data
#TODO
#   Let the code select a starting system
#   Add port economy (once Fdev fixes it)
#   Add custom maximum e.g. maximize wealth^2*techlevel (will need to switch to minlp)

pyglet.options['win32_gdi_font'] = True
if getattr(sys, "frozen", False) and hasattr(sys, '_MEIPASS'):
    #I'm bundling the windows CBC solver with this .exe, so this might not work on non windows OS
    cbc_path = os.path.join(sys._MEIPASS, "cbc.exe")
    solver = pulp.COIN_CMD(path=cbc_path)
    font_path = os.path.join(sys._MEIPASS, "eurostile.TTF")
    pyglet.font.add_file(font_path)
else:
    solver = None
    pyglet.font.add_file('eurostile.TTF')

def convert_maybe(variable, default=None):
    value = variable.get()
    if value != "": return int(value)
    return default

def get_int_var_value(variable):
    try:
        return variable.get()
    except tkinter.TclError:
        return 0

def solve():
    #requirements
    M = 10000

    # Get data from the Entry widgets
    orbitalfacilityslots = available_slots_currently_vars["space"].get()
    groundfacilityslots = available_slots_currently_vars["ground"].get()
    asteroidslots = available_slots_currently_vars["asteroid"].get()
    maximize = data.from_printable(maximizeinput.get())
    initial_T2points = T2points_variable.get()
    initial_T3points = T3points_variable.get()
    choose_first_station = choose_first_station_var.get()

    if building_input[0].name_var.get() == "Pick your first station" and not choose_first_station:
        printresult("Error: pick your first station")
        return None

    nb_ports_already_present = sum(row.already_present for row in building_input if row.is_port)
    max_nb_ports = orbitalfacilityslots + groundfacilityslots + nb_ports_already_present

    #problem
    direction = pulp.LpMinimize if maximize == "construction_cost" else pulp.LpMaximize
    prob = pulp.LpProblem("optimal_system_colonization_layout", direction)

    #create all the variables for each of the facilities
    all_vars = {} # for each building name, the variables that decide how many will be BUILT
    first_station_vars = {} # for each building name, a boolean variable for the first station
    all_values = {} # for each building name, the expressions that give how many will be in TOTAL (=all_var + already_present)
    port_vars = {} # for ports: for each port name, kth variable is 1 if the k-th port built is of this type
    for n, b in all_buildings.items():
        if not data.is_port(b):
            all_vars[n] = pulp.LpVariable(n, cat='Integer', lowBound=0)
        else:
            # orbital and planetary ports, subject to cost increase
            # Speculation for how construction points increase based on
            # https://old.reddit.com/r/EliteDangerous/comments/1jfm0y6/psa_construction_points_costs_triple_after_third/
            port_vars[n] = [ pulp.LpVariable(f"{n}_{k+1}", cat='Binary') for k in range(max_nb_ports) ]
            all_vars[n] = pulp.lpSum(port_vars[n])
        all_values[n] = all_vars[n]

    if choose_first_station:
        for i in all_categories["First Station"]:
            first_station_vars[i] = pulp.LpVariable("first station binary variable for " + i, cat="Binary")
            all_values[i] = all_values[i] + first_station_vars[i]

        T2_benefit = all_buildings[i].T2points
        if T2_benefit != "port" and T2_benefit > 0:
            initial_T2points = initial_T2points + T2_benefit * first_station_vars[i]
        T3_benefit = all_buildings[i].T3points
        if T3_benefit != "port" and T3_benefit > 0:
            initial_T3points = initial_T3points + T3_benefit * first_station_vars[i]

        if not first_station_cb_coriolis_var.get():
            prob += first_station_vars["Coriolis"] == 0, "cannot build coriolis"
        if not first_station_cb_asteroid_var.get():
            prob += first_station_vars["Asteroid_Base"] == 0, "cannot build asteroid base"
        if not first_station_cb_orbis_var.get():
            prob += first_station_vars["Orbis_or_Ocellus"] == 0, "cannot build orbis/ocellus"
        prob += pulp.lpSum(first_station_vars.values()) == 1, "only one first station"

    if not criminalinput.get():
        all_vars["Pirate_Base"].upBound = 0
        all_vars["Criminal_Outpost"].upBound = 0
        if "Criminal_Outpost" in first_station_vars:
            first_station_vars["Criminal_Outpost"].upBound = 0

    # number of slots
    usedslots = {}
    for slot in ("space", "ground"):
        usedslots[slot] = pulp.lpSum(all_vars[building_name]
                                        for building_name, building in all_buildings.items()
                                        if building.slot == slot)

    #number of slots
    prob += all_vars["Asteroid_Base"] <= asteroidslots, "asteroid slots"
    prob += usedslots["space"] <= orbitalfacilityslots, "orbital facility slots"
    prob += usedslots["ground"] <= groundfacilityslots, "ground facility slots"

    # Include already present buildings as constants in all_values[...]
    for row in building_input:
        if not row.valid:
            continue
        if row.first_station and choose_first_station:
            continue
        building_name = row.building_name
        already_present = row.already_present
        if already_present:
            if building_name != 'Let_the_program_choose_for_me':
                all_values[building_name] = all_values[building_name] + already_present

                if building_name in ["Pirate_Base", "Criminal_Outpost"] and not criminalinput.get():
                    resultlabel.config(text="Error: criminal outpost or pirate base already present, but you do not want criminal outposts to be built")
                    return False

    # Already present ports can not be built
    for port_var in port_vars.values():
        for k in range(nb_ports_already_present):
            port_var[k].upBound = 0

    # Constraints on the total number of facilities in the system
    for row in building_input:
        if not row.valid:
            continue
        building_name = row.building_name
        at_least = convert_maybe(row.at_least_var)
        if at_least is not None:
            prob += all_values[building_name] >= at_least
        at_most = convert_maybe(row.at_most_var)
        if at_most is not None:
            prob += all_values[building_name] <= at_most

    # Consistency constraints for the port variables
    for k in range(max_nb_ports):
        # Only one port can be k-th
        prob += pulp.lpSum(port_var[k] for port_var in port_vars.values()) <= 1, f"port ordering limit {k+1}"
        if k > nb_ports_already_present:
            # No k-th port if there was no (k-1)-th port
            prob += pulp.lpSum(port_var[k] for port_var in port_vars.values()) <= pulp.lpSum(port_var[k-1] for port_var in port_vars.values()), f"port ordering consistency {k+1}"

    # Computing system scores
    systemscores = {}
    for score in data.base_scores:
        if score != "construction_cost":
            systemscores[score] = pulp.lpSum(getattr(building, score) * all_values[building_name]
                                             for building_name, building in all_buildings.items())
        else:
            # Do not count already present buildings for construction cost, but count the chosen first station
            systemscores[score] = pulp.lpSum(getattr(building, score) * all_vars[building_name]
                                             for building_name, building in all_buildings.items())
            if choose_first_station:
                systemscores[score] += pulp.lpSum(getattr(all_buildings[building_name], score) * var
                                                 for building_name, var in first_station_vars.items())

    for score in data.compound_scores:
        systemscores[score] = data.compute_compound_score(score, systemscores)

    # Objective function
    if maximize in systemscores:
        prob += systemscores[maximize]
    else:
        resultlabel.config(text=f"Error: One or more inputs are blank: select an objective to optimize")
        return False

    # Constraints on minimum and maximum scores
    for score in all_scores:
        minvalue = convert_maybe(minvars[score])
        maxvalue = convert_maybe(maxvars[score])
        if minvalue is not None:
            prob += systemscores[score] >= minvalue, "minimum " + score
        if maxvalue is not None:
            prob += systemscores[score] <= maxvalue, "maximum " + score

    # Constraints on the construction points
    portsT2constructionpoints = pulp.lpSum( pulp.lpSum(port_var[k] for name, port_var in port_vars.items()
                                                       if all_buildings[name].T2points == "port") * max(3, 2*k+1)
                                            for k in range(max_nb_ports))
    portsT3constructionpoints = pulp.lpSum( pulp.lpSum(port_var[k] for name, port_var in port_vars.items()
                                                       if all_buildings[name].T3points == "port") * max(6, 6*k)
                                            for k in range(max_nb_ports))

    finalT2points = pulp.lpSum( building.T2points * all_vars[name]
                        for name, building in all_buildings.items()
                        if building.T2points != "port" ) - portsT2constructionpoints + initial_T2points
    finalT3points = pulp.lpSum( building.T3points * all_vars[name]
                        for name, building in all_buildings.items()
                        if building.T3points != "port" ) - portsT3constructionpoints + initial_T3points

    prob += finalT2points >= 0, "tier 2 construction points"
    prob += finalT3points >= 0, "tier 3 construction points"

    #sort out dependencies for facilities
    indicator_dependency_variables = {}
    ap_counter = 1
    for target_name, target_building in all_buildings.items():
        if target_building.dependencies:
            deps = tuple(target_building.dependencies)
            if  deps not in indicator_dependency_variables:
                individual_variables = [ (name, pulp.LpVariable(f"indic {name}", cat="Binary"))
                                         for name in target_building.dependencies ]
                for name, bool_var in individual_variables:
                    prob += all_values[name] <= M * bool_var
                    prob += all_values[name] >= bool_var
                if len(target_building.dependencies) == 1:
                    any_positive = individual_variables[0][1]
                else:
                    any_positive = pulp.LpVariable(f"any_positive {ap_counter}", cat="Binary")
                    ap_counter += 1
                    for name, bool_var in individual_variables:
                        prob += any_positive >= bool_var
                    prob += any_positive <= M * pulp.lpSum(bool_var for name, bool_var in individual_variables)
                indicator_dependency_variables[deps] = any_positive

            prob += all_values[target_name] <= M * indicator_dependency_variables[deps]

    # Solve the problem
    prob.solve(solver)
    if pulp.LpStatus[prob.status] == "Infeasible":
        resultlabel.config(text="Error: There is no possible system arrangement that can fit the conditions you have specified")
        return False

    clear_result()
    for building_name in all_buildings.keys():
        value = int(pulp.value(all_vars[building_name]))
        if value <= 0:
            continue
        result_row = None
        for row in reversed(building_input): # Makes sure I finish with the First Station
            if row.building_name == building_name:
                result_row = row
                break
        if result_row is None:
            add_empty_building_row(result_building=data.to_printable(building_name))
            result_row = building_input[-1]
        result_row.set_build_result(value)

    for score in all_scores:
        resultvars[score].set(int(pulp.value(systemscores[score])))

    T2points_variable_after.set(int(pulp.value(finalT2points)))
    T3points_variable_after.set(int(pulp.value(finalT3points)))

    available_slots_after_vars["space"].set(orbitalfacilityslots - int(pulp.value(usedslots["space"])))
    available_slots_after_vars["ground"].set(groundfacilityslots - int(pulp.value(usedslots["ground"])))
    available_slots_after_vars["asteroid"].set(asteroidslots - int(pulp.value(all_vars["Asteroid_Base"])))

    port_types = set()
    port_ordering_string = "Suggested port build order: "
    for port_index in range(nb_ports_already_present, max_nb_ports):
        for port_name, port_var in port_vars.items():
            if pulp.value(port_var[port_index]) >= 1:
                if port_types:
                    port_ordering_string += " --> "
                port_types.add(port_name)
                cost = max(6, 6*port_index) if all_buildings[port_name].T3points == "port" else max(3, 1+2*port_index)
                port_ordering_string += f"{port_index+1}: {data.to_printable(port_name)}"
    if len(port_types) > 1:
        printresult(port_ordering_string)
        ToolTip(resultlabel, text="If you want to force a different ordering, you can set ports as 'already built' in your favorite order.\nThe system will build facilities to provide the required construction points.\nRemember to update the number of available slots accordingly.")

    if choose_first_station:
        for fs_name, fs_var in first_station_vars.items():
            if pulp.value(fs_var) == 1:
                building_input[0].name_var.set(data.to_printable(fs_name))
                building_input[0].set_build_result(1)

    return True

def printresult(text):
    current_text = resultlabel.cget("text")
    new_text = current_text + "\n" + text
    resultlabel.config(text=new_text)

# tkinter setup
def validate_input(P):
    return P.isdigit() or P == "" or P == "-" or (P[0] == "-" and P[1:].isdigit())

def validate_input_positive(P):
    return P.isdigit() or P == ""

def on_focus_out(event, var):
    value = event.widget.get().lower()
    if value == "-":
        value = ""
    var.set(value)

def on_focus_out_integer(event, var):
    value = event.widget.get().lower()
    if value == "-" or value == "":
        value = 0
    var.set(value)

def set_style_if_negative(variable, entry, style1="danger", style2="success"):
    def callback(var, index, mode):
        val = variable.get()
        if val < 0:
            entry.config(bootstyle=style1)
        else:
            entry.config(bootstyle=style2)
    variable.trace_add("write", callback)

def get_widget_hierarchy(widget):
    #Recursively retrieves all widgets and their parents in a nested dictionary
    #Mainly for debugging
    hierarchy = {}
    for child in widget.winfo_children():
        hierarchy[child] = get_widget_hierarchy(child)
    return hierarchy

def print_hierarchy(hierarchy, level=0):
    #Prints the widget hierarchy in a readable format
    #Mainly for debugging
    for widget, children in hierarchy.items():
        print("  " * level + f"{widget.winfo_class()} - {widget.winfo_name()}")
        print_hierarchy(children, level + 1)

def remove_widgets_from_frame(frame, widget_classes=None, widget_names=None):
    for child in frame.winfo_children():
        if (widget_classes and child.winfo_class() in widget_classes) or \
           (widget_names and child.winfo_name() in widget_names):
            child.destroy()

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tkinter.Canvas(self, borderwidth=0)
        self.vscrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vscrollbar.set)
        self.vscrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        container.bind_all("<MouseWheel>", self._on_mousewheel)
        container.bind_all("<Button-4>", self._on_up)
        container.bind_all("<Button-5>", self._on_down)
        # Prevent Combo Boxes to use the wheel
        container.unbind_class("TCombobox", "<MouseWheel>")
        container.unbind_class("TCombobox", "<ButtonPress-4>")
        container.unbind_class("TCombobox", "<ButtonPress-5>")


    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.window_id, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_up(self, event):
        self.canvas.yview_scroll(-1, "units")

    def _on_down(self, event):
        self.canvas.yview_scroll(1, "units")

# Main window
root = ttk.Window(themename="darkly")
vcmd = root.register(validate_input)
vcmd_positive = root.register(validate_input_positive)
style = ttk.Style()
style.configure('.', font=("Eurostile", 12))
## style.configure('TEntry', fieldbackground=[("active", "black"), ("disabled", "red")])
style.map('success.TEntry', fieldbackground=[])
style.map('TEntry', fieldbackground=[])
root.title("Elite Dangerous colonisation planner")
root.geometry("1000x1000")
scroll_frame = ScrollableFrame(root)
scroll_frame.pack(fill="both", expand=True)

def on_dark_mode_change(*args):
    if dark_mode_var.get():
        root.style.theme_use("darkly")
    else:
        root.style.theme_use("litera")

dark_mode_var = ttk.BooleanVar(value=True)
dark_mode_button = ttk.Checkbutton(scroll_frame.scrollable_frame, text="Dark mode", variable=dark_mode_var, bootstyle="round-toggle")
dark_mode_var.trace_add("write", on_dark_mode_change)
dark_mode_button.place(x=5, y=5)

maximizeinput = ttk.StringVar()
frame = ttk.Frame(scroll_frame.scrollable_frame)
frame.pack(pady=5)
label = ttk.Label(frame, text="Select what you are trying to optimise:")
label.pack(side="left", padx=4, pady=5)
dropdown = tkinter.OptionMenu(frame, maximizeinput, *data.to_printable_list(all_scores))
dropdown.pack(side="left", padx=4, pady=5)

minvars = {}
maxvars = {}
resultvars = {}

mixed_frame = ttk.Frame(scroll_frame.scrollable_frame)
mixed_frame.pack()

constraint_frame = ttk.LabelFrame(mixed_frame, text="Sytem Stats", padding=2)
constraint_frame.pack(padx=10, pady=5, side="left", fill="y")
ttk.Label(constraint_frame, text="min. value").grid(column=1, row=1)
ttk.Label(constraint_frame, text="max. value").grid(column=2, row=1)
ttk.Label(constraint_frame, text="solution value").grid(column=3, row=1)
for i, name in enumerate(all_scores):
    minvars[name] = ttk.StringVar(value="")
    maxvars[name] = ttk.StringVar(value="")
    resultvars[name] = ttk.IntVar()

    display_name = data.to_printable(name)
    label = ttk.Label(constraint_frame, text=display_name)
    label.grid(column=0, row=2+i, pady=2, padx=2)
    entry_min = ttk.Entry(constraint_frame, textvariable=minvars[name], validate="key", validatecommand=(vcmd, "%P"), width=7, justify=ttk.RIGHT)
    entry_max = ttk.Entry(constraint_frame, textvariable=maxvars[name], validate="key", validatecommand=(vcmd, "%P"), width=7, justify=ttk.RIGHT)
    entry_min.grid(column=1, row=2+i, pady=2, padx=2)
    entry_max.grid(column=2, row=2+i, pady=2, padx=2)
    entry_min.bind("<FocusOut>", lambda event, var=minvars[name]: on_focus_out(event, var))
    entry_max.bind("<FocusOut>", lambda event, var=maxvars[name]: on_focus_out(event, var))

    result = ttk.Entry(constraint_frame, textvariable=resultvars[name], width=7, justify=ttk.RIGHT)
    result.grid(column=3, row=2+i, padx=5, pady=2)
    result.config(state="readonly")
    set_style_if_negative(resultvars[name], result)

all_slots = {"space": "Orbital", "ground": "Ground", "asteroid": "Asteroid"}
available_slots_currently_vars = {}
total_slots_currently_vars = {}
available_slots_currently_entries = {}
total_slots_currently_entries = {}
available_slots_after_vars = {}
used_slots_after_vars = {}
slot_behavior = "fix_available"

def on_toggle_slot_input(button_name):
    global slot_behavior
    slot_behavior = button_name
    if button_name == "fix_available":
        for slot in all_slots.keys():
            available_slots_currently_entries[slot].config(state="normal")
            total_slots_currently_entries[slot].config(state="readonly")
    else:
        for slot in all_slots.keys():
            available_slots_currently_entries[slot].config(state="readonly")
            total_slots_currently_entries[slot].config(state="normal")

right_frame = ttk.Frame(mixed_frame)
right_frame.pack(side="left", expand=True, fill="both")
slots_frame = ttk.LabelFrame(right_frame, text="System slots", padding=2)
slots_frame.pack(padx=10, pady=5, side="top", fill="y")
ttk.Label(slots_frame, text="currently").grid(column=1, row=0, columnspan=2)
ttk.Label(slots_frame, text="in solution").grid(column=3, row=0, columnspan=2)
slots_available_button = ttk.Button(slots_frame, text="available", bootstyle="link", command=lambda: on_toggle_slot_input("fix_available"))
slots_available_button.grid(column=1, row=1)
slots_total_button = ttk.Button(slots_frame, text="total", bootstyle="link", command=lambda: on_toggle_slot_input("fix_total"))
slots_total_button.grid(column=2, row=1)
ToolTip(slots_available_button, "Click to toggle between providing the available or total number of slots")
ToolTip(slots_total_button, "Click to toggle between providing the available or total number of slots")
ttk.Label(slots_frame, text="used").grid(column=3, row=1)
ttk.Label(slots_frame, text="available").grid(column=4, row=1)

for idx, (slot, slot_name) in enumerate(all_slots.items()):

    available_slots_currently_vars[slot] = ttk.IntVar()
    total_slots_currently_vars[slot] = ttk.IntVar()
    available_slots_after_vars[slot] = ttk.IntVar()
    used_slots_after_vars[slot] = ttk.IntVar()

    label = ttk.Label(slots_frame, text=slot_name)
    if slot_name == "Orbital":
        ToolTip(label, "Including asteroid bases (not first station) but excluding first station")
    if slot_name == "Asteroid":
        ToolTip(label, "Excluding first station")
    available = ttk.Entry(slots_frame, textvariable=available_slots_currently_vars[slot],
                          validate="key", validatecommand=(vcmd, "%P"), width=7, justify=ttk.RIGHT)
    total = ttk.Entry(slots_frame, textvariable=total_slots_currently_vars[slot],
                     width=7, state="readonly", justify=ttk.RIGHT)
    used_after = ttk.Entry(slots_frame, textvariable=used_slots_after_vars[slot],
                           width=7, state="readonly", justify=ttk.RIGHT)
    available_after = ttk.Entry(slots_frame, textvariable=available_slots_after_vars[slot],
                                width=7, state="readonly", justify=ttk.RIGHT)

    label.grid(row=2+idx, column=0, padx=2)
    available.grid(row=2+idx, column=1, padx=2, pady=2)
    total.grid(row=2+idx, column=2, padx=2, pady=2)
    used_after.grid(row=2+idx, column=3, padx=2, pady=2)
    available_after.grid(row=2+idx, column=4, padx=2, pady=2)

    available.bind("<FocusOut>", lambda event, var=available_slots_currently_vars[slot]: on_focus_out(event, var))
    available.config(bootstyle="primary")
    available_slots_after_vars[slot].trace_add("write", lambda *args, slot=slot: used_slots_after_vars[slot].set(total_slots_currently_vars[slot].get() - available_slots_after_vars[slot].get()))
    available_slots_currently_entries[slot] = available
    total_slots_currently_entries[slot] = total

criminalinput = ttk.BooleanVar()
checkbox = ttk.Checkbutton(slots_frame, text="Allow contraband stations (pirate base, criminal outpost)", variable=criminalinput)
checkbox.grid(row=3+len(all_slots), column=0, columnspan=5, padx=10, pady=10)

choose_first_station_var = ttk.BooleanVar(value=False)
first_station_cb_coriolis_var = ttk.BooleanVar(value=True)
first_station_cb_asteroid_var = ttk.BooleanVar(value=True)
first_station_cb_orbis_var = ttk.BooleanVar(value=True)
first_station_checkbox = ttk.Checkbutton(right_frame, text="Let the program choose the first Station", variable=choose_first_station_var)
first_station_frame = ttk.LabelFrame(right_frame, text="Test", labelwidget=first_station_checkbox, padding=2)
first_station_frame.pack(side="top", padx=10, pady=5, fill="both")
first_station_cbc_check = ttk.Checkbutton(first_station_frame, text="Allow Coriolis", variable=first_station_cb_coriolis_var, state="disabled")
first_station_cbab_check = ttk.Checkbutton(first_station_frame, text="Allow Asteroid Base", variable=first_station_cb_asteroid_var, state="disabled")
first_station_cbo_check = ttk.Checkbutton(first_station_frame, text="Allow Orbis", variable=first_station_cb_orbis_var, state="disabled")
first_station_cbc_check.pack(side="left", padx=4, pady=2)
first_station_cbab_check.pack(side="left", padx=4, pady=2)
first_station_cbo_check.pack(side="left", padx=4, pady=2)

def on_first_station_box(*args):
    checkbox_state = "normal" if choose_first_station_var.get() else "disabled"
    for w in [first_station_cbc_check, first_station_cbab_check, first_station_cbo_check]:
        w.config(state=checkbox_state)
    if choose_first_station_var.get():
        building_input[0].building_choice.config(state="disabled")
        building_input[0].name_var.set("Let the program choose for me")
        building_input[0].already_present_var.set(0)
        if len(building_input) == 1:
            add_empty_building_row()
        for row in building_input[1:]:
            row.already_present_entry.config(state="readonly")
            row.already_present_var.set(0)
    else:
        building_input[0].building_choice.config(state="readonly")
        for row in building_input[1:]:
            row.already_present_entry.config(state="normal")

choose_first_station_var.trace_add("write", on_first_station_box)

construction_points_frame = ttk.LabelFrame(right_frame, text="Construction points", padding=2)
construction_points_frame.pack(side="top", padx=10, pady=5, fill="both")
ttk.Label(construction_points_frame, text="currently").grid(row=0, column=1)
ttk.Label(construction_points_frame, text="in solution").grid(row=0, column=2)

T2points_variable = ttk.IntVar()
T2points_variable_after = ttk.IntVar()
label = ttk.Label(construction_points_frame, text="T2 points")
T2points_entry = ttk.Entry(construction_points_frame, textvariable=T2points_variable,
                           validate="key", validatecommand=(vcmd, "%P"), width=10, justify=ttk.RIGHT, state="readonly")
T2points_entry_after = ttk.Entry(construction_points_frame, textvariable=T2points_variable_after,
                                 width=10, justify=ttk.RIGHT, state="readonly")
label.grid(row=1, column=0, padx=2, pady=2)
T2points_entry.grid(row=1, column=1, padx=2, pady=2)
T2points_entry_after.grid(row=1, column=2, padx=2, pady=2)

T3points_variable = ttk.IntVar()
T3points_variable_after = ttk.IntVar()
label = ttk.Label(construction_points_frame, text="T3 points")
T3points_entry = ttk.Entry(construction_points_frame, textvariable=T3points_variable,
                           validate="key", validatecommand=(vcmd, "%P"), width=10, justify=ttk.RIGHT, state="readonly")
T3points_entry_after = ttk.Entry(construction_points_frame, textvariable=T3points_variable_after,
                                 width=10, justify=ttk.RIGHT, state="readonly")
label.grid(row=2, column=0, padx=2, pady=2)
T3points_entry.grid(row=2, column=1, padx=2, pady=2)
T3points_entry_after.grid(row=2, column=2, padx=2, pady=2)

def on_auto_construction_points(*args):
    if auto_construction_points.get():
        update_values_from_building_input()
        T2points_entry.config(state="readonly")
        T3points_entry.config(state="readonly")
    else:
        T2points_entry.config(state=ttk.NORMAL)
        T3points_entry.config(state=ttk.NORMAL)

auto_construction_points = ttk.BooleanVar(value=True)
construction_points_checkbox = ttk.Checkbutton(construction_points_frame, text="Compute automatically from already built facilities", variable=auto_construction_points)
construction_points_checkbox.grid(row=3, column=0, columnspan=3, pady=5, padx=10)
auto_construction_points.trace_add("write", on_auto_construction_points)


def on_solve():
    res = solve()
    if res and building_input[-1].valid:
        add_empty_building_row()

def on_clear_button():
    clear_result()
    add_empty_building_row()

button_frame = ttk.Frame(scroll_frame.scrollable_frame)
solve_button = ttk.Button(button_frame, text="Solve for a system", command=on_solve)
solve_button.pack(padx=5, side="left")
clear_button = ttk.Button(button_frame, text="Clear Result", command=on_clear_button)
clear_button.pack(padx=5, side="left")
button_frame.pack(pady=7)


building_frame = ttk.Frame(scroll_frame.scrollable_frame)
building_frame.pack(padx=10, pady=5)

header = [ ttk.Label(building_frame, text="Category", wraplength=150, anchor=ttk.N),
           ttk.Label(building_frame, text="Building", wraplength=250, anchor=ttk.N),
           ttk.Label(building_frame, text="Already built", wraplength=70, anchor=ttk.N),
           ttk.Label(building_frame, text="Total at least", wraplength=70, anchor=ttk.N),
           ttk.Label(building_frame, text="Total at most", wraplength=70, anchor=ttk.N),
           ttk.Label(building_frame, text="To build", wraplength=70, anchor=ttk.N),
           ttk.Label(building_frame, text="Total", wraplength=70, anchor=ttk.N)
          ]
cbclabel = ttk.Label(building_frame, text="", wraplength=150, anchor=ttk.N)
cbablabel = ttk.Label(building_frame, text="", wraplength=150, anchor=ttk.N)
cbolabel = ttk.Label(building_frame, text="", wraplength=150, anchor=ttk.N)
header += [cbclabel, cbablabel, cbolabel]
for i, label in enumerate(header):
    label.grid(row=0, column=i)

building_input = []
class Building_Row:
    def __init__(self, firststation=False, result_building=None):
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
            self.category_choice = ttk.Label(building_frame, text="First Station", width=15)
            values.append("Let the program choose for me")
        else:
            self.category_var = ttk.StringVar(value="All" if result_building is None else "Result")
            self.category_choice = ttk.Combobox(building_frame, textvariable=self.category_var,
                                                width=15, state="readonly", values=list(all_categories.keys()))
            self.category_var.trace_add("write", self.on_category_choice)

        self.building_choice = ttk.Combobox(building_frame, textvariable=self.name_var, width=25, state="readonly",
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

        self.to_build_var.trace_add("write", lambda v, i, c: self.total_var.set(self.to_build_var.get() + self.already_present_var.get()))
        self.name_var.trace_add("write", self.on_choice)
        self.already_present_var.trace_add("write", self.on_set_already_built)

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
                choose_first_station_var.set(True)
                self.already_present_var.set(0)
            if self.first_station and not choose_first_station_var.get():
                self.already_present_var.set(1)
            if self is building_input[-1]:
                add_empty_building_row()
                if self.delete_button is None and not self.first_station:
                    self.create_delete_button()
                    self.delete_button.grid(row=self.index, column=7)

    def on_set_already_built(self, *_args):
        update_values_from_building_input()

    def delete(self):
        for w in self.widgets:
            w.destroy()

    def create_delete_button(self):
        self.delete_button = ttk.Button(building_frame, text="X",
                                        width=1, command=self.on_delete, bootstyle=("outline", "secondary"))
        self.widgets.append(self.delete_button)
                    
    def on_delete(self):
        idx = building_input.index(self)
        self.delete()
        del building_input[idx]
        update_values_from_building_input()
        for i, row in enumerate(building_input):
            row.pack(i+1)

    def make_var_and_entry(self, modifiable=True, width=7, **kwargs):
        variable = ttk.StringVar()
        entry = ttk.Entry(building_frame, textvariable=variable,
                          validate="key", validatecommand=(vcmd, "%P"),
                          width=width, justify=ttk.RIGHT, **kwargs)
        if modifiable:
            entry.bind("<FocusOut>", lambda event, var=variable: on_focus_out(event, var))
        else:
            entry.config(state="readonly")
        return (variable, entry)

    def make_int_var_and_entry(self, modifiable=True, width=7, **kwargs):
        variable = ttk.IntVar()
        entry = ttk.Entry(building_frame, textvariable=variable,
                          validate="key", validatecommand=(vcmd_positive, "%P"),
                          width=width, justify=ttk.RIGHT, **kwargs)
        if modifiable:
            entry.bind("<FocusOut>", lambda event, var=variable: on_focus_out_integer(event, var))
        else:
            entry.config(state="readonly")
        return (variable, entry)

def add_empty_building_row(**kwargs):
    row = Building_Row(**kwargs)
    if choose_first_station_var.get():
        row.already_present_entry.config(state="readonly")
    building_input.append(row)
    row.pack(len(building_input) + 1)
    return row

def clear_result():
    global building_input
    resultlabel.config(text="")
    for var in available_slots_after_vars.values():
        var.set(0)
    for var in used_slots_after_vars.values():
        var.set(0)
    T2points_variable_after.set(0)
    T3points_variable_after.set(0)
    for score in all_scores:
        resultvars[score].set(0)

    if choose_first_station_var.get():
        building_input[0].name_var.set("Let the program choose for me")
    for row in building_input:
        if row.is_result:
            row.delete()
        else:
            row.remove_result()
    building_input = [ row for row in building_input if not row.is_result ]
    for i, row in enumerate(building_input):
        row.pack(i+1)

add_empty_building_row(firststation=True)

def update_values_from_building_input():
    T2points = 0
    T3points = 0
    number_of_ports = 0
    slots = {name: 0 for name in available_slots_currently_vars.keys() }
    for row in building_input:
        if row.valid:
            building = all_buildings[row.building_name]
            nb_present = row.already_present

            slots[building.slot] += nb_present
            if row.building_name == "Asteroid_Base":
                slots["asteroid"] += nb_present

            if row.first_station and (building.T2points != "port" and building.T2points > 0):
                T2points += building.T2points
            if row.first_station and (building.T3points != "port" and building.T3points > 0):
                T3points += building.T3points
            if not row.first_station:
                if building.T2points == "port":
                    for _ in range(nb_present):
                        T2points -= max(3, 1+2*number_of_ports)
                        number_of_ports += 1
                else:
                    T2points += nb_present * building.T2points
                if building.T3points == "port":
                    for _ in range(nb_present):
                        T3points -= max(6, 6*number_of_ports)
                        number_of_ports += 1
                else:
                    T3points += nb_present * building.T3points

    for slot, nb_used in slots.items():
        if slot_behavior == "fix_available":
            avail = get_int_var_value(available_slots_currently_vars[slot])
            total_slots_currently_vars[slot].set(avail + nb_used)
        else:
            total = get_int_var_value(total_slots_currently_vars[slot])
            available_slots_currently_vars[slot].set(total - nb_used)

    if auto_construction_points.get():
        T2points_variable.set(T2points)
        T3points_variable.set(T3points)

for var in available_slots_currently_vars.values():
        var.trace_add("write", lambda *args: update_values_from_building_input())

resultlabel = ttk.Label(scroll_frame.scrollable_frame, text="")
resultlabel.pack(pady=10)
root.mainloop()

