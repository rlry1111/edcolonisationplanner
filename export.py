import json
from data import all_slots, all_scores, all_buildings, from_printable, to_printable, compute_all_scores, is_port, ConstructionPointsCounter
from tksetup import get_int_var_value
from collections import defaultdict, Counter

def convert_maybe(variable, default=None):
    value = variable.get()
    if value != "": return int(value)
    return default

def maybe_add(result, name, value):
    if value is not None:
        result[name] = value

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

    def load_plan(self, system, plan, main_frame, with_solution=False):
        try:
            result = self.contents[system][plan]
        except KeyError as e:
            self.warnings = f"Unknown system or plan '{e}'"
        import_into_frame(main_frame, result)
        if with_solution:
            import_solution_into_frame(main_frame, result)

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
    result["advanced_objective"] = main_frame.advancedobjective.get()
    if main_frame.advancedobjective.get():
        result["direction_input"] = main_frame.direction_input.get()
        result["objective_input"] = main_frame.objectiveinput.get()
        result["advanced_objective_value"] = main_frame.adv_solution_value_var.get()
    else:
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
        result["already_present"] = ap = defaultdict(int)
        result["already_present.ports"] = app = []
        result["first_station"] = main_frame.building_input[0].building_name
        for row in main_frame.building_input[1:]:
            if not row.valid:
                continue
            building_name = row.building_name
            already_present = row.already_present
            if already_present:
                if row.is_port:
                    app.append( (building_name, already_present) )
                else:
                    ap[building_name] = ap[building_name] + already_present

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
            building_name = row.building_name
            if building_name in bc:
                combined = combine_building_constraints(extracted, bc[building_name])
                bc[building_name] = combined
            else:
                bc[building_name] = extracted

    if not with_solution:
        return result

    result["solution"] = solution = {}
    if main_frame.choose_first_station_var.get():
        solution["first_station"] = main_frame.building_input[0].building_name
    solution["to_build"] = rs = {}
    for row in main_frame.building_input:
        if not row.valid:
            continue
        if main_frame.choose_first_station_var.get() and row.first_station:
            continue
        to_build = get_int_var_value(row.to_build_var)
        if to_build:
            rs[row.building_name] = to_build

    if main_frame.port_order:
        solution["port_order"] = main_frame.port_order

    return result

def extract_min_max_from_variables(minvar, maxvar):
    min_value = convert_maybe(minvar)
    max_value = convert_maybe(maxvar)
    if min_value is None and max_value is None:
        return None
    result = {}
    maybe_add(result, "min", min_value)
    maybe_add(result, "max", max_value)
    return result

def extract_score_from_frame(main_frame, score):
    return extract_min_max_from_variables(main_frame.minvars[score], main_frame.maxvars[score])

def extract_building_constraint_from_row(row):
    return extract_min_max_from_variables(row.at_least_var, row.at_most_var)

def combine_building_constraints(first, second):
    def combine(v1, v2, combiner=min):
        if v1 is None:
            return v2
        if v2 is None:
            return v1
        return combiner(v1, v2)
    result = {}
    min_value = combine(first.get("min"), second.get("min"), max) ## Keep the strongest constraint
    max_value = combine(first.get("max"), second.get("max"), min) ## Keep the strongest constraint
    maybe_add(result, "min", min_value)
    maybe_add(result, "max", max_value)
    return result


