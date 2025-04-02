import json
from data import all_slots, all_scores, from_printable, to_printable
from tksetup import get_int_var_value

def convert_maybe(variable, default=None):
    value = variable.get()
    if value != "": return int(value)
    return default


class SaveFile:
    def __init__(self, filename):
        self.filename = filename
        self.contents = {}
        self.warnings = ""
        try:
            with open(filename, "r") as fp:
                self.contents.update(json.load(fp))
        except Exception as e:
            self.warnings = f"Could not load from '{filename}': {e}"

    def get_warnings(self):
        res = self.warnings
        self.warnings = ""
        return res

    def get_system_list(self):
        return list(self.contents.keys())

    def get_plan_list(self, system):
        if system not in self.contents:
            return []
        return list(self.contents[system].keys())

    def load_plan(self, system, plan, main_frame):
        try:
            result = self.contents[system][plan]
        except KeyError as e:
            self.warnings = f"Unknown system or plan '{e}'"
        import_into_frame(main_frame, result)
        # if "solution" in result:
        #     import_solution_into_frame(main_frame, result)

    def save_plan(self, system, plan, main_frame):
        result = extract_from_frame(main_frame)
        if system not in self.contents:
            self.contents[system] = {}
        self.contents[system][plan] = result
        self.dump()

    def dump(self):
        with open(self.filename, "w") as fp:
            json.dump(self.contents, fp, indent=2)

# Creates a dictionary with the current state of the app
def extract_from_frame(main_frame, with_solution=True):
    result = {}
    result["optimize"] = from_printable(main_frame.maximizeinput.get())
    result["score_constraints"] = {}
    for score in all_scores:
        extracted = extract_score_from_frame(main_frame, score)
        if extracted is not None:
            result["score_constraints"][score] = extracted
    if main_frame.slot_behavior == "fix_available":
        result["slots_available"] = sa = {}
        for slot in all_slots:
            sa[slot] = get_int_var_value(main_frame.available_slots_currently_vars[slot])
    else:
        result["slots_total"] = sa = {}
        for slot in all_slots:
            sa[slot] = get_int_var_value(main_frame.total_slots_currently_vars[slot])
    result["contraband_allowed"] = main_frame.criminalinput.get()

    if main_frame.choose_first_station_var.get():
        result["initial_state"] = "automatic"
        result["first_station_constraints"] = fsc = {}
        fsc["coriolis"] = main_frame.first_station_cb_coriolis_var.get()
        fsc["asteroid"] = main_frame.first_station_cb_asteroid_var.get()
        fsc["orbis"] = main_frame.first_station_cb_orbis_var.get()
    else:
        result["initial_state"] = "list"
        result["already_present"] = ap = {}
        result["first_station"] = main_frame.building_input[0].building_name
        for row in main_frame.building_input[1:]:
            if not row.valid:
                continue
            building_name = row.building_name
            already_present = row.already_present
            if already_present:
                ap[building_name] = already_present

    if not main_frame.auto_construction_points.get():
        result["manual_construction_points"] = mcp = {}
        mcp["T2"] = get_int_var_value(main_frame.T2points_variable)
        mcp["T3"] = get_int_var_value(main_frame.T3points_variable)

    result["building_constraints"] = bc = {}
    for row in main_frame.building_input:
        if not row.valid:
            continue
        extracted = extract_building_constraint_from_row(row)
        if extracted is not None:
            bc[row.building_name] = extracted

    if not with_solution:
        return result
    
    result["solution"] = rs = {}
    for row in main_frame.building_input:
        if not row.valid:
            continue
        to_build = get_int_var_value(row.to_build_var)
        if to_build:
            rs[row.building_name] = to_build

    if main_frame.port_order:
        result["solution.port_order"] = main_frame.port_order

    return result

def extract_score_from_frame(main_frame, score):
    min_value = convert_maybe(main_frame.minvars[score])
    max_value = convert_maybe(main_frame.maxvars[score])
    if min_value is None and max_value is None:
        return None
    result = {}
    if min_value is not None:
        result["min"] = min_value
    if max_value is not None:
        result["max"] = max_value
    return result

def extract_building_constraint_from_row(row):
    min_value = convert_maybe(row.at_least_var)
    max_value = convert_maybe(row.at_most_var)
    if min_value is None and max_value is None:
        return None
    result = {}
    if min_value is not None:
        result["min"] = min_value
    if max_value is not None:
        result["max"] = max_value
    return result

# This will ignore the solution, only imports the initial state and constraints
def import_into_frame(main_frame, result):
    main_frame.clear_all()

    main_frame.maximizeinput.set(to_printable(result["optimize"]))
    for score, constraints in result["score_constraints"].items():
        if "min" in constraints:
            main_frame.minvars[score].set(constraints["min"])
        if "max" in constraints:
            main_frame.maxvars[score].set(constraints["max"])

    if "slots_available" in result:
        main_frame.on_toggle_slot_input("fix_available")
        for slot in all_slots:
            main_frame.available_slots_currently_vars[slot].set(result["slots_available"][slot])
    else:
        main_frame.on_toggle_slot_input("fix_total")
        for slot in all_slots:
            main_frame.total_slots_currently_vars.set(result["slots_total"][slot])
    main_frame.criminalinput.set(result["contraband_allowed"])

    for building_name, constraints in result["building_constraints"].items():
        row = main_frame.get_row_for_building(building_name)
        if "min" in constraints:
            row.at_least_var.set(constraints["min"])
        if "max" in constraints:
            row.at_most_var.set(constraints["max"])

    if result["initial_state"] == "automatic":
        fsc = result["first_station_constraints"]
        main_frame.choose_first_station_var.set(True)
        main_frame.first_station_cb_coriolis_var.set(fsc["coriolis"])
        main_frame.first_station_cb_asteroid_var.set(fsc["asteroid"])
        main_frame.first_station_cb_orbis_var.set(fsc["orbis"])
    else:
        main_frame.choose_first_station_var.set(False)
        for building_name, already_present in result["already_present"].items():
            row = main_frame.add_empty_building_row(result_building=to_printable(building_name))
            row.already_present_var.set(already_present)
        main_frame.building_input[0].name_var.set(to_printable(result["first_station"]))

    if "manual_construction_points" in result:
        main_frame.auto_construction_points.set(False)
        mcp = result["manual_construction_points"]
        main_frame.T2points_variable.set(mcp["T2"])
        main_frame.T3points_variable.set(mcp["T3"])
    else:
        main_frame.auto_construction_points.set(True)

    main_frame.add_empty_building_row()
