import pulp
import re
import tkinter
import os
import sys

from data import all_buildings, all_scores, all_categories
import data

if getattr(sys, "frozen", False) and hasattr(sys, '_MEIPASS'):
    #I'm bundling the windows CBC solver with this .exe, so this might not work on non windows OS
    cbc_path = os.path.join(sys._MEIPASS, "cbc.exe")
    solver = pulp.COIN_CMD(path=cbc_path)
else:
    solver = None

def convert_maybe(value, default=None):
    if value != "": return int(value)
    return default

def solve():
    #requirements
    resultlabel.config(text="")
    M = 10000
    max_nb_ports = 20

    # Get data from the Entry widgets
    firststation = data.from_printable(firststationinput.get())
    if firststation not in all_buildings:
        printresult(f"Unknown or absent First Station: '{firststation}'")
        return
    initial_construction_cost = all_buildings[firststation].construction_cost
    orbitalfacilityslots = orbitalfacilityslotsinput.get()
    groundfacilityslots = groundfacilityslotsinput.get()
    asteroidslots = asteroidslotsinput.get()
    maximize = data.from_printable(maximizeinput.get())

    if firststation == "Asteroid_Base" and asteroidslots <= 0:
        resultlabel.config(text="Error: your starting station is an asteroid base but there are no slots for asteroid bases to be built")
        return None
    if firststation in ["Pirate_Base", "Criminal_Outpost"] and not criminalinput.get():
        resultlabel.config(text="Error: your starting station is a criminal outpost but you do not want criminal outposts to be built")
        return None

    #problem
    direction = pulp.LpMinimize if maximize == "construction_cost" else pulp.LpMaximize
    prob = pulp.LpProblem("optimal_system_colonization_layout", direction)

    #create all the variables for each of the facilities
    all_vars = {}
    port_vars = {}
    for n, b in all_buildings.items():
        lower_bound = 1 if firststation == n else 0
        if b.T2points != "port" and b.T3points != "port":
            all_vars[n] = pulp.LpVariable(n, cat='Integer', lowBound=lower_bound)
        else:
            # orbital and planetary ports, subject to cost increase
            # Speculation for how construction points increase based on
            # https://old.reddit.com/r/EliteDangerous/comments/1jfm0y6/psa_construction_points_costs_triple_after_third/
            # kth variable is 1 if the k-th port built is of this type
            port_vars[n] = [ pulp.LpVariable(f"{n}_{k+1}", cat='Binary') for k in range(max_nb_ports) ]
            all_vars[n] = pulp.lpSum(port_vars[n]) + lower_bound

    for k in range(max_nb_ports):
        # Only one port can be k-th
        prob += pulp.lpSum(port_var[k] for port_var in port_vars.values()) <= 1, f"port ordering limit {k+1}"
        if k > 0:
            # No k-th port if there was no (k-1)-th port
            prob += pulp.lpSum(port_var[k] for port_var in port_vars.values()) <= pulp.lpSum(port_var[k-1] for port_var in port_vars.values()), f"port ordering consistency {k+1}"

    if not criminalinput.get():
        all_vars["Pirate_Base"].upBound = 0
        all_vars["Criminal_Outpost"].upBound = 0

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
        return None

    #minimum and maximum stats
    for score in all_scores:
        minvalue = convert_maybe(minvars[score].get())
        maxvalue = convert_maybe(maxvars[score].get())
        if minvalue is not None:
            prob += systemscores[score] >= minvalue, "minimum " + score
        if maxvalue is not None:
            prob += systemscores[score] <= maxvalue, "maximum " + score

    #number of slots
    prob += all_vars["Asteroid_Base"] <= asteroidslots, "asteroid slots"
    prob += pulp.lpSum(all_vars[building_name]
                       for building_name, building in all_buildings.items()
                       if building.slot == "space") + 1 <= orbitalfacilityslots, "orbital facility slots"
    prob += pulp.lpSum(all_vars[building_name]
                       for building_name, building in all_buildings.items()
                       if building.slot == "ground") <= groundfacilityslots, "ground facility slots"

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
        return None
    printresult("Here is what you need to build in the system (including the first station) to achieve these requirements: ")

    def print_var_result(variable):
        value = int(variable.varValue)
        if value > 0:
            printresult(f"{data.to_printable(variable.name)} = {value}")

    # If first station is a port, print it as index 0
    if firststation in port_vars:
        printresult(f"{firststation} 0 = 1")

    for building_name in all_buildings.keys():
        if building_name in port_vars:
            for var in port_vars[building_name]:
                print_var_result(var)
        else:
            print_var_result(all_vars[building_name])

    for score in all_scores:
        resultvars[score].set(int(pulp.value(systemscores[score])))

