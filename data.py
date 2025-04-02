from collections import namedtuple, defaultdict

base_scores = ["initial_population_increase", "max_population_increase", "security", "tech_level", "wealth", "standard_of_living", "development_level", "construction_cost"]
compound_scores = [ "system_score_(beta)" ]
all_scores = base_scores + compound_scores

all_slots = {"space": "Orbital", "ground": "Ground", "asteroid": "Asteroid"}

# System score from https://forums.frontier.co.uk/threads/v3-of-the-colonization-construction-spreadsheet-is-now-available.635762/
def compute_compound_score(score, values):
    if score == "system_score_(beta)":
        return values["security"] + values["tech_level"] + values["wealth"] + values["standard_of_living"]

Building = namedtuple("Building", ['slot'] + base_scores + ['T2points', 'T3points', 'dependencies'],
                      defaults=(0,)*len(base_scores) + (0, 0, []))

all_buildings = {}
all_categories = defaultdict(list)

def add_building(name, *args, **kwargs):
    assert name not in all_buildings
    result = Building(*args, **kwargs)
    all_buildings[name] = result

def make_category(category_name, *building_names):
    assert category_name not in all_categories
    all_categories[category_name] = building_names

# Values from Colonization Construction Details (By DaftMav) -- https://docs.google.com/spreadsheets/d/16_hh1G6Tb66OdS01Li0955lITp7yLleb3a8dmqVqq2o/edit?usp=sharing

#            NAME                              SLOT   IP MP SEC TL  W SoL DL  cost   T2    T3
add_building("Orbis_or_Ocellus",              "space", 5, 1, -3, 6, 7,  5, 8, 209122, 0, "port")
add_building("Coriolis",                      "space", 1, 0, -2, 1, 2,  3, 2,  53723, "port", 1)
add_building("Asteroid_Base",                 "space", 1, 0, -1, 3, 5, -4, 7,  53723, "port", 1)

add_building("Commercial_Outpost",            "space", 0, 0, -1, 0, 2,  5, 0,  18988,      1, 0)
add_building("Industrial_Outpost",            "space", 0, 0,  0, 3, 0,  0, 2,  18988,      1, 0)
add_building("Criminal_Outpost",              "space", 0, 0, -2, 0, 2,  0, 0,  18988,      1, 0)
add_building("Civilian_Outpost",              "space", 0, 0, -1, 0, 1,  1, 1,  18988,      1, 0)
add_building("Scientific_Outpost",            "space", 1, 0,  0, 3, 0,  0, 0,  18988,      1, 0)
add_building("Military_Outpost",              "space", 1, 0,  2, 0, 0,  0, 0,  18988,      1, 0)

add_building("Satellite",                     "space", 0, 0,  0, 0, 1,  1, 1,   6721,      1, 0)
add_building("Communication_Station",         "space", 0, 0,  1, 3, 0,  0, 0,   6721,      1, 0)
add_building("Space_Farm",                    "space", 0, 0,  0, 0, 0,  5, 1,   6721,      1, 0)
add_building("Pirate_Base",                   "space", 0, 0, -4, 0, 3,  0, 0,   6721,      1, 0)
add_building("Mining_Outpost",                "space", 0, 0,  0, 0, 3, -2, 0,   6721,      1, 0)
add_building("Relay_Station",                 "space", 0, 0,  1, 0, 0,  0, 1,   6721,      1, 0)

