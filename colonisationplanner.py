import pulp
import re
import tkinter
from tkinter import ttk
import os
import sys
from collections import defaultdict

from data import all_buildings, all_scores, all_categories
import data

if getattr(sys, "frozen", False) and hasattr(sys, '_MEIPASS'):
    #I'm bundling the windows CBC solver with this .exe, so this might not work on non windows OS
    cbc_path = os.path.join(sys._MEIPASS, "cbc.exe")
    solver = pulp.COIN_CMD(path=cbc_path)
else:
    solver = None

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

    max_nb_ports = orbitalfacilityslots + groundfacilityslots

    #problem
    direction = pulp.LpMinimize if maximize == "construction_cost" else pulp.LpMaximize
    prob = pulp.LpProblem("optimal_system_colonization_layout", direction)

    #create all the variables for each of the facilities
    all_vars = {}
    port_vars = {}
    for n, b in all_buildings.items():
        if not data.is_port(b):
            all_vars[n] = pulp.LpVariable(n, cat='Integer', lowBound=0)
        else:
            # orbital and planetary ports, subject to cost increase
            # Speculation for how construction points increase based on
            # https://old.reddit.com/r/EliteDangerous/comments/1jfm0y6/psa_construction_points_costs_triple_after_third/
            # kth variable is 1 if the k-th port built is of this type
            port_vars[n] = [ pulp.LpVariable(f"{n}_{k+1}", cat='Binary') for k in range(max_nb_ports) ]
            all_vars[n] = pulp.lpSum(port_vars[n])

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

    initial_construction_cost = 0
    port_count = 0
    for row in building_input:
        if not row.valid:
            continue
        building_name = data.from_printable(row.name_var.get())
        if building_name not in all_buildings:
            printresult(f"Unknown or absent Building: '{building_name}'")
            return False
        already_present = convert_maybe(row.already_present_var)
        if already_present:
            building = all_buildings[building_name]
            if data.is_port(building) and not row.first_station:
                port_vars[building_name][port_count].lowBound = 1
                port_count += 1
            else:
                all_vars[building_name] += already_present

            initial_construction_cost += all_buildings[building_name].construction_cost * already_present
            if building_name == "Asteroid_Base" and asteroidslots <= already_present:
                resultlabel.config(text="Error: asteroid base already present, but there are not enough slots for asteroid bases available")
                return False
            if building_name in ["Pirate_Base", "Criminal_Outpost"] and not criminalinput.get():
                resultlabel.config(text="Error: criminal outpost or pirate base already present, but you do not want criminal outposts to be built")
                return False

    for row in building_input:
        if not row.valid:
            continue
        building_name = data.from_printable(row.name_var.get())
        at_least = convert_maybe(row.at_least_var)
        if at_least is not None:
            prob += all_vars[building_name] >= at_least
        at_most = convert_maybe(row.at_most_var)
        if at_most is not None:
            prob += all_vars[building_name] <= at_most

    for k in range(max_nb_ports):
        # Only one port can be k-th
        prob += pulp.lpSum(port_var[k] for port_var in port_vars.values()) <= 1, f"port ordering limit {k+1}"
        if k > 0:
            # No k-th port if there was no (k-1)-th port
            prob += pulp.lpSum(port_var[k] for port_var in port_vars.values()) <= pulp.lpSum(port_var[k-1] for port_var in port_vars.values()), f"port ordering consistency {k+1}"

    # compute system scores
    systemscores = {}
    for score in all_scores:
        systemscores[score] = pulp.lpSum(getattr(building, score) * all_vars[building_name]
                                         for building_name, building in all_buildings.items())
        if score == "construction_cost":
            systemscores[score] -= initial_construction_cost

    #objective function
    if maximize in systemscores:
        prob += systemscores[maximize]
    else:
        resultlabel.config(text=f"Error: One or more inputs are blank: unknown objective '{maximize}'")
        return False

    #minimum and maximum stats
    for score in all_scores:
        minvalue = convert_maybe(minvars[score])
        maxvalue = convert_maybe(maxvars[score])
        if minvalue is not None:
            prob += systemscores[score] >= minvalue, "minimum " + score
        if maxvalue is not None:
            prob += systemscores[score] <= maxvalue, "maximum " + score

    #construction points
    portsT2constructionpoints = pulp.lpSum( pulp.lpSum(port_var[k] for name, port_var in port_vars.items()
                                                       if all_buildings[name].T2points == "port") * max(3, 2*k+1)
                                            for k in range(max_nb_ports))
    portsT3constructionpoints = pulp.lpSum( pulp.lpSum(port_var[k] for name, port_var in port_vars.items()
                                                       if all_buildings[name].T3points == "port") * max(6, 6*k)
                                            for k in range(max_nb_ports))

    prob += pulp.lpSum( building.T2points * all_vars[name]
                        for name, building in all_buildings.items()
                        if building.T2points != "port" ) - portsT2constructionpoints >= 0, "tier 2 construction points"
    prob += pulp.lpSum( building.T3points * all_vars[name]
                        for name, building in all_buildings.items()
                        if building.T3points != "port" ) - portsT3constructionpoints >= 0, "tier 3 construction points"

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
                    prob += all_vars[name] <= M * bool_var
                    prob += all_vars[name] >= bool_var
                if len(target_building.dependencies) == 1:
                    any_positive = individual_variables[0][1]
                else:
                    any_positive = pulp.LpVariable(f"any_positive {ap_counter}", cat="Binary")
                    ap_counter += 1
                    for name, bool_var in individual_variables:
                        prob += any_positive >= bool_var
                    prob += any_positive <= M * pulp.lpSum(bool_var for name, bool_var in individual_variables)
                indicator_dependency_variables[deps] = any_positive

            prob += all_vars[target_name] <= M * indicator_dependency_variables[deps]

    #solve
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
        for row in building_input:
            if data.from_printable(row.name_var.get()) == building_name:
                result_row = row
                break
        if result_row is None:
            add_empty_building_row(result_building=data.to_printable(building_name))
            result_row = building_input[-1]
        result_row.set_build_result(value)

    for score in all_scores:
        resultvars[score].set(int(pulp.value(systemscores[score])))

    return True