def printresult(text):
    current_text = resultlabel.cget("text")
    new_text = current_text + "\n" + text
    resultlabel.config(text=new_text)
# tkinter setup
def validate_input(P):
    return P.isdigit() or P == "" or P == "-" or (P[0] == "-" and P[1:].isdigit())

def on_focus_out(event, var):
    value = event.widget.get().lower()
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
tkinter.Label(constraint_frame, text="System Scores",font=("calibri", 12)).grid(column=0, columnspan=3, row=0)
tkinter.Label(constraint_frame, text="min. value",font=("calibri", 12)).grid(column=1, row=1)
tkinter.Label(constraint_frame, text="max. value",font=("calibri", 12)).grid(column=2, row=1)
tkinter.Label(constraint_frame, text="solution value",font=("calibri", 12)).grid(column=3, row=1)
for i, name in enumerate(all_scores):
    minvars[name] = tkinter.StringVar(value="")
    maxvars[name] = tkinter.StringVar(value="")
    resultvars[name] = tkinter.IntVar()

    display_name = data.to_printable(name)
    label = tkinter.Label(constraint_frame, text=display_name,font=("calibri", 12))
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
label = tkinter.Label(frame20, text="Enter the number of orbital facility slots your system has (excluding the first station):", font=("calibri", 12))
label.pack(side="left")
entry = tkinter.Entry(frame20, textvariable=orbitalfacilityslotsinput, validate="key", validatecommand=(vcmd, "%P"),width=10)
entry.pack(side="left")
entry.bind("<FocusOut>", lambda event, var=orbitalfacilityslotsinput: on_focus_out(event, var))
frame21 = tkinter.Frame(root)
frame21.pack(pady=5)
label = tkinter.Label(frame21, text="Enter the number of ground facility slots your system has:", font=("calibri", 12))
label.pack(side="left")
entry = tkinter.Entry(frame21, textvariable=groundfacilityslotsinput, validate="key", validatecommand=(vcmd, "%P"),width=10)
entry.pack(side="left")
entry.bind("<FocusOut>", lambda event, var=groundfacilityslotsinput: on_focus_out(event, var))
frame22 = tkinter.Frame(root)
frame22.pack(pady=5)
label = tkinter.Label(frame22, text="Enter the number of slots your system has that can have asteroid bases (including the first station):", font=("calibri", 12))
label.pack(side="left")
entry = tkinter.Entry(frame22, textvariable=asteroidslotsinput, validate="key", validatecommand=(vcmd, "%P"),width=10)
entry.pack(side="left")
entry.bind("<FocusOut>", lambda event, var=asteroidslotsinput: on_focus_out(event, var))
criminalinput = tkinter.BooleanVar()
checkbox = tkinter.Checkbutton(root, text="Are you okay with contraband stations being built in your system? (pirate base, criminal outpost)", variable=criminalinput, font=("calibri", 12))
checkbox.pack(pady=5)
firststationinput = tkinter.StringVar()
frame23 = tkinter.Frame(root)
frame23.pack(pady=5)
label = tkinter.Label(frame23, text="Select your first station:", font=("calibri", 12))
label.pack(side="left")
dropdown = tkinter.OptionMenu(frame23, firststationinput, *data.to_printable_list(all_categories["First Station"]))
dropdown.pack(side="left")
button = tkinter.Button(root, text="Solve for a system", command=lambda: solve())
button.pack(pady=7)
resultlabel = tkinter.Label(root, text="", font=("calibri", 12))
resultlabel.pack(pady=10)
root.mainloop()