add_building("Military",                      "space", 0, 0,  6, 0, 0,  0, 0,  10080,     -1, 1, dependencies=["Small_Military_Settlement", "Medium_Military_Settlement", "Large_Military_Settlement"])
add_building("Security_Station",              "space", 0, 0,  8, 0, 0,  3, 2,  10080,     -1, 1, dependencies=["Relay_Station"])
add_building("Government",                    "space", 0, 0,  2, 0, 0,  6, 2,  10080,     -1, 1)
add_building("Medical",                       "space", 0, 0,  0, 3, 0,  5, 0,  10080,     -1, 1)
add_building("Research_Station",              "space", 0, 0,  0, 8, 0,  0, 2,  10080,     -1, 1, dependencies=["Small_Scientific_Settlement", "Medium_Scientific_Settlement", "Large_Scientific_Settlement"])
add_building("Tourist",                       "space", 0, 0, -3, 0, 6,  0, 2,  10080,     -1, 1, dependencies=["Small_Tourism_Settlement", "Medium_Tourism_Settlement", "Large_Tourism_Settlement"])
add_building("Space_Bar",                     "space", 0, 0, -2, 0, 2,  3, 0,  10080,     -1, 1)

#            NAME                              SLOT   IP MP SEC TL  W SoL DL  cost   T2    T3
add_building("Civilian_Planetary_Outpost",   "ground", 2, 0, -2, 0, 0,  3, 0,  36829,      1, 0)
add_building("Industrial_Planetary_Outpost", "ground", 1, 0, -1, 0, 2,  0, 0,  36829,      1, 0)
add_building("Scientific_Planetary_Outpost", "ground", 1, 0, -1, 5, 0,  0, 1,  36829,      1, 0)
add_building("Planetary_Port",               "ground",10,10, -3, 5, 5,  6,10, 215882, 0, "port")

add_building("Extraction_Hub",               "ground", 0, 0,  0, 0,10, -4, 2,   9800,     -1, 1, dependencies=["Small_Extraction_Settlement", "Medium_Extraction_Settlement", "Large_Extraction_Settlement"])
add_building("Civilian_Hub",                 "ground", 0, 0, -3, 0, 0,  3, 2,   9800,     -1, 1, dependencies=["Small_Agricultural_Settlement", "Medium_Agricultural_Settlement", "Large_Agricultural_Settlement"])
add_building("Exploration_Hub",              "ground", 0, 0, -1, 6, 0,  0, 2,   9800,     -1, 1, dependencies=["Communication_Station"])
add_building("Outpost_Hub",                  "ground", 0, 0, -2, 0, 0,  3, 2,   9800,     -1, 1, dependencies=["Space_Farm"])
add_building("Scientific_Hub",               "ground", 0, 0,  0,10, 0,  0, 0,   9800,     -1, 1)
add_building("Military_Hub",                 "ground", 0, 0, 10, 0, 0,  0, 0,   9800,     -1, 1, dependencies=["Military"])
add_building("Refinery_Hub",                 "ground", 0, 0, -1, 3, 5, -2, 7,   9800,     -1, 1)
add_building("High_Tech_Hub",                "ground", 0, 0, -2,10,-2,  0, 0,   9800,     -1, 1)
add_building("Industrial_Hub",               "ground", 0, 0,  0, 3, 5, -4, 2,   9800,     -1, 1, dependencies=["Mining_Outpost"])

add_building("Small_Agricultural_Settlement",  "ground", standard_of_living=3, construction_cost=2840, T2points=1)
add_building("Medium_Agricultural_Settlement", "ground", standard_of_living=6, construction_cost=5690, T2points=1)
add_building("Large_Agricultural_Settlement",  "ground", standard_of_living=10, construction_cost=8530, T2points=-1, T3points=2)

add_building("Small_Extraction_Settlement",  "ground", wealth=2, construction_cost=2840, T2points=1)
add_building("Medium_Extraction_Settlement", "ground", wealth=5, construction_cost=5690, T2points=1)
add_building("Large_Extraction_Settlement",  "ground", tech_level=1, wealth=7, standard_of_living=-2, construction_cost=8530, T2points=-1, T3points=2)

add_building("Small_Industrial_Settlement",  "ground", development_level=2, construction_cost=2840, T2points=1)
add_building("Medium_Industrial_Settlement", "ground", development_level=5, construction_cost=5690, T2points=1)
add_building("Large_Industrial_Settlement",  "ground", development_level=8, wealth=2, construction_cost=8530, T2points=-1, T3points=2)

