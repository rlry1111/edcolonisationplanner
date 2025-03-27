import re
import os
import sys
from collections import defaultdict

import pulp

import tkinter
from tkinter import ttk
import ttkbootstrap
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

def solve():
    #requirements
    resultlabel.config(text="")
    M = 10000

    # Get data from the Entry widgets
    orbitalfacilityslots = orbitalfacilityslotsinput.get()
    groundfacilityslots = groundfacilityslotsinput.get()
    asteroidslots = asteroidslotsinput.get()
    maximize = data.from_printable(maximizeinput.get())
    initial_T2points = T2points_variable.get()
    initial_T3points = T3points_variable.get()

    nb_ports_already_present = sum(row.already_present for row in building_input if row.is_port)
    max_nb_ports = orbitalfacilityslots + groundfacilityslots + nb_ports_already_present

    #problem
    direction = pulp.LpMinimize if maximize == "construction_cost" else pulp.LpMaximize
    prob = pulp.LpProblem("optimal_system_colonization_layout", direction)

    #create all the variables for each of the facilities
    all_vars = {}   # for each building name, the variables that decide how many will be BUILT
    all_values = {} # for each building name, the expressions that give how many will be in TOTAL (=all_var + already_present)
    port_vars = {}  # for ports: for each port name, kth variable is 1 if the k-th port built is of this type
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

    if not criminalinput.get():
        all_vars["Pirate_Base"].upBound = 0
        all_vars["Criminal_Outpost"].upBound = 0

    #number of slots
    prob += all_vars["Asteroid_Base"] <= asteroidslots, "asteroid slots"
    prob += pulp.lpSum(all_vars[building_name]
                       for building_name, building in all_buildings.items()
                       if building.slot == "space") <= orbitalfacilityslots, "orbital facility slots"
    prob += pulp.lpSum(all_vars[building_name]
                       for building_name, building in all_buildings.items()
                       if building.slot == "ground") <= groundfacilityslots, "ground facility slots"

    # Include already present buildings as constants in all_values[...]
    for row in building_input:
        if not row.valid:
            continue
        building_name = row.building_name
        already_present = row.already_present
        if already_present:
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
    for score in all_scores:
        if score != "construction_cost":
            systemscores[score] = pulp.lpSum(getattr(building, score) * all_values[building_name]
                                             for building_name, building in all_buildings.items())
        else:
            # Do not count already present buildings for construction cost
            systemscores[score] = pulp.lpSum(getattr(building, score) * all_vars[building_name]
                                             for building_name, building in all_buildings.items())

    # Objective function
    if maximize in systemscores:
        prob += systemscores[maximize]
    else:
        resultlabel.config(text=f"Error: One or more inputs are blank: unknown objective '{maximize}'")
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

    prob += pulp.lpSum( building.T2points * all_vars[name]
                        for name, building in all_buildings.items()
                        if building.T2points != "port" ) - portsT2constructionpoints + initial_T2points >= 0, "tier 2 construction points"
    prob += pulp.lpSum( building.T3points * all_vars[name]
                        for name, building in all_buildings.items()
                        if building.T3points != "port" ) - portsT3constructionpoints + initial_T3points >= 0, "tier 3 construction points"

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

    nb_ports = 0
    port_ordering_string = "Suggested port build order: "
    for port_index in range(nb_ports_already_present, max_nb_ports):
        for port_name, port_var in port_vars.items():
            if pulp.value(port_var[port_index]) >= 1:
                if nb_ports > 0:
                    port_ordering_string += " --> "
                nb_ports += 1
                cost = max(6, 6*port_index) if all_buildings[port_name].T3points == "port" else max(3, 1+2*port_index)
                port_ordering_string += f"{port_index+1}: {data.to_printable(port_name)}"
    if nb_ports > 1:
        printresult(port_ordering_string)

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

def set_color_if_negative(variable, entry, color="red", color2="green"):
    def callback(var, index, mode):
        val = variable.get()
        if val < 0:
            entry.config(fg=color)
        else:
            entry.config(fg=color2)
    variable.trace_add("write", callback)