# This will ignore the solution, only imports the initial state and constraints
def import_into_frame(main_frame, result):
    main_frame.clear_all()
    main_frame.advancedobjective.set(result.get("advanced_objective", False))
    main_frame.direction_input.set(result.get("direction_input", False))
    main_frame.objectiveinput.set(result.get("objective_input", ""))
    main_frame.adv_solution_value_var.set(result.get("advanced_objective_value", 0))
    main_frame.maximizeinput.set(to_printable(result.get("optimize", "")))
    for score, constraints in result.get("score_constraints", {}).items():
        if "min" in constraints:
            main_frame.minvars[score].set(constraints["min"])
        if "max" in constraints:
            main_frame.maxvars[score].set(constraints["max"])

    if "slots_available" in result:
        main_frame.on_toggle_slot_input("fix_available")
        for slot in all_slots:
            main_frame.available_slots_currently_vars[slot].set(result["slots_available"].get(slot, 0))
    else:
        st = result.get("slots_total", {})
        main_frame.on_toggle_slot_input("fix_total")
        for slot in all_slots:
            main_frame.total_slots_currently_vars.set(st.get(slot, 0))
    main_frame.criminalinput.set(result.get("contraband_allowed", False))

    for building_name, constraints in result.get("building_constraints", {}).items():
        row = main_frame.get_row_for_building(building_name)
        if "min" in constraints:
            row.at_least_var.set(constraints["min"])
        if "max" in constraints:
            row.at_most_var.set(constraints["max"])

    if result.get("initial_state", "list") == "automatic":
        fsc = result.get("first_station_constraints", {})
        main_frame.choose_first_station_var.set(True)
        main_frame.first_station_cb_coriolis_var.set(fsc.get("coriolis", True))
        main_frame.first_station_cb_asteroid_var.set(fsc.get("asteroid", True))
        main_frame.first_station_cb_orbis_var.set(fsc.get("orbis", True))
    else:
        main_frame.choose_first_station_var.set(False)
        for building_name, already_present in result.get("already_present", {}).items():
            row = main_frame.add_empty_building_row(result_building=to_printable(building_name))
            row.already_present_var.set(already_present)
        for building_name, already_present in result.get("already_present.ports", []):
            row = main_frame.add_empty_building_row(result_building=to_printable(building_name))
            row.already_present_var.set(already_present)
        main_frame.building_input[0].name_var.set(to_printable(result.get("first_station", "Pick_your_first_station")))

    if "manual_construction_points" in result:
        main_frame.auto_construction_points.set(False)
        mcp = result["manual_construction_points"]
        main_frame.T2points_variable.set(mcp.get("T2", 0))
        main_frame.T3points_variable.set(mcp.get("T3", 0))
    else:
        main_frame.auto_construction_points.set(True)

    if main_frame.building_input[-1].valid:
        main_frame.add_empty_building_row()

# Uses result["solution"]
# Assumes that the current state of main_frame is consistent with the rest of the contents of result
# TODO: if there is a benefit, compute everything from result without relying on main_frame to be consistent
def import_solution_into_frame(main_frame, result):
    main_frame.clear_result()
    solution = result.get("solution", {})
    to_build = solution.get("to_build", {})
    first_station_name = solution.get("first_station", None)
    if not to_build and not first_station_name:
        return
    for building_name, nb in to_build.items():
        result_row = main_frame.get_row_for_building(building_name)
        result_row.set_build_result(nb)

    port_order = solution.get("port_order", [])
    if port_order:
        main_frame.set_port_ordering(port_order)

    # Need to combine solution with already present buildings to compute total scores
    already_present = result.get("already_present", {})
    port_order = result.get("already_present.ports", [])
    first_station = {}
    if first_station_name:
        first_station = {first_station_name: 1}
    elif result["first_station"]:
        first_station = {result["first_station"]: 1}
    already_present = combine_solutions(already_present, first_station,
                                        count_ports_from_port_order(port_order))
    complete_system = combine_solutions(to_build, already_present)

    # Compute scores, except for construction cost which does not count already present buildings
    scores = compute_all_scores(complete_system)
    partial_scores = compute_all_scores(to_build)
    scores["construction_cost"] = partial_scores["construction_cost"]
    for score, value in scores.items():
        main_frame.resultvars[score].set(value)

    # Count available slots
    for slot in all_slots:
        available = main_frame.available_slots_currently_vars[slot].get()
        if slot == "asteroid":
            used = to_build.get("Asteroid_Base", 0)
        else:
            used = sum(nb_built for building_name, nb_built in to_build.items()
                       if all_buildings[building_name].slot == slot)
        main_frame.available_slots_after_vars[slot].set(available - used)

    # Count construction points.
    nb_ports_already_present = sum(is_port(all_buildings[name]) * nb
                                   for name, nb in result.get("already_present", {}).items())
    construction_points = ConstructionPointsCounter(nb_ports_already_present)
    construction_points.T2points = main_frame.T2points_variable.get()
    construction_points.T3points = main_frame.T3points_variable.get()
    if first_station_name:
        if first_station_name != 'Let_the_program_choose_for_me':
            construction_points.add_building(all_buildings[first_station_name], 1, first_station=True)
    for name, nb in to_build.items():
        construction_points.add_building(all_buildings[name], nb)
    main_frame.T2points_variable_after.set(construction_points.T2points)
    main_frame.T3points_variable_after.set(construction_points.T3points)

    # Set First Station if it is specified
    if first_station_name:
        main_frame.building_input[0].name_var.set(to_printable(first_station_name))
        main_frame.building_input[0].set_build_result(1)

    if main_frame.building_input[-1].valid:
        main_frame.add_empty_building_row()

def combine_solutions(*solutions):
    result = sum((Counter(solution) for solution in solutions), Counter())
    return dict(result)

def count_ports_from_port_order(port_order):
    result = Counter()
    for name, value in port_order:
        result[name] += value
    return dict(result)