add_building("Small_Military_Settlement",  "ground", security=2, construction_cost=2840, T2points=1)
add_building("Medium_Military_Settlement", "ground", security=4, construction_cost=5690, T2points=1)
add_building("Large_Military_Settlement",  "ground", security=6, development_level=2, construction_cost=8530, T2points=-1, T3points=2)

add_building("Small_Scientific_Settlement",  "ground", tech_level=3, development_level=1, construction_cost=2840, T2points=-1, T3points=1)
add_building("Medium_Scientific_Settlement", "ground", tech_level=6, development_level=1, construction_cost=5690, T2points=-1, T3points=1)
add_building("Large_Scientific_Settlement",  "ground", tech_level=10, development_level=2, construction_cost=8530, T2points=-1, T3points=2)

add_building("Small_Tourism_Settlement",  "ground", security=-1, wealth=1, construction_cost=2840, T2points=-1, T3points=1, dependencies=["Satellite"])
add_building("Medium_Tourism_Settlement", "ground", security=-1, wealth=2, construction_cost=5690, T2points=-1, T3points=1, dependencies=["Satellite"])
add_building("Large_Tourism_Settlement",  "ground", security=-1, wealth=5, construction_cost=8530, T2points=-1, T3points=2, dependencies=["Satellite"])

# Categories
make_category("All", *all_buildings.keys())
make_category("First Station", "Orbis_or_Ocellus", "Coriolis", "Asteroid_Base", "Commercial_Outpost", "Industrial_Outpost", "Criminal_Outpost", "Civilian_Outpost", "Scientific_Outpost", "Military_Outpost")
make_category("Space", *(n for n, b in all_buildings.items() if b.slot == "space"))
make_category("Ground", *(n for n, b in all_buildings.items() if b.slot == "ground"))
make_category("T1", *(n for n, b in all_buildings.items() if b.T2points != "port" and b.T2points > 0))
make_category("T2", *(n for n, b in all_buildings.items() if b.T2points == "port" or b.T2points < 0))
make_category("T3", *(n for n, b in all_buildings.items() if b.T3points == "port" or b.T3points < 0))
make_category("Star/Ground Port", "Orbis_or_Ocellus", "Coriolis", "Asteroid_Base", "Civilian_Planetary_Outpost", "Industrial_Planetary_Outpost", "Scientific_Planetary_Outpost", "Planetary_Port")
make_category("Installation", "Satellite", "Communication_Station", "Space_Farm", "Pirate_Base", "Mining_Outpost", "Relay_Station", "Military", "Security_Station", "Government", "Medical", "Research_Station", "Tourist", "Space_Bar")
make_category("Hub", *(n for n in all_buildings.keys() if n.endswith("Hub")))
make_category("Small Settlement", *(n for n in all_buildings.keys() if n.endswith("Settlement") and n.startswith("Small")))
make_category("Medium Settlement", *(n for n in all_buildings.keys() if n.endswith("Settlement") and n.startswith("Medium")))
make_category("Large Settlement", *(n for n in all_buildings.keys() if n.endswith("Settlement") and n.startswith("Large")))


def is_port(building):
    return building.T2points == "port" or building.T3points == "port"

def to_printable(name):
    return name.replace("_", " ")

def to_printable_list(names):
    return [ to_printable(name) for name in names ]

def from_printable(display_name):
    return display_name.replace(" ", "_")

# Solution defined as a dictionary Building_Name to number of buildings
def print_scores(solution):
    values = {}
    for score in base_scores:
        value = sum(getattr(all_buildings[b], score) * nb for b, nb in solution.items())
        values[score] = value
        print(score, value)
    for score in compound_scores:
        values[score] = compute_compound_score(score, values)
        print(score, values[score])

    print(sum(all_buildings[b].T2points * nb for b, nb in solution.items() if all_buildings[b].T2points != "port"))
    print(sum(all_buildings[b].T3points * nb for b, nb in solution.items() if all_buildings[b].T3points != "port"))