# Main window
root = ttkbootstrap.Window(themename="darkly")
vcmd = root.register(validate_input)
vcmd_positive = root.register(validate_input_positive)
root.title("Elite Dangerous colonisation planner")
root.geometry("1000x1000")
maximizeinput = tkinter.StringVar()
frame = tkinter.Frame(root)
frame.pack(pady=5)
label = tkinter.Label(frame, text="Select what you are trying to optimise:", font=("Eurostile", 12))
label.pack(side="left")
dropdown = tkinter.OptionMenu(frame, maximizeinput, *data.to_printable_list(all_scores))
dropdown.pack(side="left")
dropdown.config(font=("Eurostile", 10))

minframes = {}
minvars = {}
maxvars = {}
resultvars = {}

constraint_frame = tkinter.Frame(root)
constraint_frame.pack(padx=10, pady=5)
tkinter.Label(constraint_frame, text="System Scores", font=("Eurostile", 12)).grid(column=0, columnspan=3, row=0)
tkinter.Label(constraint_frame, text="min. value", font=("Eurostile", 12)).grid(column=1, row=1)
tkinter.Label(constraint_frame, text="max. value", font=("Eurostile", 12)).grid(column=2, row=1)
tkinter.Label(constraint_frame, text="solution value", font=("Eurostile", 12)).grid(column=3, row=1)
for i, name in enumerate(all_scores):
    minvars[name] = tkinter.StringVar(value="")
    maxvars[name] = tkinter.StringVar(value="")
    resultvars[name] = tkinter.IntVar()

    display_name = data.to_printable(name)
    label = tkinter.Label(constraint_frame, text=display_name, font=("Eurostile", 12))
    label.grid(column=0, row=2+i)
    entry_min = tkinter.Entry(constraint_frame, textvariable=minvars[name], validate="key", validatecommand=(vcmd, "%P"), width=10, justify=tkinter.RIGHT)
    entry_max = tkinter.Entry(constraint_frame, textvariable=maxvars[name], validate="key", validatecommand=(vcmd, "%P"), width=10, justify=tkinter.RIGHT)
    entry_min.grid(column=1, row=2+i)
    entry_max.grid(column=2, row=2+i)
    entry_min.bind("<FocusOut>", lambda event, var=minvars[name]: on_focus_out(event, var))
    entry_max.bind("<FocusOut>", lambda event, var=maxvars[name]: on_focus_out(event, var))

    result = tkinter.Entry(constraint_frame, textvariable=resultvars[name], width=10, justify=tkinter.RIGHT)
    result.grid(column=3, row=2+i, padx=5)
    result.config(state="readonly")
    set_color_if_negative(resultvars[name], result)

orbitalfacilityslotsinput = tkinter.IntVar()
groundfacilityslotsinput = tkinter.IntVar()
asteroidslotsinput = tkinter.IntVar()
frame20 = tkinter.Frame(root)
frame20.pack(pady=5)
label = tkinter.Label(frame20, text="Number of available orbital facility slots (excluding already built facilities):", font=("Eurostile", 12))
label.pack(side="left")
entry = tkinter.Entry(frame20, textvariable=orbitalfacilityslotsinput, validate="key", validatecommand=(vcmd, "%P"),width=10)
entry.pack(side="left")
entry.bind("<FocusOut>", lambda event, var=orbitalfacilityslotsinput: on_focus_out(event, var))
frame21 = tkinter.Frame(root)
frame21.pack(pady=5)
label = tkinter.Label(frame21, text="Number of available ground facility slots (excluding already built facilities):", font=("Eurostile", 12))
label.pack(side="left")
entry = tkinter.Entry(frame21, textvariable=groundfacilityslotsinput, validate="key", validatecommand=(vcmd, "%P"),width=10)
entry.pack(side="left")
entry.bind("<FocusOut>", lambda event, var=groundfacilityslotsinput: on_focus_out(event, var))
frame22 = tkinter.Frame(root)
frame22.pack(pady=5)
label = tkinter.Label(frame22, text="Number of available slots for asteroid bases (excluding already built asteroid bases):", font=("Eurostile", 12))
label.pack(side="left")
entry = tkinter.Entry(frame22, textvariable=asteroidslotsinput, validate="key", validatecommand=(vcmd, "%P"),width=10)
entry.pack(side="left")
entry.bind("<FocusOut>", lambda event, var=asteroidslotsinput: on_focus_out(event, var))

