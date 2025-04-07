from collections import Counter
import random

import data

from_scuffed_to_edcp_dict = {
    "Starport Ocellus": "Orbis_or_Ocellus",
    "Starport Coriolis": "Coriolis",
    "Starport Asteroid": "Asteroid_Base",
    "Outpost Commercial": "Commercial_Outpost",
    "Outpost Industrial": "Industrial_Outpost",
    "Outpost Pirate": "Criminal_Outpost",
    "Outpost Civilian": "Civilian_Outpost",
    "Outpost Scientific": "Scientific_Outpost",
    "Outpost Military": "Military_Outpost",
    "Installation Satellite": "Satellite",
    "Installation Communication": "Communication_Station",
    "Installation Agricultural": "Space_Farm",
    "Installation Pirate Base": "Pirate_Base",
    "Installation Mining/Industrial": "Mining_Outpost",
    "Installation Relay": "Relay_Station",
    "Surface Outpost Civilian": "Civilian_Planetary_Outpost",
    "Surface Outpost Industrial": "Industrial_Planetary_Outpost",
    "Surface Outpost Scientific": "Scientific_Planetary_Outpost",
    "Port Large": "Planetary_Port",
    "Settlement Small Agriculture": "Small_Agricultural_Settlement",
    "Settlement Medium Agriculture": "Medium_Agricultural_Settlement",
    "Settlement Large Agriculture": "Large_Agricultural_Settlement",
    "Settlement Small Mining": "Small_Extraction_Settlement",
    "Settlement Medium Mining": "Medium_Extraction_Settlement",
    "Settlement Large Mining": "Large_Extraction_Settlement",
    "Settlement Small Industrial": "Small_Industrial_Settlement",
    "Settlement Medium Industrial": "Medium_Industrial_Settlement",
    "Settlement Large Industrial": "Large_Industrial_Settlement",
    "Settlement Small Military": "Small_Military_Settlement",
    "Settlement Medium Military": "Medium_Military_Settlement",
    "Settlement Large Military": "Large_Military_Settlement",
    "Settlement Small Bio": "Small_Scientific_Settlement",
    "Settlement Medium Bio": "Medium_Scientific_Settlement",
    "Settlement Large Bio": "Large_Scientific_Settlement",
    "Settlement Small Tourist": "Small_Tourism_Settlement",
    "Settlement Medium Tourist": "Medium_Tourism_Settlement",
    "Settlement Large Tourist": "Large_Tourism_Settlement",
    "Installation Military": "Military",
    "Installation Security": "Security_Station",
    "Installation Government": "Government",
    "Installation Medical": "Medical",
    "Installation Bar": "Space_Bar",
    "Installation Research": "Research_Station",
    "Installation Tourist": "Tourist",
    "Hub Extraction": "Extraction_Hub",
    "Hub Civilian": "Civilian_Hub",
    "Hub Exploration": "Exploration_Hub",
    "Hub Outpost": "Outpost_Hub",
    "Hub Scientific": "Scientific_Hub",
    "Hub Military": "Military_Hub",
    "Hub Refinery": "Refinery_Hub",
    "Hub High Tech": "High_Tech_Hub",
    "Hub Industrial": "Industrial_Hub",
}