def printresult(text):
    current_text = resultlabel.cget("text")
    new_text = current_text + "\n" + text
    resultlabel.config(text=new_text)
# tkinter setup
def validate_input(P):
    return P.isdigit() or P == "" or P == "-" or (P[0] == "-" and P[1:].isdigit())

def on_focus_out(event, var):
    value = event.widget.get().lower()
    if value == "-":
        value = ""
    var.set(value)

def set_color_if_negative(variable, entry, color="red"):
    original_color = entry.cget("fg")
    def callback(var, index, mode):
        val = variable.get()
        if val < 0:
            entry.config(fg=color)
        else:
            entry.config(fg=original_color)
    variable.trace_add("write", callback)

def make_var_and_entry(frame, modifiable=True, intVar=None, **kwargs):
    if intVar is None:
        intVar = not modifiable
    if intVar:
        variable = tkinter.IntVar()
    else:
        variable = tkinter.StringVar()
    entry = tkinter.Entry(frame, textvariable=variable,
                          validate="key", validatecommand=(vcmd, "%P"),
                          width=10, justify=tkinter.RIGHT, **kwargs)
    if modifiable:
        entry.bind("<FocusOut>", lambda event, var=variable: on_focus_out(event, var))
    else:
        entry.config(state="readonly")
        if intVar:
            set_color_if_negative(variable, entry)
    return (variable, entry)

# Main window
root = tkinter.Tk()
vcmd = root.register(validate_input)
root.title("Elite Dangerous colonisation planner")
root.geometry("800x1000")
maximizeinput = tkinter.StringVar()
frame = tkinter.Frame(root)
frame.pack(pady=5)
label = tkinter.Label(frame, text="Select what you are trying to optimise:", font=("calibri", 12))
label.pack(side="left")
dropdown = tkinter.OptionMenu(frame, maximizeinput, *data.to_printable_list(all_scores))
dropdown.pack(side="left")

minframes = {}
minvars = {}
maxvars = {}
resultvars = {}

constraint_frame = tkinter.Frame(root)
constraint_frame.pack(padx=10, pady=5)
tkinter.Label(constraint_frame, text="System Scores", font=("calibri", 12)).grid(column=0, columnspan=3, row=0)
tkinter.Label(constraint_frame, text="min. value", font=("calibri", 12)).grid(column=1, row=1)
tkinter.Label(constraint_frame, text="max. value", font=("calibri", 12)).grid(column=2, row=1)
tkinter.Label(constraint_frame, text="solution value", font=("calibri", 12)).grid(column=3, row=1)
for i, name in enumerate(all_scores):
    minvars[name] = tkinter.StringVar(value="")
    maxvars[name] = tkinter.StringVar(value="")
    resultvars[name] = tkinter.IntVar()

    display_name = data.to_printable(name)
    label = tkinter.Label(constraint_frame, text=display_name, font=("calibri", 12))
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
label = tkinter.Label(frame20, text="Number of available orbital facility slots (excluding already built facilities):", font=("calibri", 12))
label.pack(side="left")
entry = tkinter.Entry(frame20, textvariable=orbitalfacilityslotsinput, validate="key", validatecommand=(vcmd, "%P"),width=10)
entry.pack(side="left")
entry.bind("<FocusOut>", lambda event, var=orbitalfacilityslotsinput: on_focus_out(event, var))
frame21 = tkinter.Frame(root)
frame21.pack(pady=5)
label = tkinter.Label(frame21, text="Number of available ground facility slots (excluding already built facilities):", font=("calibri", 12))
label.pack(side="left")
entry = tkinter.Entry(frame21, textvariable=groundfacilityslotsinput, validate="key", validatecommand=(vcmd, "%P"),width=10)
entry.pack(side="left")
entry.bind("<FocusOut>", lambda event, var=groundfacilityslotsinput: on_focus_out(event, var))
frame22 = tkinter.Frame(root)
frame22.pack(pady=5)
label = tkinter.Label(frame22, text="Number of available slots for asteroid bases (excluding already built asteroid bases):", font=("calibri", 12))
label.pack(side="left")
entry = tkinter.Entry(frame22, textvariable=asteroidslotsinput, validate="key", validatecommand=(vcmd, "%P"),width=10)
entry.pack(side="left")
entry.bind("<FocusOut>", lambda event, var=asteroidslotsinput: on_focus_out(event, var))
criminalinput = tkinter.BooleanVar()
checkbox = tkinter.Checkbutton(root, text="Are you okay with contraband stations being built in your system? (pirate base, criminal outpost)", variable=criminalinput, font=("calibri", 12))
checkbox.pack(pady=5)


