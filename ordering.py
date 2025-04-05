from collections import Counter

import data
import extract


def get_tier(building_name):
    building = data.all_buildings[building_name]
    if building.T3points == "port" or building.T3points < 0:
        return 3
    if building.T2points == "port" or building.T2points < 0:
        return 2
    return 1

def find_first_index(elts, predicate):
    for i, e in enumerate(elts):
        if predicate(e):
            return i
    return None

# facilities is a dict (building_name, nb_buildings).
# ports is a list of building_names (possibly with repetitions)
# first_station is a building_name or None
# Can come from result["already_present"] or result["solution"]["to_build"]
def compute_feasible_order(state, facilities, ports, first_station=None):
    result = []
    if first_station:
        state.add_first_station(first_station)
        result.append(first_station)

    elements = list(Counter(facilities).elements())
    required_dependencies = set( tuple(data.all_buildings[name].dependencies)
                                 for name in facilities.keys()
                                 if data.all_buildings[name].dependencies )
    total_nb_buildings = len(elements) + len(ports)
    dependency_unlockers = []
    for dep in required_dependencies:
        idx = find_first_index(elements, lambda name: name in dep)
        if idx:
            dependency_unlockers.append(elements[idx])
            del elements[idx]
        else:
            print("CFO: Could not find unlocker for", dep, "in", elements)

    by_tiers = {1: [], 2: []}
    for name in elements:
        by_tiers[get_tier(name)].append(name)

    def insert_building(name):
        nonlocal total_nb_buildings
        state.add_building(name, 1)
        result.append(name)
        total_nb_buildings -= 1

    def build_first_from_list(building_names):
        idx = find_first_index(building_names, state.can_build)
        if idx is not None:
            insert_building(building_names[idx])
            del building_names[idx]
            return True
        return False
        
    while total_nb_buildings > 0:
        if build_first_from_list(dependency_unlockers):
            continue
        if ports:
            next_port = ports[0]
            if state.can_build(next_port):
                insert_building(next_port)
                del ports[0]
                continue
            target_tier = get_tier(next_port) - 1
        else:
            target_tier = 2
        if build_first_from_list(by_tiers[target_tier]):
            continue
        if build_first_from_list(by_tiers[3 - target_tier]):
            continue
        print("CFO: Remains", total_nb_buildings, dependency_unlockers, ports, by_tiers)
        print("CFO: State", state.T2points, state.T3points, state.dependencies_locked)
        t = by_tiers[1][0]
        bt = data.all_buildings[t]
        print("CFO: CB", t, state.can_build(t), state._construction_points(bt, 1), bt.dependencies)
        raise RuntimeError("Could not finish ordering")

    return result

def get_ordering_from_result(result, with_solution=True, with_already_present=True):
    ordering = []
    state = data.SystemState()
    if with_already_present:
        first_station = result.get("first_station", None)
        if first_station not in data.all_buildings:
            first_station = None
        facilities = result.get("already_present", {})
        ports_multiple = result.get("already_present.ports", [])
        ports = []
        for name, nb in ports_multiple:
            ports.extend([name] * nb)
        ordering.extend(compute_feasible_order(state, facilities, ports, first_station))
    else:
        state.add_result(result)

    if with_solution:
        solution = result.get("solution", {})
        first_station = solution.get("first_station", None)
        if first_station not in data.all_buildings:
            first_station = None
        facilities = solution.get("to_build", {})
        ports = solution.get("port_order", [])
        if ports:
            facilities = { name: nb for name, nb in facilities.items()
                           if not data.is_port(data.all_buildings[name]) }
        ordering.extend(compute_feasible_order(state, facilities, ports, first_station))

    return ordering