scuffed_variants = {
    "Orbis_or_Ocellus": ["ocellus"],
    "Coriolis": ["no_truss", "dual_truss", "quad_truss"],
    "Asteroid_Base": ["rock", "ice"],
    "Commercial_Outpost": ["plutus"],
    "Industrial_Outpost": ["vulcan"],
    "Pirate_Base": ["dysnomia"],
    "Civilian_Outpost": ["vesta"],
    "Scientific_Outpost": ["prometheus"],
    "Military_Outpost": ["nemesis"],
    "Satellite": ["hermese", "angelia", "eirene"],
    "Communication_Station": ["pistis", "soter", "aletheia"],
    "Space_Farm": ["demeter"],
    "Pirate_Base": ["apate", "laverna"],
    "Mining_Outpost": ["euthenia", "phorcys"],
    "Relay_Station": ["enodia", "ichnaea"],
    "Military": ["vacuna", "alastor"],
    "Security_Station": ["dicaeosyne", "poena", "eunomia", "nomos"],
    "Government": ["harmonia"],
    "Medical": ["asclepius", "eupraxia"],
    "Research_Station": ["astraeus", "coeus", "dione"],
    "Tourist": ["hedone", "opora", "pasithea"],
    "Space_Bar": ["dionysus", "bachus"],
    "Civilian_Planetary_Outpost": ["hestia", "decima", "atropos", "nona", "lachesis", "clotho"],
    "Industrial_Planetary_Outpost": ["hephaestus", "opis", "ponos", "tethys", "bia", "mefitis"],
    "Scientific_Planetary_Outpost": ["necessitas", "ananke", "fauna", "providentia", "antevorta", "porrima"],
    "Planetary_Port": ["zeus", "hera", "poseidon", "aphrodite"],
    "Small_Agricultural_Settlement": ["consus"],
    "Medium_Agricultural_Settlement": ["picumnus", "annona"],
    "Large_Agricultural_Settlement": ["ceres", "fornax"],
    "Small_Extraction_Settlement": ["ourea"],
    "Medium_Extraction_Settlement": ["mantus", "orcus"],
    "Large_Extraction_Settlement": ["erebus", "aerecura"],
    "Small_Industrial_Settlement": ["fontus"],
    "Medium_Industrial_Settlement": ["metope", "palici", "minthe"],
    "Large_Industrial_Settlement": ["gaea"],
    "Small_Military_Settlement": ["ioke"],
    "Medium_Military_Settlement": ["bellona", "enyo", "polemos"],
    "Large_Military_Settlement": ["minerva"],
    "Small_Scientific_Settlement": ["pheobe"],
    "Medium_Scientific_Settlement": ["asteria", "caerus"],
    "Large_Scientific_Settlement": ["chronos"],
    "Small_Tourism_Settlement": ["aergia"],
    "Medium_Tourism_Settlement": ["comus", "gelos"],
    "Large_Tourism_Settlement": ["fufluns"],
    "Extraction_Hub": ["tartarus"],
    "Civilian_Hub": ["aegle"],
    "Exploration_Hub": ["tellus_e"],
    "Outpost_Hub": ["io"],
    "Scientific_Hub": ["athena", "caelus"],
    "Military_Hub": ["alala", "ares"],
    "Refinery_Hub": ["silenus"],
    "High_Tech_Hub": ["janus"],
    "Industrial_Hub": ["molae", "tellus_i", "eunostus"],
}

from_edcp_to_scuffed_dict = { edcp_name: scuffed_name
                              for scuffed_name, edcp_name in from_scuffed_to_edcp_dict.items() }

def from_scuffed_to_edcp(name):
    building, *_ = name.split('|')
    return from_scuffed_to_edcp_dict[building]

def from_edcp_to_scuffed(name):
    try:
        base = from_edcp_to_scuffed_dict[name]
    except KeyError:
        return f"Unknown {name}"
    variant = random.choice(scuffed_variants[name])
    return f"{base}|{variant}"

def export_ordering(ordering):
    ordering = [ from_edcp_to_scuffed(line) for line in ordering ]
    # Apparently it is not necessary to include the additional lines at the end that contain specific settings
    return "\n".join(ordering)

def import_state(main_frame, text, with_system_name=False):
    lines = text.splitlines()
    for l in lines:
        l = l.strip()
    lines = [ l for l in lines if l != "" ]
    try:
        ending_point = lines.index("-")
    except ValueError:
        ending_point = len(lines)
    try:
        converted = [ from_scuffed_to_edcp(line)
                      for line in lines[:ending_point] ]
    except KeyError as e:
        return f"Error: facility '{e}' unknown"
    if not converted:
        return "Error: no facilities found. Make sure you exported your construction list"
    first_station = converted[0]
    facilities = [ name for name in converted[1:]
                   if not data.is_port(data.all_buildings[name]) ]
    facilities = Counter(facilities)
    ports = [ name for name in converted[1:]
              if data.is_port(data.all_buildings[name]) ]

    main_frame.clear_result()
    main_frame.choose_first_station_var.set(False)
    main_frame.clear_already_built()
    main_frame.set_first_station(first_station)
    for name, nb in facilities.items():
        row = main_frame.get_row_for_building(name, include_first_station=False)
        row.already_present_var.set(nb)
    for name in ports:
        row = main_frame.add_empty_building_row(result_building=data.to_printable(name))
        row.already_present_var.set(1)