# firststationinput = tkinter.StringVar()
# frame23 = tkinter.Frame(root)
# frame23.pack(pady=5)
# label = tkinter.Label(frame23, text="Select your first station:", font=("calibri", 12))
# label.pack(side="left")
# dropdown = tkinter.OptionMenu(frame23, firststationinput, *data.to_printable_list(all_categories["First Station"]))
# dropdown.pack(side="left")

def on_solve():
    res = solve()
    if res:
        add_empty_building_row()

button = tkinter.Button(root, text="Solve for a system", command=on_solve)
button.pack(pady=7)


building_frame = tkinter.Frame(root)
building_frame.pack(padx=10, pady=5)

header = [ tkinter.Label(building_frame, text="Category"),
           tkinter.Label(building_frame, text="Building"),
           tkinter.Label(building_frame, text="Already built"),
           tkinter.Label(building_frame, text="Total at least"),
           tkinter.Label(building_frame, text="Total at most"),
           tkinter.Label(building_frame, text="To build"),
           tkinter.Label(building_frame, text="Total")
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
            self.category_choice = tkinter.Label(building_frame, text="First Station", width=15, font=("calibri", 12))
        else:
            self.category_var = tkinter.StringVar(value="All" if result_building is None else "Result")
            self.category_choice = ttk.Combobox(building_frame, textvariable=self.category_var,
                                                width=15, state="readonly", values=list(all_categories.keys()))
            self.category_var.trace_add("write", self.on_category_choice)

        self.building_choice = ttk.Combobox(building_frame, textvariable=self.name_var, width=25, state="readonly",
                                            values=values)
        self.already_present_var, self.already_present_entry = make_var_and_entry(building_frame, intVar=True)
        self.at_least_var, self.at_least_entry = make_var_and_entry(building_frame )
        self.at_most_var, self.at_most_entry = make_var_and_entry(building_frame)
        self.to_build_var, self.to_build_entry = make_var_and_entry(building_frame, modifiable=False)
        self.total_var, self.total_entry = make_var_and_entry(building_frame, modifiable=False)
        self.total_var.trace_add("write", lambda v, i, c: self.to_build_var.set(self.total_var.get() - self.already_present_var.get()))
        self.name_var.trace_add("write", self.on_choice)
        self.index = len(building_input) + 1

        if firststation:
            self.already_present_entry.config(state="readonly")

        if result_building:
            self.name_var.set(result_building)
            self.valid = True
            # self.building_choice.config(state="disabled")
            # self.already_present_entry.config(state="readonly")

    def pack(self, index):
        self.category_choice.grid(row=index, column=0)
        self.building_choice.grid(row=index, column=1)
        self.already_present_entry.grid(row=index, column=2)
        self.at_least_entry.grid(row=index, column=3)
        self.at_most_entry.grid(row=index, column=4)
        self.to_build_entry.grid(row=index, column=5)
        self.total_entry.grid(row=index, column=6)

    def set_build_result(self, value):
        self.total_var.set(value)
        if self.to_build_var.get() > 0:
            self.to_build_entry.config(fg="green")

    def on_category_choice(self, var, index, mode):
        category = self.category_var.get()
        self.building_choice.config(values=data.to_printable_list(all_categories[category]))
        self.name_var.set("Pick a facility")
        self.valid = False

    def on_choice(self, var, index, mode):
        if self.name_var.get() in self.building_choice.cget("values"):
            self.valid = True
            if self.index == 1:
                self.already_present_var.set(1)
            else:
                self.already_present_entry.focus()
            if self.index == len(building_input):
                add_empty_building_row()

    def delete(self):
        self.category_choice.destroy()
        self.building_choice.destroy()
        self.already_present_entry.destroy()
        self.at_least_entry.destroy()
        self.at_most_entry.destroy()
        self.to_build_entry.destroy()
        self.total_entry.destroy()

    @property
    def is_result(self):
        return self.already_present_var.get() == 0 and self.at_least_var.get() == "" and self.at_most_var.get() == ""

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
            row.total_var.set(row.already_present_var.get())
            row.to_build_entry.config(fg="black")
    building_input = [ row for row in building_input if not row.is_result ]
    for i, row in enumerate(building_input):
        row.pack(i+1)

add_empty_building_row(firststation=True)

resultlabel = tkinter.Label(root, text="", font=("calibri", 12))
resultlabel.pack(pady=10)
root.mainloop()

