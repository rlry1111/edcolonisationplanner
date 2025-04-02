import json
from data import all_slots, all_scores, from_printable
from tksetup import get_int_var_value

def convert_maybe(variable, default=None):
    value = variable.get()
    if value != "": return int(value)
    return default


# Creates a dictionary with the current state of the app
def extract_from_frame(main_frame, with_solution=True):
    result = {}
    result["optimize"] = data.from_printable(main_frame.maximizeinput.get())
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