T2points_variable = tkinter.IntVar()
frame23 = tkinter.Frame(root)
frame23.pack(pady=5)
label = tkinter.Label(frame23, text="Number of available T2 construction points:", font=("Eurostile", 12))
label.pack(side="left")
T2points_entry = tkinter.Entry(frame23, textvariable=T2points_variable, validate="key", validatecommand=(vcmd, "%P"),width=10)
T2points_entry.pack(side="left")

T3points_variable = tkinter.IntVar()
frame24 = tkinter.Frame(root)
frame24.pack(pady=5)
label = tkinter.Label(frame24, text="Number of available T3 construction points:", font=("Eurostile", 12))
label.pack(side="left")
T3points_entry = tkinter.Entry(frame24, textvariable=T3points_variable, validate="key", validatecommand=(vcmd, "%P"),width=10)
T3points_entry.pack(side="left")

T2points_entry.config(state="readonly")
T3points_entry.config(state="readonly")

def on_auto_construction_points(*args):
    update_values_from_building_input()
    if auto_construction_points.get():
        T2points_entry.config(state="readonly")
        T3points_entry.config(state="readonly")
    else:
        T2points_entry.config(state=tkinter.NORMAL)
        T3points_entry.config(state=tkinter.NORMAL)

auto_construction_points = tkinter.BooleanVar(value=True)
construction_points_checkbox = tkinter.Checkbutton(root, text="Automatically compute T2 / T3 construction points  from already built facilities", variable=auto_construction_points, font=("Eurostile", 12))
construction_points_checkbox.pack(pady=5)
auto_construction_points.trace_add("write", on_auto_construction_points)


criminalinput = tkinter.BooleanVar()
checkbox = tkinter.Checkbutton(root, text="Are you okay with contraband stations being built in your system? (pirate base, criminal outpost)", variable=criminalinput, font=("Eurostile", 12))
checkbox.pack(pady=5)

def on_solve():
    res = solve()
    if res:
        add_empty_building_row()

button = tkinter.Button(root, text="Solve for a system", command=on_solve, font=("Eurostile", 12))
button.pack(pady=7)


building_frame = tkinter.Frame(root)
building_frame.pack(padx=10, pady=5)

header = [ tkinter.Message(building_frame, text="Category", width=150, anchor="n", font=("Eurostile", 12)),
           tkinter.Message(building_frame, text="Building", width=250, anchor="n", font=("Eurostile", 12)),
           tkinter.Message(building_frame, text="Already built", width=70, anchor="n", font=("Eurostile", 12)),
           tkinter.Message(building_frame, text="Total at least", width=70, anchor="n", font=("Eurostile", 12)),
           tkinter.Message(building_frame, text="Total at most", width=70, anchor="n", font=("Eurostile", 12)),
           tkinter.Message(building_frame, text="To build", width=70, anchor="n", font=("Eurostile", 12)),
           tkinter.Message(building_frame, text="Total", width=70, anchor="n", font=("Eurostile", 12))
          ]
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
        self.name_var = tkinter.StringVar(value=init_text)
        self.valid = False
        self.first_station = firststation

        if firststation:
            self.category_choice = tkinter.Label(building_frame, text="First Station", width=15, font=("Eurostile", 12))
        else:
            self.category_var = tkinter.StringVar(value="All" if result_building is None else "Result")
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
        if result_building:
            self.create_delete_button()

        self.to_build_var.trace_add("write", lambda v, i, c: self.total_var.set(self.to_build_var.get() + self.already_present_var.get()))
        self.name_var.trace_add("write", self.on_choice)
        self.already_present_var.trace_add("write", self.on_set_already_built)

        if firststation:
            self.already_present_entry.config(state="readonly")

        if result_building:
            self.name_var.set(result_building)
            self.valid = True
            # self.building_choice.config(state="disabled")
            # self.already_present_entry.config(state="readonly")

    @property
    def is_result(self):
        return self.already_present == 0 and self.at_least_var.get() == "" and self.at_most_var.get() == ""
    @property
    def is_port(self):
        building_name = data.from_printable(self.name_var.get())
        return not self.first_station and self.valid and data.is_port(all_buildings[building_name])
    @property
    def building_name(self):
        return data.from_printable(self.name_var.get())
    @property
    def already_present(self):
        try:
            return self.already_present_var.get()
        except tkinter.TclError:
            return 0

    def pack(self, index=None):
        if index is None:
            index = self.index
        else:
            self.index = index
        self.category_choice.grid(row=index, column=0)
        self.building_choice.grid(row=index, column=1)
        self.already_present_entry.grid(row=index, column=2)
        self.at_least_entry.grid(row=index, column=3)
        self.at_most_entry.grid(row=index, column=4)
        self.to_build_entry.grid(row=index, column=5)
        self.total_entry.grid(row=index, column=6)
        if self.delete_button:
            self.delete_button.grid(row=index, column=7)

    def set_build_result(self, value):
        self.to_build_var.set(value)
        if value > 0:
            self.to_build_entry.config(fg="green")

    def remove_result(self):
        self.to_build_var.set(0)
        self.to_build_entry.config(fg="black")

    def on_category_choice(self, var, index, mode):
        category = self.category_var.get()
        self.building_choice.config(values=data.to_printable_list(all_categories[category]))
        self.name_var.set("Pick a facility")
        self.valid = False

    def on_choice(self, var, index, mode):
        if self.name_var.get() in self.building_choice.cget("values"):
            self.valid = True
            if self.first_station:
                self.already_present_var.set(1)
            update_values_from_building_input()
            if self is building_input[-1]:
                add_empty_building_row()
                if self.delete_button is None and not self.first_station:
                    self.create_delete_button()
                    self.delete_button.grid(row=self.index, column=7)

    def on_set_already_built(self, *_args):
        update_values_from_building_input()

    def delete(self):
        self.category_choice.destroy()
        self.building_choice.destroy()
        self.already_present_entry.destroy()
        self.at_least_entry.destroy()
        self.at_most_entry.destroy()
        self.to_build_entry.destroy()
        self.total_entry.destroy()
        if self.delete_button:
            self.delete_button.destroy()

    def create_delete_button(self):
        self.delete_button = tkinter.Button(building_frame, text="X", padx=2, pady=0,
                                            width=1, command=self.on_delete)

    def on_delete(self):
        idx = building_input.index(self)
        self.delete()
        del building_input[idx]
        update_values_from_building_input()
        for i, row in enumerate(building_input):
            row.pack(i+1)

    def make_var_and_entry(self, modifiable=True, width=7, **kwargs):
        variable = tkinter.StringVar()
        entry = tkinter.Entry(building_frame, textvariable=variable,
                              validate="key", validatecommand=(vcmd, "%P"),
                              width=width, justify=tkinter.RIGHT, **kwargs)
        if modifiable:
            entry.bind("<FocusOut>", lambda event, var=variable: on_focus_out(event, var))
        else:
            entry.config(state="readonly")
        return (variable, entry)

    def make_int_var_and_entry(self, modifiable=True, width=7, **kwargs):
        variable = tkinter.IntVar()
        entry = tkinter.Entry(building_frame, textvariable=variable,
                              validate="key", validatecommand=(vcmd_positive, "%P"),
                              width=width, justify=tkinter.RIGHT, **kwargs)
        if modifiable:
            entry.bind("<FocusOut>", lambda event, var=variable: on_focus_out_integer(event, var))
        else:
            entry.config(state="readonly")
        return (variable, entry)

def add_empty_building_row(**kwargs):
    row = Building_Row(**kwargs)
    building_input.append(row)
    row.pack(len(building_input) + 1)
    return row

def clear_result():
    global building_input
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
    # For now only need to update construction points
    if auto_construction_points.get():
        T2points = 0
        T3points = 0
        number_of_ports = 0
        for row in building_input:
            if row.valid:
                building = all_buildings[row.building_name]
                nb_present = row.already_present

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
        T2points_variable.set(T2points)
        T3points_variable.set(T3points)

resultlabel = tkinter.Label(root, text="", font=("Eurostile", 12))
resultlabel.pack(pady=10)
root.mainloop()

## TODOs:
## "Clear result" button
## Give output ordering
